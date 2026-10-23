package com.csas.domains.generation;

import com.csas.common.exception.ApiException;
import com.csas.domains.quiz.service.QuizCatalogService;
import com.csas.integrations.rag.HttpRagGateway;
import com.csas.integrations.rag.RagGateway;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

@Service
public class GenerationService {
  private final JdbcTemplate jdbc;
  private final ObjectMapper mapper;
  private final TransactionTemplate tx;
  private final RagGateway rag;
  private final HttpRagGateway configuration;
  private final QuizCatalogService quizzes;

  public GenerationService(
      JdbcTemplate jdbc,
      ObjectMapper mapper,
      TransactionTemplate tx,
      RagGateway rag,
      HttpRagGateway configuration,
      QuizCatalogService quizzes) {
    this.jdbc = jdbc;
    this.mapper = mapper;
    this.tx = tx;
    this.rag = rag;
    this.configuration = configuration;
    this.quizzes = quizzes;
  }

  public GenerationResult generate(UUID user, UUID key, GenerationRequest input) {
    String hash = hash(json(input));
    Prepared prepared = tx.execute(status -> prepare(user, key, input, hash));
    if (prepared == null) {
      throw new IllegalStateException("Missing generation");
    }
    if (prepared.replay() != null) {
      return prepared.replay();
    }
    UUID id = prepared.id();
    try {
      var request = mapper.createObjectNode();
      request
          .put("request_id", id.toString())
          .put("deadline_at", configuration.deadlineAt())
          .put("index_version", configuration.activeIndex())
          .put("difficulty", input.difficulty())
          .put("learning_context", prepared.context());
      request.set("concept_ids", mapper.valueToTree(prepared.concepts()));
      request.set("concept_labels", mapper.valueToTree(prepared.labels()));
      JsonNode response = rag.generate(request);
      return tx.execute(status -> complete(user, id, input, prepared.concepts(), response));
    } catch (RuntimeException ex) {
      String code = ex instanceof ApiException api ? api.code() : "GENERATION_SAVE_FAILED";
      tx.executeWithoutResult(
          status ->
              jdbc.update(
                  "UPDATE csas.generation_requests SET status='FAILED',failure_code=? WHERE id=? AND user_id=? AND status IN ('GENERATING','VALIDATING')",
                  code,
                  id,
                  user));
      throw ex;
    }
  }

