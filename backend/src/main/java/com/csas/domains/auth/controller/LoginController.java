package com.csas.domains.auth.controller;

import com.csas.common.security.AuthenticatedUser;
import com.csas.common.security.SessionAuthenticator;
import com.csas.domains.auth.dto.LoginRequest;
import com.csas.domains.auth.dto.UserResponse;
import com.csas.domains.auth.service.LoginService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class LoginController {
  private final LoginService login;
  private final SessionAuthenticator sessions;

  public LoginController(LoginService login, SessionAuthenticator sessions) {
    this.login = login;
    this.sessions = sessions;
  }

  @PostMapping("/api/v1/auth/login")
  UserResponse login(
      @Valid @RequestBody LoginRequest input,
      HttpServletRequest request,
      HttpServletResponse response) {
    var user = login.authenticate(input);
    sessions.login(new AuthenticatedUser(user.id()), request, response);
    return user;
  }

  @GetMapping("/api/v1/auth/me")
  UserResponse me(@AuthenticationPrincipal AuthenticatedUser user) {
    return login.current(user.id());
  }
}
