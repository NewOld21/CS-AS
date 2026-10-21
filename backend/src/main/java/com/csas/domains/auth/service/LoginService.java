package com.csas.domains.auth.service;

import com.csas.common.exception.ApiException;
import com.csas.domains.auth.dto.LoginRequest;
import com.csas.domains.auth.dto.UserResponse;
import com.csas.domains.auth.repository.UserRepository;
import java.util.UUID;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class LoginService {
  private final UserRepository users;
  private final PasswordEncoder passwords;
  private final String dummyHash;

  public LoginService(UserRepository users, PasswordEncoder passwords) {
    this.users = users;
    this.passwords = passwords;
    this.dummyHash = passwords.encode(UUID.randomUUID().toString());
  }

  @Transactional(readOnly = true)
  public UserResponse authenticate(LoginRequest request) {
    var user = users.findByEmail(request.email());
    boolean matches =
        passwords.matches(
            request.password(), user.map(value -> value.getPasswordHash()).orElse(dummyHash));
    if (user.isEmpty() || !matches) {
      throw new ApiException(401, "INVALID_CREDENTIALS", "Invalid email or password.");
    }
    return UserResponse.from(user.get());
  }

  @Transactional(readOnly = true)
  public UserResponse current(UUID id) {
    return users
        .findById(id)
        .map(UserResponse::from)
        .orElseThrow(() -> new ApiException(401, "AUTH_REQUIRED", "Authentication is required."));
  }
}
