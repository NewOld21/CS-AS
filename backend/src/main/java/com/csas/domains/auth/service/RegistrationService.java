package com.csas.domains.auth.service;

import com.csas.common.exception.ApiException;
import com.csas.domains.auth.dto.SignupRequest;
import com.csas.domains.auth.dto.UserResponse;
import com.csas.domains.auth.entity.User;
import com.csas.domains.auth.repository.UserRepository;
import org.hibernate.exception.ConstraintViolationException;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class RegistrationService {
  private final UserRepository users;
  private final PasswordEncoder passwords;

  public RegistrationService(UserRepository users, PasswordEncoder passwords) {
    this.users = users;
    this.passwords = passwords;
  }

  @Transactional
  public UserResponse register(SignupRequest request) {
    if (users.existsByEmail(request.email())) {
      throw duplicate();
    }
    try {
      return UserResponse.from(
          users.saveAndFlush(
              new User(request.email(), passwords.encode(request.password()), request.nickname())));
    } catch (DataIntegrityViolationException ex) {
      for (Throwable cause = ex; cause != null; cause = cause.getCause()) {
        if (cause instanceof ConstraintViolationException constraint
            && "users_email_normalized_key".equals(constraint.getConstraintName())) {
          throw duplicate();
        }
      }
      throw ex;
    }
  }

  private ApiException duplicate() {
    return new ApiException(409, "EMAIL_ALREADY_EXISTS", "Email is already registered.");
  }
}
