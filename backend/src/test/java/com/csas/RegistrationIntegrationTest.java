package com.csas;

import static org.assertj.core.api.Assertions.assertThat;

import com.csas.domains.auth.repository.UserRepository;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.Executors;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;

class RegistrationIntegrationTest extends HttpTestSupport {
  private static final String PASSWORD = "correct-horse-battery";
  @Autowired UserRepository users;
  @Autowired PasswordEncoder passwords;
  @Autowired JdbcTemplate jdbc;

  private String email() {
    return UUID.randomUUID() + "@example.com";
  }

  @Test
  void signupPersistsHashAndPublicDtoWithoutLoggingIn() throws Exception {
    var browser = browser();
    browser.refreshCsrf();
    String email = email();
    var response =
        browser.request(
            "POST",
            "/api/v1/auth/signup",
            Map.of(
                "email",
                " " + email.toUpperCase() + " ",
                "password",
                PASSWORD,
                "nickname",
                " learner "),
            true);
    assertThat(response.status()).isEqualTo(201);
    assertThat(UUID.fromString(response.body().get("id").asText())).isNotNull();
    assertThat(response.body().get("email").asText()).isEqualTo(email);
    assertThat(response.body().get("nickname").asText()).isEqualTo("learner");
    assertThat(response.body().size()).isEqualTo(3);
    var user = users.findByEmail(email).orElseThrow();
    assertThat(user.getPasswordHash()).startsWith("$2a$12$").isNotEqualTo(PASSWORD);
    assertThat(passwords.matches(PASSWORD, user.getPasswordHash())).isTrue();
    assertThat(passwords.matches("incorrect-password", user.getPasswordHash())).isFalse();
    assertThat(browser.request("GET", "/api/v1/auth/me", null, false).status()).isEqualTo(401);
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.flyway_schema_history WHERE version='2' AND success",
                Integer.class))
        .isEqualTo(1);
  }

  @Test
  void duplicateAndCaseVariantsReturn409() throws Exception {
    var browser = browser();
    browser.refreshCsrf();
    String email = email();
    assertThat(
            browser
                .request(
                    "POST",
                    "/api/v1/auth/signup",
                    Map.of("email", email, "password", PASSWORD),
                    true)
                .status())
        .isEqualTo(201);
    var duplicate =
        browser.request(
            "POST",
            "/api/v1/auth/signup",
            Map.of("email", email.toUpperCase(), "password", PASSWORD),
            true);
    assertThat(duplicate.status()).isEqualTo(409);
    assertThat(duplicate.body().get("code").asText()).isEqualTo("EMAIL_ALREADY_EXISTS");
    assertThat(duplicate.body().hasNonNull("request_id")).isTrue();
    assertThat(duplicate.body().hasNonNull("timestamp")).isTrue();
  }

  @Test
  void invalidInputsAndUnexpectedFieldsAreRejected() throws Exception {
    var browser = browser();
    browser.refreshCsrf();
    for (var body : ListInputs.invalid(PASSWORD)) {
      var response = browser.request("POST", "/api/v1/auth/signup", body, true);
      assertThat(response.status()).as("invalid request").isEqualTo(400);
      assertThat(response.body().get("code").asText()).isEqualTo("INVALID_INPUT");
      assertThat(response.body().toString()).doesNotContain(PASSWORD);
    }
  }

  @Test
  void csrfIsRequiredEvenForSignup() throws Exception {
    assertThat(
            browser()
                .request(
                    "POST",
                    "/api/v1/auth/signup",
                    Map.of("email", email(), "password", PASSWORD),
                    false)
                .status())
        .isEqualTo(403);
  }

  @Test
  void concurrentSignupHasOneWinnerAndDatabaseUniqueConstraint() throws Exception {
    String email = email();
    var first = browser();
    var second = browser();
    first.refreshCsrf();
    second.refreshCsrf();
    Callable<Integer> a =
        () ->
            first
                .request(
                    "POST",
                    "/api/v1/auth/signup",
                    Map.of("email", email, "password", PASSWORD),
                    true)
                .status();
    Callable<Integer> b =
        () ->
            second
                .request(
                    "POST",
                    "/api/v1/auth/signup",
                    Map.of("email", email.toUpperCase(), "password", PASSWORD),
                    true)
                .status();
    try (var pool = Executors.newFixedThreadPool(2)) {
      var results = pool.invokeAll(java.util.List.of(a, b));
      assertThat(java.util.List.of(results.get(0).get(), results.get(1).get()))
          .containsExactlyInAnyOrder(201, 409);
    }
    assertThat(
            jdbc.queryForObject(
                "SELECT count(*) FROM csas.users WHERE email_normalized=?", Integer.class, email))
        .isEqualTo(1);
  }

  private static class ListInputs {
    static java.util.List<Map<String, String>> invalid(String password) {
      return java.util.List.of(
          Map.of("email", "not-an-email", "password", password),
          Map.of("email", "", "password", password),
          Map.of("email", "valid@example.com", "password", "short"),
          Map.of("email", "valid@example.com", "password", "a".repeat(73)),
          Map.of("email", "valid@example.com", "password", "가".repeat(25)),
          Map.of("email", "valid@example.com", "password", password, "nickname", "   "),
          Map.of("email", "valid@example.com", "password", password, "role", "ADMIN"),
          Map.of("email", "valid@example.com"));
    }
  }
}