  private Prepared prepare(UUID user, UUID key, GenerationRequest input, String hash) {
    jdbc.query("SELECT pg_advisory_xact_lock(hashtextextended(?,0))", rs -> {}, user + ":" + key);
    var old =
        jdbc.queryForList(
            "SELECT id,request_hash FROM csas.generation_requests WHERE user_id=? AND idempotency_key=?",
            user,
            key);
    if (!old.isEmpty()) {
      if (!hash.equals(old.getFirst().get("request_hash"))) {
        throw new ApiException(409, "IDEMPOTENCY_CONFLICT", "Request key was reused.");
      }
      return new Prepared(null, List.of(), List.of(), "", recover(user, key));
    }
    String context = "";
    Set<String> contextual = new HashSet<>();
    if (input.chat_session_id() != null) {
      var sessions =
          jdbc.queryForList(
              "SELECT id FROM csas.chat_sessions WHERE id=? AND user_id=?",
              input.chat_session_id(),
              user);
      if (sessions.isEmpty()) {
        throw new ApiException(404, "RESOURCE_NOT_FOUND", "Chat not found.");
      }
      var recent =
          jdbc.queryForList(
              "SELECT content,concept_ids FROM csas.chat_messages WHERE session_id=? AND content IS NOT NULL ORDER BY sequence_no DESC LIMIT 6",
              input.chat_session_id());
      for (var row : recent) {
        context += String.valueOf(row.get("content")) + "\n";
        contextual.addAll(strings(String.valueOf(row.get("concept_ids"))));
      }
      contextual.addAll(
          jdbc.queryForList(
              "SELECT qc.concept_id FROM csas.chat_sessions s JOIN csas.quiz_attempts a ON a.id=s.context_attempt_id JOIN csas.quiz_concepts qc ON qc.quiz_id=a.quiz_id WHERE s.id=? AND s.user_id=?",
              String.class,
              input.chat_session_id(),
              user));
    }
    var concepts = new ArrayList<>(input.concept_ids());
    if (new HashSet<>(concepts).size() != concepts.size()) {
      throw new ApiException(400, "INVALID_INPUT", "Duplicate concepts.");
    }
    if (concepts.isEmpty()) {
      if (!contextual.isEmpty()) {
        concepts.addAll(contextual.stream().sorted().limit(5).toList());
      } else {
        String text = context.toLowerCase(Locale.ROOT);
        jdbc.query(
            "SELECT id,name_ko,name_en FROM csas.concepts ORDER BY id",
            rs -> {
              if (text.contains(rs.getString("name_ko").toLowerCase(Locale.ROOT))
                  || text.contains(rs.getString("name_en").toLowerCase(Locale.ROOT))) {
                concepts.add(rs.getString("id"));
              }
            });
      }
    } else if (input.chat_session_id() != null && !contextual.containsAll(concepts)) {
      throw new ApiException(
          400, "INVALID_CONCEPT_CONTEXT", "Concepts do not belong to this chat.");
    }
    if (concepts.isEmpty() || concepts.size() > 5) {
      throw new ApiException(400, "CONCEPT_REQUIRED", "Choose a registered concept.");
    }
    List<String> labels = new ArrayList<>();
    for (String concept : concepts) {
      var rows =
          jdbc.queryForList("SELECT name_ko FROM csas.concepts WHERE id=?", String.class, concept);
      if (rows.isEmpty()) {
        throw new ApiException(400, "INVALID_CONCEPT", "Unknown concept.");
      }
      labels.add(rows.getFirst());
    }
    UUID id = UUID.randomUUID();
    jdbc.update(
        "INSERT INTO csas.generation_requests(id,user_id,chat_session_id,idempotency_key,request_hash,concept_ids,difficulty,status) VALUES (?,?,?,?,?,?,?,'GENERATING')",
        id,
        user,
        input.chat_session_id(),
        key,
        hash,
        json(concepts),
        input.difficulty());
    return new Prepared(
        id, concepts, labels, context.substring(0, Math.min(context.length(), 2000)), null);
  }

  public GenerationResult recover(UUID user, UUID key) {
    var rows =
        jdbc.queryForList(
            "SELECT id,status,outcome,quiz_id,failure_code FROM csas.generation_requests WHERE user_id=? AND idempotency_key=?",
            user,
            key);
    if (rows.isEmpty()) {
      throw new ApiException(404, "RESOURCE_NOT_FOUND", "Generation not found.");
    }
    var row = rows.getFirst();
    String status = String.valueOf(row.get("status"));
    if (status.equals("GENERATING") || status.equals("VALIDATING")) {
      throw new ApiException(409, "GENERATION_IN_PROGRESS", "Generation is in progress.");
    }
    if (status.equals("FAILED")) {
      String code = String.valueOf(row.get("failure_code"));
      int httpStatus =
          switch (code) {
            case "RAG_TIMEOUT" -> 504;
            case "RAG_UNAVAILABLE" -> 503;
            case "GENERATION_SAVE_FAILED" -> 500;
            default -> 502;
          };
      throw new ApiException(httpStatus, code, "Stored generation failed. Use a new request key.");
    }
    UUID quiz = (UUID) row.get("quiz_id");
    return new GenerationResult(
        (UUID) row.get("id"),
        String.valueOf(row.get("outcome")),
        quiz == null ? null : quizzes.get(user, quiz));
  }

