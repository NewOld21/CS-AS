package com.csas.domains.chat.service;

import com.csas.common.exception.ApiException;
import com.csas.domains.chat.dto.ChatAnswerResponse;
import com.csas.domains.chat.dto.ChatQuestionRequest;
import com.csas.domains.chat.dto.ChatSessionResponse;
import com.csas.domains.chat.dto.CreateChatSessionRequest;
import com.csas.domains.learning.dto.SourceResponse;
import com.csas.integrations.rag.HttpRagGateway;
import com.csas.integrations.rag.RagGateway;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ChatService {
  private final JdbcTemplate jdbc;
  private final RagGateway rag;
  private final HttpRagGateway ragConfiguration;
  private final ObjectMapper mapper;

  public ChatService(
      JdbcTemplate jdbc, RagGateway rag, HttpRagGateway ragConfiguration, ObjectMapper mapper) {
    this.jdbc = jdbc;
    this.rag = rag;
    this.ragConfiguration = ragConfiguration;
    this.mapper = mapper;
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
        throw new ApiException(404, "RESOURCE_NOT_FOUND", "Attempt not found.");
      }
    }
    UUID id = UUID.randomUUID();
    Instant created = Instant.now();
    jdbc.update(
        "INSERT INTO csas.chat_sessions(id,user_id,context_attempt_id,created_at) VALUES (?,?,?,?)",
        id,
        userId,
        request.attempt_id(),
        Timestamp.from(created));
    return new ChatSessionResponse(id, request.quiz_id(), request.attempt_id(), created);
  }

  @Transactional
  public ChatAnswerResponse ask(
      UUID userId, UUID sessionId, ChatQuestionRequest question, String requestId) {
    jdbc.query(
        "SELECT pg_advisory_xact_lock(hashtextextended(?, 0))",
        resultSet -> {},
        sessionId.toString());
    SessionContext context = loadContext(userId, sessionId);
    List<RagGateway.History> history = history(sessionId);
    jdbc.update(
        "INSERT INTO csas.chat_messages(id,session_id,role,content,created_at) VALUES (?,?, 'USER', ?, now())",
        UUID.randomUUID(),
        sessionId,
        question.question().trim());
    RagGateway.Answer response =
        rag.answer(
            new RagGateway.AnswerRequest(
                requestId,
                ragConfiguration.deadlineAt(),
                ragConfiguration.activeIndex(),
                question.question().trim(),
                history,
                context == null ? null : context.toRag()));
    validateResponse(requestId, response);
    UUID messageId = UUID.randomUUID();
    jdbc.update(
        """
        INSERT INTO csas.chat_messages(
          id,session_id,role,content,status,concept_ids,request_id,model_version,index_version,prompt_version,created_at)
        VALUES (?,?,'ASSISTANT',?,?,?,?,?,?,?,now())
        """,
        messageId,
        sessionId,
        response.answer(),
        response.status(),
        json(response.conceptIds()),
        requestId,
        response.modelVersion(),
        response.indexVersion(),
        response.promptVersion());
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
      sources.add(
          new SourceResponse(
              chunk.sourceId(),
              chunk.documentId(),
              chunk.revision(),
              chunk.chunkId(),
              response.indexVersion(),
              chunk.title(),
              chunk.url(),
              chunk.locator()));
    }
    return new ChatAnswerResponse(
        requestId, messageId, response.status(), response.answer(), sources, response.conceptIds());
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
      throw new ApiException(404, "RESOURCE_NOT_FOUND", "Chat session not found.");
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
          SELECT role,content,created_at,id FROM csas.chat_messages
           WHERE session_id=? AND content IS NOT NULL ORDER BY created_at DESC,id DESC LIMIT 12
        ) recent ORDER BY created_at,id
        """,
        (rs, row) ->
            new RagGateway.History(rs.getString("role").toLowerCase(), rs.getString("content")),
        sessionId);
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

  private String json(Object value) {
    try {
      return mapper.writeValueAsString(value);
    } catch (JsonProcessingException ex) {
      throw new IllegalStateException("JSON serialization failed", ex);
    }
  }

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
