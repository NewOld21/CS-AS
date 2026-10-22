package com.csas.domains.chat.service;

import com.csas.common.exception.ApiException;
import com.csas.domains.chat.dto.ChatAnswerResponse;
import com.csas.domains.chat.dto.ChatMessagePageResponse;
import com.csas.domains.chat.dto.ChatMessageResponse;
import com.csas.domains.chat.dto.ChatQuestionRequest;
import com.csas.domains.chat.dto.ChatSessionPageResponse;
import com.csas.domains.chat.dto.ChatSessionResponse;
import com.csas.domains.chat.dto.CreateChatSessionRequest;
import com.csas.domains.learning.dto.SourceResponse;
import com.csas.integrations.rag.HttpRagGateway;
import com.csas.integrations.rag.RagGateway;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionTemplate;

@Service
public class ChatService {
  private static final int MAX_PAGE_SIZE = 50;
  private final JdbcTemplate jdbc;
  private final RagGateway rag;
  private final HttpRagGateway ragConfiguration;
  private final ObjectMapper mapper;
  private final TransactionTemplate transactions;

  public ChatService(
      JdbcTemplate jdbc,
      RagGateway rag,
      HttpRagGateway ragConfiguration,
      ObjectMapper mapper,
      TransactionTemplate transactions) {
    this.jdbc = jdbc;
    this.rag = rag;
    this.ragConfiguration = ragConfiguration;
    this.mapper = mapper;
    this.transactions = transactions;
  }

  @Transactional
  public ChatSessionResponse create(UUID userId, CreateChatSessionRequest request) {
    if ((request.quiz_id() == null) != (request.attempt_id() == null)) {
      throw new ApiException(400, "INVALID_INPUT", "Quiz and attempt must be provided together.");
    }
    if (request.attempt_id() != null) {
      Integer count =
          jdbc.queryForObject(
              "SELECT count(*) FROM csas.quiz_attempts WHERE id=? AND user_id=? AND quiz_id=?",
              Integer.class,
              request.attempt_id(),
              userId,
              request.quiz_id());
      if (count == null || count == 0) {
        throw notFound();
      }
    }
    UUID id = UUID.randomUUID();
    Instant created = Instant.now();
    String title = normalizeTitle(request.title());
    jdbc.update(
        "INSERT INTO csas.chat_sessions(id,user_id,context_attempt_id,title,created_at,updated_at) VALUES (?,?,?,?,?,?)",
        id,
        userId,
        request.attempt_id(),
        title,
        Timestamp.from(created),
        Timestamp.from(created));
    return new ChatSessionResponse(
        id, title, request.quiz_id(), request.attempt_id(), created, created);
  }

  @Transactional(readOnly = true)
  public ChatSessionPageResponse list(UUID userId, int page, int limit) {
    validatePage(page, limit);
    List<ChatSessionResponse> rows =
        jdbc.query(
            """
        SELECT s.id,s.title,a.quiz_id,s.context_attempt_id,s.created_at,s.updated_at
          FROM csas.chat_sessions s
          LEFT JOIN csas.quiz_attempts a ON a.id=s.context_attempt_id
         WHERE s.user_id=? ORDER BY s.updated_at DESC,s.id DESC LIMIT ? OFFSET ?
        """,
            (rs, row) -> session(rs),
            userId,
            limit + 1,
            page * limit);
    Integer next = rows.size() > limit ? page + 1 : null;
    if (next != null) {
      rows = new ArrayList<>(rows.subList(0, limit));
    }
    return new ChatSessionPageResponse(rows, next);
  }

  @Transactional(readOnly = true)
  public ChatSessionResponse get(UUID userId, UUID sessionId) {
    var rows =
        jdbc.query(
            """
        SELECT s.id,s.title,a.quiz_id,s.context_attempt_id,s.created_at,s.updated_at
          FROM csas.chat_sessions s
          LEFT JOIN csas.quiz_attempts a ON a.id=s.context_attempt_id
         WHERE s.id=? AND s.user_id=?
        """,
            (rs, row) -> session(rs),
            sessionId,
            userId);
    if (rows.isEmpty()) {
      throw notFound();
    }
    return rows.getFirst();
  }

