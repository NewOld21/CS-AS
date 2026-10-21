package com.csas.common.security;

import com.csas.common.exception.ApiException;
import java.util.UUID;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

@Component
public class CurrentUser {
  public UUID id() {
    var authentication = SecurityContextHolder.getContext().getAuthentication();
    if (authentication == null
        || !(authentication.getPrincipal() instanceof AuthenticatedUser user)) {
      throw new ApiException(401, "AUTH_REQUIRED", "Authentication is required.");
    }
    return user.id();
  }

  /** Call with the owner loaded from storage, never a client-supplied owner assertion. */
  public void requireOwner(UUID storedOwnerId) {
    if (!id().equals(storedOwnerId)) {
      throw new ApiException(404, "RESOURCE_NOT_FOUND", "Resource not found.");
    }
  }
}
