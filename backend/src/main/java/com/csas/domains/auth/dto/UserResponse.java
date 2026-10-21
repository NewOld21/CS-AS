package com.csas.domains.auth.dto;

import com.csas.domains.auth.entity.User;
import java.util.UUID;

public record UserResponse(UUID id, String email, String nickname) {
  public static UserResponse from(User user) {
    return new UserResponse(user.getId(), user.getEmail(), user.getNickname());
  }
}