  @Transactional(readOnly = true)
  public ChatMessagePageResponse messages(UUID userId, UUID sessionId, int page, int limit) {
    validatePage(page, limit);
    requireOwnedSession(userId, sessionId);
    List<ChatMessageResponse> rows =
        jdbc.query(
            """
        SELECT id,role,content,status,created_at,request_id,concept_ids
          FROM csas.chat_messages WHERE session_id=? ORDER BY sequence_no LIMIT ? OFFSET ?
        """,
            (rs, row) ->
                new ChatMessageResponse(
                    rs.getObject("id", UUID.class),
                    rs.getString("role"),
                    rs.getString("content"),
                    rs.getString("status"),
                    rs.getTimestamp("created_at").toInstant(),
                    rs.getString("request_id"),
                    concepts(rs.getString("concept_ids")),
                    citations(rs.getObject("id", UUID.class))),
            sessionId,
            limit + 1,
            page * limit);
    Integer next = rows.size() > limit ? page + 1 : null;
    if (next != null) {
      rows = new ArrayList<>(rows.subList(0, limit));
    }
    return new ChatMessagePageResponse(rows, next);
  }

  public ChatAnswerResponse ask(
      UUID userId,
      UUID sessionId,
      ChatQuestionRequest question,
      UUID idempotencyKey,
      String requestId) {
    String content = question.question().trim();
    Prepared prepared =
        transactions.execute(
            status ->
                prepare(userId, sessionId, content, idempotencyKey, hash(content), requestId));
    if (prepared == null) {
      throw new IllegalStateException("Chat preparation returned no result");
    }
    if (prepared.replay() != null) {
      return prepared.replay();
    }
    try {
      RagGateway.Answer response =
          rag.answer(
              new RagGateway.AnswerRequest(
                  requestId,
                  ragConfiguration.deadlineAt(),
                  ragConfiguration.activeIndex(),
                  content,
                  prepared.history(),
                  prepared.context() == null ? null : prepared.context().toRag()));
      validateResponse(requestId, response);
      ChatAnswerResponse saved =
          transactions.execute(
              status -> complete(userId, sessionId, prepared.assistantId(), response));
      if (saved == null) {
        throw new IllegalStateException("Chat completion returned no result");
      }
      return saved;
    } catch (RuntimeException failure) {
      String code = failure instanceof ApiException api ? api.code() : "CHAT_SAVE_FAILED";
      transactions.executeWithoutResult(
          status -> markFailed(userId, sessionId, prepared.assistantId(), code));
      throw failure;
    }
  }

  private Prepared prepare(
      UUID userId, UUID sessionId, String content, UUID key, String requestHash, String requestId) {
    SessionContext context = loadContext(userId, sessionId);
    jdbc.query(
        "SELECT pg_advisory_xact_lock(hashtextextended(?, 0))", rs -> {}, sessionId + ":" + key);
    Existing existing = findByKey(userId, sessionId, key);
    if (existing != null) {
      if (!requestHash.equals(existing.requestHash())) {
        throw new ApiException(409, "IDEMPOTENCY_CONFLICT", "Idempotency key was reused.");
      }
      if ("answered".equals(existing.status())
          || "insufficient_evidence".equals(existing.status())) {
        return new Prepared(existing.id(), context, List.of(), storedAnswer(existing));
      }
      if ("pending".equals(existing.status())) {
        throw new ApiException(409, "CHAT_IN_PROGRESS", "The answer is still being generated.");
      }
      jdbc.update(
          "UPDATE csas.chat_messages SET status='pending',failure_code=NULL,request_id=?,created_at=now() WHERE id=? AND session_id=?",
          requestId,
          existing.id(),
          sessionId);
      return new Prepared(existing.id(), context, history(sessionId), null);
    }
    List<RagGateway.History> history = history(sessionId);
    UUID userMessageId = UUID.randomUUID();
    UUID assistantId = UUID.randomUUID();
    jdbc.update(
        "INSERT INTO csas.chat_messages(id,session_id,role,content,created_at) VALUES (?,?,'USER',?,now())",
        userMessageId,
        sessionId,
        content);
    jdbc.update(
        """
        INSERT INTO csas.chat_messages(
          id,session_id,role,status,concept_ids,request_id,request_key,request_hash,user_message_id,created_at)
        VALUES (?,?,'ASSISTANT','pending','[]',?,?,?,?,now())
        """,
        assistantId,
        sessionId,
        requestId,
        key,
        requestHash,
        userMessageId);
    jdbc.update(
        "UPDATE csas.chat_sessions SET title=CASE WHEN title='새 CS 질문' THEN left(?,200) ELSE title END,updated_at=now() WHERE id=? AND user_id=?",
        content,
        sessionId,
        userId);
    return new Prepared(assistantId, context, history, null);
  }

