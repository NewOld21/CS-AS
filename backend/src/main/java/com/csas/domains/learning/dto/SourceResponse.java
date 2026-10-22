package com.csas.domains.learning.dto;

public record SourceResponse(
    String source_id,
    String document_id,
    String revision,
    String chunk_id,
    String index_version,
    String title,
    String url,
    String locator) {}
