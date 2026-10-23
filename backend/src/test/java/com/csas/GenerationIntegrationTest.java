package com.csas;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.csas.common.exception.ApiException;
import com.csas.integrations.rag.HttpRagGateway;
import com.csas.integrations.rag.RagGateway;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

class GenerationIntegrationTest extends HttpTestSupport {
  @Autowired JdbcTemplate jdbc;
  @Autowired ObjectMapper mapper;
  @MockitoBean HttpRagGateway rag;
  private String stem;

  @BeforeEach
  void setup() {
    stem = "Index question " + UUID.randomUUID();
    when(rag.activeIndex()).thenReturn("test-v1");
    when(rag.deadlineAt()).thenReturn(Instant.now().plusSeconds(60).toString());
    doAnswer(call -> response(call.getArgument(0), "validated")).when(rag).generate(any());
  }

  private JsonNode response(JsonNode request, String status) {
    var result = mapper.createObjectNode();
    result
        .put("request_id", request.path("request_id").asText())
        .put("index_version", "test-v1")
        .put("status", status)
        .put("model_version", "mock-gms")
        .put("prompt_version", "quiz-generate-v1")
        .put("validator_version", "quiz-validator-v1")
        .put("corpus_digest", "fixture-corpus");
    result.set(
        "candidate",
        status.equals("validated")
            ? mapper.valueToTree(
                Map.of(
                    "stem",
                    stem,
                    "options",
                    List.of(
                        Map.of("position", 1, "text", "Maintenance costs"),
                        Map.of("position", 2, "text", "No storage"),
                        Map.of("position", 3, "text", "All writes faster"),
                        Map.of("position", 4, "text", "Replaces tables")),
                    "correct_option_position",
                    1,
                    "explanation",
                    "Indexes incur maintenance costs.",
                    "difficulty",
                    "EASY",
                    "concept_ids",
                    List.of("concept:database-index"),
                    "evidence_chunk_ids",
                    List.of("chunk:1")))
            : mapper.nullNode());
    result.set(
        "retrieved_chunks",
        mapper.valueToTree(
            List.of(
                Map.of(
                    "source_id",
                    "fixture",
                    "document_id",
                    "doc:1",
                    "revision",
                    "r1",
                    "chunk_id",
                    "chunk:1",
                    "title",
                    "Indexes",
                    "url",
                    "https://example.org/index",
                    "locator",
                    "section:1",
                    "evidence_text",
                    "Indexes incur maintenance costs."))));
    result.set(
        "validation_report",
        mapper.valueToTree(
            List.of(
                Map.of("stage", "structure", "passed", true),
                Map.of("stage", "blind_solution", "passed", true),
                Map.of("stage", "evidence_audit", "passed", true))));
    result.set(
        "reason_codes",
        mapper.valueToTree(status.equals("validated") ? List.of() : List.of("UNSUPPORTED")));
    return result;
  }

  private Browser account() throws Exception {
    Browser b = browser();
    b.refreshCsrf();
    var credentials =
        Map.of("email", UUID.randomUUID() + "@example.com", "password", "correct-horse-battery");
    b.request("POST", "/api/v1/auth/signup", credentials, true);
    b.request("POST", "/api/v1/auth/login", credentials, true);
    b.refreshCsrf();
    return b;
  }

  private Result generate(Browser b, String key) throws Exception {
    return b.request(
        "POST",
        "/api/v1/quiz-generations",
        Map.of("concept_ids", List.of("concept:database-index"), "difficulty", "EASY"),
        true,
        Map.of("Idempotency-Key", key));
  }

