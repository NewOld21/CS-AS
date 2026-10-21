package com.csas.common.config;

import com.csas.common.exception.ErrorWriter;
import com.csas.common.security.SessionLifetimeFilter;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.session.ChangeSessionIdAuthenticationStrategy;
import org.springframework.security.web.authentication.session.CompositeSessionAuthenticationStrategy;
import org.springframework.security.web.authentication.session.SessionAuthenticationStrategy;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.security.web.context.SecurityContextRepository;
import org.springframework.security.web.csrf.CsrfAuthenticationStrategy;
import org.springframework.security.web.csrf.CsrfFilter;
import org.springframework.security.web.csrf.CsrfTokenRepository;
import org.springframework.security.web.csrf.HttpSessionCsrfTokenRepository;

@Configuration
public class SecurityConfig {
  @Bean
  Clock clock() {
    return Clock.systemUTC();
  }

  @Bean
  SecurityContextRepository securityContexts() {
    return new HttpSessionSecurityContextRepository();
  }

  @Bean
  CsrfTokenRepository csrfTokens() {
    var repository = new HttpSessionCsrfTokenRepository();
    repository.setHeaderName("X-CSRF-Token");
    return repository;
  }

  @Bean
  SessionAuthenticationStrategy sessionAuthenticationStrategy(CsrfTokenRepository tokens) {
    return new CompositeSessionAuthenticationStrategy(
        List.of(
            new ChangeSessionIdAuthenticationStrategy(), new CsrfAuthenticationStrategy(tokens)));
  }

  @Bean
  PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder(12);
  }

  @Bean
  SecurityFilterChain securityFilterChain(
      HttpSecurity http,
      ErrorWriter errors,
      SecurityContextRepository contexts,
      CsrfTokenRepository tokens,
      Clock clock,
      @Value("${csas.security.absolute-session-seconds:43200}") long absoluteSessionSeconds)
      throws Exception {
    return http.formLogin(AbstractHttpConfigurer::disable)
        .httpBasic(AbstractHttpConfigurer::disable)
        .logout(AbstractHttpConfigurer::disable)
        .requestCache(AbstractHttpConfigurer::disable)
        .securityContext(
            context -> context.securityContextRepository(contexts).requireExplicitSave(true))
        .csrf(csrf -> csrf.csrfTokenRepository(tokens))
        .addFilterBefore(
            new SessionLifetimeFilter(clock, Duration.ofSeconds(absoluteSessionSeconds)),
            CsrfFilter.class)
        .authorizeHttpRequests(
            auth ->
                auth.requestMatchers(HttpMethod.GET, "/health", "/api/v1/auth/csrf")
                    .permitAll()
                    .requestMatchers(HttpMethod.POST, "/api/v1/auth/signup", "/api/v1/auth/login")
                    .permitAll()
                    .requestMatchers(HttpMethod.GET, "/api/v1/auth/me")
                    .authenticated()
                    .anyRequest()
                    .denyAll())
        .exceptionHandling(
            ex ->
                ex.authenticationEntryPoint(
                        (request, response, cause) ->
                            errors.write(
                                request,
                                response,
                                401,
                                "AUTH_REQUIRED",
                                "Authentication is required."))
                    .accessDeniedHandler(
                        (request, response, cause) ->
                            errors.write(
                                request, response, 403, "ACCESS_DENIED", "Access denied.")))
        .build();
  }
}
