package com.pcfps.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * WebClient for the embedded Python filter HTTP service.
 *
 * @author PCFPS
 * @date 2026-05-08
 */
@Configuration
public class PythonHttpClientConfiguration {

    /**
     * Client bound to {@code pcfps.python.base-url}; not registered when {@code mock-python} profile is active.
     *
     * @param pcfpsProperties bound PCFPS settings
     * @return configured WebClient
     */
    @Bean
    @Profile("!mock-python")
    public WebClient pythonFilterWebClient(PcfpsProperties pcfpsProperties) {
        return WebClient.builder()
                .baseUrl(pcfpsProperties.python().baseUrl())
                .build();
    }
}
