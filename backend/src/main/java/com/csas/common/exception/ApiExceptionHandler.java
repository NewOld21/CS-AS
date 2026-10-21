package com.csas.common.exception;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.resource.NoResourceFoundException;

@RestControllerAdvice
public class ApiExceptionHandler {
  private final ErrorWriter errors;

  public ApiExceptionHandler(ErrorWriter errors) {
    this.errors = errors;
  }

  @ExceptionHandler(ApiException.class)
  ResponseEntity<ApiError> business(ApiException ex, HttpServletRequest request) {
    return ResponseEntity.status(ex.status())
        .body(errors.error(request, ex.code(), ex.getMessage()));
  }

  @ExceptionHandler({MethodArgumentNotValidException.class, HttpMessageNotReadableException.class})
  ResponseEntity<ApiError> invalid(Exception ex, HttpServletRequest request) {
    return ResponseEntity.badRequest()
        .body(errors.error(request, "INVALID_INPUT", "Invalid request input."));
  }

  @ExceptionHandler(NoResourceFoundException.class)
  ResponseEntity<ApiError> missing(HttpServletRequest request) {
    return ResponseEntity.status(404)
        .body(errors.error(request, "RESOURCE_NOT_FOUND", "Resource not found."));
  }

  @ExceptionHandler(Exception.class)
  ResponseEntity<ApiError> unexpected(Exception ex, HttpServletRequest request) {
    // Never echo exception messages: validation and persistence errors may contain secrets.
    return ResponseEntity.internalServerError()
        .body(errors.error(request, "INTERNAL_ERROR", "Internal server error."));
  }
}
