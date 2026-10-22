package com.csas.domains.chat.dto;

import java.time.Instant;
import java.util.UUID;

public record ChatSessionResponse(
    UUID id,
    String title,
    UUID quiz_id,
    UUID attempt_id,
    Instant created_at,
    Instant updated_at) {}
