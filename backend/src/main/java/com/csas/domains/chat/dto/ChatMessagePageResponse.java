package com.csas.domains.chat.dto;

import java.util.List;

public record ChatMessagePageResponse(List<ChatMessageResponse> items, Integer next_page) {}
