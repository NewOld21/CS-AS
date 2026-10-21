package com.csas.common.config;

import com.csas.common.exception.ErrorWriter;
import com.csas.common.security.SessionLifetimeFilter;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;
import org.springframework.core.env.Profiles;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.security.web.authentication.session.ChangeSessionIdAuthenticationStrategy;
import org.springframework.security.web.authentication.session.CompositeSessionAuthenticationStrategy;
import org.springframework.security.web.authentication.session.SessionAuthenticationStrategy;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.security.web.context.SecurityContextRepository;
import org.springframework.security.web.csrf.CsrfAuthenticationStrategy;
import org.springframework.security.web.csrf.CsrfException;
import org.springframework.security.web.csrf.CsrfFilter;
import org.springframework.security.web.csrf.CsrfTokenRepository;
import org.springframework.security.web.csrf.HttpSessionCsrfTokenRepository;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

@Configuration
@EnableMethodSecurity
public class SecurityConfig {
  @Bean
  AccessDeniedHandler apiDeniedHandler(ErrorWriter errors) {
    return (request, response, cause) -> {
      var authentication = SecurityContextHolder.getContext().getAuthentication();
      boolean anonymous =
          authentication == null
              || authentication instanceof AnonymousAuthenticationToken
              || !authentication.isAuthenticated();
      boolean publicCredentials =
          request.getMethod().equals("POST")
              && (request.getServletPath().equals("/api/v1/auth/login")
                  || request.getServletPath().equals("/api/v1/auth/signup"));
      if (anonymous && !publicCredentials) {
        errors.write(request, response, 401, "AUTH_REQUIRED", "Authentication is required.");
      } else {
        errors.write(
            request,
            response,
            403,
            cause instanceof CsrfException ? "CSRF_INVALID" : "ACCESS_DENIED",
            "Access denied.");
      }
    };
  }

  @Bean
  CorsConfigurationSource apiCors(Environment environment) {
    var source = new UrlBasedCorsConfigurationSource();
    var configuration = new CorsConfiguration();
    if (environment.acceptsProfiles(Profiles.of("local"))) {
      configuration.setAllowedOrigins(List.of("http://localhost:5173"));
      configuration.setAllowedMethods(List.of("GET", "POST", "OPTIONS"));
      configuration.setAllowedHeaders(
          List.of("Content-Type", "X-CSRF-Token", "Idempotency-Key", "X-Request-Id"));
      configuration.setExposedHeaders(List.of("X-Request-Id"));
      configuration.setAllowCredentials(true);
    }
    source.registerCorsConfiguration("/**", configuration);
    return source;
  }

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
      AccessDeniedHandler apiDeniedHandler,
      CorsConfigurationSource apiCors,
      @Value("${csas.security.absolute-session-seconds:43200}") long absoluteSessionSeconds)
      throws Exception {
    return http.formLogin(AbstractHttpConfigurer::disable)
        .httpBasic(AbstractHttpConfigurer::disable)
        .logout(
            logout ->
                logout
                    .logoutRequestMatcher(
                        request -> {
                          var auth = SecurityContextHolder.getContext().getAuthentication();
                          return request.getMethod().equals("POST")
                              && request.getServletPath().equals("/api/v1/auth/logout")
                              && auth != null
                              && auth.isAuthenticated()
                              && !(auth instanceof AnonymousAuthenticationToken);
                        })
                    .invalidateHttpSession(true)
                    .clearAuthentication(true)
                    .deleteCookies("CSAS_SESSION")
                    .logoutSuccessHandler(
                        (request, response, authentication) -> response.setStatus(204)))
        .requestCache(AbstractHttpConfigurer::disable)
        .cors(cors -> cors.configurationSource(apiCors))
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
                    .requestMatchers("/api/v1/**")
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
                    .accessDeniedHandler(apiDeniedHandler))
        .build();
  }
}
