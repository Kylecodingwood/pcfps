package com.pcfps.job;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

/**
 * Task summary for API responses (filter or derived segment/classify).
 *
 * @param id                   task id
 * @param status               lifecycle status token
 * @param inputLasPath         source LAS path on server (for derived: parent filtered LAS path)
 * @param outputBasePath       task output directory
 * @param errorMessage         failure detail when status is FAILED
 * @param createdAt            creation time
 * @param filterMethod         persisted filter algorithm; null for derived or legacy
 * @param filterParamsJson     persisted filter parameters; null for derived or legacy
 * @param filterSummary        human-readable filter configuration (legacy rows use historical text)
 * @param taskKind             {@link TaskKind} name
 * @param parentTaskId         parent id string when derived; otherwise null
 * @param derivedMethod        segment/classify algorithm token when derived; otherwise null
 * @param derivedParamsJson    derived parameter snapshot when derived; otherwise null
 * @param derivedSummary       one-line derived configuration when derived; otherwise null
 * @param derivedMetricsJson   metrics after success when derived; otherwise null
 * @author PCFPS
 * @date 2026-04-12
 */
public record TaskResponseDto(
        UUID id,
        String status,
        String inputLasPath,
        String outputBasePath,
        String errorMessage,
        Instant createdAt,
        String filterMethod,
        Map<String, Object> filterParamsJson,
        String filterSummary,
        String taskKind,
        String parentTaskId,
        String derivedMethod,
        Map<String, Object> derivedParamsJson,
        String derivedSummary,
        Map<String, Object> derivedMetricsJson
) {
}
