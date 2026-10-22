package com.csas.domains.learning.dto;

import com.csas.domains.quiz.dto.QuizResponse;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record AttemptResultResponse(
    UUID id,
    QuizResponse quiz,
    UUID selected_option_id,
    UUID correct_option_id,
    boolean is_correct,
    String explanation,
    List<SourceResponse> sources,
    Instant submitted_at) {}
