package com.csas.domains.chat.dto;

import java.time.Instant;
import java.util.UUID;

public record ChatSessionResponse(UUID id, UUID quiz_id, UUID attempt_id, Instant created_at) {}
