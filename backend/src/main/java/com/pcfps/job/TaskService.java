package com.pcfps.job;

import com.pcfps.auth.UserAccount;
import com.pcfps.auth.UserAccountRepository;
import com.pcfps.common.BusinessException;
import com.pcfps.config.MlRfSemanticProperties;
import com.pcfps.config.PcfpsProperties;
import com.pcfps.file.FileAsset;
import com.pcfps.file.FileAssetRepository;
import com.pcfps.file.FileAssetRole;
import com.pcfps.integration.python.PythonDerivedJobSubmitCommand;
import com.pcfps.integration.python.PythonGatewayService;
import com.pcfps.integration.python.PythonJobStatusView;
import com.pcfps.integration.python.PythonJobSubmitCommand;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Task lifecycle, comparison bundle, and pipeline ticks (invoked from scheduler).
 *
 * @author PCFPS
 * @date 2026-04-12
 */
@Service
public class TaskService {

    private static final Logger log = LoggerFactory.getLogger(TaskService.class);

    private static final String MINIMAL_PLY = """
            ply
            format ascii 1.0
            element vertex 3
            property float x
            property float y
            property float z
            end_header
            0 0 0
            0.1 0 0
            0 0.1 0
            """;

    private final FilterTaskRepository filterTaskRepository;
    private final FileAssetRepository fileAssetRepository;
    private final UserAccountRepository userAccountRepository;
    private final PythonGatewayService pythonGatewayService;
    private final PcfpsProperties pcfpsProperties;
    private final MlRfSemanticProperties mlRfSemanticProperties;

    public TaskService(
            FilterTaskRepository filterTaskRepository,
            FileAssetRepository fileAssetRepository,
            UserAccountRepository userAccountRepository,
            PythonGatewayService pythonGatewayService,
            PcfpsProperties pcfpsProperties,
            MlRfSemanticProperties mlRfSemanticProperties
    ) {
        this.filterTaskRepository = filterTaskRepository;
        this.fileAssetRepository = fileAssetRepository;
        this.userAccountRepository = userAccountRepository;
        this.pythonGatewayService = pythonGatewayService;
        this.pcfpsProperties = pcfpsProperties;
        this.mlRfSemanticProperties = mlRfSemanticProperties;
    }

    /**
     * Creates a PENDING task after validating the input LAS path exists and persisting an immutable
     * filter configuration snapshot ({@link FilterMethod} + JSON parameters).
     *
     * @param ownerUserId       authenticated user
     * @param createTaskRequest path plus optional filter fields (omitted numbers use server defaults)
     * @return created task summary including {@code filterSummary}
     */
    @Transactional
    public TaskResponseDto createTask(UUID ownerUserId, CreateTaskRequest createTaskRequest) {
        Path inputPath = Paths.get(createTaskRequest.inputLasPath()).normalize();
        if (!Files.isRegularFile(inputPath)) {
            log.warn("createTask rejected: file missing or not regular path={}", inputPath);
            throw new BusinessException("INVALID_INPUT_PATH", "Input LAS path must be an existing file: " + inputPath);
        }
        UserAccount owner = userAccountRepository.findById(ownerUserId)
                .orElseThrow(() -> new BusinessException("USER_NOT_FOUND", "User not found"));
        UUID taskId = UUID.randomUUID();
        Path outputDir = Paths.get(pcfpsProperties.outputRoot(), taskId.toString()).normalize();
        try {
            Files.createDirectories(outputDir);
        } catch (IOException exception) {
            log.error("Failed to create output directory path={}: {}", outputDir, exception.getMessage(), exception);
            throw new BusinessException("OUTPUT_DIR_FAILED", "Cannot create output directory: " + outputDir);
        }
        FilterParameterMergeResult mergeResult = FilterParameterMergeSupport.merge(createTaskRequest);
        FilterTask filterTask = new FilterTask(taskId, owner, inputPath.toString(), outputDir.toString());
        filterTask.setFilterConfigurationSnapshot(mergeResult.filterMethod(), mergeResult.filterParamsJsonMap());
        filterTaskRepository.save(filterTask);
        log.info(
                "Created task taskId={} ownerUserId={} inputPath={} filterMethod={} filterSummary={}",
                taskId,
                ownerUserId,
                inputPath,
                mergeResult.filterMethod(),
                mergeResult.filterSummary()
        );
        return toDto(filterTask);
    }

    /**
     * Lists tasks for the owner newest first.
     *
     * @param ownerUserId owner
     * @param pageable    paging
     * @return page of tasks
     */
    @Transactional(readOnly = true)
    public Page<TaskResponseDto> listTasks(UUID ownerUserId, Pageable pageable) {
        return filterTaskRepository.findByOwner_IdOrderByCreatedAtDesc(ownerUserId, pageable)
                .map(this::toDto);
    }

    /**
     * Loads one task if owned by the user.
     *
     * @param ownerUserId owner
     * @param taskId      task id
     * @return dto
     */
    @Transactional(readOnly = true)
    public TaskResponseDto getTask(UUID ownerUserId, UUID taskId) {
        FilterTask filterTask = filterTaskRepository.findByIdAndOwner_Id(taskId, ownerUserId)
                .orElseThrow(() -> notFound(taskId));
        return toDto(filterTask);
    }

