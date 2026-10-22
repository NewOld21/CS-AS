package com.csas.domains.chat.dto;

import com.csas.domains.learning.dto.SourceResponse;
import java.util.List;
import java.util.UUID;

public record ChatAnswerResponse(
    String request_id,
    UUID message_id,
    String status,
    String answer,
    List<SourceResponse> sources,
    List<String> concept_ids) {}
