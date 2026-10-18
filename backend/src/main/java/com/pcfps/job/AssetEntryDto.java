package com.pcfps.job;

import java.util.UUID;

/**
 * One downloadable asset in a comparison bundle.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
public record AssetEntryDto(
        String role,
        UUID fileId,
        String filename,
        String mimeType,
        String downloadPath
) {
}
