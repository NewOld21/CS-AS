package com.csas.common.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

public class SessionLifetimeFilter extends OncePerRequestFilter {
  private final Clock clock;
  private final Duration maximumAge;

  public SessionLifetimeFilter(Clock clock, Duration maximumAge) {
    this.clock = clock;
    this.maximumAge = maximumAge;
  }

  @Override
  protected void doFilterInternal(
      HttpServletRequest request, HttpServletResponse response, FilterChain chain)
      throws ServletException, IOException {
    var session = request.getSession(false);
    if (session != null
        && session.getAttribute(SessionAuthenticator.AUTHENTICATED_AT)
            instanceof Long authenticatedAt
        && clock.millis() - authenticatedAt >= maximumAge.toMillis()) {
      session.invalidate();
      SecurityContextHolder.clearContext();
    }
    chain.doFilter(request, response);
  }
}
