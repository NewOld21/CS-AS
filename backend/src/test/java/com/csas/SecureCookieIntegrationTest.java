package com.csas;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.test.context.TestPropertySource;

@TestPropertySource(properties = "server.servlet.session.cookie.secure=true")
class SecureCookieIntegrationTest extends HttpTestSupport {
  @Test
  void productionCookieFlagsAreEnforcedByServletContainer() throws Exception {
    var response = browser().request("GET", "/api/v1/auth/csrf", null, false);
    assertThat(response.status()).isEqualTo(200);
    assertThat(String.join(";", response.cookies())).contains("Secure", "HttpOnly", "SameSite=Lax");
  }
}
