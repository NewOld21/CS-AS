package com.csas.domains.generation;

import com.csas.domains.quiz.dto.QuizResponse;
import java.util.UUID;

public record GenerationResult(UUID generation_id, String status, QuizResponse quiz) {}
