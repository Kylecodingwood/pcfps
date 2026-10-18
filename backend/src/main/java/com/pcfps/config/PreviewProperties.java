package com.pcfps.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Preview sampling limits, LAS subprocess toggles, and PLY parser caps.
 *
 * @param maxPointsDefault       default max points when client omits {@code maxPoints}
 * @param maxFileBytes           max bytes read for ASCII PLY preview
 * @param pythonCommand          interpreter for {@code las_preview_sample.py} (e.g. {@code python3})
 * @param lasPreviewEnabled      when false, LAS/LAZ path previews return {@code LAS_PREVIEW_DISABLED}
 * @param processTimeoutSeconds  subprocess wait timeout for LAS sampling
 * @author PCFPS
 * @date 2026-05-07
 */
@ConfigurationProperties(prefix = "pcfps.preview")
public record PreviewProperties(
        int maxPointsDefault,
        long maxFileBytes,
        String pythonCommand,
        boolean lasPreviewEnabled,
        int processTimeoutSeconds
) {
    public PreviewProperties {
        if (maxPointsDefault <= 0) {
            throw new IllegalArgumentException("pcfps.preview.max-points-default must be positive");
        }
        if (maxFileBytes <= 0) {
            throw new IllegalArgumentException("pcfps.preview.max-file-bytes must be positive");
        }
        if (pythonCommand == null || pythonCommand.isBlank()) {
            throw new IllegalArgumentException("pcfps.preview.python-command must be non-blank");
        }
        if (processTimeoutSeconds <= 0) {
            throw new IllegalArgumentException("pcfps.preview.process-timeout-seconds must be positive");
        }
    }
}
