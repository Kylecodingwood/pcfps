package com.pcfps.preview;

import com.pcfps.common.BusinessException;
import com.pcfps.config.PreviewProperties;
import com.pcfps.file.FileAsset;
import com.pcfps.file.FileAssetRepository;
import com.pcfps.file.FileAssetRole;
import com.pcfps.job.FilterTask;
import com.pcfps.job.TaskKind;
import com.pcfps.preview.dto.LasPathDualPreviewRequest;
import com.pcfps.preview.dto.LasPathDualPreviewResponse;
import com.pcfps.preview.dto.PointPreviewRequest;
import com.pcfps.preview.dto.PointPreviewResponse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

/**
 * Builds JSON preview payloads for file assets owned by the authenticated user, or for arbitrary server paths
 * (path APIs: absolute path + regular file; same trust model as task {@code inputLasPath}).
 *
 * @author PCFPS
 * @date 2026-05-07
 */
@Service
public class PointPreviewService {

    private static final Logger log = LoggerFactory.getLogger(PointPreviewService.class);

    private final FileAssetRepository fileAssetRepository;
    private final PreviewProperties previewProperties;
    private final LasPreviewSubprocessRunner lasPreviewSubprocessRunner;

    public PointPreviewService(
            FileAssetRepository fileAssetRepository,
            PreviewProperties previewProperties,
            LasPreviewSubprocessRunner lasPreviewSubprocessRunner
    ) {
        this.fileAssetRepository = fileAssetRepository;
        this.previewProperties = previewProperties;
        this.lasPreviewSubprocessRunner = lasPreviewSubprocessRunner;
    }

    /**
     * Loads preview points for a stored asset after ownership check.
     *
     * @param fileAssetId      persisted asset id
     * @param ownerUserId      authenticated user id
     * @param previewRequest   optional caps from JSON body
     * @return subsampled preview
     */
    @Transactional(readOnly = true)
    public PointPreviewResponse buildPreviewForOwnedFile(UUID fileAssetId, UUID ownerUserId, PointPreviewRequest previewRequest) {
        FileAsset fileAsset = fileAssetRepository.findByIdAndTask_Owner_Id(fileAssetId, ownerUserId)
                .orElseThrow(() -> {
                    log.warn("Preview denied or missing fileId={} ownerUserId={}", fileAssetId, ownerUserId);
                    return new BusinessException("FILE_NOT_FOUND", "File not found: " + fileAssetId);
                });
        Path storedFilePath = Path.of(fileAsset.getStoredPath());
        if (!Files.isRegularFile(storedFilePath)) {
            log.error("Preview path missing on disk fileId={} path={}", fileAssetId, storedFilePath);
            throw new BusinessException("FILE_NOT_FOUND", "File content missing on server: " + fileAssetId);
        }
        String lasPreviewPaletteHint = resolveLasPreviewPaletteHint(fileAsset);
        return buildPreviewFromResolvedPath(storedFilePath, previewRequest, "fileId=" + fileAssetId, lasPreviewPaletteHint);
    }

    /**
     * Builds preview from an absolute server path (no {@link FileAsset}). Caller must be authenticated;
     * path must exist as a regular file (same idea as task input path).
     *
     * @param lasPathString  absolute path to LAS/LAZ/ASCII PLY
     * @param previewRequest optional max points
     * @return subsampled preview
     */
    public PointPreviewResponse buildPreviewForServerPath(String lasPathString, PointPreviewRequest previewRequest) {
        Path resolvedPath = validateAndResolveServerPreviewPath(lasPathString);
        return buildPreviewFromResolvedPath(resolvedPath, previewRequest, "path=" + resolvedPath, "default");
    }

    /**
     * Builds two previews for manual dual-pane path comparison.
     *
     * @param dualPreviewRequest source and filtered absolute paths
     * @return both preview payloads
     */
    public LasPathDualPreviewResponse buildDualPreviewForServerPaths(LasPathDualPreviewRequest dualPreviewRequest) {
        PointPreviewRequest pointPreviewRequest = new PointPreviewRequest(dualPreviewRequest.maxPoints(), null);
        Path sourcePath = validateAndResolveServerPreviewPath(dualPreviewRequest.sourceLasPath());
        Path filteredPath = validateAndResolveServerPreviewPath(dualPreviewRequest.filteredLasPath());
        PointPreviewResponse sourcePreview = buildPreviewFromResolvedPath(
                sourcePath,
                pointPreviewRequest,
                "path=" + sourcePath,
                "default"
        );
        PointPreviewResponse filteredPreview = buildPreviewFromResolvedPath(
                filteredPath,
                pointPreviewRequest,
                "path=" + filteredPath,
                "default"
        );
        return new LasPathDualPreviewResponse(sourcePreview, filteredPreview);
    }

    private Path validateAndResolveServerPreviewPath(String lasPathString) {
        if (lasPathString == null || lasPathString.isBlank()) {
            log.warn("Preview path rejected: blank path");
            throw new BusinessException("PREVIEW_PATH_INVALID", "Path must be a non-blank absolute path");
        }
        String trimmedPathString = lasPathString.trim();
        Path rawPath = Paths.get(trimmedPathString);
        if (!rawPath.isAbsolute()) {
            log.warn("Preview path rejected: not absolute path={}", trimmedPathString);
            throw new BusinessException("PREVIEW_PATH_INVALID", "Path must be absolute: " + trimmedPathString);
        }
        Path normalizedPath = rawPath.normalize();
        Path absoluteNormalizedPath = normalizedPath.toAbsolutePath();
        if (!Files.isRegularFile(absoluteNormalizedPath)) {
            log.warn("Preview path rejected: not a regular file path={}", absoluteNormalizedPath);
            throw new BusinessException("FILE_NOT_FOUND", "File not found or not a regular file: " + absoluteNormalizedPath);
        }
        log.info("Preview path accepted path={}", absoluteNormalizedPath);
        return absoluteNormalizedPath;
    }