  private ChatAnswerResponse complete(
      UUID userId, UUID sessionId, UUID messageId, RagGateway.Answer response) {
    requireOwnedSession(userId, sessionId);
    int updated =
        jdbc.update(
            """
        UPDATE csas.chat_messages
           SET content=?,status=?,concept_ids=?,request_id=?,model_version=?,index_version=?,
               prompt_version=?,failure_code=NULL
         WHERE id=? AND session_id=? AND role='ASSISTANT' AND status='pending'
        """,
            response.answer(),
            response.status(),
            json(response.conceptIds()),
            response.requestId(),
            response.modelVersion(),
            response.indexVersion(),
            response.promptVersion(),
            messageId,
            sessionId);
    if (updated != 1) {
      throw new IllegalStateException("Pending assistant message was not found");
    }
    List<SourceResponse> sources = storeCitations(messageId, response);
    jdbc.update(
        "UPDATE csas.chat_sessions SET updated_at=now() WHERE id=? AND user_id=?",
        sessionId,
        userId);
    return new ChatAnswerResponse(
        response.requestId(),
        messageId,
        response.status(),
        response.answer(),
        sources,
        response.conceptIds());
  }

  private void markFailed(UUID userId, UUID sessionId, UUID messageId, String code) {
    jdbc.update(
        """
        UPDATE csas.chat_messages m SET status='failed',failure_code=?
          FROM csas.chat_sessions s
         WHERE m.id=? AND m.session_id=s.id AND s.id=? AND s.user_id=? AND m.status='pending'
        """,
        code,
        messageId,
        sessionId,
        userId);
    jdbc.update(
        "UPDATE csas.chat_sessions SET updated_at=now() WHERE id=? AND user_id=?",
        sessionId,
        userId);
  }

  private List<SourceResponse> storeCitations(UUID messageId, RagGateway.Answer response) {
    List<SourceResponse> sources = new ArrayList<>();
    Set<String> cited = new HashSet<>(response.citedChunkIds());
    int ordinal = 0;
    for (RagGateway.RetrievedChunk chunk : response.retrievedChunks()) {
      if (!cited.contains(chunk.chunkId())) {
        continue;
      }
      jdbc.update(
          """
          INSERT INTO csas.message_citations(
            message_id,ordinal,source_id,document_id,revision,chunk_id,index_version,title,url,locator)
          VALUES (?,?,?,?,?,?,?,?,?,?)
          """,
          messageId,
          ordinal++,
          chunk.sourceId(),
          chunk.documentId(),
          chunk.revision(),
          chunk.chunkId(),
          response.indexVersion(),
          chunk.title(),
          chunk.url(),
          chunk.locator());
      sources.add(source(chunk, response.indexVersion()));
    }
    return sources;
  }

  private Existing findByKey(UUID userId, UUID sessionId, UUID key) {
    var rows =
        jdbc.query(
            """
        SELECT m.id,m.status,m.content,m.request_id,m.request_hash,m.concept_ids
          FROM csas.chat_messages m JOIN csas.chat_sessions s ON s.id=m.session_id
         WHERE m.session_id=? AND m.request_key=? AND s.user_id=?
        """,
            (rs, row) ->
                new Existing(
                    rs.getObject("id", UUID.class),
                    rs.getString("status"),
                    rs.getString("content"),
                    rs.getString("request_id"),
                    rs.getString("request_hash"),
                    concepts(rs.getString("concept_ids"))),
            sessionId,
            key,
            userId);
    return rows.isEmpty() ? null : rows.getFirst();
  }

