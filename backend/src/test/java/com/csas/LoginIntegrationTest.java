package com.csas;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.reset;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Clock;
import java.time.Duration;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;

class LoginIntegrationTest extends HttpTestSupport {
  static final String PASSWORD = "correct-horse-battery";
  @MockitoSpyBean Clock clock;

  private String email() {
    return UUID.randomUUID() + "@example.com";
  }

  @Test
  void loginRotatesSessionAndPersistsAuthenticatedIdentity() throws Exception {
    var browser = browser();
    browser.refreshCsrf();
    String email = email();
    var registered =
        browser.request(
            "POST", "/api/v1/auth/signup", Map.of("email", email, "password", PASSWORD), true);
    String previous = browser.sessionId();
    var response =
        browser.request(
            "POST",
            "/api/v1/auth/login",
            Map.of("email", email.toUpperCase(), "password", PASSWORD),
            true);
    assertThat(response.status()).isEqualTo(200);
    assertThat(response.body()).isEqualTo(registered.body());
    assertThat(browser.sessionId()).isNotEqualTo(previous);
    assertThat(String.join(";", response.cookies())).contains("HttpOnly", "SameSite=Lax");
    assertThat(browser.request("GET", "/api/v1/auth/me", null, false).body())
        .isEqualTo(registered.body());
    assertThat(withCookie(previous, "/api/v1/auth/me")).isEqualTo(401);
    // The pre-authentication CSRF token must not survive successful login.
    assertThat(
            browser
                .request(
                    "POST",
                    "/api/v1/auth/signup",
                    Map.of("email", email(), "password", PASSWORD),
                    true)
                .status())
        .isEqualTo(403);
    browser.refreshCsrf();
    assertThat(browser.request("GET", "/api/v1/auth/me", null, false).status()).isEqualTo(200);
  }

  @Test
  void wrongPasswordAndUnknownEmailReturnSameFailure() throws Exception {
    var browser = browser();
    browser.refreshCsrf();
    String email = email();
    browser.request(
        "POST", "/api/v1/auth/signup", Map.of("email", email, "password", PASSWORD), true);
    var wrong =
        browser.request(
            "POST",
            "/api/v1/auth/login",
            Map.of("email", email, "password", "incorrect-password"),
            true);
    var missing =
        browser.request(
            "POST", "/api/v1/auth/login", Map.of("email", email(), "password", PASSWORD), true);
    assertThat(wrong.status()).isEqualTo(401);
    assertThat(missing.status()).isEqualTo(401);
    assertThat(wrong.body().get("code")).isEqualTo(missing.body().get("code"));
    assertThat(wrong.body().get("message")).isEqualTo(missing.body().get("message"));
    assertThat(browser.request("GET", "/api/v1/auth/me", null, false).status()).isEqualTo(401);
  }

  @Test
  void absoluteLifetimeRejectsPreviouslyValidCookie() throws Exception {
    var browser = browser();
    browser.refreshCsrf();
    String email = email();
    browser.request(
        "POST", "/api/v1/auth/signup", Map.of("email", email, "password", PASSWORD), true);
    assertThat(
            browser
                .request(
                    "POST",
                    "/api/v1/auth/login",
                    Map.of("email", email, "password", PASSWORD),
                    true)
                .status())
        .isEqualTo(200);
    long afterExpiry = clock.millis() + Duration.ofHours(12).toMillis();
    doReturn(afterExpiry).when(clock).millis();
    try {
      assertThat(browser.request("GET", "/api/v1/auth/me", null, false).status()).isEqualTo(401);
    } finally {
      reset(clock);
    }
  }

  @Test
  void anonymousAndForgedCookiesCannotReadCurrentUser() throws Exception {
    assertThat(browser().request("GET", "/api/v1/auth/me", null, false).status()).isEqualTo(401);
    assertThat(withCookie("forged-session", "/api/v1/auth/me")).isEqualTo(401);
  }

  private int withCookie(String cookie, String path) throws Exception {
    return HttpClient.newHttpClient()
        .send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + path))
                .header("Cookie", "CSAS_SESSION=" + cookie)
                .GET()
                .build(),
            HttpResponse.BodyHandlers.discarding())
        .statusCode();
  }
}
