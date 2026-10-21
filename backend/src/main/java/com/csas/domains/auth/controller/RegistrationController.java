package com.csas.domains.auth.controller;

import com.csas.domains.auth.dto.SignupRequest;
import com.csas.domains.auth.dto.UserResponse;
import com.csas.domains.auth.service.RegistrationService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RegistrationController {
  private final RegistrationService registration;

  public RegistrationController(RegistrationService registration) {
    this.registration = registration;
  }

  @PostMapping("/api/v1/auth/signup")
  @ResponseStatus(HttpStatus.CREATED)
  UserResponse signup(@Valid @RequestBody SignupRequest request) {
    return registration.register(request);
  }
}
