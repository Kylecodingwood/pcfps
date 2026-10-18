package com.pcfps.integration.python;

import java.util.Map;

/**
 * Status snapshot returned when polling the Python worker.
 *
 * @param phase          e.g. RUNNING, SUCCEEDED, FAILED
 * @param errorMessage   present when phase is FAILED
 * @param metricsBundle  optional copy of Python {@code metrics_bundle} when succeeded
 * @author PCFPS
 * @date 2026-04-12
 */
public record PythonJobStatusView(String phase, String errorMessage, Map<String, Object> metricsBundle) {
}
