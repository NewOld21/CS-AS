package com.csas.domains.learning.service;

import com.csas.common.exception.ApiException;
import com.csas.domains.learning.dto.ReviewItemResponse;
import com.csas.domains.learning.dto.ReviewPageResponse;
import com.csas.domains.learning.dto.StatsResponse;
import java.nio.charset.StandardCharsets;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Set;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true, isolation = Isolation.REPEATABLE_READ)
public class ReviewService {
  private final JdbcTemplate jdbc;
  private final QuizAttemptService attempts;

  public ReviewService(JdbcTemplate jdbc, QuizAttemptService attempts) {
    this.jdbc = jdbc;
    this.attempts = attempts;
  }

  public ReviewPageResponse list(
      UUID user, String cursor, int limit, String category, String status, String origin) {
    HistoryService.validate(limit, category, origin);
    if (status != null && !Set.of("NEEDS_REVIEW", "RESOLVED").contains(status)) {
      throw new ApiException(400, "INVALID_INPUT", "Invalid review status.");
    }
    String binding = user + "|review|" + category + "|" + status + "|" + origin;
    var args = new ArrayList<Object>();
    args.add(user);
    var where =
        new StringBuilder(
            " FROM csas.review_states r JOIN csas.quiz_attempts a ON a.id=r.latest_attempt_id AND a.user_id=r.user_id AND a.quiz_id=r.quiz_id JOIN csas.quizzes q ON q.id=r.quiz_id WHERE r.user_id=?");
    if (category != null) {
      where.append(" AND a.quiz_snapshot->>'category'=?");
      args.add(category);
    }
    if (status != null) {
      where.append(" AND r.status=?");
      args.add(status);
    }
    if (origin != null) {
      where.append(" AND a.quiz_snapshot->>'origin'=?");
      args.add(origin);
    }
    Long total = jdbc.queryForObject("SELECT count(*)" + where, Long.class, args.toArray());
    if (cursor != null) {
      try {
        if (cursor.length() > 2048) {
          throw new IllegalArgumentException();
        }
        String[] parts =
            new String(Base64.getUrlDecoder().decode(cursor), StandardCharsets.UTF_8)
                .split("\n", -1);
        if (parts.length != 3 || !binding.equals(parts[0])) {
          throw new IllegalArgumentException();
        }
        where.append(" AND (r.last_wrong_at,r.quiz_id) < (?,?)");
        args.add(Timestamp.from(Instant.parse(parts[1])));
        args.add(UUID.fromString(parts[2]));
      } catch (IllegalArgumentException | java.time.format.DateTimeParseException ex) {
        throw new ApiException(400, "INVALID_CURSOR", "Invalid review cursor.");
      }
    }
    args.add(limit + 1);
    var rows =
        jdbc.query(
            "SELECT r.*, q.status='READY' AND (q.origin='CURATED' OR q.owner_user_id=r.user_id) retryable,"
                + " (SELECT count(*) FROM csas.quiz_attempts w WHERE w.user_id=r.user_id AND w.quiz_id=r.quiz_id AND NOT w.is_correct) wrong_attempts"
                + where
                + " ORDER BY r.last_wrong_at DESC,r.quiz_id DESC LIMIT ?",
            (rs, row) ->
                new ReviewRow(
                    rs.getObject("quiz_id", UUID.class),
                    rs.getObject("latest_attempt_id", UUID.class),
                    rs.getString("status"),
                    rs.getTimestamp("first_wrong_at").toInstant(),
                    rs.getTimestamp("last_wrong_at").toInstant(),
                    rs.getTimestamp("last_reviewed_at") == null
                        ? null
                        : rs.getTimestamp("last_reviewed_at").toInstant(),
                    rs.getLong("wrong_attempts"),
                    rs.getBoolean("retryable")),
            args.toArray());
    String next = null;
    if (rows.size() > limit) {
      rows = new ArrayList<>(rows.subList(0, limit));
      var last = rows.getLast();
      next =
          Base64.getUrlEncoder()
              .withoutPadding()
              .encodeToString(
                  (binding + "\n" + last.wrong() + "\n" + last.quiz())
                      .getBytes(StandardCharsets.UTF_8));
    }
    return new ReviewPageResponse(
        rows.stream()
            .map(
                r ->
                    new ReviewItemResponse(
                        attempts.get(user, r.attempt()).quiz(),
                        r.status(),
                        r.attempt(),
                        r.first(),
                        r.wrong(),
                        r.reviewed(),
                        r.count(),
                        r.retryable()))
            .toList(),
        next,
        total == null ? 0 : total);
  }

  public StatsResponse stats(UUID user) {
    var total =
        jdbc.queryForMap(
            "SELECT count(*) total,count(*) FILTER (WHERE is_correct) correct,count(DISTINCT quiz_id) unique_quizzes FROM csas.quiz_attempts WHERE user_id=?",
            user);
    long count = ((Number) total.get("total")).longValue();
    long correct = ((Number) total.get("correct")).longValue();
    var reviews =
        jdbc.queryForMap(
            "SELECT count(*) FILTER (WHERE status='NEEDS_REVIEW') needs_review,count(*) FILTER (WHERE status='RESOLVED') resolved FROM csas.review_states WHERE user_id=?",
            user);
    var categories =
        jdbc.query(
            "SELECT quiz_snapshot->>'category' category,count(*) total,count(*) FILTER (WHERE is_correct) correct FROM csas.quiz_attempts WHERE user_id=? GROUP BY quiz_snapshot->>'category' ORDER BY category",
            (rs, row) ->
                new StatsResponse.CategoryStats(
                    rs.getString("category"),
                    rs.getLong("total"),
                    rs.getLong("correct"),
                    ratio(rs.getLong("correct"), rs.getLong("total"))),
            user);
    return new StatsResponse(
        count,
        correct,
        ratio(correct, count),
        ((Number) total.get("unique_quizzes")).longValue(),
        ((Number) reviews.get("needs_review")).longValue(),
        ((Number) reviews.get("resolved")).longValue(),
        categories);
  }

  private static Double ratio(long correct, long total) {
    return total == 0 ? null : (double) correct / total;
  }

  private record ReviewRow(
      UUID quiz,
      UUID attempt,
      String status,
      Instant first,
      Instant wrong,
      Instant reviewed,
      long count,
      boolean retryable) {}
}