  @Test
  void questionGenerationWrongReviewRetryAndReloginPreserveHistory() throws Exception {
    doAnswer(
            call -> {
              RagGateway.AnswerRequest request = call.getArgument(0);
              var chunk =
                  new RagGateway.RetrievedChunk(
                      "fixture",
                      "doc:1",
                      "r1",
                      "chunk:1",
                      "Indexes",
                      "https://example.org/index",
                      "section:1",
                      "Indexes incur maintenance costs.",
                      "DATABASE",
                      "17");
              return new RagGateway.Answer(
                  request.requestId(),
                  "answered",
                  List.of("concept:database-index"),
                  "Indexes incur maintenance costs.",
                  List.of(chunk),
                  List.of("chunk:1"),
                  "test-v1",
                  "mock-gms",
                  "answer-v1");
            })
        .when(rag)
        .answer(any());
    var credentials =
        Map.of("email", UUID.randomUUID() + "@example.com", "password", "correct-horse-battery");
    var owner = browser();
    owner.refreshCsrf();
    assertThat(owner.request("POST", "/api/v1/auth/signup", credentials, true).status())
        .isEqualTo(201);
    assertThat(owner.request("POST", "/api/v1/auth/login", credentials, true).status())
        .isEqualTo(200);
    owner.refreshCsrf();
    var session =
        owner.request("POST", "/api/v1/chat/sessions", Map.of("title", "Index review"), true);
    assertThat(session.status()).isEqualTo(201);
    var chatId = session.body().path("id").asText();
    var answer =
        owner.request(
            "POST",
            "/api/v1/chat/sessions/" + chatId + "/messages",
            Map.of("question", "What are index maintenance costs?"),
            true,
            Map.of("Idempotency-Key", UUID.randomUUID().toString()));
    assertThat(answer.status()).isEqualTo(200);
    assertThat(answer.body().path("concept_ids").get(0).asText())
        .isEqualTo("concept:database-index");
    var generation =
        owner.request(
            "POST",
            "/api/v1/quiz-generations",
            Map.of(
                "concept_ids",
                List.of("concept:database-index"),
                "difficulty",
                "EASY",
                "chat_session_id",
                chatId),
            true,
            Map.of("Idempotency-Key", UUID.randomUUID().toString()));
    assertThat(generation.status()).isEqualTo(200);
    var quiz = generation.body().path("quiz");
    assertThat(quiz.has("correct_option_id")).isFalse();
    String submitPath = "/api/v1/quizzes/" + quiz.path("id").asText() + "/attempts";
    var wrong =
        owner.request(
            "POST",
            submitPath,
            Map.of("selected_option_id", quiz.path("options").get(1).path("id").asText()),
            true,
            Map.of("Idempotency-Key", UUID.randomUUID().toString()));
    assertThat(wrong.status()).isEqualTo(200);
    assertThat(wrong.body().path("is_correct").asBoolean()).isFalse();
    var wrongId = wrong.body().path("id").asText();
    var notebook =
        owner.request(
            "GET", "/api/v1/me/wrong-answers?origin=AI_GENERATED&status=NEEDS_REVIEW", null, false);
    assertThat(notebook.body().path("total_count").asInt()).isEqualTo(1);
    assertThat(notebook.body().path("items").get(0).path("latest_attempt_id").asText())
        .isEqualTo(wrongId);
    var retryBody =
        Map.of(
            "selected_option_id",
            quiz.path("options").get(0).path("id").asText(),
            "retry_of_attempt_id",
            wrongId);
    var key = Map.of("Idempotency-Key", UUID.randomUUID().toString());
    var retry = owner.request("POST", submitPath, retryBody, true, key);
    assertThat(retry.status()).isEqualTo(200);
    assertThat(retry.body().path("is_correct").asBoolean()).isTrue();
    assertThat(owner.request("POST", submitPath, retryBody, true, key).body())
        .isEqualTo(retry.body());
    assertThat(
            owner
                .request("GET", "/api/v1/me/wrong-answers?status=NEEDS_REVIEW", null, false)
                .body()
                .path("total_count")
                .asInt())
        .isZero();
    assertThat(
            owner
                .request("GET", "/api/v1/me/wrong-answers?status=RESOLVED", null, false)
                .body()
                .path("total_count")
                .asInt())
        .isEqualTo(1);
    var before = owner.request("GET", "/api/v1/me/attempts", null, false).body();
    assertThat(before.path("total_count").asInt()).isEqualTo(2);
    assertThat(owner.request("POST", "/api/v1/auth/logout", null, true).status()).isEqualTo(204);
    assertThat(owner.request("GET", "/api/v1/me/attempts", null, false).status()).isEqualTo(401);
    owner.refreshCsrf();
    assertThat(owner.request("POST", "/api/v1/auth/login", credentials, true).status())
        .isEqualTo(200);
    owner.refreshCsrf();
    assertThat(owner.request("GET", "/api/v1/me/attempts", null, false).body()).isEqualTo(before);
    assertThat(
            owner
                .request("GET", "/api/v1/me/attempts/" + wrongId, null, false)
                .body()
                .path("is_correct")
                .asBoolean())
        .isFalse();
    var stats = owner.request("GET", "/api/v1/me/stats", null, false).body();
    assertThat(stats.path("total_attempts").asInt()).isEqualTo(2);
    assertThat(stats.path("correct_attempts").asInt()).isEqualTo(1);
    assertThat(stats.path("accuracy").asDouble()).isEqualTo(0.5);
    assertThat(stats.path("resolved_reviews").asInt()).isEqualTo(1);
    var stranger = account();
    assertThat(stranger.request("GET", "/api/v1/me/attempts/" + wrongId, null, false).status())
        .isEqualTo(404);
    assertThat(
            stranger
                .request("GET", "/api/v1/me/wrong-answers", null, false)
                .body()
                .path("total_count")
                .asInt())
        .isZero();
    assertThat(
            stranger
                .request("GET", "/api/v1/quizzes/" + quiz.path("id").asText(), null, false)
                .status())
        .isEqualTo(404);
  }