  private GenerationResult complete(
      UUID user, UUID id, GenerationRequest input, List<String> concepts, JsonNode response) {
    if (response == null
        || !id.toString().equals(response.path("request_id").asText())
        || !configuration.activeIndex().equals(response.path("index_version").asText())) {
      throw invalid();
    }
    String state = response.path("status").asText();
    boolean passed = state.equals("validated");
    if (!passed && !Set.of("insufficient_evidence", "validation_failed").contains(state)) {
      throw invalid();
    }
    if (!passed && !response.path("candidate").isNull()) {
      throw invalid();
    }
    jdbc.update(
        "UPDATE csas.generation_requests SET status='VALIDATING' WHERE id=? AND user_id=? AND status='GENERATING'",
        id,
        user);
    if (passed) {
      checkCandidate(response, concepts, input.difficulty());
    }
    jdbc.update(
        "INSERT INTO csas.generation_validations(generation_id,report,reason_codes,passed) VALUES (?,?,?,?)",
        id,
        json(response.path("validation_report")),
        json(response.path("reason_codes")),
        passed);
    UUID quizId = null;
    if (passed) {
      var c = response.path("candidate");
      Integer duplicate =
          jdbc.queryForObject(
              "SELECT count(*) FROM csas.quizzes WHERE (origin='CURATED' OR owner_user_id=?) AND lower(btrim(stem))=lower(btrim(?))",
              Integer.class,
              user,
              c.path("stem").asText());
      if (duplicate != null && duplicate > 0) {
        throw new ApiException(502, "DUPLICATE_GENERATED_QUIZ", "Duplicate generated question.");
      }
      quizId = UUID.randomUUID();
      String category =
          jdbc.queryForObject(
              "SELECT category FROM csas.concepts WHERE id=?", String.class, concepts.getFirst());
      JsonNode first = response.path("retrieved_chunks").get(0);
      jdbc.update(
          "INSERT INTO csas.quizzes(id,family_id,version,stem,category,difficulty,origin,status,owner_user_id,explanation,source_url,reviewed_at) VALUES (?,?,1,?,?,?,'AI_GENERATED','DRAFT',?,?,?,now())",
          quizId,
          quizId,
          c.path("stem").asText(),
          category,
          input.difficulty(),
          user,
          c.path("explanation").asText(),
          first.path("url").asText());
      for (var option : c.path("options")) {
        jdbc.update(
            "INSERT INTO csas.quiz_options(id,quiz_id,position,text,is_correct) VALUES (?,?,?,?,?)",
            UUID.randomUUID(),
            quizId,
            option.path("position").asInt(),
            option.path("text").asText(),
            option.path("position").asInt() == c.path("correct_option_position").asInt());
      }
      int index = 0;
      for (var concept : c.path("concept_ids")) {
        jdbc.update(
            "INSERT INTO csas.quiz_concepts VALUES (?,?,?)",
            quizId,
            concept.asText(),
            index++ == 0);
      }
      int ordinal = 0;
      Set<String> cited = new HashSet<>(strings(json(c.path("evidence_chunk_ids"))));
      for (var chunk : response.path("retrieved_chunks")) {
        if (cited.contains(chunk.path("chunk_id").asText())) {
          jdbc.update(
              "INSERT INTO csas.quiz_evidence(quiz_id,ordinal,source_id,document_id,revision,chunk_id,index_version,title,url,locator,evidence_text,category,technology_version) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
              quizId,
              ordinal++,
              chunk.path("source_id").asText(),
              chunk.path("document_id").asText(),
              chunk.path("revision").asText(),
              chunk.path("chunk_id").asText(),
              configuration.activeIndex(),
              chunk.path("title").asText(),
              chunk.path("url").asText(),
              chunk.path("locator").asText(),
              chunk.path("evidence_text").asText(),
              chunk.path("category").asText(null),
              chunk.path("technology_version").asText(null));
        }
      }
      jdbc.update("UPDATE csas.quizzes SET status='READY' WHERE id=?", quizId);
    }
    String outcome = passed ? "ready" : state;
    jdbc.update(
        "UPDATE csas.generation_requests SET status=?,outcome=?,quiz_id=?,model_version=?,prompt_version=?,validator_version=?,index_version=?,corpus_digest=? WHERE id=? AND user_id=?",
        passed ? "READY" : "REJECTED",
        outcome,
        quizId,
        response.path("model_version").asText(),
        response.path("prompt_version").asText(),
        response.path("validator_version").asText(),
        response.path("index_version").asText(),
        response.path("corpus_digest").asText(),
        id,
        user);
    return new GenerationResult(id, outcome, quizId == null ? null : quizzes.get(user, quizId));
  }

