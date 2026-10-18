package com.pcfps.preview;

import com.pcfps.preview.dto.LasPathDualPreviewRequest;
import com.pcfps.preview.dto.LasPathDualPreviewResponse;
import com.pcfps.preview.dto.LasPathPreviewRequest;
import com.pcfps.preview.dto.PointPreviewRequest;
import com.pcfps.preview.dto.PointPreviewResponse;

import jakarta.validation.Valid;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

/**
 * Path-based preview endpoints (JWT required). Server resolves absolute paths to regular files on disk;
 * same trust model as submitting an absolute {@code inputLasPath} when creating a task.
 *
 * @author PCFPS
 * @date 2026-05-08
 */
@RestController
@RequestMapping("/api/v1/preview")
public class PreviewPathController {

    private static final Logger log = LoggerFactory.getLogger(PreviewPathController.class);

    private final PointPreviewService pointPreviewService;

    public PreviewPathController(PointPreviewService pointPreviewService) {
        this.pointPreviewService = pointPreviewService;
    }

    /**
     * Returns subsampled preview JSON for one LAS/LAZ/ASCII PLY on disk (no {@code FileAsset}).
     *
     * @param lasPathPreviewRequest absolute path + optional max points
     * @return preview payload
     */
    @PostMapping(
            value = "/las-path",
            consumes = MediaType.APPLICATION_JSON_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE
    )
    public ResponseEntity<PointPreviewResponse> previewSingleLasPath(@Valid @RequestBody LasPathPreviewRequest lasPathPreviewRequest) {
        UUID callerUserId = currentUserId();
        log.info("Path preview single request callerUserId={}", callerUserId);
        PointPreviewRequest pointPreviewRequest = new PointPreviewRequest(lasPathPreviewRequest.maxPoints(), null);
        PointPreviewResponse previewResponse = pointPreviewService.buildPreviewForServerPath(
                lasPathPreviewRequest.lasPath(),
                pointPreviewRequest
        );
        return ResponseEntity.ok(previewResponse);
    }

    /**
     * Returns two subsampled previews for manual dual-pane comparison.
     *
     * @param lasPathDualPreviewRequest two absolute paths + optional shared max points
     * @return source and filtered preview payloads
     */
    @PostMapping(
            value = "/las-path/dual",
            consumes = MediaType.APPLICATION_JSON_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE
    )
    public ResponseEntity<LasPathDualPreviewResponse> previewDualLasPaths(
            @Valid @RequestBody LasPathDualPreviewRequest lasPathDualPreviewRequest
    ) {
        UUID callerUserId = currentUserId();
        log.info("Path preview dual request callerUserId={}", callerUserId);
        LasPathDualPreviewResponse dualPreviewResponse =
                pointPreviewService.buildDualPreviewForServerPaths(lasPathDualPreviewRequest);
        return ResponseEntity.ok(dualPreviewResponse);
    }

    private static UUID currentUserId() {
        Object principal = SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        if (principal instanceof UUID userId) {
            return userId;
        }
        throw new IllegalStateException("Expected UUID principal");
    }
}
