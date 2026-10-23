package com.csas;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

class ReviewIntegrationTest extends HttpTestSupport {
  private static final String QUIZ = "10000000-0000-0000-0000-000000000007";
  private static final String CORRECT = "20000000-0000-0000-0000-000000000026";
  private static final String WRONG = "20000000-0000-0000-0000-000000000025";
  @Autowired JdbcTemplate jdbc;

  private Browser account() throws Exception {
    var b = browser();
    b.refreshCsrf();
    var credentials =
        Map.of("email", UUID.randomUUID() + "@example.com", "password", "correct-horse-battery");
    b.request("POST", "/api/v1/auth/signup", credentials, true);
    b.request("POST", "/api/v1/auth/login", credentials, true);
    b.refreshCsrf();
    return b;
  }

  private Result submit(Browser b, String quiz, String option, String key, String retry)
      throws Exception {
    var body = new java.util.HashMap<String, Object>();
    body.put("selected_option_id", option);
    if (retry != null) {
      body.put("retry_of_attempt_id", retry);
    }
    return b.request(
        "POST",
        "/api/v1/quizzes/" + quiz + "/attempts",
        body,
        true,
        Map.of("Idempotency-Key", key));
  }

  private Result wrongs(Browser b, String filter) throws Exception {
    return b.request("GET", "/api/v1/me/wrong-answers" + filter, null, false);
  }

  @Test
  void emptyStatisticsAndCorrectFirstAttemptCreateNoReview() throws Exception {
    var owner = account();
    var empty = owner.request("GET", "/api/v1/me/stats", null, false);
    assertThat(empty.body().path("accuracy").isNull()).isTrue();
    assertThat(empty.body().path("total_attempts").asLong()).isZero();
    submit(owner, QUIZ, CORRECT, UUID.randomUUID().toString(), null);
    assertThat(wrongs(owner, "").body().path("total_count").asLong()).isZero();
    assertThat(
            owner
                .request("GET", "/api/v1/me/stats", null, false)
                .body()
                .path("accuracy")
                .asDouble())
        .isEqualTo(1.0);
    assertThat(browser().request("GET", "/api/v1/me/wrong-answers", null, false).status())
        .isEqualTo(401);
    assertThat(browser().request("GET", "/api/v1/me/stats", null, false).status()).isEqualTo(401);
  }

  @Test
  void wrongCorrectWrongPreservesAllAttemptsAndReopensReview() throws Exception {
    var owner = account();
    String key = UUID.randomUUID().toString();
    var first = submit(owner, QUIZ, WRONG, key, null);
    String firstId = first.body().path("id").asText();
    var note = wrongs(owner, "");
    assertThat(note.body().path("items").get(0).path("status").asText()).isEqualTo("NEEDS_REVIEW");
    var second = submit(owner, QUIZ, CORRECT, UUID.randomUUID().toString(), firstId);
    assertThat(second.body().path("is_correct").asBoolean()).isTrue();
    assertThat(wrongs(owner, "?status=RESOLVED").body().path("total_count").asLong()).isEqualTo(1);
    assertThat(submit(owner, QUIZ, WRONG, key, null).body()).isEqualTo(first.body());
    assertThat(wrongs(owner, "?status=NEEDS_REVIEW").body().path("total_count").asLong()).isZero();
    submit(owner, QUIZ, WRONG, UUID.randomUUID().toString(), second.body().path("id").asText());
    var latest = wrongs(owner, "").body().path("items").get(0);
    assertThat(latest.path("status").asText()).isEqualTo("NEEDS_REVIEW");
    assertThat(latest.path("wrong_attempts").asLong()).isEqualTo(2);
    assertThat(latest.path("last_reviewed_at").isNull()).isFalse();
    assertThat(latest.path("first_wrong_at"))
        .isEqualTo(note.body().path("items").get(0).path("first_wrong_at"));
    var stats = owner.request("GET", "/api/v1/me/stats", null, false).body();
    assertThat(stats.path("total_attempts").asLong()).isEqualTo(3);
    assertThat(stats.path("unique_quizzes").asLong()).isEqualTo(1);
    assertThat(stats.path("correct_attempts").asLong()).isEqualTo(1);
    assertThat(stats.path("accuracy").asDouble()).isEqualTo(1.0 / 3);
    assertThat(stats.path("needs_review").asLong()).isEqualTo(1);
    assertThat(
            owner
                .request("GET", "/api/v1/me/attempts", null, false)
                .body()
                .path("total_count")
                .asLong())
        .isEqualTo(3);
  }