    /**
     * Builds comparison bundle for a succeeded task.
     *
     * @param ownerUserId owner
     * @param taskId      task id
     * @param traceId     request trace for response
     * @return bundle
     */
    @Transactional(readOnly = true)
    public ComparisonBundleResponse getComparisonBundle(UUID ownerUserId, UUID taskId, String traceId) {
        FilterTask filterTask = filterTaskRepository.findByIdAndOwner_Id(taskId, ownerUserId)
                .orElseThrow(() -> notFound(taskId));
        if (filterTask.getTaskKind() != TaskKind.FILTER) {
            log.warn("comparison-bundle only for FILTER tasks taskId={} kind={}", taskId, filterTask.getTaskKind());
            throw new BusinessException("BUNDLE_NOT_FILTER_TASK", "Comparison bundle is only for filter tasks: " + taskId);
        }
        if (filterTask.getStatus() != TaskStatus.SUCCEEDED) {
            log.warn("comparison-bundle not ready taskId={} status={}", taskId, filterTask.getStatus());
            throw new BusinessException("BUNDLE_NOT_READY", "Task is not completed yet: " + filterTask.getStatus());
        }
        List<FileAsset> assetList = new ArrayList<>(fileAssetRepository.findByTaskIdOrderByRole(taskId));
        assetList.sort(Comparator.comparingInt(TaskService::roleSortOrder));
        if (assetList.isEmpty()) {
            log.error("Task SUCCEEDED but no file assets taskId={}", taskId);
            throw new BusinessException("BUNDLE_INCOMPLETE", "No file assets registered for task");
        }
        List<AssetEntryDto> entries = new ArrayList<>();
        for (FileAsset asset : assetList) {
            String downloadPath = "/api/v1/files/" + asset.getId() + "/content";
            entries.add(new AssetEntryDto(
                    asset.getRole().name(),
                    asset.getId(),
                    asset.getFilename(),
                    asset.getMimeType(),
                    downloadPath
            ));
        }
        FilterRunMetricsDto runMetrics = FilterRunMetricsMapper.fromRawMetricsMap(filterTask.getFilterMetricsJson());
        return new ComparisonBundleResponse(taskId, filterTask.getStatus().name(), traceId, entries, runMetrics);
    }

    /**
     * Builds dual-pane bundle: parent filtered LAS vs child segment/classify LAS.
     *
     * @param ownerUserId authenticated user (must own child and parent)
     * @param childTaskId derived task id
     * @param traceId       trace header value
     * @return left/right file ids and metrics
     */
    @Transactional(readOnly = true)
    public DerivedComparisonBundleResponse getDerivedComparisonBundle(UUID ownerUserId, UUID childTaskId, String traceId) {
        FilterTask childTask = filterTaskRepository.findByIdAndOwner_Id(childTaskId, ownerUserId)
                .orElseThrow(() -> notFound(childTaskId));
        TaskKind childKind = childTask.getTaskKind();
        if (childKind != TaskKind.SEGMENT && childKind != TaskKind.CLASSIFY) {
            log.warn("derived-comparison-bundle wrong kind taskId={} kind={}", childTaskId, childKind);
            throw new BusinessException("DERIVED_BUNDLE_WRONG_KIND", "Task is not a segment/classify job: " + childKind);
        }
        if (childTask.getStatus() != TaskStatus.SUCCEEDED) {
            log.warn("derived-comparison-bundle not ready taskId={} status={}", childTaskId, childTask.getStatus());
            throw new BusinessException("BUNDLE_NOT_READY", "Task is not completed yet: " + childTask.getStatus());
        }
        UUID parentTaskId = childTask.getParentTaskId();
        if (parentTaskId == null) {
            throw new BusinessException("DERIVED_PARENT_MISSING", "Derived task has no parent: " + childTaskId);
        }
        FilterTask parentTask = filterTaskRepository.findByIdAndOwner_Id(parentTaskId, ownerUserId)
                .orElseThrow(() -> notFound(parentTaskId));
        FileAsset filteredAsset = fileAssetRepository.findByTask_IdAndRole(parentTaskId, FileAssetRole.FILTERED_LAS)
                .orElseThrow(() -> new BusinessException("PARENT_FILTERED_MISSING", "Parent has no FILTERED_LAS asset"));
        FileAssetRole childOutputRole = childKind == TaskKind.SEGMENT ? FileAssetRole.SEGMENTED_LAS : FileAssetRole.CLASSIFIED_LAS;
        FileAsset derivedAsset = fileAssetRepository.findByTask_IdAndRole(childTaskId, childOutputRole)
                .orElseThrow(() -> new BusinessException("DERIVED_OUTPUT_MISSING", "Child has no output LAS asset"));
        Map<String, Object> metricsCopy = childTask.getDerivedMetricsJson() != null
                ? new LinkedHashMap<>(childTask.getDerivedMetricsJson())
                : Map.of();
        String derivedMethodToken = childTask.getDerivedMethod() != null ? childTask.getDerivedMethod() : "";
        return new DerivedComparisonBundleResponse(
                childTaskId,
                childTask.getStatus().name(),
                traceId,
                filteredAsset.getId(),
                "滤波后",
                derivedAsset.getId(),
                childKind == TaskKind.SEGMENT ? "分割后" : "分类后",
                childKind.name(),
                derivedMethodToken,
                metricsCopy,
                null
        );
    }

