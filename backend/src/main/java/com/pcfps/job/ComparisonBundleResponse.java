package com.pcfps.job;

import java.util.List;
import java.util.UUID;

/**
 * Aggregated payload for dual-pane viewer.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
public record ComparisonBundleResponse(
        UUID taskId,
        String status,
        String traceId,
        List<AssetEntryDto> assets,
        FilterRunMetricsDto runMetrics
) {
}