  @Test
  void notebookIsOwnedFilteredAndPaginatedAndRetiredQuizCannotBeRetried() throws Exception {
    var owner = account();
    var stranger = account();
    submit(owner, QUIZ, WRONG, UUID.randomUUID().toString(), null);
    UUID other = UUID.fromString("10000000-0000-0000-0000-000000000008");
    UUID wrong =
        jdbc.queryForObject(
            "SELECT id FROM csas.quiz_options WHERE quiz_id=? AND NOT is_correct ORDER BY position LIMIT 1",
            UUID.class,
            other);
    submit(owner, other.toString(), wrong.toString(), UUID.randomUUID().toString(), null);
    var first = wrongs(owner, "?limit=1");
    String cursor = first.body().path("next_cursor").asText();
    assertThat(first.body().path("total_count").asLong()).isEqualTo(2);
    var second = wrongs(owner, "?limit=1&cursor=" + cursor);
    assertThat(second.body().path("items")).hasSize(1);
    assertThat(second.body().path("next_cursor").isNull()).isTrue();
    assertThat(wrongs(stranger, "").body().path("items")).isEmpty();
    assertThat(wrongs(stranger, "?cursor=" + cursor).status()).isEqualTo(400);
    assertThat(wrongs(owner, "?origin=AI_GENERATED").body().path("items")).isEmpty();
    assertThat(wrongs(owner, "?category=DATABASE").body().path("total_count").asLong())
        .isEqualTo(2);
    assertThat(wrongs(owner, "?status=INVALID").status()).isEqualTo(400);
    jdbc.update("UPDATE csas.quizzes SET status='RETIRED' WHERE id=?", UUID.fromString(QUIZ));
    try {
      var all = wrongs(owner, "").body().path("items");
      for (var item : all) {
        if (item.path("quiz").path("id").asText().equals(QUIZ)) {
          assertThat(item.path("retryable").asBoolean()).isFalse();
        }
      }
      assertThat(submit(owner, QUIZ, CORRECT, UUID.randomUUID().toString(), null).status())
          .isEqualTo(409);
    } finally {
      jdbc.update("UPDATE csas.quizzes SET status='READY' WHERE id=?", UUID.fromString(QUIZ));
    }
  }

  @Test
  void retryCannotReferenceAnotherUsersAttemptOrDifferentQuiz() throws Exception {
    var owner = account();
    var stranger = account();
    var foreign = submit(stranger, QUIZ, WRONG, UUID.randomUUID().toString(), null);
    assertThat(
            submit(
                    owner,
                    QUIZ,
                    CORRECT,
                    UUID.randomUUID().toString(),
                    foreign.body().path("id").asText())
                .status())
        .isEqualTo(404);
    var own = submit(owner, QUIZ, WRONG, UUID.randomUUID().toString(), null);
    UUID other = UUID.fromString("10000000-0000-0000-0000-000000000008");
    UUID option =
        jdbc.queryForObject(
            "SELECT id FROM csas.quiz_options WHERE quiz_id=? ORDER BY position LIMIT 1",
            UUID.class,
            other);
    assertThat(
            submit(
                    owner,
                    other.toString(),
                    option.toString(),
                    UUID.randomUUID().toString(),
                    own.body().path("id").asText())
                .status())
        .isEqualTo(404);
  }

  @Test
  void reviewWriteFailureRollsBackAttempt() throws Exception {
    var owner = account();
    String key = UUID.randomUUID().toString();
    jdbc.execute(
        "CREATE FUNCTION csas.review_test_fail() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'test failure'; END $$");
    jdbc.execute(
        "CREATE TRIGGER review_test_fail BEFORE INSERT ON csas.review_states FOR EACH ROW EXECUTE FUNCTION csas.review_test_fail()");
    try {
      assertThat(submit(owner, QUIZ, WRONG, key, null).status()).isEqualTo(500);
      assertThat(
              jdbc.queryForObject(
                  "SELECT count(*) FROM csas.quiz_attempts WHERE idempotency_key=?",
                  Integer.class,
                  UUID.fromString(key)))
          .isZero();
    } finally {
      jdbc.execute("DROP TRIGGER review_test_fail ON csas.review_states");
      jdbc.execute("DROP FUNCTION csas.review_test_fail()");
    }
  }
}
