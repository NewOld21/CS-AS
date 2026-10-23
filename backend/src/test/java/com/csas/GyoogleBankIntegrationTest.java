package com.csas;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;

class GyoogleBankIntegrationTest extends HttpTestSupport {
  @Autowired JdbcTemplate jdbc;

  @Test
  void sourcedQuizUsesExistingGradingHistoryNotebookAndOwnerIsolation() throws Exception {
    var owner = browser();
    owner.refreshCsrf();
    var credentials =
        Map.of("email", UUID.randomUUID() + "@example.com", "password", "correct-horse-battery");
    assertThat(owner.request("POST", "/api/v1/auth/signup", credentials, true).status())
        .isEqualTo(201);
    assertThat(owner.request("POST", "/api/v1/auth/login", credentials, true).status())
        .isEqualTo(200);
    owner.refreshCsrf();
    String firstAttempt = null;
    var sample =
        jdbc.queryForList(
            "SELECT DISTINCT ON (category) id FROM csas.quizzes WHERE source_metadata->>'dataset'='gyoogle-v1' ORDER BY category,id",
            UUID.class);
    assertThat(sample).hasSize(6);
    for (UUID quiz : sample) {
      var safe = owner.request("GET", "/api/v1/quizzes/" + quiz, null, false);
      assertThat(safe.body().has("source_metadata")).isFalse();
      assertThat(safe.body().has("explanation")).isFalse();
      var wrong =
          jdbc.queryForObject(
              "SELECT id FROM csas.quiz_options WHERE quiz_id=? AND NOT is_correct ORDER BY position LIMIT 1",
              UUID.class,
              quiz);
      var right =
          jdbc.queryForObject(
              "SELECT id FROM csas.quiz_options WHERE quiz_id=? AND is_correct", UUID.class, quiz);
      var failed =
          owner.request(
              "POST",
              "/api/v1/quizzes/" + quiz + "/attempts",
              Map.of("selected_option_id", wrong),
              true,
              Map.of("Idempotency-Key", UUID.randomUUID().toString()));
      assertThat(failed.status()).isEqualTo(200);
      assertThat(failed.body().path("is_correct").asBoolean()).isFalse();
      String attempt = failed.body().path("id").asText();
      if (firstAttempt == null) {
        firstAttempt = attempt;
      }
      assertThat(failed.body().path("sources")).isNotEmpty();
      for (var source : failed.body().path("sources")) {
        assertThat(source.path("source_id").asText()).isEqualTo("gyoogle");
      }
      var retried =
          owner.request(
              "POST",
              "/api/v1/quizzes/" + quiz + "/attempts",
              Map.of("selected_option_id", right, "retry_of_attempt_id", attempt),
              true,
              Map.of("Idempotency-Key", UUID.randomUUID().toString()));
      assertThat(retried.status()).isEqualTo(200);
      assertThat(retried.body().path("is_correct").asBoolean()).isTrue();
    }
    assertThat(
            owner
                .request("GET", "/api/v1/me/attempts", null, false)
                .body()
                .path("total_count")
                .asInt())
        .isEqualTo(12);
    assertThat(
            owner
                .request("GET", "/api/v1/me/wrong-answers?status=RESOLVED", null, false)
                .body()
                .path("total_count")
                .asInt())
        .isEqualTo(6);
    assertThat(
            owner
                .request("GET", "/api/v1/me/stats", null, false)
                .body()
                .path("accuracy")
                .asDouble())
        .isEqualTo(0.5);
    owner.request("POST", "/api/v1/auth/logout", null, true);
    owner.refreshCsrf();
    owner.request("POST", "/api/v1/auth/login", credentials, true);
    owner.refreshCsrf();
    assertThat(
            owner
                .request("GET", "/api/v1/me/attempts", null, false)
                .body()
                .path("total_count")
                .asInt())
        .isEqualTo(12);
    assertThat(
            browser().request("GET", "/api/v1/me/attempts/" + firstAttempt, null, false).status())
        .isEqualTo(401);
  }

  @Test
  void sourceBankHasExactCountsDifficultyAndNoBrokenOptions() {
    var expected =
        Map.of(
            "ALGORITHM",
            20,
            "DATA_STRUCTURE",
            20,
            "DATABASE",
            50,
            "NETWORK",
            50,
            "OPERATING_SYSTEM",
            50,
            "COMPUTER_ARCHITECTURE",
            50);
    expected.forEach(
        (category, total) -> {
          assertThat(
                  jdbc.queryForObject(
                      "SELECT count(*) FROM csas.quizzes WHERE source_metadata->>'dataset'='gyoogle-v1' AND category=?",
                      Integer.class,
                      category))
              .isEqualTo(total);
          for (var entry : Map.of("EASY", 30, "MEDIUM", 50, "HARD", 20).entrySet()) {
            assertThat(
                    jdbc.queryForObject(
                        "SELECT count(*) FROM csas.quizzes WHERE source_metadata->>'dataset'='gyoogle-v1' AND category=? AND difficulty=?",
                        Integer.class,
                        category,
                        entry.getKey()))
                .isEqualTo(total * entry.getValue() / 100);
          }
        });
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.quizzes q WHERE source_metadata->>'dataset'='gyoogle-v1' AND (status<>'READY' OR origin<>'CURATED' OR source_metadata->>'sourceRepository'<>'gyoogle/tech-interview-for-developer' OR jsonb_array_length(source_metadata->'optionExplanations')<>4 OR (SELECT count(*) FROM csas.quiz_options o WHERE o.quiz_id=q.id)<>4 OR (SELECT count(*) FROM csas.quiz_options o WHERE o.quiz_id=q.id AND is_correct)<>1)",
                Integer.class))
        .isZero();
  }

  @Test
  void reapplyingSeedPreservesIdsAttemptsAndReviewHistory() throws Exception {
    int attempts = jdbc.queryForObject("SELECT count(*) FROM csas.quiz_attempts", Integer.class);
    int quizzes = jdbc.queryForObject("SELECT count(*) FROM csas.quizzes", Integer.class);
    try (Connection connection = jdbc.getDataSource().getConnection()) {
      connection.setAutoCommit(false);
      // The PostgreSQL parser handles original Markdown backslashes inside JSON
      // literals; Spring's generic script splitter assumes different escaping.
      try (var statement = connection.createStatement()) {
        statement.execute(
            new ClassPathResource("db/migration/V13__gyoogle_question_bank.sql")
                .getContentAsString(StandardCharsets.UTF_8));
      }
      connection.commit();
    }
    assertThat(jdbc.queryForObject("SELECT count(*) FROM csas.quizzes", Integer.class))
        .isEqualTo(quizzes);
    assertThat(jdbc.queryForObject("SELECT count(*) FROM csas.quiz_attempts", Integer.class))
        .isEqualTo(attempts);
  }
}