  @Test
  void storesPrivateValidatedQuizReplaysAndUsesExistingGrading() throws Exception {
    var owner = account();
    String key = UUID.randomUUID().toString();
    var generated = generate(owner, key);
    assertThat(generated.status()).isEqualTo(200);
    var quiz = generated.body().path("quiz");
    assertThat(quiz.path("origin").asText()).isEqualTo("AI_GENERATED");
    assertThat(quiz.has("correct_option_position")).isFalse();
    assertThat(quiz.has("explanation")).isFalse();
    assertThat(quiz.has("sources")).isFalse();
    assertThat(generate(owner, key).body()).isEqualTo(generated.body());
    verify(rag, times(1)).generate(any());
    assertThat(owner.request("GET", "/api/v1/quiz-generations/" + key, null, false).status())
        .isEqualTo(200);
    var stranger = account();
    assertThat(
            stranger
                .request("GET", "/api/v1/quizzes/" + quiz.path("id").asText(), null, false)
                .status())
        .isEqualTo(404);
    assertThat(stranger.request("GET", "/api/v1/quiz-generations/" + key, null, false).status())
        .isEqualTo(404);
    String option = quiz.path("options").get(0).path("id").asText();
    var attempt =
        owner.request(
            "POST",
            "/api/v1/quizzes/" + quiz.path("id").asText() + "/attempts",
            Map.of("selected_option_id", option),
            true,
            Map.of("Idempotency-Key", UUID.randomUUID().toString()));
    assertThat(attempt.status()).isEqualTo(200);
    assertThat(attempt.body().path("is_correct").asBoolean()).isTrue();
    assertThat(attempt.body().path("sources").get(0).path("evidence_text").asText())
        .contains("maintenance");
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.quiz_attempts WHERE quiz_id=?",
                Integer.class,
                UUID.fromString(quiz.path("id").asText())))
        .isEqualTo(1);
    var wrong =
        owner.request(
            "POST",
            "/api/v1/quizzes/" + quiz.path("id").asText() + "/attempts",
            Map.of("selected_option_id", quiz.path("options").get(1).path("id").asText()),
            true,
            Map.of("Idempotency-Key", UUID.randomUUID().toString()));
    assertThat(wrong.body().path("is_correct").asBoolean()).isFalse();
    var history = owner.request("GET", "/api/v1/me/attempts?origin=AI_GENERATED", null, false);
    assertThat(history.status()).isEqualTo(200);
    assertThat(history.body().path("total_count").asLong()).isEqualTo(2);
    assertThat(history.body().path("items").get(0).path("quiz").path("origin").asText())
        .isEqualTo("AI_GENERATED");
  }

  @Test
  void rejectedCandidatesAndMissingEvidenceAreNotPublished() throws Exception {
    var owner = account();
    doAnswer(call -> response(call.getArgument(0), "validation_failed")).when(rag).generate(any());
    var result = generate(owner, UUID.randomUUID().toString());
    assertThat(result.status()).isEqualTo(200);
    assertThat(result.body().path("quiz").isNull()).isTrue();
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.quizzes WHERE stem=?", Integer.class, stem))
        .isZero();
    doAnswer(
            call -> {
              var r =
                  (com.fasterxml.jackson.databind.node.ObjectNode)
                      response(call.getArgument(0), "validated");
              r.set("retrieved_chunks", mapper.createArrayNode());
              return r;
            })
        .when(rag)
        .generate(any());
    assertThat(generate(owner, UUID.randomUUID().toString()).status()).isEqualTo(502);
  }

  @Test
  void refusesUnknownConceptsForeignChatAndChangedKeyBody() throws Exception {
    var owner = account();
    String key = UUID.randomUUID().toString();
    generate(owner, key);
    var changed =
        owner.request(
            "POST",
            "/api/v1/quiz-generations",
            Map.of("concept_ids", List.of("concept:os-thread"), "difficulty", "HARD"),
            true,
            Map.of("Idempotency-Key", key));
    assertThat(changed.status()).isEqualTo(409);
    assertThat(
            owner
                .request(
                    "POST",
                    "/api/v1/quiz-generations",
                    Map.of("concept_ids", List.of("concept:made-up"), "difficulty", "EASY"),
                    true,
                    Map.of("Idempotency-Key", UUID.randomUUID().toString()))
                .status())
        .isEqualTo(400);
    var stranger = account();
    String session =
        owner
            .request("POST", "/api/v1/chat/sessions", Map.of("title", "Private"), true)
            .body()
            .path("id")
            .asText();
    assertThat(
            stranger
                .request(
                    "POST",
                    "/api/v1/quiz-generations",
                    Map.of(
                        "concept_ids", List.of(), "difficulty", "EASY", "chat_session_id", session),
                    true,
                    Map.of("Idempotency-Key", UUID.randomUUID().toString()))
                .status())
        .isEqualTo(404);
  }

  @Test
  void failedKeyDoesNotCallProviderAgain() throws Exception {
    var owner = account();
    String key = UUID.randomUUID().toString();
    doThrow(new ApiException(504, "RAG_TIMEOUT", "timeout")).when(rag).generate(any());
    assertThat(generate(owner, key).status()).isEqualTo(504);
    assertThat(generate(owner, key).status()).isEqualTo(504);
    verify(rag, times(1)).generate(any());
  }

  @Test
  void concurrentSameKeySeesInProgressWithoutAnotherModelCall() throws Exception {
    var owner = account();
    String key = UUID.randomUUID().toString();
    doAnswer(
            call -> {
              assertThat(generate(owner, key).status()).isEqualTo(409);
              return response(call.getArgument(0), "validated");
            })
        .when(rag)
        .generate(any());
    assertThat(generate(owner, key).status()).isEqualTo(200);
    verify(rag, times(1)).generate(any());
  }

  @Test
  void optionInsertFailureRollsBackQuizEvidenceAndValidation() throws Exception {
    var owner = account();
    jdbc.execute(
        "CREATE FUNCTION csas.generation_test_fail() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.text='Maintenance costs' THEN RAISE EXCEPTION 'test-only failure' USING ERRCODE='23514'; END IF; RETURN NEW; END $$");
    jdbc.execute(
        "CREATE TRIGGER generation_test_fail BEFORE INSERT ON csas.quiz_options FOR EACH ROW EXECUTE FUNCTION csas.generation_test_fail()");
    try {
      assertThat(generate(owner, UUID.randomUUID().toString()).status()).isEqualTo(500);
      assertThat(
              jdbc.queryForObject(
                  "SELECT count(*) FROM csas.quizzes WHERE stem=?", Integer.class, stem))
          .isZero();
      assertThat(
              jdbc.queryForObject(
                  "SELECT count(*) FROM csas.generation_validations v JOIN csas.generation_requests g ON g.id=v.generation_id WHERE g.status='FAILED' AND g.user_id=(SELECT id FROM csas.users WHERE id=g.user_id)",
                  Integer.class))
          .isZero();
    } finally {
      jdbc.execute("DROP TRIGGER generation_test_fail ON csas.quiz_options");
      jdbc.execute("DROP FUNCTION csas.generation_test_fail()");
    }
  }
}
