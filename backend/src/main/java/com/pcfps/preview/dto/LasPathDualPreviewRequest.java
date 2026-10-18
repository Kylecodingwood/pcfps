package com.pcfps.preview.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

/**
 * JSON body for dual path-based preview (no {@code FileAsset}).
 *
 * @param sourceLasPath    absolute path to source cloud
 * @param filteredLasPath absolute path to filtered cloud
 * @param maxPoints        optional cap for both branches (1..10_000_000)
 * @author PCFPS
 * @date 2026-05-08
 */
public record LasPathDualPreviewRequest(
        @NotBlank(message = "sourceLasPath is required")
        String sourceLasPath,
        @NotBlank(message = "filteredLasPath is required")
        String filteredLasPath,
        @Min(1)
        @Max(10_000_000)
        Integer maxPoints
) {
}
