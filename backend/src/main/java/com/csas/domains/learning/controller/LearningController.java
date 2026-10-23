package com.csas.domains.learning.controller;

import com.csas.common.security.CurrentUser;
import com.csas.domains.learning.dto.AttemptPageResponse;
import com.csas.domains.learning.dto.AttemptResultResponse;
import com.csas.domains.learning.service.HistoryService;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class LearningController {
  private final CurrentUser user;
  private final HistoryService history;

  public LearningController(CurrentUser user, HistoryService history) {
    this.user = user;
    this.history = history;
  }

  @GetMapping("/api/v1/me/attempts")
  AttemptPageResponse list(
      @RequestParam(required = false) String cursor,
      @RequestParam(defaultValue = "20") int limit,
      @RequestParam(required = false) String category,
      @RequestParam(required = false) Boolean correct,
      @RequestParam(required = false) String origin) {
    return history.list(user.id(), cursor, limit, category, correct, origin);
  }

  @GetMapping("/api/v1/me/attempts/{attemptId}")
  AttemptResultResponse detail(@PathVariable UUID attemptId) {
    return history.detail(user.id(), attemptId);
  }
}