  private ChatAnswerResponse storedAnswer(Existing row) {
    return new ChatAnswerResponse(
        row.requestId(),
        row.id(),
        row.status(),
        row.content(),
        citations(row.id()),
        row.conceptIds());
  }

  private List<SourceResponse> citations(UUID messageId) {
    return jdbc.query(
        """
        SELECT source_id,document_id,revision,chunk_id,index_version,title,url,locator
          FROM csas.message_citations WHERE message_id=? ORDER BY ordinal
        """,
        (rs, row) ->
            new SourceResponse(
                rs.getString("source_id"),
                rs.getString("document_id"),
                rs.getString("revision"),
                rs.getString("chunk_id"),
                rs.getString("index_version"),
                rs.getString("title"),
                rs.getString("url"),
                rs.getString("locator")),
        messageId);
  }

  private static SourceResponse source(RagGateway.RetrievedChunk chunk, String indexVersion) {
    return new SourceResponse(
        chunk.sourceId(),
        chunk.documentId(),
        chunk.revision(),
        chunk.chunkId(),
        indexVersion,
        chunk.title(),
        chunk.url(),
        chunk.locator());
  }

  private SessionContext loadContext(UUID userId, UUID sessionId) {
    var rows =
        jdbc.query(
            """
        SELECT a.id attempt_id,a.quiz_id,a.selected_option_id,a.correct_option_id,a.is_correct,
               a.explanation_snapshot,q.stem
          FROM csas.chat_sessions s
          LEFT JOIN csas.quiz_attempts a ON a.id=s.context_attempt_id
          LEFT JOIN csas.quizzes q ON q.id=a.quiz_id
         WHERE s.id=? AND s.user_id=?
        """,
            (rs, row) ->
                rs.getObject("attempt_id") == null
                    ? null
                    : new SessionContext(
                        rs.getObject("attempt_id", UUID.class),
                        rs.getObject("quiz_id", UUID.class),
                        rs.getObject("selected_option_id", UUID.class),
                        rs.getObject("correct_option_id", UUID.class),
                        rs.getBoolean("is_correct"),
                        rs.getString("explanation_snapshot"),
                        rs.getString("stem")),
            sessionId,
            userId);
    if (rows.isEmpty()) {
      throw notFound();
    }
    SessionContext context = rows.getFirst();
    if (context != null) {
      context.options =
          jdbc.query(
              "SELECT id,text FROM csas.quiz_options WHERE quiz_id=? ORDER BY position",
              (rs, row) ->
                  new RagGateway.Option(rs.getObject("id", UUID.class), rs.getString("text")),
              context.quizId);
      context.conceptIds =
          jdbc.query(
              "SELECT concept_id FROM csas.quiz_concepts WHERE quiz_id=? ORDER BY concept_id",
              (rs, row) -> rs.getString(1),
              context.quizId);
    }
    return context;
  }

  private List<RagGateway.History> history(UUID sessionId) {
    return jdbc.query(
        """
        SELECT role,content FROM (
          SELECT role,content,sequence_no FROM csas.chat_messages
           WHERE session_id=? AND content IS NOT NULL ORDER BY sequence_no DESC LIMIT 12
        ) recent ORDER BY sequence_no
        """,
        (rs, row) ->
            new RagGateway.History(rs.getString("role").toLowerCase(), rs.getString("content")),
        sessionId);
  }

  private void requireOwnedSession(UUID userId, UUID sessionId) {
    Integer count =
        jdbc.queryForObject(
            "SELECT count(*) FROM csas.chat_sessions WHERE id=? AND user_id=?",
            Integer.class,
            sessionId,
            userId);
    if (count == null || count == 0) {
      throw notFound();
    }
  }

