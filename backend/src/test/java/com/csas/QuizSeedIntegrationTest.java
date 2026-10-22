package com.csas;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

class QuizSeedIntegrationTest extends HttpTestSupport {
  @Autowired JdbcTemplate jdbc;

  @Test
  void seedContainsFifteenReviewedReadyQuestionsInRequiredDistribution() {
    assertThat(seedCount()).isEqualTo(15);
    Map<String, Integer> distribution =
        jdbc.query(
            """
            SELECT category, count(*) FROM csas.quizzes
             WHERE id::text LIKE '10000000-0000-0000-0000-0000000000%'
             GROUP BY category
            """,
            rs -> {
              var result = new java.util.HashMap<String, Integer>();
              while (rs.next()) {
                result.put(rs.getString(1), rs.getInt(2));
              }
              return result;
            });
    assertThat(distribution)
        .containsExactlyInAnyOrderEntriesOf(
            Map.of(
                "OPERATING_SYSTEM", 3,
                "NETWORK", 3,
                "DATABASE", 3,
                "DATA_STRUCTURE", 2,
                "ALGORITHM", 2,
                "COMPUTER_ARCHITECTURE", 2));
    assertThat(
            jdbc.queryForObject(
                """
                SELECT count(*) FROM csas.quizzes
                 WHERE id::text LIKE '10000000-0000-0000-0000-0000000000%'
                   AND (status <> 'READY' OR source_url IS NULL OR reviewed_at IS NULL
                        OR btrim(explanation) = '')
                """,
                Integer.class))
        .isZero();
  }

  @Test
  void everySeedQuestionHasFourDistinctOptionsOneAnswerAndPrimaryConcept() {
    assertThat(
            jdbc.queryForObject(
                """
                SELECT count(*) FROM (
                    SELECT q.id
                      FROM csas.quizzes q
                      JOIN csas.quiz_options o ON o.quiz_id=q.id
                      JOIN csas.quiz_concepts c ON c.quiz_id=q.id
                     WHERE q.id::text LIKE '10000000-0000-0000-0000-0000000000%'
                     GROUP BY q.id
                    HAVING count(DISTINCT o.id) <> 4
                        OR count(DISTINCT o.id) FILTER (WHERE o.is_correct) <> 1
                        OR count(DISTINCT o.text) <> 4
                        OR count(DISTINCT c.concept_id) FILTER (WHERE c.is_primary) <> 1
                ) invalid
                """,
                Integer.class))
        .isZero();
  }

  @Test
  void stableIdentifiersMakeTheSeedIdempotent() {
    assertThat(
            jdbc.queryForObject(
                "SELECT count(DISTINCT family_id) FROM csas.quizzes WHERE id::text LIKE '10000000-0000-0000-0000-0000000000%'",
                Integer.class))
        .isEqualTo(15);
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.quiz_options WHERE id::text LIKE '20000000-0000-0000-0000-0000000000%'",
                Integer.class))
        .isEqualTo(60);
    assertThat(seedCount()).isEqualTo(15);
  }

  private int seedCount() {
    return jdbc.queryForObject(
        "SELECT count(*) FROM csas.quizzes WHERE id::text LIKE '10000000-0000-0000-0000-0000000000%'",
        Integer.class);
  }
}
