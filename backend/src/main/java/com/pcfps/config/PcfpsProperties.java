package com.pcfps.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Application-level PCFPS settings.
 *
 * @param outputRoot                  root directory for per-task output folders
 * @param filterMaxConcurrentRunning max RUNNING tasks globally
 * @author PCFPS
 * @date 2026-04-12
 */
@ConfigurationProperties(prefix = "pcfps")
public record PcfpsProperties(
        String outputRoot,
        int filterMaxConcurrentRunning,
        PythonProps python,
        MockPythonProps mockPython
) {
    public record PythonProps(String baseUrl) {
    }

    public record MockPythonProps(int succeedAfterTicks) {
    }
}
