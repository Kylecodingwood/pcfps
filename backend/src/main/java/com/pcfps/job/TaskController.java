package com.pcfps.job;

import com.pcfps.config.TraceIdFilter;

import jakarta.validation.Valid;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

/**
 * Filter task REST API.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
@RestController
@RequestMapping("/api/v1/tasks")
public class TaskController {

    private static final Logger log = LoggerFactory.getLogger(TaskController.class);

    private final TaskService taskService;

    public TaskController(TaskService taskService) {
        this.taskService = taskService;
    }

    @PostMapping
    public ResponseEntity<TaskResponseDto> createTask(@Valid @RequestBody CreateTaskRequest createTaskRequest) {
        UUID ownerUserId = currentUserId();
        TaskResponseDto dto = taskService.createTask(ownerUserId, createTaskRequest);
        return ResponseEntity.ok(dto);
    }

    @GetMapping
    public ResponseEntity<Page<TaskResponseDto>> listTasks(
            @PageableDefault(size = 20, sort = "createdAt", direction = org.springframework.data.domain.Sort.Direction.DESC)
            Pageable pageable
    ) {
        UUID ownerUserId = currentUserId();
        return ResponseEntity.ok(taskService.listTasks(ownerUserId, pageable));
    }

    @GetMapping("/{taskId}")
    public ResponseEntity<TaskResponseDto> getTask(@PathVariable UUID taskId) {
        UUID ownerUserId = currentUserId();
        return ResponseEntity.ok(taskService.getTask(ownerUserId, taskId));
    }

    @GetMapping("/{taskId}/comparison-bundle")
    public ResponseEntity<ComparisonBundleResponse> comparisonBundle(@PathVariable UUID taskId) {
        UUID ownerUserId = currentUserId();
        String traceId = MDC.get(TraceIdFilter.TRACE_ID_MDC);
        ComparisonBundleResponse bundle = taskService.getComparisonBundle(ownerUserId, taskId, traceId != null ? traceId : "");
        return ResponseEntity.ok(bundle);
    }

    /**
     * Creates a segment or classify child task from a succeeded parent filter task.
     *
     * @param parentTaskId parent filter task id
     * @param request      kind, algorithm, optional parameters
     * @return created child task
     */
    @PostMapping("/{parentTaskId}/derived-jobs")
    public ResponseEntity<TaskResponseDto> createDerivedJob(
            @PathVariable UUID parentTaskId,
            @Valid @RequestBody CreateDerivedTaskRequest request
    ) {
        UUID ownerUserId = currentUserId();
        log.info(
                "createDerivedJob parentTaskId={} ownerUserId={} taskKind={} algorithm={}",
                parentTaskId,
                ownerUserId,
                request.taskKind(),
                request.normalizedAlgorithm()
        );
        TaskResponseDto dto = taskService.createDerivedTask(ownerUserId, parentTaskId, request);
        return ResponseEntity.ok(dto);
    }

    /**
     * Dual-pane bundle: parent filtered LAS vs child segment/classify LAS (metrics from child).
     *
     * @param childTaskId derived task id
     * @return left/right file ids and metrics map
     */
    @GetMapping("/{childTaskId}/derived-comparison-bundle")
    public ResponseEntity<DerivedComparisonBundleResponse> derivedComparisonBundle(@PathVariable UUID childTaskId) {
        UUID ownerUserId = currentUserId();
        String traceId = MDC.get(TraceIdFilter.TRACE_ID_MDC);
        log.info("derivedComparisonBundle childTaskId={} ownerUserId={}", childTaskId, ownerUserId);
        DerivedComparisonBundleResponse bundle = taskService.getDerivedComparisonBundle(
                ownerUserId,
                childTaskId,
                traceId != null ? traceId : ""
        );
        return ResponseEntity.ok(bundle);
    }

    /**
     * Creates a semantic-prune child task from a succeeded classify task (drops classes 3/4, voxels ground).
     *
     * @param classifyTaskId succeeded {@code CLASSIFY} task id
     * @param request          optional ground voxel size in metres
     * @return created prune task
     */
    @PostMapping("/{classifyTaskId}/semantic-prune-jobs")
    public ResponseEntity<TaskResponseDto> createSemanticPruneJob(
            @PathVariable UUID classifyTaskId,
            @Valid @RequestBody CreateSemanticPruneTaskRequest request
    ) {
        UUID ownerUserId = currentUserId();
        log.info(
                "createSemanticPruneJob classifyTaskId={} ownerUserId={} groundVoxelSizeM={}",
                classifyTaskId,
                ownerUserId,
                request.groundVoxelSizeM()
        );
        TaskResponseDto dto = taskService.createSemanticPruneTask(ownerUserId, classifyTaskId, request);
        return ResponseEntity.ok(dto);
    }

    /**
     * Dual-pane bundle: parent classified LAS vs child semantic-prune LAS.
     *
     * @param pruneTaskId semantic-prune task id (child of classify)
     * @return left/right file ids and metrics
     */
    @GetMapping("/{pruneTaskId}/semantic-prune-comparison-bundle")
    public ResponseEntity<DerivedComparisonBundleResponse> semanticPruneComparisonBundle(@PathVariable UUID pruneTaskId) {
        UUID ownerUserId = currentUserId();
        String traceId = MDC.get(TraceIdFilter.TRACE_ID_MDC);
        log.info("semanticPruneComparisonBundle pruneTaskId={} ownerUserId={}", pruneTaskId, ownerUserId);
        DerivedComparisonBundleResponse bundle = taskService.getSemanticPruneComparisonBundle(
                ownerUserId,
                pruneTaskId,
                traceId != null ? traceId : ""
        );
        return ResponseEntity.ok(bundle);
    }

    private static UUID currentUserId() {
        Object principal = SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        if (principal instanceof UUID userId) {
            return userId;
        }
        throw new IllegalStateException("Expected UUID principal");
    }
}
