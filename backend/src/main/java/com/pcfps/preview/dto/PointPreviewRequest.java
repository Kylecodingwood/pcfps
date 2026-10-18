package com.pcfps.preview.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;

/**
 * JSON body for {@code POST /api/v1/files/{fileId}/preview-points}. Additional ROI fields may be added later.
 *
 * @param maxPoints  optional cap on returned points (1..10_000_000); when null the server default from {@code pcfps.preview} applies
 * @param colorMode  optional LAS/LAZ colouring: {@code native} prefers file RGB when dimensions exist;
 *                   {@code classification} uses {@code classification}/{@code user_data} pseudo-colour and ignores LAS RGB
 *                   for display even when RGB dimensions exist. {@code label} is accepted as an alias of {@code classification}.
 *                   When null or blank, the server uses {@code native}.
 * @author PCFPS
 * @date 2026-05-07
 */
public record PointPreviewRequest(
        @Min(1)
        @Max(10_000_000)
        Integer maxPoints,
        @Size(max = 32)
        String colorMode
) {
}
