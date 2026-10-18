package com.pcfps.preview.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

/**
 * JSON body for path-based LAS/PLY/LAZ preview (no {@code FileAsset}).
 *
 * @param lasPath   absolute filesystem path on the server (must fall under configured prefixes)
 * @param maxPoints optional cap (1..10_000_000); server default applies when null
 * @author PCFPS
 * @date 2026-05-08
 */
public record LasPathPreviewRequest(
        @NotBlank(message = "lasPath is required")
        String lasPath,
        @Min(1)
        @Max(10_000_000)
        Integer maxPoints
) {
}
