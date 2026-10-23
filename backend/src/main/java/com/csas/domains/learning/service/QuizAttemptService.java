package com.csas.domains.learning.service;

import com.csas.common.exception.ApiException;
import com.csas.domains.learning.dto.AttemptRequest;
import com.csas.domains.learning.dto.AttemptResultResponse;
import com.csas.domains.learning.dto.SourceResponse;
import com.csas.domains.quiz.service.QuizCatalogService;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class QuizAttemptService {
  private final JdbcTemplate jdbc;
  private final QuizCatalogService quizzes;

  public QuizAttemptService(JdbcTemplate jdbc, QuizCatalogService quizzes) {
    this.jdbc = jdbc;
    this.quizzes = quizzes;
  }

  @Transactional
  public AttemptResultResponse submit(
      UUID userId, UUID quizId, UUID idempotencyKey, AttemptRequest request) {
    String requestHash = hash(quizId, request);
    AttemptRow replay = findByKey(userId, idempotencyKey);
    if (replay != null) {
      return replay(userId, replay, requestHash);
    }

    QuizRow quiz = loadQuiz(userId, quizId);
    OptionRow selected = loadOption(quizId, request.selected_option_id());
    OptionRow correct = loadCorrectOption(quizId);
    validateRetry(userId, quizId, request.retry_of_attempt_id());
    UUID attemptId = UUID.randomUUID();
    Instant submittedAt = Instant.now();
    List<UUID> inserted =
        jdbc.query(
            """
            INSERT INTO csas.quiz_attempts(
              id, user_id, quiz_id, selected_option_id, correct_option_id, is_correct,
              explanation_snapshot, source_url_snapshot, submitted_at, idempotency_key,
              request_hash, retry_of_attempt_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (user_id, idempotency_key) DO NOTHING
            RETURNING id
            """,
            (rs, row) -> rs.getObject(1, UUID.class),
            attemptId,
            userId,
            quizId,
            selected.id(),
            correct.id(),
            selected.isCorrect(),
            quiz.explanation(),
            quiz.sourceUrl(),
            Timestamp.from(submittedAt),
            idempotencyKey,
            requestHash,
            request.retry_of_attempt_id());
    if (inserted.isEmpty()) {
      return replay(userId, findRequiredByKey(userId, idempotencyKey), requestHash);
    }
    return result(userId, findRequiredByKey(userId, idempotencyKey));
  }

  private QuizRow loadQuiz(UUID userId, UUID quizId) {
    var rows =
        jdbc.query(
            """
            SELECT status, explanation, source_url
              FROM csas.quizzes
             WHERE id=? AND (origin='CURATED' OR owner_user_id=?)
             FOR SHARE
            """,
            (rs, row) ->
                new QuizRow(
                    rs.getString("status"),
                    rs.getString("explanation"),
                    rs.getString("source_url")),
            quizId,
            userId);
    if (rows.isEmpty() || "DRAFT".equals(rows.getFirst().status())) {
      throw new ApiException(404, "QUIZ_NOT_FOUND", "Quiz not found.");
    }
    if ("RETIRED".equals(rows.getFirst().status())) {
      throw new ApiException(409, "QUIZ_RETIRED", "Quiz is retired.");
    }
    return rows.getFirst();
  }

  private OptionRow loadOption(UUID quizId, UUID optionId) {
    var rows =
        jdbc.query(
            "SELECT id, is_correct FROM csas.quiz_options WHERE quiz_id=? AND id=?",
            (rs, row) -> new OptionRow(rs.getObject("id", UUID.class), rs.getBoolean("is_correct")),
            quizId,
            optionId);
    if (rows.isEmpty()) {
      throw new ApiException(400, "INVALID_OPTION", "Option does not belong to quiz.");
    }
    return rows.getFirst();
  }

  private OptionRow loadCorrectOption(UUID quizId) {
    return jdbc.queryForObject(
        "SELECT id, is_correct FROM csas.quiz_options WHERE quiz_id=? AND is_correct",
        (rs, row) -> new OptionRow(rs.getObject("id", UUID.class), true),
        quizId);
  }

  private void validateRetry(UUID userId, UUID quizId, UUID retryId) {
    if (retryId == null) {
      return;
    }
    Integer count =
        jdbc.queryForObject(
            "SELECT count(*) FROM csas.quiz_attempts WHERE id=? AND user_id=? AND quiz_id=?",
            Integer.class,
            retryId,
            userId,
            quizId);
    if (count == null || count == 0) {
      throw new ApiException(404, "RESOURCE_NOT_FOUND", "Resource not found.");
    }
  }

  private AttemptRow findByKey(UUID userId, UUID key) {
    var rows =
        jdbc.query(
            """
            SELECT id, quiz_id, selected_option_id, correct_option_id, is_correct,
                   explanation_snapshot, submitted_at, request_hash
              FROM csas.quiz_attempts WHERE user_id=? AND idempotency_key=?
            """,
            (rs, row) ->
                new AttemptRow(
                    rs.getObject("id", UUID.class),
                    rs.getObject("quiz_id", UUID.class),
                    rs.getObject("selected_option_id", UUID.class),
                    rs.getObject("correct_option_id", UUID.class),
                    rs.getBoolean("is_correct"),
                    rs.getString("explanation_snapshot"),
                    rs.getTimestamp("submitted_at").toInstant(),
                    rs.getString("request_hash")),
            userId,
            key);
    return rows.isEmpty() ? null : rows.getFirst();
  }

  private AttemptRow findRequiredByKey(UUID userId, UUID key) {
    AttemptRow row = findByKey(userId, key);
    if (row == null) {
      throw new IllegalStateException("Idempotent insert conflict without stored attempt");
    }
    return row;
  }

  private AttemptResultResponse replay(UUID userId, AttemptRow row, String requestHash) {
    if (!row.requestHash().equals(requestHash)) {
      throw new ApiException(409, "IDEMPOTENCY_CONFLICT", "Idempotency key was reused.");
    }
    return result(userId, row);
  }

  private AttemptResultResponse result(UUID userId, AttemptRow row) {
    return new AttemptResultResponse(
        row.id(),
        quizzes.getForRecordedAttempt(userId, row.quizId()),
        row.selectedOptionId(),
        row.correctOptionId(),
        row.isCorrect(),
        row.explanation(),
        evidence(row.quizId()),
        row.submittedAt());
  }

  private List<SourceResponse> evidence(UUID quizId) {
    return jdbc.query(
        "SELECT * FROM csas.quiz_evidence WHERE quiz_id=? ORDER BY ordinal",
        (rs, row) ->
            new SourceResponse(
                rs.getString("source_id"),
                rs.getString("document_id"),
                rs.getString("revision"),
                rs.getString("chunk_id"),
                rs.getString("index_version"),
                rs.getString("title"),
                rs.getString("url"),
                rs.getString("locator"),
                rs.getString("evidence_text"),
                rs.getString("category"),
                rs.getString("technology_version")),
        quizId);
  }

  private String hash(UUID quizId, AttemptRequest request) {
    String normalized =
        quizId
            + ":"
            + request.selected_option_id()
            + ":"
            + String.valueOf(request.retry_of_attempt_id());
    try {
      return HexFormat.of()
          .formatHex(
              MessageDigest.getInstance("SHA-256")
                  .digest(normalized.getBytes(StandardCharsets.UTF_8)));
    } catch (NoSuchAlgorithmException ex) {
      throw new IllegalStateException("SHA-256 unavailable", ex);
    }
  }

  private record QuizRow(String status, String explanation, String sourceUrl) {}

  private record OptionRow(UUID id, boolean isCorrect) {}

  private record AttemptRow(
      UUID id,
      UUID quizId,
      UUID selectedOptionId,
      UUID correctOptionId,
      boolean isCorrect,
      String explanation,
      Instant submittedAt,
      String requestHash) {}
}
