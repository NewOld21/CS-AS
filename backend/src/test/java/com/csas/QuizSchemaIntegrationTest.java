package com.csas;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.support.TransactionTemplate;

class QuizSchemaIntegrationTest extends HttpTestSupport {
  @Autowired JdbcTemplate jdbc;
  @Autowired TransactionTemplate transactions;

  @Test
  void migrationCreatesCuratedQuizTablesAndIndexes() {
    assertThat(
            jdbc.queryForList(
                """
                SELECT table_name FROM information_schema.tables
                 WHERE table_schema='csas'
                   AND table_name IN ('concepts', 'quizzes', 'quiz_options', 'quiz_concepts')
                 ORDER BY table_name
                """,
                String.class))
        .containsExactly("concepts", "quiz_concepts", "quiz_options", "quizzes");
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.flyway_schema_history WHERE version='3' AND success",
                Integer.class))
        .isEqualTo(1);
  }

  @Test
  void foreignKeysAndDisplayOrderUniquenessRejectInvalidData() {
    UUID quizId = UUID.randomUUID();
    assertThatThrownBy(
            () ->
                jdbc.update(
                    "INSERT INTO csas.quiz_options(id, quiz_id, position, text) VALUES (?, ?, 1, 'x')",
                    UUID.randomUUID(),
                    quizId))
        .isInstanceOf(DataIntegrityViolationException.class);

    insertDraft(quizId);
    jdbc.update(
        "INSERT INTO csas.quiz_options(id, quiz_id, position, text) VALUES (?, ?, 1, 'first')",
        UUID.randomUUID(),
        quizId);
    assertThatThrownBy(
            () ->
                jdbc.update(
                    "INSERT INTO csas.quiz_options(id, quiz_id, position, text) VALUES (?, ?, 1, 'duplicate')",
                    UUID.randomUUID(),
                    quizId))
        .isInstanceOf(DataIntegrityViolationException.class);
    assertThatThrownBy(
            () ->
                jdbc.update(
                    "INSERT INTO csas.quiz_concepts(quiz_id, concept_id, is_primary) VALUES (?, 'concept:missing', true)",
                    quizId))
        .isInstanceOf(DataIntegrityViolationException.class);
  }

  @Test
  void readyQuizRequiresFourOptionsOneAnswerAndOnePrimaryConcept() {
    UUID quizId = UUID.randomUUID();
    assertThatThrownBy(
            () ->
                transactions.executeWithoutResult(
                    ignored -> {
                      insertDraft(quizId);
                      jdbc.update("UPDATE csas.quizzes SET status='READY' WHERE id=?", quizId);
                    }))
        .isInstanceOf(DataIntegrityViolationException.class);

    transactions.executeWithoutResult(
        ignored -> {
          insertDraft(quizId);
          insertConcept("concept:test-publication");
          jdbc.update(
              "INSERT INTO csas.quiz_concepts(quiz_id, concept_id, is_primary) VALUES (?, 'concept:test-publication', true)",
              quizId);
          for (int position = 1; position <= 4; position++) {
            jdbc.update(
                "INSERT INTO csas.quiz_options(id, quiz_id, position, text, is_correct) VALUES (?, ?, ?, ?, ?)",
                UUID.randomUUID(),
                quizId,
                position,
                "option " + position,
                position == 2);
          }
          jdbc.update("UPDATE csas.quizzes SET status='READY' WHERE id=?", quizId);
        });
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.quizzes WHERE id=? AND status='READY'",
                Integer.class,
                quizId))
        .isEqualTo(1);
  }

  private void insertDraft(UUID id) {
    jdbc.update(
        """
        INSERT INTO csas.quizzes(
            id, family_id, version, stem, category, difficulty, origin, status,
            explanation, source_url, reviewed_at)
        VALUES (?, ?, 1, 'schema test?', 'DATABASE', 'EASY', 'CURATED', 'DRAFT',
                'schema explanation', 'https://example.com/reference', now())
        """,
        id,
        id);
  }

  private void insertConcept(String id) {
    jdbc.update(
        """
        INSERT INTO csas.concepts(id, slug, name_ko, name_en, category, description)
        VALUES (?, 'test-publication', '테스트', 'Test', 'DATABASE', 'Schema test concept')
        ON CONFLICT DO NOTHING
        """,
        id);
  }
}
