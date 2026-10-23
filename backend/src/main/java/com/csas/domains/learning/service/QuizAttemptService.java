package com.csas.domains.learning.service;

import com.csas.common.exception.ApiException;
import com.csas.domains.learning.dto.AttemptRequest;
import com.csas.domains.learning.dto.AttemptResultResponse;
import com.csas.domains.learning.dto.SourceResponse;
import com.csas.domains.quiz.dto.QuizResponse;
import com.csas.domains.quiz.service.QuizCatalogService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
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
  private final ObjectMapper mapper;

  public QuizAttemptService(JdbcTemplate jdbc, QuizCatalogService quizzes, ObjectMapper mapper) {
    this.jdbc = jdbc;
    this.quizzes = quizzes;
    this.mapper = mapper;
  }

  @Transactional
  public AttemptResultResponse submit(
      UUID userId, UUID quizId, UUID idempotencyKey, AttemptRequest request) {
    String requestHash = hash(quizId, request);
    jdbc.query(
        "SELECT pg_advisory_xact_lock(hashtextextended(?,0))", rs -> {}, userId + ":" + quizId);
    AttemptRow replay = findByKey(userId, idempotencyKey);
    if (replay != null) {
      return replay(userId, replay, requestHash);
    }

    QuizRow quiz = loadQuiz(userId, quizId);
    OptionRow selected = loadOption(quizId, request.selected_option_id());
    OptionRow correct = loadCorrectOption(quizId);
    validateRetry(userId, quizId, request.retry_of_attempt_id());
    String quizSnapshot = json(quizzes.get(userId, quizId));
    String evidenceSnapshot = json(evidence(quizId));
    UUID attemptId = UUID.randomUUID();
    Instant submittedAt = Instant.now();
    List<UUID> inserted =
        jdbc.query(
            """
            INSERT INTO csas.quiz_attempts(
              id, user_id, quiz_id, selected_option_id, correct_option_id, is_correct,
              explanation_snapshot, source_url_snapshot, submitted_at, idempotency_key,
              request_hash, retry_of_attempt_id, quiz_snapshot, evidence_snapshot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?::jsonb, ?::jsonb)
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
            request.retry_of_attempt_id(),
            quizSnapshot,
            evidenceSnapshot);
    if (inserted.isEmpty()) {
      return replay(userId, findRequiredByKey(userId, idempotencyKey), requestHash);
    }
    updateReview(userId, quizId, attemptId, selected.isCorrect(), submittedAt);
    return result(userId, findRequiredByKey(userId, idempotencyKey));
  }

  private void updateReview(UUID user, UUID quiz, UUID attempt, boolean correct, Instant at) {
    if (correct) {
      jdbc.update(
          "UPDATE csas.review_states SET status='RESOLVED',latest_attempt_id=?,last_reviewed_at=? WHERE user_id=? AND quiz_id=?",
          attempt,
          Timestamp.from(at),
          user,
          quiz);
    } else {
      jdbc.update(
          """
        INSERT INTO csas.review_states(user_id,quiz_id,status,latest_attempt_id,first_wrong_at,last_wrong_at)
        VALUES (?,?,'NEEDS_REVIEW',?,?,?)
        ON CONFLICT (user_id,quiz_id) DO UPDATE SET status='NEEDS_REVIEW',latest_attempt_id=excluded.latest_attempt_id,
          last_wrong_at=excluded.last_wrong_at,last_reviewed_at=excluded.last_wrong_at
        """,
          user,
          quiz,
          attempt,
          Timestamp.from(at),
          Timestamp.from(at));
    }
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
                   explanation_snapshot, submitted_at, request_hash, quiz_snapshot, evidence_snapshot
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
                    rs.getString("request_hash"),
                    rs.getString("quiz_snapshot"),
                    rs.getString("evidence_snapshot")),
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
        read(row.quizSnapshot(), QuizResponse.class),
        row.selectedOptionId(),
        row.correctOptionId(),
        row.isCorrect(),
        row.explanation(),
        sources(row.evidenceSnapshot()),
        row.submittedAt());
  }

  public AttemptResultResponse get(UUID userId, UUID attemptId) {
    var rows =
        jdbc.query(
            """
        SELECT id, quiz_id, selected_option_id, correct_option_id, is_correct,
               explanation_snapshot, submitted_at, request_hash, quiz_snapshot, evidence_snapshot
          FROM csas.quiz_attempts WHERE id=? AND user_id=?
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
                    rs.getString("request_hash"),
                    rs.getString("quiz_snapshot"),
                    rs.getString("evidence_snapshot")),
            attemptId,
            userId);
    if (rows.isEmpty()) {
      throw new ApiException(404, "RESOURCE_NOT_FOUND", "Attempt not found.");
    }
    return result(userId, rows.getFirst());
  }

  private String json(Object value) {
    try {
      return mapper.writeValueAsString(value);
    } catch (java.io.IOException ex) {
      throw new IllegalStateException("Snapshot serialization failed", ex);
    }
  }

  private <T> T read(String value, Class<T> type) {
    try {
      return mapper.readValue(value, type);
    } catch (java.io.IOException ex) {
      throw new IllegalStateException("Stored snapshot is invalid", ex);
    }
  }

  private List<SourceResponse> sources(String value) {
    try {
      return mapper.readValue(value, new TypeReference<List<SourceResponse>>() {});
    } catch (java.io.IOException ex) {
      throw new IllegalStateException("Stored evidence is invalid", ex);
    }
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
      String requestHash,
      String quizSnapshot,
      String evidenceSnapshot) {}
}
