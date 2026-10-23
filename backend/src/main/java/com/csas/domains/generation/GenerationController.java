package com.csas.domains.generation;

import com.csas.common.exception.ApiException;
import com.csas.common.security.CurrentUser;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class GenerationController {
  private final CurrentUser currentUser;
  private final GenerationService service;

  public GenerationController(CurrentUser currentUser, GenerationService service) {
    this.currentUser = currentUser;
    this.service = service;
  }

  @PostMapping("/api/v1/quiz-generations")
  GenerationResult generate(
      @Valid @RequestBody GenerationRequest request,
      @RequestHeader(name = "Idempotency-Key") String key) {
    UUID id;
    try {
      id = UUID.fromString(key);
    } catch (IllegalArgumentException ex) {
      throw new ApiException(400, "INVALID_INPUT", "Invalid idempotency key.");
    }
    return service.generate(currentUser.id(), id, request);
  }

  @GetMapping("/api/v1/quiz-generations/{key}")
  GenerationResult recover(@PathVariable UUID key) {
    return service.recover(currentUser.id(), key);
  }
}
