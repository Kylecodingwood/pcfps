package com.pcfps.job;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * Request body to create a derived segment or classify task from a succeeded parent filter task.
 *
 * @param taskKind   {@link TaskKind#SEGMENT} or {@link TaskKind#CLASSIFY}
 * @param algorithm  segment: {@code euclidean_cluster} | {@code region_growing}; classify: {@code pmf} | {@code csf} | {@code rule_semantic_campus} | {@code ml_rf_semantic}
 * @author PCFPS
 * @date 2026-05-10
 */
public record CreateDerivedTaskRequest(
        @NotNull TaskKind taskKind,
        @NotBlank String algorithm,
        Double clusterTolerance,
        Integer minClusterPoints,
        Integer maxClusterPoints,
        Boolean useXyOnly,
        Integer normalNeighborCount,
        Double angleThresholdDeg,
        Double distanceThreshold,
        Integer minRegionPoints,
        Integer maxSeeds,
        Double cellSizeM,
        Integer maxWindowSize,
        Double slopeThreshold,
        Double clothResolution,
        Integer rigidness,
        Integer csfIterations,
        Double classifyThreshold,
        Integer semanticNeighborCount,
        Double semanticPlanarityBuildingMax,
        Double semanticZStdVegetationMin,
        String mlRfModelDir
) {
    /**
     * @return normalized algorithm token (lowercase)
     */
    public String normalizedAlgorithm() {
        return algorithm.trim().toLowerCase();
    }
}
