package com.pcfps.file;

import com.pcfps.common.BusinessException;
import com.pcfps.preview.PointPreviewService;
import com.pcfps.preview.dto.PointPreviewRequest;
import com.pcfps.preview.dto.PointPreviewResponse;

import jakarta.validation.Valid;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;

/**
 * Streams file content for assets owned by the caller's tasks.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
@RestController
@RequestMapping("/api/v1/files")
public class FileDownloadController {

    private static final Logger log = LoggerFactory.getLogger(FileDownloadController.class);

    private final FileAssetRepository fileAssetRepository;
    private final PointPreviewService pointPreviewService;

    public FileDownloadController(FileAssetRepository fileAssetRepository, PointPreviewService pointPreviewService) {
        this.fileAssetRepository = fileAssetRepository;
        this.pointPreviewService = pointPreviewService;
    }

    /**
     * Returns the binary content of a file asset if it belongs to the current user.
     *
     * @param fileId asset id
     * @return streamed body
     */
    @GetMapping("/{fileId}/content")
    public ResponseEntity<Resource> download(@PathVariable UUID fileId) {
        UUID ownerUserId = currentUserId();
        FileAsset fileAsset = fileAssetRepository.findByIdAndTask_Owner_Id(fileId, ownerUserId)
                .orElseThrow(() -> {
                    log.warn("File download denied or missing fileId={} ownerUserId={}", fileId, ownerUserId);
                    return new BusinessException("FILE_NOT_FOUND", "File not found: " + fileId);
                });
        Path storedPath = Path.of(fileAsset.getStoredPath());
        if (!Files.isRegularFile(storedPath)) {
            log.error("Stored path missing on disk fileId={} path={}", fileId, storedPath);
            throw new BusinessException("FILE_NOT_FOUND", "File content missing on server: " + fileId);
        }
        FileSystemResource resource = new FileSystemResource(storedPath.toFile());
        MediaType mediaType = MediaType.parseMediaType(fileAsset.getMimeType());
        return ResponseEntity.ok()
                .contentType(mediaType)
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + fileAsset.getFilename() + "\"")
                .body(resource);
    }

    /**
     * Returns subsampled XYZ preview points as JSON for Web rendering (LAS/LAZ via Python, ASCII PLY via Java).
     *
     * @param fileId          asset id
     * @param previewRequestBody optional JSON body (e.g. maxPoints); when omitted server defaults apply
     * @return preview payload
     */
    @PostMapping(
            value = "/{fileId}/preview-points",
            consumes = MediaType.APPLICATION_JSON_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE
    )
    public ResponseEntity<PointPreviewResponse> previewPoints(
            @PathVariable UUID fileId,
            @Valid @RequestBody(required = false) PointPreviewRequest previewRequestBody
    ) {
        UUID ownerUserId = currentUserId();
        PointPreviewResponse previewResponse = pointPreviewService.buildPreviewForOwnedFile(fileId, ownerUserId, previewRequestBody);
        return ResponseEntity.ok(previewResponse);
    }

    private static UUID currentUserId() {
        Object principal = SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        if (principal instanceof UUID userId) {
            return userId;
        }
        throw new IllegalStateException("Expected UUID principal");
    }
}
