package com.csas.domains.chat.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChatQuestionRequest(@NotBlank @Size(max = 2000) String question) {}
