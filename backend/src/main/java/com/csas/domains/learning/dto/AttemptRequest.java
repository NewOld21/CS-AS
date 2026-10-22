package com.csas.domains.learning.dto;

import jakarta.validation.constraints.NotNull;
import java.util.UUID;

public record AttemptRequest(@NotNull UUID selected_option_id, UUID retry_of_attempt_id) {}
