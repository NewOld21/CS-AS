package com.csas;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.CookieManager;
import java.net.CookiePolicy;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
abstract class HttpTestSupport {
  @LocalServerPort int port;
  @Autowired ObjectMapper mapper;

  protected Browser browser() {
    return new Browser();
  }

  protected class Browser {
    final CookieManager cookies = new CookieManager(null, CookiePolicy.ACCEPT_ALL);
    final HttpClient client =
        HttpClient.newBuilder()
            .cookieHandler(cookies)
            .connectTimeout(Duration.ofSeconds(5))
            .build();
    String csrf;

    String refreshCsrf() throws Exception {
      csrf = request("GET", "/api/v1/auth/csrf", null, false).body().get("token").asText();
      return csrf;
    }

    Result request(String method, String path, Object body, boolean withCsrf) throws Exception {
      return request(method, path, body, withCsrf, Map.of());
    }

    Result request(
        String method, String path, Object body, boolean withCsrf, Map<String, String> headers)
        throws Exception {
      var builder =
          HttpRequest.newBuilder(URI.create("http://localhost:" + port + path))
              .timeout(Duration.ofSeconds(30));
      if (withCsrf) {
        builder.header("X-CSRF-Token", csrf);
      }
      if (body != null) {
        builder.header("Content-Type", "application/json");
      }
      headers.forEach(builder::header);
      var response =
          client.send(
              builder
                  .method(
                      method,
                      body == null
                          ? HttpRequest.BodyPublishers.noBody()
                          : HttpRequest.BodyPublishers.ofString(mapper.writeValueAsString(body)))
                  .build(),
              HttpResponse.BodyHandlers.ofString());
      return new Result(
          response.statusCode(),
          response.body().isEmpty() ? mapper.nullNode() : mapper.readTree(response.body()),
          response.headers().allValues("set-cookie"));
    }

    String sessionId() {
      return cookies.getCookieStore().getCookies().stream()
          .filter(c -> c.getName().equals("CSAS_SESSION"))
          .findFirst()
          .orElseThrow()
          .getValue();
    }
  }

  protected record Result(int status, JsonNode body, List<String> cookies) {}
}
