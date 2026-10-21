package com.csas.common.exception;

import java.time.Instant;

public record ApiError(String request_id, String code, String message, Instant timestamp) {}
