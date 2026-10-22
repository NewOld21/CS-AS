package com.csas.domains.chat.dto;

import java.util.List;

public record ChatSessionPageResponse(List<ChatSessionResponse> items, Integer next_page) {}