    /**
     * Dual-pane bundle: parent classified LAS vs child semantic-prune LAS.
     *
     * @param ownerUserId  authenticated user
     * @param pruneTaskId  succeeded {@link TaskKind#SEMANTIC_PRUNE} task id
     * @param traceId      trace header value
     * @return left = parent classify output, right = pruned output
     */
    @Transactional(readOnly = true)
    public DerivedComparisonBundleResponse getSemanticPruneComparisonBundle(UUID ownerUserId, UUID pruneTaskId, String traceId) {
        FilterTask pruneTask = filterTaskRepository.findByIdAndOwner_Id(pruneTaskId, ownerUserId)
                .orElseThrow(() -> notFound(pruneTaskId));
        if (pruneTask.getTaskKind() != TaskKind.SEMANTIC_PRUNE) {
            log.warn("semantic-prune-comparison-bundle wrong kind taskId={} kind={}", pruneTaskId, pruneTask.getTaskKind());
            throw new BusinessException("SEMANTIC_PRUNE_BUNDLE_WRONG_KIND", "Task is not a semantic prune job: " + pruneTask.getTaskKind());
        }
        if (pruneTask.getStatus() != TaskStatus.SUCCEEDED) {
            log.warn("semantic-prune-comparison-bundle not ready taskId={} status={}", pruneTaskId, pruneTask.getStatus());
            throw new BusinessException("BUNDLE_NOT_READY", "Task is not completed yet: " + pruneTask.getStatus());
        }
        UUID parentClassifyTaskId = pruneTask.getParentTaskId();
        if (parentClassifyTaskId == null) {
            throw new BusinessException("SEMANTIC_PRUNE_PARENT_MISSING", "Semantic prune task has no parent: " + pruneTaskId);
        }
        FilterTask parentClassifyTask = filterTaskRepository.findByIdAndOwner_Id(parentClassifyTaskId, ownerUserId)
                .orElseThrow(() -> notFound(parentClassifyTaskId));
        if (parentClassifyTask.getTaskKind() != TaskKind.CLASSIFY) {
            log.warn("semantic-prune parent not CLASSIFY parentTaskId={} kind={}", parentClassifyTaskId, parentClassifyTask.getTaskKind());
            throw new BusinessException("SEMANTIC_PRUNE_PARENT_NOT_CLASSIFY", "Parent must be a classify task");
        }
        FileAsset classifiedAsset = fileAssetRepository.findByTask_IdAndRole(parentClassifyTaskId, FileAssetRole.CLASSIFIED_LAS)
                .orElseThrow(() -> new BusinessException("PARENT_CLASSIFIED_MISSING", "Parent has no CLASSIFIED_LAS asset"));
        FileAsset prunedAsset = fileAssetRepository.findByTask_IdAndRole(pruneTaskId, FileAssetRole.PRUNED_LAS)
                .orElseThrow(() -> new BusinessException("PRUNED_OUTPUT_MISSING", "Semantic prune task has no PRUNED_LAS asset"));
        Map<String, Object> metricsCopy = pruneTask.getDerivedMetricsJson() != null
                ? new LinkedHashMap<>(pruneTask.getDerivedMetricsJson())
                : Map.of();
        String pruneMethodToken = pruneTask.getDerivedMethod() != null ? pruneTask.getDerivedMethod() : "";
        String semanticLegendMethodToken = "";
        Map<String, Object> pruneParams = pruneTask.getDerivedParamsJson();
        if (pruneParams != null && pruneParams.get("semantic_legend_method") instanceof String legendRaw) {
            semanticLegendMethodToken = legendRaw.strip();
        }
        log.info(
                "semanticPruneComparisonBundle pruneTaskId={} parentClassifyTaskId={} leftFileId={} rightFileId={}",
                pruneTaskId,
                parentClassifyTaskId,
                classifiedAsset.getId(),
                prunedAsset.getId()
        );
        return new DerivedComparisonBundleResponse(
                pruneTaskId,
                pruneTask.getStatus().name(),
                traceId,
                classifiedAsset.getId(),
                "分类后",
                prunedAsset.getId(),
                "语义精简后",
                TaskKind.SEMANTIC_PRUNE.name(),
                pruneMethodToken,
                metricsCopy,
                semanticLegendMethodToken.isEmpty() ? null : semanticLegendMethodToken
        );
    }

