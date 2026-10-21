package com.csas.domains.auth.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "users", schema = "csas")
public class User {
  @Id private UUID id;

  @Column(name = "email_normalized", nullable = false, unique = true, length = 254)
  private String email;

  @JsonIgnore
  @Column(name = "password_hash", nullable = false, length = 60)
  private String passwordHash;

  @Column(length = 40)
  private String nickname;

  @Column(name = "created_at", nullable = false, updatable = false)
  private Instant createdAt;

  @Column(name = "updated_at", nullable = false)
  private Instant updatedAt;

  protected User() {}

  public User(String email, String passwordHash, String nickname) {
    this.id = UUID.randomUUID();
    this.email = email;
    this.passwordHash = passwordHash;
    this.nickname = nickname;
    this.createdAt = Instant.now();
    this.updatedAt = createdAt;
  }

  public UUID getId() {
    return id;
  }

  public String getEmail() {
    return email;
  }

  @JsonIgnore
  public String getPasswordHash() {
    return passwordHash;
  }

  public String getNickname() {
    return nickname;
  }
}
