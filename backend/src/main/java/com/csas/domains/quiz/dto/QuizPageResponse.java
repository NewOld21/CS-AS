package com.csas.domains.quiz.dto;

import java.util.List;

public record QuizPageResponse(List<QuizResponse> items, String next_cursor) {}
