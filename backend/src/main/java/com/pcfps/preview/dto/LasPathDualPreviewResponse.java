package com.pcfps.preview.dto;

/**
 * Dual subsampled previews for path-based comparison.
 *
 * @param sourcePreview   preview built from {@code sourceLasPath}
 * @param filteredPreview preview built from {@code filteredLasPath}
 * @author PCFPS
 * @date 2026-05-08
 */
public record LasPathDualPreviewResponse(
        PointPreviewResponse sourcePreview,
        PointPreviewResponse filteredPreview
) {
}
