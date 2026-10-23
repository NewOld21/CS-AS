package com.csas.domains.learning.dto;

import java.util.List;

public record AttemptPageResponse(
    List<AttemptResultResponse> items, String next_cursor, long total_count) {}
