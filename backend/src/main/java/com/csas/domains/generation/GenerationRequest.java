package com.csas.domains.generation;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.util.List;
import java.util.UUID;

public record GenerationRequest(
    @NotNull @Size(max = 5) List<@Pattern(regexp = "concept:[a-z0-9-]{1,92}") String> concept_ids,
    @NotNull @Pattern(regexp = "EASY|MEDIUM|HARD") String difficulty,
    UUID chat_session_id) {}
