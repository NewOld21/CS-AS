package com.csas.domains.chat.dto;

import jakarta.validation.constraints.Size;
import java.util.UUID;

public record CreateChatSessionRequest(
    @Size(max = 200) String title, UUID quiz_id, UUID attempt_id) {}
