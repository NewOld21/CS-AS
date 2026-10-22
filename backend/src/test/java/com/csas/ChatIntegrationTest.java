package com.csas;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.csas.integrations.rag.HttpRagGateway;
import com.csas.integrations.rag.RagGateway;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

class ChatIntegrationTest extends HttpTestSupport {
  private static final UUID QUIZ = UUID.fromString("10000000-0000-0000-0000-000000000007");
  private static final UUID WRONG = UUID.fromString("20000000-0000-0000-0000-000000000025");
  private static final String PASSWORD = "correct-horse-battery";
  @Autowired JdbcTemplate jdbc;
  @MockitoBean HttpRagGateway rag;

  @BeforeEach
  void configureRag() {
    when(rag.activeIndex()).thenReturn("cs-test-v1");
    when(rag.answer(any()))
        .thenAnswer(
            invocation -> {
              RagGateway.AnswerRequest request = invocation.getArgument(0);
              var chunk =
                  new RagGateway.RetrievedChunk(
                      "fixture-source",
                      "doc:index",
                      "r1",
                      "chunk:index",
                      "Database index",
                      "https://example.test/index",
                      "index.md#cost");
              return new RagGateway.Answer(
                  request.requestId(),
                  "answered",
                  List.of("concept:database-index"),
                  "인덱스 유지 비용 때문에 정답이 아닙니다.",
                  List.of(chunk),
                  List.of("chunk:index"),
                  "cs-test-v1",
                  "mock-v1",
                  "answer-v1");
            });
  }

  @Test
  void restoresOwnedAttemptContextStoresAnswerAndTrustedCitation() throws Exception {
    var account = account();
    var attempt = submit(account.browser());
    var session =
        account
            .browser()
            .request(
                "POST",
                "/api/v1/chat/sessions",
                Map.of("quiz_id", QUIZ, "attempt_id", attempt),
                true);
    assertThat(session.status()).isEqualTo(201);
    UUID sessionId = UUID.fromString(session.body().get("id").asText());

    var answer =
        account
            .browser()
            .request(
                "POST",
                "/api/v1/chat/sessions/" + sessionId + "/messages",
                Map.of("question", "왜 틀렸어?"),
                true);
    assertThat(answer.status()).isEqualTo(200);
    assertThat(answer.body().get("status").asText()).isEqualTo("answered");
    assertThat(answer.body().get("sources").get(0).get("chunk_id").asText())
        .isEqualTo("chunk:index");

    ArgumentCaptor<RagGateway.AnswerRequest> captured =
        ArgumentCaptor.forClass(RagGateway.AnswerRequest.class);
    verify(rag).answer(captured.capture());
    assertThat(captured.getValue().quizContext().attemptId()).isEqualTo(attempt);
    assertThat(captured.getValue().quizContext().selectedOptionId()).isEqualTo(WRONG);
    assertThat(captured.getValue().quizContext().options()).hasSize(4);
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.chat_messages WHERE session_id=?",
                Integer.class,
                sessionId))
        .isEqualTo(2);
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.message_citations WHERE message_id=?",
                Integer.class,
                UUID.fromString(answer.body().get("message_id").asText())))
        .isEqualTo(1);
  }

  @Test
  void rejectsAnotherUsersAttemptAndSession() throws Exception {
    var owner = account();
    UUID attempt = submit(owner.browser());
    var stranger = account();
    assertThat(
            stranger
                .browser()
                .request(
                    "POST",
                    "/api/v1/chat/sessions",
                    Map.of("quiz_id", QUIZ, "attempt_id", attempt),
                    true)
                .status())
        .isEqualTo(404);

    var session =
        owner
            .browser()
            .request(
                "POST",
                "/api/v1/chat/sessions",
                Map.of("quiz_id", QUIZ, "attempt_id", attempt),
                true);
    assertThat(
            stranger
                .browser()
                .request(
                    "POST",
                    "/api/v1/chat/sessions/" + session.body().get("id").asText() + "/messages",
                    Map.of("question", "steal context"),
                    true)
                .status())
        .isEqualTo(404);
  }

  @Test
  void rejectsPartialOrUnsubmittedContext() throws Exception {
    var account = account();
    assertThat(
            account
                .browser()
                .request("POST", "/api/v1/chat/sessions", Map.of("quiz_id", QUIZ), true)
                .status())
        .isEqualTo(400);
    assertThat(
            account
                .browser()
                .request(
                    "POST",
                    "/api/v1/chat/sessions",
                    Map.of("quiz_id", QUIZ, "attempt_id", UUID.randomUUID()),
                    true)
                .status())
        .isEqualTo(404);
  }

  private UUID submit(Browser browser) throws Exception {
    return UUID.fromString(
        browser
            .request(
                "POST",
                "/api/v1/quizzes/" + QUIZ + "/attempts",
                Map.of("selected_option_id", WRONG),
                true,
                Map.of("Idempotency-Key", UUID.randomUUID().toString()))
            .body()
            .get("id")
            .asText());
  }

  private Account account() throws Exception {
    var browser = browser();
    browser.refreshCsrf();
    var credentials = Map.of("email", UUID.randomUUID() + "@example.com", "password", PASSWORD);
    browser.request("POST", "/api/v1/auth/signup", credentials, true);
    browser.request("POST", "/api/v1/auth/login", credentials, true);
    browser.refreshCsrf();
    return new Account(browser);
  }

  private record Account(Browser browser) {}
}