  private void validateResponse(String requestId, RagGateway.Answer answer) {
    if (!requestId.equals(answer.requestId())
        || !ragConfiguration.activeIndex().equals(answer.indexVersion())
        || !("answered".equals(answer.status())
            || "insufficient_evidence".equals(answer.status()))) {
      throw new ApiException(502, "RAG_FAILED", "RAG response validation failed.");
    }
    Set<String> retrieved = new HashSet<>();
    answer.retrievedChunks().forEach(chunk -> retrieved.add(chunk.chunkId()));
    if (!retrieved.containsAll(answer.citedChunkIds())
        || ("answered".equals(answer.status())
            && (answer.answer() == null || answer.citedChunkIds().isEmpty()))
        || ("insufficient_evidence".equals(answer.status())
            && (answer.answer() != null || !answer.citedChunkIds().isEmpty()))) {
      throw new ApiException(502, "RAG_FAILED", "RAG response validation failed.");
    }
    for (String concept : answer.conceptIds()) {
      Integer count =
          jdbc.queryForObject(
              "SELECT count(*) FROM csas.concepts WHERE id=?", Integer.class, concept);
      if (count == null || count == 0) {
        throw new ApiException(502, "RAG_FAILED", "RAG response validation failed.");
      }
    }
  }

  private static ChatSessionResponse session(ResultSet rs) throws SQLException {
    return new ChatSessionResponse(
        rs.getObject("id", UUID.class),
        rs.getString("title"),
        rs.getObject("quiz_id", UUID.class),
        rs.getObject("context_attempt_id", UUID.class),
        rs.getTimestamp("created_at").toInstant(),
        rs.getTimestamp("updated_at").toInstant());
  }

  private static void validatePage(int page, int limit) {
    if (page < 0 || limit < 1 || limit > MAX_PAGE_SIZE || page > Integer.MAX_VALUE / limit) {
      throw new ApiException(400, "INVALID_INPUT", "Invalid pagination.");
    }
  }

  private static String normalizeTitle(String title) {
    return title == null || title.isBlank() ? "새 CS 질문" : title.trim();
  }

  private static String hash(String value) {
    try {
      return HexFormat.of()
          .formatHex(
              MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8)));
    } catch (NoSuchAlgorithmException ex) {
      throw new IllegalStateException("SHA-256 unavailable", ex);
    }
  }

  private String json(Object value) {
    try {
      return mapper.writeValueAsString(value);
    } catch (JsonProcessingException ex) {
      throw new IllegalStateException("JSON serialization failed", ex);
    }
  }

  private List<String> concepts(String value) {
    try {
      return mapper.readValue(value == null ? "[]" : value, new TypeReference<>() {});
    } catch (JsonProcessingException ex) {
      throw new IllegalStateException("Stored concept IDs are invalid", ex);
    }
  }

  private static ApiException notFound() {
    return new ApiException(404, "RESOURCE_NOT_FOUND", "Chat session not found.");
  }

  private record Prepared(
      UUID assistantId,
      SessionContext context,
      List<RagGateway.History> history,
      ChatAnswerResponse replay) {}

  private record Existing(
      UUID id,
      String status,
      String content,
      String requestId,
      String requestHash,
      List<String> conceptIds) {}

  private static class SessionContext {
    final UUID attemptId;
    final UUID quizId;
    final UUID selectedOptionId;
    final UUID correctOptionId;
    final boolean correct;
    final String explanation;
    final String stem;
    List<RagGateway.Option> options = List.of();
    List<String> conceptIds = List.of();

    SessionContext(
        UUID attemptId,
        UUID quizId,
        UUID selectedOptionId,
        UUID correctOptionId,
        boolean correct,
        String explanation,
        String stem) {
      this.attemptId = attemptId;
      this.quizId = quizId;
      this.selectedOptionId = selectedOptionId;
      this.correctOptionId = correctOptionId;
      this.correct = correct;
      this.explanation = explanation;
      this.stem = stem;
    }

    RagGateway.QuizContext toRag() {
      return new RagGateway.QuizContext(
          quizId,
          attemptId,
          stem,
          options,
          selectedOptionId,
          correctOptionId,
          correct,
          explanation,
          conceptIds);
    }
  }
}
