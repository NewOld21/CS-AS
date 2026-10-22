package com.csas.domains.quiz.controller;

import com.csas.common.security.CurrentUser;
import com.csas.domains.quiz.dto.CategoryResponse;
import com.csas.domains.quiz.dto.QuizPageResponse;
import com.csas.domains.quiz.dto.QuizResponse;
import com.csas.domains.quiz.service.QuizCatalogService;
import java.util.List;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class QuizController {
  private final CurrentUser currentUser;
  private final QuizCatalogService quizzes;

  public QuizController(CurrentUser currentUser, QuizCatalogService quizzes) {
    this.currentUser = currentUser;
    this.quizzes = quizzes;
  }

  @GetMapping("/api/v1/quiz/categories")
  List<CategoryResponse> categories() {
    return quizzes.categories(currentUser.id());
  }

  @GetMapping("/api/v1/quizzes")
  QuizPageResponse list(
      @RequestParam(required = false) String cursor,
      @RequestParam(defaultValue = "20") int limit,
      @RequestParam(required = false) String category,
      @RequestParam(required = false) String difficulty,
      @RequestParam(name = "concept_id", required = false) String conceptId) {
    return quizzes.list(currentUser.id(), category, difficulty, conceptId, cursor, limit);
  }

  @GetMapping("/api/v1/quizzes/{quizId}")
  QuizResponse get(@PathVariable UUID quizId) {
    return quizzes.get(currentUser.id(), quizId);
  }
}
