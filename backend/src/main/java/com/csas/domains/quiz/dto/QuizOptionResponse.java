package com.csas.domains.quiz.dto;

import java.util.UUID;

public record QuizOptionResponse(UUID id, int position, String text) {}
