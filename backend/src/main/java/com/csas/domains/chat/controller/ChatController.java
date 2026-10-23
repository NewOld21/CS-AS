package com.csas.domains.chat.controller;

import com.csas.common.exception.ApiException;
import com.csas.common.security.CurrentUser;
import com.csas.domains.chat.dto.ChatAnswerResponse;
import com.csas.domains.chat.dto.ChatMessagePageResponse;
import com.csas.domains.chat.dto.ChatQuestionRequest;
import com.csas.domains.chat.dto.ChatSessionPageResponse;
import com.csas.domains.chat.dto.ChatSessionResponse;
import com.csas.domains.chat.dto.CreateChatSessionRequest;
import com.csas.domains.chat.service.ChatService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ChatController {
  private final CurrentUser currentUser;
  private final ChatService chats;
  private final com.csas.integrations.rag.HttpRagGateway rag;

  public ChatController(
      CurrentUser currentUser, ChatService chats, com.csas.integrations.rag.HttpRagGateway rag) {
    this.currentUser = currentUser;
    this.chats = chats;
    this.rag = rag;
  }

  @GetMapping("/api/v1/chat/status")
  java.util.Map<String, Object> status() {
    currentUser.id();
    return rag.status();
  }

  @PostMapping("/api/v1/chat/sessions")
  @ResponseStatus(HttpStatus.CREATED)
  ChatSessionResponse create(@Valid @RequestBody CreateChatSessionRequest request) {
    return chats.create(currentUser.id(), request);
  }

  @GetMapping("/api/v1/chat/sessions")
  ChatSessionPageResponse list(
      @RequestParam(defaultValue = "0") int page, @RequestParam(defaultValue = "20") int limit) {
    return chats.list(currentUser.id(), page, limit);
  }

  @GetMapping("/api/v1/chat/sessions/{sessionId}")
  ChatSessionResponse get(@PathVariable UUID sessionId) {
    return chats.get(currentUser.id(), sessionId);
  }

  @GetMapping("/api/v1/chat/sessions/{sessionId}/messages")
  ChatMessagePageResponse messages(
      @PathVariable UUID sessionId,
      @RequestParam(defaultValue = "0") int page,
      @RequestParam(defaultValue = "50") int limit) {
    return chats.messages(currentUser.id(), sessionId, page, limit);
  }

  @PostMapping("/api/v1/chat/sessions/{sessionId}/messages")
  ChatAnswerResponse ask(
      @PathVariable UUID sessionId,
      @Valid @RequestBody ChatQuestionRequest question,
      @RequestHeader(name = "Idempotency-Key", required = false) String idempotencyKey,
      HttpServletRequest request) {
    UUID key;
    try {
      key = UUID.fromString(idempotencyKey);
    } catch (IllegalArgumentException | NullPointerException ex) {
      throw new ApiException(400, "INVALID_INPUT", "Valid Idempotency-Key is required.");
    }
    return chats.ask(
        currentUser.id(), sessionId, question, key, (String) request.getAttribute("request_id"));
  }
}
