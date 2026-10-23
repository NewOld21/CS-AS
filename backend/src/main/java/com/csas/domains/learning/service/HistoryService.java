package com.csas.domains.learning.service;

import com.csas.common.exception.ApiException;
import com.csas.domains.learning.dto.AttemptPageResponse;
import com.csas.domains.learning.dto.AttemptResultResponse;
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
public class HistoryService {
  private final JdbcTemplate jdbc;
  private final QuizAttemptService attempts;

  public HistoryService(JdbcTemplate jdbc, QuizAttemptService attempts) {
    this.jdbc = jdbc;
    this.attempts = attempts;
  }

  @Transactional(readOnly = true, isolation = Isolation.REPEATABLE_READ)
  public AttemptPageResponse list(
      UUID user, String cursor, int limit, String category, Boolean correct, String origin) {
    validate(limit, category, origin);
    String binding = user + "|" + String.valueOf(category) + "|" + correct + "|" + origin;
    var args = new ArrayList<Object>();
    args.add(user);
    var where = new StringBuilder(" FROM csas.quiz_attempts WHERE user_id=?");
    if (category != null) {
      where.append(" AND quiz_snapshot->>'category'=?");
      args.add(category);
    }
    if (correct != null) {
      where.append(" AND is_correct=?");
      args.add(correct);
    }
    if (origin != null) {
      where.append(" AND quiz_snapshot->>'origin'=?");
      args.add(origin);
    }
    Long count = jdbc.queryForObject("SELECT count(*)" + where, Long.class, args.toArray());
    if (cursor != null) {
      try {
        if (cursor.length() > 2048) {
          throw new IllegalArgumentException();
        }
        var parts =
            new String(Base64.getUrlDecoder().decode(cursor), StandardCharsets.UTF_8)
                .split("\n", -1);
        if (parts.length != 3 || !binding.equals(parts[0])) {
          throw new IllegalArgumentException();
        }
        Instant date = Instant.parse(parts[1]);
        UUID id = UUID.fromString(parts[2]);
        where.append(" AND (submitted_at,id) < (?,?)");
        args.add(Timestamp.from(date));
        args.add(id);
      } catch (IllegalArgumentException | java.time.format.DateTimeParseException ex) {
        throw new ApiException(400, "INVALID_CURSOR", "Invalid history cursor.");
      }
    }
    args.add(limit + 1);
    var rows =
        jdbc.query(
            "SELECT id,submitted_at" + where + " ORDER BY submitted_at DESC,id DESC LIMIT ?",
            (rs, row) ->
                new Position(
                    rs.getObject("id", UUID.class), rs.getTimestamp("submitted_at").toInstant()),
            args.toArray());
    String next = null;
    if (rows.size() > limit) {
      rows = new ArrayList<>(rows.subList(0, limit));
      var last = rows.getLast();
      next =
          Base64.getUrlEncoder()
              .withoutPadding()
              .encodeToString(
                  (binding + "\n" + last.at() + "\n" + last.id()).getBytes(StandardCharsets.UTF_8));
    }
    var items = rows.stream().map(row -> attempts.get(user, row.id())).toList();
    return new AttemptPageResponse(items, next, count == null ? 0 : count);
  }

  @Transactional(readOnly = true)
  public AttemptResultResponse detail(UUID user, UUID id) {
    return attempts.get(user, id);
  }

  public static void validate(int limit, String category, String origin) {
    if (limit < 1
        || limit > 100
        || (category != null
            && !Set.of(
                    "OPERATING_SYSTEM",
                    "NETWORK",
                    "DATABASE",
                    "DATA_STRUCTURE",
                    "ALGORITHM",
                    "COMPUTER_ARCHITECTURE")
                .contains(category))
        || (origin != null && !Set.of("CURATED", "AI_GENERATED").contains(origin))) {
      throw new ApiException(400, "INVALID_INPUT", "Invalid learning filters.");
    }
  }

  private record Position(UUID id, Instant at) {}
}
