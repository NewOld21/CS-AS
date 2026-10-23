package com.csas.domains.learning.dto;

public record SourceResponse(
    String source_id,
    String document_id,
    String revision,
    String chunk_id,
    String index_version,
    String title,
    String url,
    String locator,
    String evidence_text,
    String category,
    String technology_version) {
  public SourceResponse(
      String sourceId,
      String documentId,
      String revision,
      String chunkId,
      String indexVersion,
      String title,
      String url,
      String locator) {
    this(
        sourceId,
        documentId,
        revision,
        chunkId,
        indexVersion,
        title,
        url,
        locator,
        null,
        null,
        null);
  }
}
