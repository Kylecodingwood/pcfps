package com.pcfps.job;

/**
 * Normalized filter-run metrics for API consumers (dual preview experiment panel).
 *
 * @param nBefore                full input point count from Python {@code N_before}
 * @param nAfter                 retained point count {@code N_after}
 * @param removalRatioPercent    {@code (nBefore - nAfter) / nBefore * 100} when {@code nBefore > 0}
 * @param timingTotalSec         wall-clock style total from Python {@code timing_total_sec}
 * @param timingDecodeSec        optional decode phase seconds
 * @param timingFilterSec        optional filter phase seconds
 * @param timingWriteSec         optional write phase seconds
 * @author PCFPS
 * @date 2026-05-09
 */
public record FilterRunMetricsDto(
        Long nBefore,
        Long nAfter,
        Double removalRatioPercent,
        Double timingTotalSec,
        Double timingDecodeSec,
        Double timingFilterSec,
        Double timingWriteSec
) {
}
