package com.csas.domains.chat.controller;

import com.csas.common.security.CurrentUser;
import com.csas.domains.chat.dto.ChatAnswerResponse;
import com.csas.domains.chat.dto.ChatQuestionRequest;
import com.csas.domains.chat.dto.ChatSessionResponse;
import com.csas.domains.chat.dto.CreateChatSessionRequest;
import com.csas.domains.chat.service.ChatService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ChatController {
  private final CurrentUser currentUser;
  private final ChatService chats;

  public ChatController(CurrentUser currentUser, ChatService chats) {
    this.currentUser = currentUser;
    this.chats = chats;
  }

  @PostMapping("/api/v1/chat/sessions")
  @ResponseStatus(HttpStatus.CREATED)
  ChatSessionResponse create(@RequestBody CreateChatSessionRequest request) {
    return chats.create(currentUser.id(), request);
  }

  @PostMapping("/api/v1/chat/sessions/{sessionId}/messages")
  ChatAnswerResponse ask(
      @PathVariable UUID sessionId,
      @Valid @RequestBody ChatQuestionRequest question,
      HttpServletRequest request) {
    return chats.ask(
        currentUser.id(), sessionId, question, (String) request.getAttribute("request_id"));
  }
}