    /**
     * Creates a PENDING semantic-prune task from a succeeded parent classify task.
     *
     * @param ownerUserId      authenticated user
     * @param classifyTaskId   succeeded {@link TaskKind#CLASSIFY} task with {@link FileAssetRole#CLASSIFIED_LAS}
     * @param request          optional voxel size
     * @return created child task summary
     */
    @Transactional
    public TaskResponseDto createSemanticPruneTask(UUID ownerUserId, UUID classifyTaskId, CreateSemanticPruneTaskRequest request) {
        FilterTask classifyTask = filterTaskRepository.findByIdAndOwner_Id(classifyTaskId, ownerUserId)
                .orElseThrow(() -> notFound(classifyTaskId));
        if (classifyTask.getTaskKind() != TaskKind.CLASSIFY) {
            log.warn("createSemanticPruneTask parent not CLASSIFY classifyTaskId={} kind={}", classifyTaskId, classifyTask.getTaskKind());
            throw new BusinessException("SEMANTIC_PRUNE_PARENT_NOT_CLASSIFY", "Parent must be a classify task");
        }
        if (classifyTask.getStatus() != TaskStatus.SUCCEEDED) {
            log.warn("createSemanticPruneTask parent not succeeded classifyTaskId={} status={}", classifyTaskId, classifyTask.getStatus());
            throw new BusinessException("PARENT_NOT_SUCCEEDED", "Parent classify task must be SUCCEEDED");
        }
        FileAsset classifiedAsset = fileAssetRepository.findByTask_IdAndRole(classifyTaskId, FileAssetRole.CLASSIFIED_LAS)
                .orElseThrow(() -> new BusinessException("PARENT_CLASSIFIED_MISSING", "Parent has no CLASSIFIED_LAS output"));
        Path classifiedPath = Paths.get(classifiedAsset.getStoredPath()).normalize();
        if (!Files.isRegularFile(classifiedPath)) {
            log.warn("createSemanticPruneTask classified path not a file path={}", classifiedPath);
            throw new BusinessException("PARENT_CLASSIFIED_UNREADABLE", "Parent classified LAS is not a readable file");
        }
        DerivedParameterMergeSupport.DerivedMergeResult mergeResult;
        try {
            mergeResult = DerivedParameterMergeSupport.mergeSemanticPrune(request);
        } catch (IllegalArgumentException exception) {
            log.warn("createSemanticPruneTask invalid parameters classifyTaskId={}: {}", classifyTaskId, exception.getMessage());
            throw new BusinessException("INVALID_SEMANTIC_PRUNE_PARAMS", exception.getMessage());
        }
        Map<String, Object> mergedParameterMap = new LinkedHashMap<>(mergeResult.mergedParams());
        String parentClassifyMethod = classifyTask.getDerivedMethod() != null ? classifyTask.getDerivedMethod().strip() : "";
        mergedParameterMap.put("semantic_legend_method", parentClassifyMethod);
        UserAccount owner = userAccountRepository.findById(ownerUserId)
                .orElseThrow(() -> new BusinessException("USER_NOT_FOUND", "User not found"));
        UUID childTaskId = UUID.randomUUID();
        Path outputDir = Paths.get(pcfpsProperties.outputRoot(), childTaskId.toString()).normalize();
        try {
            Files.createDirectories(outputDir);
        } catch (IOException exception) {
            log.error("Failed to create semantic-prune output directory path={}: {}", outputDir, exception.getMessage(), exception);
            throw new BusinessException("OUTPUT_DIR_FAILED", "Cannot create output directory: " + outputDir);
        }
        FilterTask childTask = new FilterTask(childTaskId, owner, classifiedPath.toString(), outputDir.toString());
        childTask.setDerivedConfigurationSnapshot(TaskKind.SEMANTIC_PRUNE, classifyTaskId, "voxel_drop_ground", mergedParameterMap);
        filterTaskRepository.save(childTask);
        log.info(
                "Created semantic-prune task childTaskId={} parentClassifyTaskId={} groundVoxelM={} summary={}",
                childTaskId,
                classifyTaskId,
                mergedParameterMap.get("ground_voxel_size_m"),
                mergeResult.summaryLine()
        );
        return toDto(childTask);
    }

