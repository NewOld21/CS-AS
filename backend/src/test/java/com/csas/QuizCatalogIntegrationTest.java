package com.csas;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

class QuizCatalogIntegrationTest extends HttpTestSupport {
  private static final String PASSWORD = "correct-horse-battery";
  @Autowired JdbcTemplate jdbc;

  @Test
  void categoriesCountOnlyReadyQuestions() throws Exception {
    var browser = account();
    var response = browser.request("GET", "/api/v1/quiz/categories", null, false);
    assertThat(response.status()).isEqualTo(200);
    assertThat(response.body()).hasSize(6);
    int total = 0;
    for (var category : response.body()) {
      total += category.get("quiz_count").asInt();
      assertThat(category.size()).isEqualTo(3);
      assertThat(category.has("id") && category.has("name") && category.has("quiz_count")).isTrue();
    }
    assertThat(total)
        .isEqualTo(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.quizzes WHERE status='READY' AND origin='CURATED'",
                Integer.class));
  }

  @Test
  void listSupportsFiltersStableCursorAndBoundedLimit() throws Exception {
    var browser = account();
    var filtered =
        browser.request("GET", "/api/v1/quizzes?category=DATABASE&difficulty=MEDIUM", null, false);
    assertThat(filtered.status()).isEqualTo(200);
    int matching =
        jdbc.queryForObject(
            "SELECT count(*) FROM csas.quizzes WHERE status='READY' AND origin='CURATED' AND category='DATABASE' AND difficulty='MEDIUM'",
            Integer.class);
    assertThat(filtered.body().get("items")).hasSize(Math.min(20, matching));
    filtered
        .body()
        .get("items")
        .forEach(
            quiz -> {
              assertThat(quiz.get("category").asText()).isEqualTo("DATABASE");
              assertThat(quiz.get("difficulty").asText()).isEqualTo("MEDIUM");
            });

    var first = browser.request("GET", "/api/v1/quizzes?limit=2", null, false);
    assertThat(first.status()).isEqualTo(200);
    assertThat(first.body().get("items")).hasSize(2);
    String cursor = first.body().get("next_cursor").asText();
    var second = browser.request("GET", "/api/v1/quizzes?limit=2&cursor=" + cursor, null, false);
    assertThat(second.status()).isEqualTo(200);
    assertThat(second.body().get("items").get(0).get("id"))
        .isNotEqualTo(first.body().get("items").get(0).get("id"));
    assertThat(
            browser
                .request(
                    "GET", "/api/v1/quizzes?limit=2&category=NETWORK&cursor=" + cursor, null, false)
                .status())
        .isEqualTo(400);
    assertThat(browser.request("GET", "/api/v1/quizzes?limit=101", null, false).status())
        .isEqualTo(400);
  }

  @Test
  void detailNeverExposesAnswerExplanationOrReviewMetadata() throws Exception {
    var browser = account();
    String id = "10000000-0000-0000-0000-000000000007";
    var response = browser.request("GET", "/api/v1/quizzes/" + id, null, false);
    assertThat(response.status()).isEqualTo(200);
    assertThat(response.body().size()).isEqualTo(8);
    for (String field :
        java.util.List.of(
            "id",
            "version",
            "stem",
            "category",
            "difficulty",
            "origin",
            "concept_ids",
            "options")) {
      assertThat(response.body().has(field)).as(field).isTrue();
    }
    assertThat(response.body().get("options")).hasSize(4);
    response
        .body()
        .get("options")
        .forEach(
            option -> {
              assertThat(option.size()).isEqualTo(3);
              assertThat(option.has("id") && option.has("position") && option.has("text")).isTrue();
            });
    assertThat(response.body().toString())
        .doesNotContain(
            "is_correct", "correct_option_id", "explanation", "source_url", "reviewed_at");
  }

  @Test
  void missingAndDraftQuestionsReturn404() throws Exception {
    var browser = account();
    UUID draft = UUID.randomUUID();
    jdbc.update(
        """
        INSERT INTO csas.quizzes(
          id, family_id, version, stem, category, difficulty, origin, status, explanation)
        VALUES (?, ?, 1, 'draft?', 'DATABASE', 'EASY', 'CURATED', 'DRAFT', '')
        """,
        draft,
        draft);
    assertThat(browser.request("GET", "/api/v1/quizzes/" + draft, null, false).status())
        .isEqualTo(404);
    assertThat(browser.request("GET", "/api/v1/quizzes/" + UUID.randomUUID(), null, false).status())
        .isEqualTo(404);
  }

  private Browser account() throws Exception {
    var browser = browser();
    browser.refreshCsrf();
    var credentials = Map.of("email", UUID.randomUUID() + "@example.com", "password", PASSWORD);
    assertThat(browser.request("POST", "/api/v1/auth/signup", credentials, true).status())
        .isEqualTo(201);
    assertThat(browser.request("POST", "/api/v1/auth/login", credentials, true).status())
        .isEqualTo(200);
    return browser;
  }
}
