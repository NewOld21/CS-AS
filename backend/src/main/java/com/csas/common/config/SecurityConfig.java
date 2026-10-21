package com.csas.common.config;

import com.csas.common.exception.ErrorWriter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {
  @Bean
  SecurityFilterChain securityFilterChain(HttpSecurity http, ErrorWriter errors) throws Exception {
    return http.formLogin(AbstractHttpConfigurer::disable)
        .httpBasic(AbstractHttpConfigurer::disable)
        .logout(AbstractHttpConfigurer::disable)
        .requestCache(AbstractHttpConfigurer::disable)
        .authorizeHttpRequests(
            auth -> auth.requestMatchers("/health").permitAll().anyRequest().denyAll())
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
