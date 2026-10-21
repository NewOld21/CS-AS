package com.csas.common.security;

import java.io.Serializable;
import java.util.UUID;

/** The session stores only the server-verified user ID, never password hashes. */
public record AuthenticatedUser(UUID id) implements Serializable {}
