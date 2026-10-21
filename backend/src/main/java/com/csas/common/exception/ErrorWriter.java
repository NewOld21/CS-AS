package com.csas.common.exception;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.time.Instant;
import java.util.UUID;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;

@Component
public class ErrorWriter {
  private final ObjectMapper mapper;

  public ErrorWriter(ObjectMapper mapper) {
    this.mapper = mapper;
  }

  public ApiError error(HttpServletRequest request, String code, String message) {
    Object id = request.getAttribute("request_id");
    return new ApiError(
        id == null ? UUID.randomUUID().toString() : id.toString(), code, message, Instant.now());
  }

  public void write(
      HttpServletRequest request,
      HttpServletResponse response,
      int status,
      String code,
      String message)
      throws IOException {
    response.setStatus(status);
    response.setContentType(MediaType.APPLICATION_JSON_VALUE);
    mapper.writeValue(response.getOutputStream(), error(request, code, message));
  }
}
