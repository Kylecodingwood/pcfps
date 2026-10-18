package com.pcfps.job;

import java.util.Map;

/**
 * Maps persisted {@code filter_metrics_json} (Python {@code metrics_bundle} shape) to {@link FilterRunMetricsDto}.
 *
 * @author PCFPS
 * @date 2026-05-09
 */
public final class FilterRunMetricsMapper {

    private FilterRunMetricsMapper() {
    }

    /**
     * @param rawMetricsMap keys such as {@code N_before}, {@code N_after}, {@code timing_total_sec}; may be null
     * @return dto with parsed fields, or null when nothing usable is present
     */
    public static FilterRunMetricsDto fromRawMetricsMap(Map<String, Object> rawMetricsMap) {
        if (rawMetricsMap == null || rawMetricsMap.isEmpty()) {
            return null;
        }
        Long nBefore = readLongKey(rawMetricsMap, "N_before");
        Long nAfter = readLongKey(rawMetricsMap, "N_after");
        Double timingTotal = readDoubleKey(rawMetricsMap, "timing_total_sec");
        Double timingDecode = readDoubleKey(rawMetricsMap, "timing_decode_sec");
        Double timingFilter = readDoubleKey(rawMetricsMap, "timing_filter_sec");
        Double timingWrite = readDoubleKey(rawMetricsMap, "timing_write_sec");
        if (nBefore == null && nAfter == null && timingTotal == null) {
            return null;
        }
        Double removalRatioPercent = null;
        if (nBefore != null && nBefore > 0 && nAfter != null) {
            removalRatioPercent = (nBefore - nAfter) * 100.0 / nBefore;
        }
        return new FilterRunMetricsDto(
                nBefore,
                nAfter,
                removalRatioPercent,
                timingTotal,
                timingDecode,
                timingFilter,
                timingWrite
        );
    }

    private static Long readLongKey(Map<String, Object> rawMetricsMap, String key) {
        Object rawValue = rawMetricsMap.get(key);
        if (rawValue instanceof Number number) {
            return number.longValue();
        }
        return null;
    }

    private static Double readDoubleKey(Map<String, Object> rawMetricsMap, String key) {
        Object rawValue = rawMetricsMap.get(key);
        if (rawValue instanceof Number number) {
            return number.doubleValue();
        }
        return null;
    }
}
