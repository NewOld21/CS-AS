package com.csas.domains.quiz.dto;

import java.util.List;
import java.util.UUID;

public record QuizResponse(
    UUID id,
    int version,
    String stem,
    String category,
    String difficulty,
    String origin,
    List<String> concept_ids,
    List<QuizOptionResponse> options) {}
