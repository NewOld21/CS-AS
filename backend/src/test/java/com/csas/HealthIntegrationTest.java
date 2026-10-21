package com.csas;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.reset;

import java.sql.SQLException;
import javax.sql.DataSource;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.system.CapturedOutput;
import org.springframework.boot.test.system.OutputCaptureExtension;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ExtendWith(OutputCaptureExtension.class)
class HealthIntegrationTest {
  @Autowired TestRestTemplate http;
  @Autowired Flyway flyway;
  @Autowired JdbcTemplate jdbc;
  @MockitoSpyBean DataSource dataSource;

  @Test
  void migratesOnlyOnceAndServesDatabaseHealth(CapturedOutput output) {
    assertThat(jdbc.queryForObject("SELECT 1", Integer.class)).isEqualTo(1);
    assertThat(flyway.info().current().getVersion().toString()).isEqualTo("1");
    assertThat(flyway.migrate().migrationsExecuted).isZero();
    var response = http.getForEntity("/health", String.class);
    assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
    assertThat(response.getBody()).isEqualTo("{\"status\":\"UP\"}");
    assertThat(output).doesNotContain(System.getenv("DB_PASSWORD"));
  }

  @Test
  void databaseFailureReturns503WithoutConnectionDetails() throws Exception {
    doThrow(new SQLException("database deliberately unavailable")).when(dataSource).getConnection();
    try {
      var response = http.getForEntity("/health", String.class);
      assertThat(response.getStatusCode()).isEqualTo(HttpStatus.SERVICE_UNAVAILABLE);
      assertThat(response.getBody()).isEqualTo("{\"status\":\"DOWN\"}");
    } finally {
      reset(dataSource);
    }
  }
}
