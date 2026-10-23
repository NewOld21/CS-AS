package com.csas.domains.learning.dto;

import com.csas.domains.quiz.dto.QuizResponse;
import java.time.Instant;
import java.util.UUID;

public record ReviewItemResponse(
    QuizResponse quiz,
    String status,
    UUID latest_attempt_id,
    Instant first_wrong_at,
    Instant last_wrong_at,
    Instant last_reviewed_at,
    long wrong_attempts,
    boolean retryable) {}
