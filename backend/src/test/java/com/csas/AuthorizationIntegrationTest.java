package com.csas;

import static org.assertj.core.api.Assertions.assertThat;

import com.csas.common.security.CurrentUser;
import jakarta.servlet.http.HttpSession;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;
import org.springframework.context.annotation.Import;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

@Import(AuthorizationIntegrationTest.OwnershipFixture.class)
@ExtendWith(OutputCaptureExtension.class)
class AuthorizationIntegrationTest extends HttpTestSupport {
  private static final String PASSWORD = "correct-horse-battery";

  private Account account() throws Exception {
    var browser = browser();
    browser.refreshCsrf();
    String email = UUID.randomUUID() + "@example.com";
    var body = Map.of("email", email, "password", PASSWORD);
    var signup = browser.request("POST", "/api/v1/auth/signup", body, true);
    assertThat(signup.status()).isEqualTo(201);
    assertThat(browser.request("POST", "/api/v1/auth/login", body, true).status()).isEqualTo(200);
    browser.refreshCsrf();
    return new Account(browser, UUID.fromString(signup.body().get("id").asText()));
  }

  @Test
  void anonymousLearningReadsAndWritesAreJson401() throws Exception {
    var browser = browser();
    for (String path :
        java.util.List.of(
            "/api/v1/quizzes",
            "/api/v1/me/attempts",
            "/api/v1/me/wrong-answers",
            "/api/v1/me/stats",
            "/api/v1/chat/sessions",
            "/api/v1/auth/me")) {
      var result = browser.request("GET", path, null, false);
      assertThat(result.status()).as(path).isEqualTo(401);
      assertThat(result.body().get("code").asText()).isEqualTo("AUTH_REQUIRED");
      assertThat(result.body().size()).isEqualTo(4);
    }
    for (String path :
        java.util.List.of(
            "/api/v1/quizzes/" + UUID.randomUUID() + "/attempts",
            "/api/v1/chat/sessions",
            "/api/v1/quiz-generations",
            "/api/v1/auth/logout")) {
      assertThat(browser.request("POST", path, Map.of(), false).status()).as(path).isEqualTo(401);
    }
  }

  @Test
  void ownerCanReadAndOtherUserGets404WithNoData() throws Exception {
    var first = account();
    var second = account();
    String path = "/api/v1/test-owned/" + first.id();
    assertThat(first.browser().request("GET", path, null, false).status()).isEqualTo(200);
    var denied = second.browser().request("GET", path, null, false);
    assertThat(denied.status()).isEqualTo(404);
    assertThat(denied.body().toString()).doesNotContain(first.id().toString());
    assertThat(first.browser().request("GET", "/api/v1/test-admin", null, false).status())
        .isEqualTo(403);
    // Real learning handlers do not exist: authenticated requests reach routing, not a fake 200.
    assertThat(first.browser().request("GET", "/api/v1/me/attempts", null, false).status())
        .isEqualTo(404);
  }

  @Test
  void logoutInvalidatesServerSessionAndRejectsExactCookieReplay(CapturedOutput output)
      throws Exception {
    var account = account();
    var browser = account.browser();
    String cookie = browser.sessionId();
    assertThat(browser.request("POST", "/api/v1/auth/logout", Map.of(), false).status())
        .isEqualTo(403);
    assertThat(browser.request("GET", "/api/v1/auth/me", null, false).status()).isEqualTo(200);
    var logout = browser.request("POST", "/api/v1/auth/logout", null, true);
    assertThat(logout.status()).isEqualTo(204);
    assertThat(String.join(";", logout.cookies())).contains("CSAS_SESSION=", "Max-Age=0");
    var replay =
        HttpClient.newHttpClient()
            .send(
                HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/api/v1/auth/me"))
                    .header("Cookie", "CSAS_SESSION=" + cookie)
                    .GET()
                    .build(),
                HttpResponse.BodyHandlers.ofString());
    assertThat(replay.statusCode()).isEqualTo(401);
    assertThat(mapper.readTree(replay.body()).get("code").asText()).isEqualTo("AUTH_REQUIRED");
    assertThat(browser.request("GET", "/api/v1/auth/me", null, false).status()).isEqualTo(401);
    assertThat(browser.request("POST", "/api/v1/auth/logout", null, true).status()).isEqualTo(401);
    assertThat(output).doesNotContain(PASSWORD, "$2a$12$");
  }

  @Test
  void idleExpirationRejectsCookieOverRealHttp() throws Exception {
    var account = account();
    assertThat(account.browser().request("POST", "/api/v1/test-expire-idle", null, true).status())
        .isEqualTo(200);
    Thread.sleep(2100);
    assertThat(account.browser().request("GET", "/api/v1/auth/me", null, false).status())
        .isEqualTo(401);
  }

  @Test
  void localCorsAllowsOnlyConfiguredOrigin() throws Exception {
    for (String origin : java.util.List.of("http://localhost:5173", "https://untrusted.example")) {
      var response =
          HttpClient.newHttpClient()
              .send(
                  HttpRequest.newBuilder(
                          URI.create("http://localhost:" + port + "/api/v1/auth/login"))
                      .header("Origin", origin)
                      .header("Access-Control-Request-Method", "POST")
                      .header("Access-Control-Request-Headers", "content-type,x-csrf-token")
                      .method("OPTIONS", HttpRequest.BodyPublishers.noBody())
                      .build(),
                  HttpResponse.BodyHandlers.discarding());
      assertThat(response.statusCode()).isEqualTo(origin.contains("localhost") ? 200 : 403);
      if (response.statusCode() == 200) {
        assertThat(response.headers().firstValue("Access-Control-Allow-Origin")).contains(origin);
        assertThat(response.headers().firstValue("Access-Control-Allow-Credentials"))
            .contains("true");
      }
    }
  }

  private record Account(Browser browser, UUID id) {}

  // Test-only resource: no learning schema or mock product endpoint is installed in the app.
  @RestController
  public static class OwnershipFixture {
    private final CurrentUser current;

    public OwnershipFixture(CurrentUser current) {
      this.current = current;
    }

    @GetMapping("/api/v1/test-owned/{ownerId}")
    Map<String, UUID> owned(@PathVariable UUID ownerId) {
      current.requireOwner(ownerId);
      return Map.of("owner_id", current.id());
    }

    @GetMapping("/api/v1/test-admin")
    @PreAuthorize("hasRole('ADMIN')")
    Map<String, Boolean> admin() {
      return Map.of("allowed", true);
    }

    @PostMapping("/api/v1/test-expire-idle")
    Map<String, Boolean> expire(HttpSession session) {
      session.setMaxInactiveInterval(1);
      return Map.of("scheduled", true);
    }
  }
}
