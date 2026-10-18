package com.pcfps.preview.dto;

import java.util.List;

/**
 * Preview point payload returned to the Web client after server-side decode and subsampling.
 *
 * @param points                     sampled coordinates; LAS previews may include linear {@code r,g,b} in {@code [0,1]}
 * @param maxPointsRequested         cap that was applied for this response
 * @param pointCountReturned         {@code points.size()}
 * @param sourcePointCountEstimate   total vertices (PLY) or LAS header point_count when known
 * @param truncated                  true when the source contained more points than returned
 * @author PCFPS
 * @date 2026-05-07
 */
public record PointPreviewResponse(
        List<Point3dDto> points,
        int maxPointsRequested,
        int pointCountReturned,
        long sourcePointCountEstimate,
        boolean truncated
) {
}
