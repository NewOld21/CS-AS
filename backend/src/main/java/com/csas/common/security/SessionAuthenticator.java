package com.csas.common.security;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.time.Clock;
import java.util.List;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.session.SessionAuthenticationStrategy;
import org.springframework.security.web.context.SecurityContextRepository;
import org.springframework.stereotype.Component;

@Component
public class SessionAuthenticator {
  public static final String AUTHENTICATED_AT =
      SessionAuthenticator.class.getName() + ".authenticatedAt";
  private final SecurityContextRepository contexts;
  private final SessionAuthenticationStrategy sessions;
  private final Clock clock;

  public SessionAuthenticator(
      SecurityContextRepository contexts, SessionAuthenticationStrategy sessions, Clock clock) {
    this.contexts = contexts;
    this.sessions = sessions;
    this.clock = clock;
  }

  public void login(
      AuthenticatedUser user, HttpServletRequest request, HttpServletResponse response) {
    var authentication =
        UsernamePasswordAuthenticationToken.authenticated(
            user, null, List.of(new SimpleGrantedAuthority("ROLE_USER")));
    sessions.onAuthentication(authentication, request, response);
    var context = SecurityContextHolder.createEmptyContext();
    context.setAuthentication(authentication);
    SecurityContextHolder.setContext(context);
    contexts.saveContext(context, request, response);
    request.getSession().setAttribute(AUTHENTICATED_AT, clock.millis());
  }
}
