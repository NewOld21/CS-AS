package com.csas.domains.learning.dto;

import java.util.List;

public record StatsResponse(
    long total_attempts,
    long correct_attempts,
    Double accuracy,
    long unique_quizzes,
    long needs_review,
    long resolved_reviews,
    List<CategoryStats> by_category) {
  public record CategoryStats(
      String category, long total_attempts, long correct_attempts, Double accuracy) {}
}
