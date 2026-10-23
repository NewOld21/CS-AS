package com.csas.integrations.rag;

import com.csas.common.exception.ApiException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class HttpRagGateway implements RagGateway {
  private final HttpClient http;
  private final ObjectMapper mapper;
  private final URI endpoint;
  private final String token;
  private final String activeIndex;
  private final int requestTimeoutSeconds;

  public HttpRagGateway(
      ObjectMapper mapper,
      @Value("${csas.rag.base-url:http://127.0.0.1:8090}") String baseUrl,
      @Value("${csas.rag.service-token:}") String token,
      @Value("${csas.rag.active-index:cs-v1}") String activeIndex,
      @Value("${csas.rag.request-timeout-seconds:30}") int requestTimeoutSeconds) {
    if (requestTimeoutSeconds < 5 || requestTimeoutSeconds > 120) {
      throw new IllegalArgumentException("RAG request timeout must be between 5 and 120 seconds");
    }
    this.mapper = mapper;
    this.token = token;
    this.activeIndex = activeIndex;
    this.requestTimeoutSeconds = requestTimeoutSeconds;
    this.endpoint = URI.create(baseUrl + "/internal/v1/answers");
    this.http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build();
  }

  public String activeIndex() {
    return activeIndex;
  }

  public String deadlineAt() {
    return Instant.now().plusSeconds(requestTimeoutSeconds - 2L).toString();
  }

  @Override
  public JsonNode generate(JsonNode request) {
    if (token.length() < 32) {
      throw new ApiException(503, "RAG_UNAVAILABLE", "RAG service is not configured.");
    }
    try {
      HttpRequest httpRequest =
          HttpRequest.newBuilder(endpoint.resolve("quiz-candidates"))
              .timeout(Duration.ofSeconds(requestTimeoutSeconds))
              .header("Content-Type", "application/json")
              .header("X-Request-Id", request.path("request_id").asText())
              .header("Authorization", "Bearer " + token)
              .POST(HttpRequest.BodyPublishers.ofString(mapper.writeValueAsString(request)))
              .build();
      var response = http.send(httpRequest, HttpResponse.BodyHandlers.ofString());
      if (response.statusCode() == 504) {
        throw new ApiException(504, "RAG_TIMEOUT", "Quiz service timed out.");
      }
      if (response.statusCode() != 200) {
        throw new ApiException(502, "RAG_FAILED", "Quiz service failed.");
      }
      return mapper.readTree(response.body());
    } catch (java.net.http.HttpTimeoutException ex) {
      throw new ApiException(504, "RAG_TIMEOUT", "Quiz service timed out.");
    } catch (InterruptedException ex) {
      Thread.currentThread().interrupt();
      throw new ApiException(504, "RAG_TIMEOUT", "Quiz service timed out.");
    } catch (IOException | IllegalArgumentException ex) {
      throw new ApiException(502, "RAG_FAILED", "Quiz service failed.");
    }
  }

  @Override
  public Answer answer(AnswerRequest request) {
    if (token.length() < 32) {
      throw new ApiException(503, "RAG_UNAVAILABLE", "RAG service is not configured.");
    }
    try {
      HttpRequest httpRequest =
          HttpRequest.newBuilder(endpoint)
              .timeout(Duration.ofSeconds(requestTimeoutSeconds))
              .header("Content-Type", "application/json")
              .header("X-Request-Id", request.requestId())
              .header("Authorization", "Bearer " + token)
              .POST(HttpRequest.BodyPublishers.ofString(mapper.writeValueAsString(request)))
              .build();
      HttpResponse<String> response = http.send(httpRequest, HttpResponse.BodyHandlers.ofString());
      if (response.statusCode() == 504) {
        throw new ApiException(504, "RAG_TIMEOUT", "RAG service timed out.");
      }
      if (response.statusCode() != 200) {
        throw new ApiException(502, "RAG_FAILED", "RAG service failed.");
      }
      JsonNode body = mapper.readTree(response.body());
      List<RetrievedChunk> chunks = new ArrayList<>();
      for (JsonNode row : body.path("retrieved_chunks")) {
        chunks.add(
            new RetrievedChunk(
                text(row, "source_id"),
                text(row, "document_id"),
                text(row, "revision"),
                text(row, "chunk_id"),
                text(row, "title"),
                text(row, "url"),
                text(row, "locator"),
                row.path("evidence_text").isTextual() ? row.path("evidence_text").asText() : null,
                row.path("category").isTextual() ? row.path("category").asText() : null,
                row.path("technology_version").isTextual()
                    ? row.path("technology_version").asText()
                    : null));
      }
      return new Answer(
          text(body, "request_id"),
          text(body, "status"),
          strings(body.path("concept_ids")),
          body.path("answer").isNull() ? null : body.path("answer").asText(),
          chunks,
          strings(body.path("cited_chunk_ids")),
          text(body, "index_version"),
          text(body, "model_version"),
          text(body, "prompt_version"));
    } catch (java.net.http.HttpTimeoutException ex) {
      throw new ApiException(504, "RAG_TIMEOUT", "RAG service timed out.");
    } catch (InterruptedException ex) {
      Thread.currentThread().interrupt();
      throw new ApiException(504, "RAG_TIMEOUT", "RAG service timed out.");
    } catch (IOException | IllegalArgumentException ex) {
      throw new ApiException(502, "RAG_FAILED", "RAG service failed.");
    }
  }

  private static String text(JsonNode node, String name) throws IOException {
    JsonNode value = node.get(name);
    if (value == null || !value.isTextual() || value.asText().isBlank()) {
      throw new IOException("Invalid RAG response");
    }
    return value.asText();
  }

  private static List<String> strings(JsonNode node) throws IOException {
    if (!node.isArray()) {
      throw new IOException("Invalid RAG response");
    }
    List<String> values = new ArrayList<>();
    for (JsonNode value : node) {
      if (!value.isTextual()) {
        throw new IOException("Invalid RAG response");
      }
      values.add(value.asText());
    }
    return values;
  }
}