    private PointPreviewResponse buildPreviewFromResolvedPath(
            Path storedFilePath,
            PointPreviewRequest previewRequest,
            String logContext,
            String lasPreviewPaletteToken
    ) {
        int effectiveMaxPointCount = previewProperties.maxPointsDefault();
        if (previewRequest != null && previewRequest.maxPoints() != null) {
            effectiveMaxPointCount = previewRequest.maxPoints();
        }
        String fileExtension = extensionLowerCase(storedFilePath);
        String lasPreviewColorModeToken = resolveLasPreviewColorModeForRequest(previewRequest);
        String paletteTokenForSubprocess = normalizeLasPreviewPaletteToken(lasPreviewPaletteToken);
        log.info(
                "Preview request {} extension={} maxPoints={} colorMode={} palette={} path={}",
                logContext,
                fileExtension,
                effectiveMaxPointCount,
                lasPreviewColorModeToken,
                paletteTokenForSubprocess,
                storedFilePath
        );
        PointPreviewResponse previewResponse = switch (fileExtension) {
            case "las", "laz" -> lasPreviewSubprocessRunner.runLasPreviewSubprocess(
                    storedFilePath,
                    effectiveMaxPointCount,
                    previewProperties,
                    lasPreviewColorModeToken,
                    paletteTokenForSubprocess
            );
            case "ply" -> AsciiPlyPreviewParser.parseAsciiPlyPreview(
                    storedFilePath,
                    effectiveMaxPointCount,
                    previewProperties.maxFileBytes()
            );
            default -> throw new BusinessException(
                    "PREVIEW_UNSUPPORTED_FORMAT",
                    "Preview not supported for extension: " + fileExtension
            );
        };
        log.info(
                "Preview done {} returned={} truncated={}",
                logContext,
                previewResponse.pointCountReturned(),
                previewResponse.truncated()
        );
        return previewResponse;
    }

    /**
     * Normalizes {@link PointPreviewRequest#colorMode()} to a subprocess token {@code native} or {@code classification}.
     *
     * @param previewRequest optional client body; null is treated as {@code native}
     * @return {@code native} or {@code classification} for the Python LAS sampler
     * @throws BusinessException when {@code colorMode} is non-blank but not a supported token
     */
    private static String resolveLasPreviewColorModeForRequest(PointPreviewRequest previewRequest) {
        if (previewRequest == null || previewRequest.colorMode() == null || previewRequest.colorMode().isBlank()) {
            return "native";
        }
        String normalizedColorMode = previewRequest.colorMode().trim().toLowerCase(Locale.ROOT);
        if ("native".equals(normalizedColorMode)) {
            return "native";
        }
        if ("classification".equals(normalizedColorMode) || "label".equals(normalizedColorMode)) {
            return "classification";
        }
        log.warn("Invalid preview colorMode requested colorModeRaw={}", previewRequest.colorMode());
        throw new BusinessException(
                "PREVIEW_INVALID_COLOR_MODE",
                "colorMode must be native or classification, got: " + previewRequest.colorMode()
        );
    }

    private static String extensionLowerCase(Path storedFilePath) {
        String fileName = storedFilePath.getFileName().toString();
        int dotIndex = fileName.lastIndexOf('.');
        if (dotIndex < 0 || dotIndex == fileName.length() - 1) {
            return "";
        }
        return fileName.substring(dotIndex + 1).toLowerCase(Locale.ROOT);
    }

    /**
     * When the owning task is a semantic-campus classify output, use a fixed RGB legend in the LAS sampler.
     *
     * @param fileAsset persisted asset including lazy {@link FilterTask}
     * @return {@code semantic_campus} or {@code default}
     */
    private static String resolveLasPreviewPaletteHint(FileAsset fileAsset) {
        FilterTask owningTask = fileAsset.getTask();
        TaskKind taskKind = owningTask.getTaskKind();
        String derivedMethodToken = owningTask.getDerivedMethod();
        if (taskKind == TaskKind.CLASSIFY
                && fileAsset.getRole() == FileAssetRole.CLASSIFIED_LAS
                && derivedMethodToken != null
                && ("rule_semantic_campus".equalsIgnoreCase(derivedMethodToken.strip())
                        || "ml_rf_semantic".equalsIgnoreCase(derivedMethodToken.strip()))) {
            return "semantic_campus";
        }
        if (taskKind == TaskKind.SEMANTIC_PRUNE && fileAsset.getRole() == FileAssetRole.PRUNED_LAS) {
            Map<String, Object> derivedParameterMap = owningTask.getDerivedParamsJson();
            if (derivedParameterMap != null) {
                Object legendMethodRaw = derivedParameterMap.get("semantic_legend_method");
                if (legendMethodRaw instanceof String legendMethodToken) {
                    String normalizedLegend = legendMethodToken.strip();
                    if ("rule_semantic_campus".equalsIgnoreCase(normalizedLegend)
                            || "ml_rf_semantic".equalsIgnoreCase(normalizedLegend)) {
                        return "semantic_campus";
                    }
                }
            }
        }
        return "default";
    }

    private static String normalizeLasPreviewPaletteToken(String rawPaletteToken) {
        if (rawPaletteToken == null || rawPaletteToken.isBlank()) {
            return "default";
        }
        String normalized = rawPaletteToken.trim().toLowerCase(Locale.ROOT);
        if ("semantic_campus".equals(normalized)) {
            return "semantic_campus";
        }
        return "default";
    }
}