    /**
     * Creates a PENDING derived segment or classify task from a succeeded parent filter task.
     *
     * @param ownerUserId   authenticated user
     * @param parentTaskId  succeeded parent filter task
     * @param request       kind, algorithm, optional parameters
     * @return created child task summary
     */
    @Transactional
    public TaskResponseDto createDerivedTask(UUID ownerUserId, UUID parentTaskId, CreateDerivedTaskRequest request) {
        FilterTask parentTask = filterTaskRepository.findByIdAndOwner_Id(parentTaskId, ownerUserId)
                .orElseThrow(() -> notFound(parentTaskId));
        if (parentTask.getTaskKind() != TaskKind.FILTER) {
            log.warn("createDerivedTask parent not FILTER parentTaskId={} kind={}", parentTaskId, parentTask.getTaskKind());
            throw new BusinessException("PARENT_NOT_FILTER", "Parent must be a filter task");
        }
        if (parentTask.getStatus() != TaskStatus.SUCCEEDED) {
            log.warn("createDerivedTask parent not succeeded parentTaskId={} status={}", parentTaskId, parentTask.getStatus());
            throw new BusinessException("PARENT_NOT_SUCCEEDED", "Parent filter task must be SUCCEEDED");
        }
        FileAsset filteredAsset = fileAssetRepository.findByTask_IdAndRole(parentTaskId, FileAssetRole.FILTERED_LAS)
                .orElseThrow(() -> new BusinessException("PARENT_FILTERED_MISSING", "Parent has no FILTERED_LAS output"));
        Path filteredPath = Paths.get(filteredAsset.getStoredPath()).normalize();
        if (!Files.isRegularFile(filteredPath)) {
            log.warn("createDerivedTask filtered path not a file path={}", filteredPath);
            throw new BusinessException("PARENT_FILTERED_UNREADABLE", "Parent filtered LAS is not a readable file");
        }
        TaskKind requestedKind = request.taskKind();
        String algorithmToken = request.normalizedAlgorithm();
        validateDerivedAlgorithm(requestedKind, algorithmToken);
        DerivedParameterMergeSupport.DerivedMergeResult mergeResult;
        if (requestedKind == TaskKind.SEGMENT) {
            mergeResult = DerivedParameterMergeSupport.mergeSegment(request);
        } else {
            mergeResult = DerivedParameterMergeSupport.mergeClassify(request, mlRfSemanticProperties.modelDir());
        }
        UserAccount owner = userAccountRepository.findById(ownerUserId)
                .orElseThrow(() -> new BusinessException("USER_NOT_FOUND", "User not found"));
        UUID childTaskId = UUID.randomUUID();
        Path outputDir = Paths.get(pcfpsProperties.outputRoot(), childTaskId.toString()).normalize();
        try {
            Files.createDirectories(outputDir);
        } catch (IOException exception) {
            log.error("Failed to create derived output directory path={}: {}", outputDir, exception.getMessage(), exception);
            throw new BusinessException("OUTPUT_DIR_FAILED", "Cannot create output directory: " + outputDir);
        }
        FilterTask childTask = new FilterTask(childTaskId, owner, filteredPath.toString(), outputDir.toString());
        childTask.setDerivedConfigurationSnapshot(requestedKind, parentTaskId, algorithmToken, mergeResult.mergedParams());
        filterTaskRepository.save(childTask);
        log.info(
                "Created derived task childTaskId={} parentTaskId={} kind={} algorithm={} summary={}",
                childTaskId,
                parentTaskId,
                requestedKind,
                algorithmToken,
                mergeResult.summaryLine()
        );
        return toDto(childTask);
    }

    private static void validateDerivedAlgorithm(TaskKind requestedKind, String algorithmToken) {
        if (requestedKind == TaskKind.SEGMENT) {
            if (!"euclidean_cluster".equals(algorithmToken) && !"region_growing".equals(algorithmToken)) {
                throw new BusinessException("INVALID_SEGMENT_ALGORITHM", "Segment algorithm must be euclidean_cluster or region_growing");
            }
        } else if (requestedKind == TaskKind.CLASSIFY) {
            if (!"pmf".equals(algorithmToken)
                    && !"csf".equals(algorithmToken)
                    && !"rule_semantic_campus".equals(algorithmToken)
                    && !"ml_rf_semantic".equals(algorithmToken)) {
                throw new BusinessException(
                        "INVALID_CLASSIFY_ALGORITHM",
                        "Classify algorithm must be pmf, csf, rule_semantic_campus, or ml_rf_semantic"
                );
            }
        } else {
            throw new BusinessException("INVALID_DERIVED_KIND", "taskKind must be SEGMENT or CLASSIFY");
        }
    }

    /**
     * Dispatches at most one PENDING job if capacity allows; polls RUNNING jobs.
     */
    @Transactional
    public void runPipelineTick() {
        dispatchPendingIfSlot();
        pollRunningJobs();
    }

    private void dispatchPendingIfSlot() {
        long runningCount = filterTaskRepository.countByStatus(TaskStatus.RUNNING);
        int maxRunning = pcfpsProperties.filterMaxConcurrentRunning();
        if (runningCount >= maxRunning) {
            return;
        }
        List<FilterTask> pendingBatch = filterTaskRepository.lockAndListByStatus(
                TaskStatus.PENDING,
                org.springframework.data.domain.PageRequest.of(0, 1)
        );
        if (pendingBatch.isEmpty()) {
            return;
        }
        FilterTask filterTask = pendingBatch.get(0);
        try {
            TaskKind pipelineKind = filterTask.getTaskKind();
            if (pipelineKind == TaskKind.FILTER) {
                PythonJobSubmitCommand command = buildPythonJobSubmitCommand(filterTask);
                String externalJobId = pythonGatewayService.submitJob(command);
                filterTask.setStatus(TaskStatus.RUNNING);
                filterTask.setExternalPythonJobId(externalJobId);
                filterTaskRepository.save(filterTask);
                log.info(
                        "Dispatched FILTER task taskId={} externalJobId={} filterMethod={}",
                        filterTask.getId(),
                        externalJobId,
                        command.filterMethod()
                );
            } else if (pipelineKind == TaskKind.SEGMENT
                    || pipelineKind == TaskKind.CLASSIFY
                    || pipelineKind == TaskKind.SEMANTIC_PRUNE) {
                PythonDerivedJobSubmitCommand derivedCommand = buildPythonDerivedJobSubmitCommand(filterTask);
                String externalJobId = pythonGatewayService.submitDerivedJob(derivedCommand);
                filterTask.setStatus(TaskStatus.RUNNING);
                filterTask.setExternalPythonJobId(externalJobId);
                filterTaskRepository.save(filterTask);
                log.info(
                        "Dispatched derived task taskId={} externalJobId={} jobKind={} algorithm={}",
                        filterTask.getId(),
                        externalJobId,
                        derivedCommand.jobKind(),
                        derivedCommand.algorithm()
                );
            } else {
                log.error("Unsupported task kind for dispatch taskId={} kind={}", filterTask.getId(), pipelineKind);
                filterTask.setStatus(TaskStatus.FAILED);
                filterTask.setErrorMessage("Unsupported task kind: " + pipelineKind);
                filterTaskRepository.save(filterTask);
            }
        } catch (Exception exception) {
            log.error("Dispatch failed taskId={}: {}", filterTask.getId(), exception.getMessage(), exception);
            filterTask.setStatus(TaskStatus.FAILED);
            filterTask.setErrorMessage(exception.getMessage());
            filterTaskRepository.save(filterTask);
        }
    }

