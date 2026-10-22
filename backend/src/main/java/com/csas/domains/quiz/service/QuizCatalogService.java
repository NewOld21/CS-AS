package com.csas.domains.quiz.service;

import com.csas.common.exception.ApiException;
import com.csas.domains.quiz.dto.CategoryResponse;
import com.csas.domains.quiz.dto.QuizOptionResponse;
import com.csas.domains.quiz.dto.QuizPageResponse;
import com.csas.domains.quiz.dto.QuizResponse;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class QuizCatalogService {
  private static final Set<String> CATEGORIES =
      Set.of(
          "OPERATING_SYSTEM",
          "NETWORK",
          "DATABASE",
          "DATA_STRUCTURE",
          "ALGORITHM",
          "COMPUTER_ARCHITECTURE");
  private static final Set<String> DIFFICULTIES = Set.of("EASY", "MEDIUM", "HARD");
  private final JdbcTemplate jdbc;

  public QuizCatalogService(JdbcTemplate jdbc) {
    this.jdbc = jdbc;
  }

  public List<CategoryResponse> categories(UUID userId) {
    return jdbc.query(
        """
        SELECT category, count(*)
          FROM csas.quizzes
         WHERE status='READY' AND (origin='CURATED' OR owner_user_id=?)
         GROUP BY category
         ORDER BY category
        """,
        (rs, row) ->
            new CategoryResponse(
                categorySlug(rs.getString(1)), categoryName(rs.getString(1)), rs.getInt(2)),
        userId);
  }

  public QuizPageResponse list(
      UUID userId, String category, String difficulty, String conceptId, String cursor, int limit) {
    validateFilters(category, difficulty, limit);
    UUID after = decodeCursor(cursor, category, difficulty, conceptId);
    var parameters = new ArrayList<Object>();
    var sql =
        new StringBuilder(
            """
            SELECT DISTINCT q.id
              FROM csas.quizzes q
              LEFT JOIN csas.quiz_concepts qc ON qc.quiz_id=q.id
             WHERE q.status='READY' AND (q.origin='CURATED' OR q.owner_user_id=?)
            """);
    parameters.add(userId);
    if (category != null) {
      sql.append(" AND q.category=?");
      parameters.add(category);
    }
    if (difficulty != null) {
      sql.append(" AND q.difficulty=?");
      parameters.add(difficulty);
    }
    if (conceptId != null) {
      sql.append(" AND qc.concept_id=?");
      parameters.add(conceptId);
    }
    if (after != null) {
      sql.append(" AND q.id>?");
      parameters.add(after);
    }
    sql.append(" ORDER BY q.id LIMIT ?");
    parameters.add(limit + 1);
    List<UUID> ids = jdbc.queryForList(sql.toString(), UUID.class, parameters.toArray());
    boolean hasMore = ids.size() > limit;
    if (hasMore) {
      ids = new ArrayList<>(ids.subList(0, limit));
    }
    var items = ids.stream().map(id -> loadAccessible(userId, id)).toList();
    String next =
        hasMore ? encodeCursor(category, difficulty, conceptId, ids.get(ids.size() - 1)) : null;
    return new QuizPageResponse(items, next);
  }

  public QuizResponse get(UUID userId, UUID quizId) {
    return loadAccessible(userId, quizId, false);
  }

  private QuizResponse loadAccessible(UUID userId, UUID quizId) {
    return loadAccessible(userId, quizId, false);
  }

  public QuizResponse getForRecordedAttempt(UUID userId, UUID quizId) {
    return loadAccessible(userId, quizId, true);
  }

  private QuizResponse loadAccessible(UUID userId, UUID quizId, boolean includeRetired) {
    String statuses = includeRetired ? "('READY','RETIRED')" : "('READY')";
    var quizzes =
        jdbc.query(
            """
            SELECT id, version, stem, category, difficulty, origin
              FROM csas.quizzes
             WHERE id=? AND status IN %s AND (origin='CURATED' OR owner_user_id=?)
            """.formatted(statuses),
            (rs, row) ->
                new QuizHeader(
                    rs.getObject("id", UUID.class),
                    rs.getInt("version"),
                    rs.getString("stem"),
                    rs.getString("category"),
                    rs.getString("difficulty"),
                    rs.getString("origin")),
            quizId,
            userId);
    if (quizzes.isEmpty()) {
      throw new ApiException(404, "QUIZ_NOT_FOUND", "Quiz not found.");
    }
    QuizHeader quiz = quizzes.getFirst();
    List<String> concepts =
        jdbc.queryForList(
            "SELECT concept_id FROM csas.quiz_concepts WHERE quiz_id=? ORDER BY is_primary DESC, concept_id",
            String.class,
            quizId);
    List<QuizOptionResponse> options =
        jdbc.query(
            "SELECT id, position, text FROM csas.quiz_options WHERE quiz_id=? ORDER BY position",
            (rs, row) ->
                new QuizOptionResponse(
                    rs.getObject("id", UUID.class), rs.getInt("position"), rs.getString("text")),
            quizId);
    return new QuizResponse(
        quiz.id(),
        quiz.version(),
        quiz.stem(),
        quiz.category(),
        quiz.difficulty(),
        quiz.origin(),
        concepts,
        options);
  }

  private void validateFilters(String category, String difficulty, int limit) {
    if ((category != null && !CATEGORIES.contains(category))
        || (difficulty != null && !DIFFICULTIES.contains(difficulty))
        || limit < 1
        || limit > 100) {
      throw new ApiException(400, "INVALID_INPUT", "Invalid quiz query.");
    }
  }

  private UUID decodeCursor(String cursor, String category, String difficulty, String conceptId) {
    if (cursor == null) {
      return null;
    }
    try {
      String decoded =
          new String(Base64.getUrlDecoder().decode(cursor), StandardCharsets.UTF_8);
      String[] parts = decoded.split("\\n", -1);
      if (parts.length != 4
          || !parts[0].equals(value(category))
          || !parts[1].equals(value(difficulty))
          || !parts[2].equals(value(conceptId))) {
        throw new IllegalArgumentException();
      }
      return UUID.fromString(parts[3]);
    } catch (IllegalArgumentException ex) {
      throw new ApiException(400, "INVALID_INPUT", "Invalid quiz cursor.");
    }
  }

  private String encodeCursor(String category, String difficulty, String conceptId, UUID lastId) {
    String payload =
        String.join("\n", value(category), value(difficulty), value(conceptId), lastId.toString());
    return Base64.getUrlEncoder()
        .withoutPadding()
        .encodeToString(payload.getBytes(StandardCharsets.UTF_8));
  }

  private String value(String value) {
    return value == null ? "" : value;
  }

  private String categorySlug(String category) {
    return category.toLowerCase(java.util.Locale.ROOT).replace('_', '-');
  }

  private String categoryName(String category) {
    return switch (category) {
      case "OPERATING_SYSTEM" -> "운영체제";
      case "NETWORK" -> "네트워크";
      case "DATABASE" -> "데이터베이스";
      case "DATA_STRUCTURE" -> "자료구조";
      case "ALGORITHM" -> "알고리즘";
      case "COMPUTER_ARCHITECTURE" -> "컴퓨터 구조";
      default -> throw new IllegalStateException("Unknown category");
    };
  }

  private record QuizHeader(
      UUID id, int version, String stem, String category, String difficulty, String origin) {}
}
