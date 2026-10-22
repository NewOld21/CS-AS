package com.csas.domains.learning.controller;

import com.csas.common.exception.ApiException;
import com.csas.common.security.CurrentUser;
import com.csas.domains.learning.dto.AttemptRequest;
import com.csas.domains.learning.dto.AttemptResultResponse;
import com.csas.domains.learning.service.QuizAttemptService;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class QuizAttemptController {
  private final CurrentUser currentUser;
  private final QuizAttemptService attempts;

  public QuizAttemptController(CurrentUser currentUser, QuizAttemptService attempts) {
    this.currentUser = currentUser;
    this.attempts = attempts;
  }

  @PostMapping("/api/v1/quizzes/{quizId}/attempts")
  AttemptResultResponse submit(
      @PathVariable UUID quizId,
      @RequestHeader(name = "Idempotency-Key", required = false) String idempotencyKey,
      @Valid @RequestBody AttemptRequest request) {
    if (idempotencyKey == null) {
      throw new ApiException(400, "INVALID_INPUT", "Idempotency-Key is required.");
    }
    try {
      return attempts.submit(currentUser.id(), quizId, UUID.fromString(idempotencyKey), request);
    } catch (IllegalArgumentException ex) {
      throw new ApiException(400, "INVALID_INPUT", "Invalid Idempotency-Key.");
    }
  }
}
