package com.csas.domains.chat.dto;

import java.util.UUID;

public record CreateChatSessionRequest(UUID quiz_id, UUID attempt_id) {}
