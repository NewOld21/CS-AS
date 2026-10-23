package com.csas.domains.learning.dto;

import java.util.List;

public record ReviewPageResponse(
    List<ReviewItemResponse> items, String next_cursor, long total_count) {}