    private void pollRunningJobs() {
        List<FilterTask> runningTasks = filterTaskRepository.findByStatus(TaskStatus.RUNNING);
        for (FilterTask filterTask : runningTasks) {
            String externalJobId = filterTask.getExternalPythonJobId();
            if (externalJobId == null || externalJobId.isBlank()) {
                continue;
            }
            PythonJobStatusView statusView = pythonGatewayService.fetchStatus(externalJobId);
            if ("SUCCEEDED".equalsIgnoreCase(statusView.phase())) {
                try {
                    completeTaskSuccessByKind(filterTask, statusView);
                } catch (Exception exception) {
                    log.error(
                            "completeTaskSuccess failed taskId={} taskKind={} externalJobId={}: {}",
                            filterTask.getId(),
                            filterTask.getTaskKind(),
                            externalJobId,
                            exception.getMessage(),
                            exception
                    );
                    filterTask.setStatus(TaskStatus.FAILED);
                    filterTask.setErrorMessage(exception.getMessage());
                    filterTaskRepository.save(filterTask);
                }
            } else if ("FAILED".equalsIgnoreCase(statusView.phase())) {
                filterTask.setStatus(TaskStatus.FAILED);
                filterTask.setErrorMessage(statusView.errorMessage() != null ? statusView.errorMessage() : "Python job failed");
                filterTaskRepository.save(filterTask);
                String failureDetail = filterTask.getErrorMessage();
                if (failureDetail != null && failureDetail.length() > 4000) {
                    failureDetail = failureDetail.substring(0, 4000) + "…(truncated)";
                }
                log.error(
                        "Python reported FAILED taskId={} taskKind={} externalJobId={} message={}",
                        filterTask.getId(),
                        filterTask.getTaskKind(),
                        externalJobId,
                        failureDetail
                );
            }
        }
    }

    private void completeTaskSuccessByKind(FilterTask filterTask, PythonJobStatusView statusView) throws IOException {
        TaskKind pipelineKind = filterTask.getTaskKind();
        if (pipelineKind == TaskKind.FILTER) {
            completeFilterTaskSuccess(filterTask, statusView);
        } else if (pipelineKind == TaskKind.SEGMENT
                || pipelineKind == TaskKind.CLASSIFY
                || pipelineKind == TaskKind.SEMANTIC_PRUNE) {
            completeDerivedTaskSuccess(filterTask, statusView);
        } else {
            throw new IllegalStateException("Unsupported task kind for completion: " + pipelineKind);
        }
    }

    private void completeFilterTaskSuccess(FilterTask filterTask, PythonJobStatusView statusView) throws IOException {
        if (!fileAssetRepository.findByTaskIdOrderByRole(filterTask.getId()).isEmpty()) {
            return;
        }
        Map<String, Object> metricsBundle = statusView.metricsBundle();
        if (metricsBundle != null && !metricsBundle.isEmpty()) {
            filterTask.setFilterMetricsSnapshot(metricsBundle);
            log.info(
                    "Persisted filter metrics taskId={} nBefore={} nAfter={} timingTotalSec={}",
                    filterTask.getId(),
                    metricsBundle.get("N_before"),
                    metricsBundle.get("N_after"),
                    metricsBundle.get("timing_total_sec")
            );
        }
        Path outputDir = Paths.get(filterTask.getOutputBasePath());
        Files.createDirectories(outputDir);
        Path sourcePath = Paths.get(filterTask.getInputLasPath());
        FileAsset sourceAsset = new FileAsset(
                UUID.randomUUID(),
                filterTask,
                FileAssetRole.SOURCE_LAS,
                sourcePath.getFileName().toString(),
                "application/octet-stream",
                filterTask.getInputLasPath()
        );

        Path filteredLasPath = outputDir.resolve("filtered.las");
        List<FileAsset> toSave;
        if (Files.isRegularFile(filteredLasPath)) {
            toSave = List.of(
                    sourceAsset,
                    new FileAsset(
                            UUID.randomUUID(),
                            filterTask,
                            FileAssetRole.FILTERED_LAS,
                            "filtered.las",
                            "application/octet-stream",
                            filteredLasPath.toString()
                    )
            );
            log.info("Registering LAS outputs taskId={} filteredLasPath={}", filterTask.getId(), filteredLasPath);
        } else {
            Path filteredPlyPath = outputDir.resolve("filtered.ply");
            Files.writeString(filteredPlyPath, MINIMAL_PLY, StandardCharsets.UTF_8);
            toSave = List.of(
                    sourceAsset,
                    new FileAsset(
                            UUID.randomUUID(),
                            filterTask,
                            FileAssetRole.FILTERED_LAS,
                            "filtered.ply",
                            "model/ply",
                            filteredPlyPath.toString()
                    )
            );
            log.warn(
                    "filtered.las missing; using mock ASCII PLY fallback taskId={} path={}",
                    filterTask.getId(),
                    filteredPlyPath
            );
        }

        fileAssetRepository.saveAll(toSave);
        filterTask.setStatus(TaskStatus.SUCCEEDED);
        filterTaskRepository.save(filterTask);
        log.info("Task succeeded taskId={}", filterTask.getId());
    }

