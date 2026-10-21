package com.csas.domains.auth.dto;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

public record SignupRequest(
    @NotBlank @Email @Size(max = 254) String email,
    @NotBlank @Size(min = 12, max = 128) String password,
    @Size(min = 1, max = 40) String nickname) {
  public SignupRequest {
    email = email == null ? null : email.strip().toLowerCase(Locale.ROOT);
    nickname = nickname == null ? null : nickname.strip();
  }

  @AssertTrue
  public boolean isPasswordWithinByteLimit() {
    return password == null || password.getBytes(StandardCharsets.UTF_8).length <= 72;
  }

  @Override
  public String toString() {
    return "SignupRequest[REDACTED]";
  }
}
