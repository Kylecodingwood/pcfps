package com.pcfps.job;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Effective filter configuration after merging client input with server defaults.
 *
 * @param filterMethod        algorithm used for dispatch and persistence
 * @param filterParamsJsonMap snapshot stored in {@code filter_task.filter_params_json} (snake_case keys)
 * @param filterSummary       one-line human-readable summary for APIs and UI
 * @author PCFPS
 * @date 2026-05-08
 */
public record FilterParameterMergeResult(
        FilterMethod filterMethod,
        Map<String, Object> filterParamsJsonMap,
        String filterSummary
) {

    /**
     * @return defensive copy suitable for JPA JSON mapping
     */
    public Map<String, Object> filterParamsJsonMapCopy() {
        return new LinkedHashMap<>(filterParamsJsonMap);
    }
}