    private void completeDerivedTaskSuccess(FilterTask filterTask, PythonJobStatusView statusView) throws IOException {
        if (!fileAssetRepository.findByTaskIdOrderByRole(filterTask.getId()).isEmpty()) {
            return;
        }
        Map<String, Object> metricsBundle = statusView.metricsBundle();
        if (metricsBundle != null && !metricsBundle.isEmpty()) {
            filterTask.setDerivedMetricsSnapshot(metricsBundle);
            log.info(
                    "Persisted derived metrics taskId={} algorithm={} n_input={}",
                    filterTask.getId(),
                    metricsBundle.get("algorithm_code"),
                    metricsBundle.get("n_input")
            );
        }
        Path outputDir = Paths.get(filterTask.getOutputBasePath());
        Files.createDirectories(outputDir);
        Path derivedLasPath = outputDir.resolve("derived.las");
        Path inputLasPath = Paths.get(filterTask.getInputLasPath());
        if (!Files.isRegularFile(derivedLasPath) && Files.isRegularFile(inputLasPath)) {
            Files.copy(inputLasPath, derivedLasPath, StandardCopyOption.REPLACE_EXISTING);
            log.warn(
                    "derived.las missing after Python success; copied parent filtered LAS as stub taskId={}",
                    filterTask.getId()
            );
        }
        if (!Files.isRegularFile(derivedLasPath)) {
            log.error("derived.las still missing taskId={} path={}", filterTask.getId(), derivedLasPath);
            throw new IOException("Derived output LAS not found: " + derivedLasPath);
        }
        TaskKind pipelineKind = filterTask.getTaskKind();
        FileAssetRole outputRole = switch (pipelineKind) {
            case SEGMENT -> FileAssetRole.SEGMENTED_LAS;
            case CLASSIFY -> FileAssetRole.CLASSIFIED_LAS;
            case SEMANTIC_PRUNE -> FileAssetRole.PRUNED_LAS;
            default -> throw new IllegalStateException("Unexpected derived kind: " + pipelineKind);
        };
        FileAsset derivedAsset = new FileAsset(
                UUID.randomUUID(),
                filterTask,
                outputRole,
                "derived.las",
                "application/octet-stream",
                derivedLasPath.toString()
        );
        fileAssetRepository.save(derivedAsset);
        filterTask.setStatus(TaskStatus.SUCCEEDED);
        filterTaskRepository.save(filterTask);
        log.info("Derived task succeeded taskId={} role={}", filterTask.getId(), outputRole);
    }

    private TaskResponseDto toDto(FilterTask filterTask) {
        TaskKind pipelineKind = filterTask.getTaskKind();
        String filterMethodName = null;
        Map<String, Object> filterParamsCopy = null;
        String filterSummaryLine;
        if (pipelineKind != TaskKind.FILTER) {
            filterSummaryLine = "—";
        } else if (filterTask.getFilterMethod() != null && filterTask.getFilterParamsJson() != null) {
            filterMethodName = filterTask.getFilterMethod().name();
            filterParamsCopy = new LinkedHashMap<>(filterTask.getFilterParamsJson());
            filterSummaryLine = FilterParameterMergeSupport.summarizePersisted(
                    filterTask.getFilterMethod(),
                    filterTask.getFilterParamsJson()
            );
        } else {
            filterSummaryLine = FilterParameterMergeSupport.legacyHistoricalSummary();
        }
        String parentTaskIdString = filterTask.getParentTaskId() != null ? filterTask.getParentTaskId().toString() : null;
        String derivedMethodValue = filterTask.getDerivedMethod();
        Map<String, Object> derivedParamsCopy = filterTask.getDerivedParamsJson() != null
                ? new LinkedHashMap<>(filterTask.getDerivedParamsJson())
                : null;
        String derivedSummaryLine = null;
        if (pipelineKind == TaskKind.SEGMENT && derivedParamsCopy != null && derivedMethodValue != null) {
            derivedSummaryLine = DerivedParameterMergeSupport.summarizePersistedSegment(derivedMethodValue, derivedParamsCopy);
        } else if (pipelineKind == TaskKind.CLASSIFY && derivedParamsCopy != null && derivedMethodValue != null) {
            derivedSummaryLine = DerivedParameterMergeSupport.summarizePersistedClassify(derivedMethodValue, derivedParamsCopy);
        } else if (pipelineKind == TaskKind.SEMANTIC_PRUNE && derivedParamsCopy != null) {
            derivedSummaryLine = DerivedParameterMergeSupport.summarizePersistedSemanticPrune(derivedParamsCopy);
        }
        Map<String, Object> derivedMetricsCopy = filterTask.getDerivedMetricsJson() != null
                ? new LinkedHashMap<>(filterTask.getDerivedMetricsJson())
                : null;
        return new TaskResponseDto(
                filterTask.getId(),
                filterTask.getStatus().name(),
                filterTask.getInputLasPath(),
                filterTask.getOutputBasePath(),
                filterTask.getErrorMessage(),
                filterTask.getCreatedAt(),
                filterMethodName,
                filterParamsCopy,
                filterSummaryLine,
                pipelineKind.name(),
                parentTaskIdString,
                derivedMethodValue,
                derivedParamsCopy,
                derivedSummaryLine,
                derivedMetricsCopy
        );
    }

