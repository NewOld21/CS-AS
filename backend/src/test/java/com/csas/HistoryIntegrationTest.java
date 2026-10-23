package com.csas;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

class HistoryIntegrationTest extends HttpTestSupport {
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

  private Result submit(Browser b, String option) throws Exception {
    return b.request(
        "POST",
        "/api/v1/quizzes/" + QUIZ + "/attempts",
        Map.of("selected_option_id", option),
        true,
        Map.of("Idempotency-Key", UUID.randomUUID().toString()));
  }

  @Test
  void emptyHistoryAndAnonymousAccess() throws Exception {
    assertThat(browser().request("GET", "/api/v1/me/attempts", null, false).status())
        .isEqualTo(401);
    var owner = account();
    var response = owner.request("GET", "/api/v1/me/attempts", null, false);
    assertThat(response.status()).isEqualTo(200);
    assertThat(response.body().path("items")).isEmpty();
    assertThat(response.body().path("total_count").asLong()).isZero();
    assertThat(response.body().path("next_cursor").isNull()).isTrue();
  }

  @Test
  void ownedDetailsAndFiltersAreIsolated() throws Exception {
    var owner = account();
    var stranger = account();
    var first = submit(owner, WRONG);
    submit(owner, CORRECT);
    submit(stranger, WRONG);
    var page =
        owner.request(
            "GET",
            "/api/v1/me/attempts?category=DATABASE&correct=false&origin=CURATED",
            null,
            false);
    assertThat(page.body().path("total_count").asLong()).isEqualTo(1);
    assertThat(page.body().path("items").get(0).path("id")).isEqualTo(first.body().path("id"));
    assertThat(
            stranger
                .request(
                    "GET", "/api/v1/me/attempts/" + first.body().path("id").asText(), null, false)
                .status())
        .isEqualTo(404);
    assertThat(
            owner
                .request("GET", "/api/v1/me/attempts?origin=AI_GENERATED", null, false)
                .body()
                .path("items"))
        .isEmpty();
    for (String query :
        List.of("limit=0", "limit=101", "category=UNKNOWN", "origin=WRONG", "cursor=broken")) {
      assertThat(owner.request("GET", "/api/v1/me/attempts?" + query, null, false).status())
          .isEqualTo(400);
    }
  }

  @Test
  void cursorOrdersTiedTimestampsAndBindsFiltersAndUser() throws Exception {
    var owner = account();
    var stranger = account();
    var first = submit(owner, WRONG);
    var second = submit(owner, CORRECT);
    UUID left = UUID.fromString(first.body().path("id").asText());
    UUID right = UUID.fromString(second.body().path("id").asText());
    jdbc.update(
        "UPDATE csas.quiz_attempts SET submitted_at='2026-10-23T10:00:00Z' WHERE id IN (?,?)",
        left,
        right);
    var page = owner.request("GET", "/api/v1/me/attempts?limit=1", null, false);
    String cursor = page.body().path("next_cursor").asText();
    String expected =
        left.toString().compareTo(right.toString()) > 0 ? left.toString() : right.toString();
    assertThat(page.body().path("items").get(0).path("id").asText()).isEqualTo(expected);
    var next = owner.request("GET", "/api/v1/me/attempts?limit=1&cursor=" + cursor, null, false);
    assertThat(next.body().path("items")).hasSize(1);
    assertThat(next.body().path("items").get(0).path("id").asText()).isNotEqualTo(expected);
    assertThat(next.body().path("next_cursor").isNull()).isTrue();
    assertThat(next.body().path("total_count").asLong()).isEqualTo(2);
    assertThat(
            owner
                .request("GET", "/api/v1/me/attempts?correct=false&cursor=" + cursor, null, false)
                .status())
        .isEqualTo(400);
    assertThat(
            stranger.request("GET", "/api/v1/me/attempts?cursor=" + cursor, null, false).status())
        .isEqualTo(400);
  }

  @Test
  void retiredAndEditedQuizDoesNotRewriteStoredAttempt() throws Exception {
    var owner = account();
    var first = submit(owner, WRONG);
    UUID id = UUID.fromString(QUIZ);
    var original = jdbc.queryForMap("SELECT stem,explanation FROM csas.quizzes WHERE id=?", id);
    try {
      jdbc.update(
          "UPDATE csas.quizzes SET status='RETIRED',stem='Updated question',explanation='Updated explanation' WHERE id=?",
          id);
      var restored =
          owner.request(
              "GET", "/api/v1/me/attempts/" + first.body().path("id").asText(), null, false);
      assertThat(restored.status()).isEqualTo(200);
      assertThat(restored.body()).isEqualTo(first.body());
    } finally {
      jdbc.update(
          "UPDATE csas.quizzes SET status='READY',stem=?,explanation=? WHERE id=?",
          original.get("stem"),
          original.get("explanation"),
          id);
    }
  }
}
