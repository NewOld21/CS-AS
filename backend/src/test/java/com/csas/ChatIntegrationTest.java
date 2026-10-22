package com.csas;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.csas.common.exception.ApiException;
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
    doAnswer(
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
            })
        .when(rag)
        .answer(any());
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
                true,
                Map.of("Idempotency-Key", UUID.randomUUID().toString()));
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
  void listsAndRestoresOwnedGeneralConversationWithStableOrder() throws Exception {
    var account = account();
    var created =
        account
            .browser()
            .request("POST", "/api/v1/chat/sessions", Map.of("title", "운영체제 질문"), true);
    UUID sessionId = UUID.fromString(created.body().get("id").asText());
    String key = UUID.randomUUID().toString();
    account
        .browser()
        .request(
            "POST",
            "/api/v1/chat/sessions/" + sessionId + "/messages",
            Map.of("question", "스레드가 뭐야?"),
            true,
            Map.of("Idempotency-Key", key));

    var sessions =
        account.browser().request("GET", "/api/v1/chat/sessions?page=0&limit=20", null, false);
    assertThat(sessions.status()).isEqualTo(200);
    assertThat(sessions.body().get("items").get(0).get("title").asText()).isEqualTo("운영체제 질문");
    assertThat(sessions.body().get("items").get(0).get("quiz_id").isNull()).isTrue();

    var messages =
        account
            .browser()
            .request(
                "GET",
                "/api/v1/chat/sessions/" + sessionId + "/messages?page=0&limit=50",
                null,
                false);
    assertThat(messages.status()).isEqualTo(200);
    assertThat(messages.body().get("items")).hasSize(2);
    assertThat(messages.body().get("items").get(0).get("role").asText()).isEqualTo("USER");
    assertThat(messages.body().get("items").get(1).get("role").asText()).isEqualTo("ASSISTANT");
    assertThat(messages.body().get("items").get(1).get("sources").get(0).get("chunk_id").asText())
        .isEqualTo("chunk:index");
  }

  @Test
  void duplicateMessageRequestReplaysWithoutDuplicateRows() throws Exception {
    var account = account();
    UUID sessionId = createGeneral(account.browser());
    String key = UUID.randomUUID().toString();
    var first = ask(account.browser(), sessionId, "인덱스란?", key);
    var replay = ask(account.browser(), sessionId, "인덱스란?", key);
    assertThat(replay.status()).isEqualTo(200);
    assertThat(replay.body().get("message_id").asText())
        .isEqualTo(first.body().get("message_id").asText());
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.chat_messages WHERE session_id=?",
                Integer.class,
                sessionId))
        .isEqualTo(2);
  }

  @Test
  void messageIdempotencyKeyIsRequiredAndCannotChangeQuestion() throws Exception {
    var account = account();
    UUID sessionId = createGeneral(account.browser());
    assertThat(
            account
                .browser()
                .request(
                    "POST",
                    "/api/v1/chat/sessions/" + sessionId + "/messages",
                    Map.of("question", "키 없음"),
                    true)
                .status())
        .isEqualTo(400);
    String key = UUID.randomUUID().toString();
    assertThat(ask(account.browser(), sessionId, "첫 질문", key).status()).isEqualTo(200);
    assertThat(ask(account.browser(), sessionId, "다른 질문", key).status()).isEqualTo(409);
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.chat_messages WHERE session_id=?",
                Integer.class,
                sessionId))
        .isEqualTo(2);
  }

  @Test
  void ragFailureIsStoredAndSameKeyRetriesWithoutDuplicateUserMessage() throws Exception {
    var account = account();
    UUID sessionId = createGeneral(account.browser());
    String key = UUID.randomUUID().toString();
    doThrow(new ApiException(504, "RAG_TIMEOUT", "timeout")).when(rag).answer(any());
    assertThat(ask(account.browser(), sessionId, "실패 후 재시도", key).status()).isEqualTo(504);
    assertThat(
            jdbc.queryForObject(
                "SELECT status FROM csas.chat_messages WHERE session_id=? AND role='ASSISTANT'",
                String.class,
                sessionId))
        .isEqualTo("failed");
    configureRag();
    assertThat(ask(account.browser(), sessionId, "실패 후 재시도", key).status()).isEqualTo(200);
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.chat_messages WHERE session_id=?",
                Integer.class,
                sessionId))
        .isEqualTo(2);
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
                    true,
                    Map.of("Idempotency-Key", UUID.randomUUID().toString()))
                .status())
        .isEqualTo(404);
    assertThat(
            stranger
                .browser()
                .request(
                    "GET",
                    "/api/v1/chat/sessions/" + session.body().get("id").asText() + "/messages",
                    null,
                    false)
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

  private UUID createGeneral(Browser browser) throws Exception {
    return UUID.fromString(
        browser
            .request("POST", "/api/v1/chat/sessions", Map.of("title", "일반 질문"), true)
            .body()
            .get("id")
            .asText());
  }

  private Result ask(Browser browser, UUID sessionId, String question, String key)
      throws Exception {
    return browser.request(
        "POST",
        "/api/v1/chat/sessions/" + sessionId + "/messages",
        Map.of("question", question),
        true,
        Map.of("Idempotency-Key", key));
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
