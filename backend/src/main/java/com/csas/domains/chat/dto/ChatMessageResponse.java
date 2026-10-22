package com.csas.domains.chat.dto;

import com.csas.domains.learning.dto.SourceResponse;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record ChatMessageResponse(
    UUID id,
    String role,
    String content,
    String status,
    Instant created_at,
    String request_id,
    List<String> concept_ids,
    List<SourceResponse> sources) {}
