package com.pcfps.job;

import java.util.Map;
import java.util.UUID;

/**
 * Bundle for dual-pane preview: parent filtered vs child segment/classify, or parent classified vs semantic-prune output.
 *
 * @param childTaskId           derived or prune task id
 * @param status                child task status (expected SUCCEEDED)
 * @param traceId               request trace id
 * @param leftFileId            left pane file id
 * @param leftLabel             UI label for left pane
 * @param rightFileId           right pane file id
 * @param rightLabel            UI label for right pane
 * @param childTaskKind         {@link TaskKind} name for legend routing
 * @param derivedMethod         persisted algorithm token (e.g. pmf, voxel_drop_ground)
 * @param derivedMetrics        metrics map from child task (may be empty)
 * @param semanticLegendMethod  when {@code childTaskKind} is {@code SEMANTIC_PRUNE}, parent classify method for palette
 * @author PCFPS
 * @date 2026-05-10
 */
public record DerivedComparisonBundleResponse(
        UUID childTaskId,
        String status,
        String traceId,
        UUID leftFileId,
        String leftLabel,
        UUID rightFileId,
        String rightLabel,
        String childTaskKind,
        String derivedMethod,
        Map<String, Object> derivedMetrics,
        String semanticLegendMethod
) {
}
