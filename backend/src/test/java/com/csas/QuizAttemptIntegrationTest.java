package com.csas;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.Executors;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

class QuizAttemptIntegrationTest extends HttpTestSupport {
  private static final String PASSWORD = "correct-horse-battery";
  private static final UUID QUIZ = UUID.fromString("10000000-0000-0000-0000-000000000007");
  private static final UUID CORRECT = UUID.fromString("20000000-0000-0000-0000-000000000026");
  private static final UUID WRONG = UUID.fromString("20000000-0000-0000-0000-000000000025");
  private static final UUID OTHER_QUIZ_OPTION =
      UUID.fromString("20000000-0000-0000-0000-000000000029");
  @Autowired JdbcTemplate jdbc;

  @Test
  void serverGradesCorrectAndWrongAnswersAndStoresAuthenticatedUser() throws Exception {
    var account = account();
    var correct = submit(account.browser(), QUIZ, CORRECT, UUID.randomUUID());
    assertThat(correct.status()).isEqualTo(200);
    assertThat(correct.body().get("is_correct").asBoolean()).isTrue();
    assertThat(correct.body().get("correct_option_id").asText()).isEqualTo(CORRECT.toString());
    assertThat(correct.body().get("explanation").asText()).isNotBlank();
    assertThat(correct.body().get("quiz").toString())
        .doesNotContain("is_correct", "correct_option_id", "explanation");

    var wrong = submit(account.browser(), QUIZ, WRONG, UUID.randomUUID());
    assertThat(wrong.status()).isEqualTo(200);
    assertThat(wrong.body().get("is_correct").asBoolean()).isFalse();
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.quiz_attempts WHERE user_id=? AND quiz_id=?",
                Integer.class,
                account.id(),
                QUIZ))
        .isEqualTo(2);
  }

  @Test
  void invalidQuizOptionAndPublicationStatesAreRejected() throws Exception {
    var account = account();
    assertThat(submit(account.browser(), QUIZ, OTHER_QUIZ_OPTION, UUID.randomUUID()).status())
        .isEqualTo(400);
    assertThat(
            submit(
                    account.browser(), UUID.randomUUID(), UUID.randomUUID(), UUID.randomUUID())
                .status())
        .isEqualTo(404);

    UUID draft = insertUnpublished("DRAFT");
    UUID retired = insertUnpublished("RETIRED");
    assertThat(submit(account.browser(), draft, UUID.randomUUID(), UUID.randomUUID()).status())
        .isEqualTo(404);
    assertThat(submit(account.browser(), retired, UUID.randomUUID(), UUID.randomUUID()).status())
        .isEqualTo(409);
    assertThat(
            account
                .browser()
                .request(
                    "POST",
                    "/api/v1/quizzes/" + QUIZ + "/attempts",
                    Map.of("selected_option_id", CORRECT),
                    true)
                .status())
        .isEqualTo(400);
  }

  @Test
  void idempotencyReplaysSameResultRejectsConflictAndAllowsNewKey() throws Exception {
    var account = account();
    UUID key = UUID.randomUUID();
    var first = submit(account.browser(), QUIZ, CORRECT, key);
    var replay = submit(account.browser(), QUIZ, CORRECT, key);
    assertThat(replay.status()).isEqualTo(200);
    assertThat(replay.body()).isEqualTo(first.body());
    assertThat(submit(account.browser(), QUIZ, WRONG, key).status()).isEqualTo(409);
    assertThat(submit(account.browser(), QUIZ, WRONG, UUID.randomUUID()).status()).isEqualTo(200);
    assertThat(attemptCount(account.id())).isEqualTo(2);
  }

  @Test
  void idempotencyIsUserScopedAndConcurrentRetryCreatesOneRow() throws Exception {
    var firstUser = account();
    var secondUser = account();
    UUID sharedKey = UUID.randomUUID();
    var first = submit(firstUser.browser(), QUIZ, CORRECT, sharedKey);
    var second = submit(secondUser.browser(), QUIZ, CORRECT, sharedKey);
    assertThat(first.status()).isEqualTo(200);
    assertThat(second.status()).isEqualTo(200);
    assertThat(first.body().get("id")).isNotEqualTo(second.body().get("id"));

    UUID concurrentKey = UUID.randomUUID();
    try (var pool = Executors.newFixedThreadPool(2)) {
      var results =
          pool.invokeAll(
              java.util.List.<Callable<Result>>of(
                  () -> submit(firstUser.browser(), QUIZ, WRONG, concurrentKey),
                  () -> submit(firstUser.browser(), QUIZ, WRONG, concurrentKey)));
      var left = results.get(0).get();
      var right = results.get(1).get();
      assertThat(left.status()).isEqualTo(200);
      assertThat(right.status()).isEqualTo(200);
      assertThat(left.body().get("id")).isEqualTo(right.body().get("id"));
    }
    assertThat(attemptCount(firstUser.id())).isEqualTo(2);
    assertThat(attemptCount(secondUser.id())).isEqualTo(1);
  }

  @Test
  void databaseFailureDoesNotReportOrPersistSuccess() throws Exception {
    var account = account();
    UUID key = UUID.randomUUID();
    jdbc.execute("DROP TRIGGER IF EXISTS quiz_attempt_test_failure ON csas.quiz_attempts");
    jdbc.execute(
        """
        CREATE OR REPLACE FUNCTION csas.fail_quiz_attempt_test() RETURNS trigger
        LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'test failure'; END; $$
        """);
    jdbc.execute(
        "CREATE TRIGGER quiz_attempt_test_failure BEFORE INSERT ON csas.quiz_attempts "
            + "FOR EACH ROW EXECUTE FUNCTION csas.fail_quiz_attempt_test()");
    try {
      var response = submit(account.browser(), QUIZ, CORRECT, key);
      assertThat(response.status()).isEqualTo(500);
      assertThat(response.body().get("code").asText()).isEqualTo("INTERNAL_ERROR");
    } finally {
      jdbc.execute("DROP TRIGGER IF EXISTS quiz_attempt_test_failure ON csas.quiz_attempts");
      jdbc.execute("DROP FUNCTION IF EXISTS csas.fail_quiz_attempt_test()");
    }
    assertThat(attemptCount(account.id())).isZero();
  }

  private Result submit(Browser browser, UUID quiz, UUID option, UUID key) throws Exception {
    return browser.request(
        "POST",
        "/api/v1/quizzes/" + quiz + "/attempts",
        Map.of("selected_option_id", option),
        true,
        Map.of("Idempotency-Key", key.toString()));
  }

  private Account account() throws Exception {
    var browser = browser();
    browser.refreshCsrf();
    var credentials =
        Map.of("email", UUID.randomUUID() + "@example.com", "password", PASSWORD);
    var signup = browser.request("POST", "/api/v1/auth/signup", credentials, true);
    assertThat(signup.status()).isEqualTo(201);
    assertThat(browser.request("POST", "/api/v1/auth/login", credentials, true).status())
        .isEqualTo(200);
    browser.refreshCsrf();
    return new Account(browser, UUID.fromString(signup.body().get("id").asText()));
  }

  private UUID insertUnpublished(String status) {
    UUID id = UUID.randomUUID();
    jdbc.update(
        """
        INSERT INTO csas.quizzes(
          id, family_id, version, stem, category, difficulty, origin, status, explanation)
        VALUES (?, ?, 1, 'unpublished?', 'DATABASE', 'EASY', 'CURATED', ?, '')
        """,
        id,
        id,
        status);
    return id;
  }

  private int attemptCount(UUID userId) {
    return jdbc.queryForObject(
        "SELECT count(*) FROM csas.quiz_attempts WHERE user_id=?", Integer.class, userId);
  }

  private record Account(Browser browser, UUID id) {}
}
