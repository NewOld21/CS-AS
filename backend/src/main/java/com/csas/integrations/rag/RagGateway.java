package com.csas.integrations.rag;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import java.util.List;
import java.util.UUID;

public interface RagGateway {
  Answer answer(AnswerRequest request);

  @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
  record AnswerRequest(
      String requestId,
      String deadlineAt,
      String indexVersion,
      String question,
      List<History> history,
      QuizContext quizContext) {}

  record History(String role, String content) {}

  @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
  record QuizContext(
      UUID quizId,
      UUID attemptId,
      String stem,
      List<Option> options,
      UUID selectedOptionId,
      UUID correctOptionId,
      boolean isCorrect,
      String explanation,
      List<String> conceptIds) {}

  record Option(UUID id, String text) {}

  record Answer(
      String requestId,
      String status,
      List<String> conceptIds,
      String answer,
      List<RetrievedChunk> retrievedChunks,
      List<String> citedChunkIds,
      String indexVersion,
      String modelVersion,
      String promptVersion) {}

  record RetrievedChunk(
      String sourceId,
      String documentId,
      String revision,
      String chunkId,
      String title,
      String url,
      String locator) {}
}