  private void checkCandidate(JsonNode response, List<String> concepts, String difficulty) {
    JsonNode c = response.path("candidate");
    if (!c.isObject()
        || c.size() != 7
        || !text(c, "stem", 2000)
        || !text(c, "explanation", 4000)
        || !difficulty.equals(c.path("difficulty").asText())
        || !c.path("options").isArray()
        || c.path("options").size() != 4
        || !c.path("correct_option_position").isIntegralNumber()
        || c.path("correct_option_position").asInt() < 1
        || c.path("correct_option_position").asInt() > 4) {
      throw invalid();
    }
    List<String> ids = strings(json(c.path("concept_ids")));
    if (ids.isEmpty() || new HashSet<>(ids).size() != ids.size() || !concepts.containsAll(ids)) {
      throw invalid();
    }
    Set<Integer> positions = new HashSet<>();
    Set<String> options = new HashSet<>();
    for (var o : c.path("options")) {
      if (o.size() != 2
          || !text(o, "text", 1000)
          || !o.path("position").isIntegralNumber()
          || o.path("position").asInt() < 1
          || o.path("position").asInt() > 4
          || !positions.add(o.path("position").asInt())
          || !options.add(o.path("text").asText().strip().toLowerCase(Locale.ROOT))) {
        throw invalid();
      }
    }
    Set<String> stages = new HashSet<>();
    for (var v : response.path("validation_report")) {
      if (!v.path("passed").isBoolean() || !v.path("passed").asBoolean()) {
        throw invalid();
      }
      stages.add(v.path("stage").asText());
    }
    if (!stages.equals(Set.of("structure", "blind_solution", "evidence_audit"))
        || !response.path("reason_codes").isArray()
        || !response.path("reason_codes").isEmpty()) {
      throw invalid();
    }
    if (!text(response, "model_version", 128)
        || !text(response, "prompt_version", 128)
        || !text(response, "validator_version", 128)) {
      throw invalid();
    }
    Set<String> available = new HashSet<>();
    if (!response.path("retrieved_chunks").isArray()
        || response.path("retrieved_chunks").size() > 5) {
      throw invalid();
    }
    for (var r : response.path("retrieved_chunks")) {
      for (String field :
          List.of(
              "source_id",
              "document_id",
              "revision",
              "chunk_id",
              "title",
              "url",
              "locator",
              "evidence_text")) {
        if (!text(r, field, 16000)) {
          throw invalid();
        }
      }
      java.net.URI uri;
      try {
        uri = java.net.URI.create(r.path("url").asText());
      } catch (IllegalArgumentException ex) {
        throw invalid();
      }
      if (!"https".equals(uri.getScheme())
          || uri.getHost() == null
          || uri.getUserInfo() != null
          || !available.add(r.path("chunk_id").asText())) {
        throw invalid();
      }
    }
    var cited = strings(json(c.path("evidence_chunk_ids")));
    if (cited.isEmpty()
        || new HashSet<>(cited).size() != cited.size()
        || !available.containsAll(cited)) {
      throw invalid();
    }
  }

  private static boolean text(JsonNode node, String key, int max) {
    var n = node.path(key);
    return n.isTextual() && !n.asText().isBlank() && n.asText().length() <= max;
  }

  private String json(Object value) {
    try {
      return mapper.writeValueAsString(value);
    } catch (java.io.IOException ex) {
      throw new IllegalStateException(ex);
    }
  }

  private List<String> strings(String value) {
    try {
      return mapper.readValue(value, new TypeReference<List<String>>() {});
    } catch (java.io.IOException ex) {
      throw invalid();
    }
  }

  private static String hash(String value) {
    try {
      return HexFormat.of()
          .formatHex(
              MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8)));
    } catch (NoSuchAlgorithmException ex) {
      throw new IllegalStateException(ex);
    }
  }

  private static ApiException invalid() {
    return new ApiException(502, "GENERATION_INVALID", "Unverifiable generation response.");
  }

  private record Prepared(
      UUID id,
      List<String> concepts,
      List<String> labels,
      String context,
      GenerationResult replay) {}
}