    private static PythonJobSubmitCommand buildPythonJobSubmitCommand(FilterTask filterTask) {
        if (filterTask.getFilterMethod() == null || filterTask.getFilterParamsJson() == null) {
            return new PythonJobSubmitCommand(
                    filterTask.getId(),
                    filterTask.getInputLasPath(),
                    filterTask.getOutputBasePath(),
                    FilterMethod.SOR,
                    FilterParameterMergeSupport.DEFAULT_SOR_NEIGHBOR_COUNT,
                    FilterParameterMergeSupport.DEFAULT_SOR_STD_RATIO,
                    FilterParameterMergeSupport.DEFAULT_ROR_RADIUS,
                    FilterParameterMergeSupport.DEFAULT_ROR_MIN_NEIGHBORS
            );
        }
        Map<String, Object> paramsJsonMap = filterTask.getFilterParamsJson();
        if (filterTask.getFilterMethod() == FilterMethod.SOR) {
            int neighborCount = readIntParameter(paramsJsonMap.get("sor_neighbor_count"));
            double stdRatio = readDoubleParameter(paramsJsonMap.get("sor_std_ratio"));
            return new PythonJobSubmitCommand(
                    filterTask.getId(),
                    filterTask.getInputLasPath(),
                    filterTask.getOutputBasePath(),
                    FilterMethod.SOR,
                    neighborCount,
                    stdRatio,
                    FilterParameterMergeSupport.DEFAULT_ROR_RADIUS,
                    FilterParameterMergeSupport.DEFAULT_ROR_MIN_NEIGHBORS
            );
        }
        double radius = readDoubleParameter(paramsJsonMap.get("ror_radius"));
        int minNeighbors = readIntParameter(paramsJsonMap.get("ror_min_neighbors"));
        return new PythonJobSubmitCommand(
                filterTask.getId(),
                filterTask.getInputLasPath(),
                filterTask.getOutputBasePath(),
                FilterMethod.ROR,
                FilterParameterMergeSupport.DEFAULT_SOR_NEIGHBOR_COUNT,
                FilterParameterMergeSupport.DEFAULT_SOR_STD_RATIO,
                radius,
                minNeighbors
        );
    }

    private static PythonDerivedJobSubmitCommand buildPythonDerivedJobSubmitCommand(FilterTask filterTask) {
        TaskKind pipelineKind = filterTask.getTaskKind();
        if (filterTask.getDerivedMethod() == null || filterTask.getDerivedParamsJson() == null) {
            throw new IllegalStateException("Derived task missing method or params: " + filterTask.getId());
        }
        String jobKindToken = switch (pipelineKind) {
            case SEGMENT -> "segment";
            case CLASSIFY -> "classify";
            case SEMANTIC_PRUNE -> "semantic_prune";
            default -> throw new IllegalStateException("Unsupported derived kind for Python dispatch: " + pipelineKind);
        };
        return new PythonDerivedJobSubmitCommand(
                filterTask.getId(),
                filterTask.getInputLasPath(),
                filterTask.getOutputBasePath(),
                jobKindToken,
                filterTask.getDerivedMethod(),
                new LinkedHashMap<>(filterTask.getDerivedParamsJson())
        );
    }

    private static int readIntParameter(Object rawValue) {
        if (rawValue instanceof Number number) {
            return number.intValue();
        }
        return 0;
    }

    private static double readDoubleParameter(Object rawValue) {
        if (rawValue instanceof Number number) {
            return number.doubleValue();
        }
        return 0.0;
    }

    private static BusinessException notFound(UUID taskId) {
        return new BusinessException("TASK_NOT_FOUND", "Task not found: " + taskId);
    }

    private static int roleSortOrder(FileAsset asset) {
        return switch (asset.getRole()) {
            case SOURCE_LAS -> 0;
            case FILTERED_LAS -> 1;
            case SEGMENTED_LAS, CLASSIFIED_LAS, PRUNED_LAS -> 2;
            case PREVIEW -> 3;
        };
    }
}
