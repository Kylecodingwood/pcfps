package com.pcfps.job;

import com.pcfps.auth.UserAccount;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.Version;

import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

/**
 * LAS filtering job owned by a user. Filter algorithm and parameters are snapshotted at creation
 * ({@code filter_method}, {@code filter_params_json}); optional {@code filter_metrics_json} stores the
 * Python {@code metrics_bundle} after a successful real filter run. Legacy rows may have filter columns null
 * (treated as historical SOR defaults for dispatch and API summaries).
 *
 * @author PCFPS
 * @date 2026-04-12
 */
@Entity
@Table(name = "filter_task")
public class FilterTask {

    @Id
    private UUID id;

    @Version
    @Column(nullable = false)
    private Long version = 0L;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "owner_user_id", nullable = false)
    private UserAccount owner;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private TaskStatus status = TaskStatus.PENDING;

    @Column(name = "input_las_path", nullable = false, columnDefinition = "TEXT")
    private String inputLasPath;

    @Column(name = "output_base_path", nullable = false, columnDefinition = "TEXT")
    private String outputBasePath;

    @Column(name = "external_python_job_id", length = 128)
    private String externalPythonJobId;

    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;

    /**
     * Filter algorithm snapshot; null on legacy rows created before this column existed.
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "filter_method", length = 16)
    private FilterMethod filterMethod;

    /**
     * Effective parameter snapshot (snake_case keys aligned with {@code python_gateway}); JSONB.
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "filter_params_json", columnDefinition = "jsonb")
    private Map<String, Object> filterParamsJson;

    /**
     * Python {@code metrics_bundle} snapshot (e.g. {@code N_before}, {@code timing_total_sec}); null for Mock or legacy.
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "filter_metrics_json", columnDefinition = "jsonb")
    private Map<String, Object> filterMetricsJson;

    /**
     * Pipeline kind; {@code FILTER} for standard LAS filter jobs. Null in memory treated as {@link TaskKind#FILTER}.
     */
    @Enumerated(EnumType.STRING)
    @Column(name = "task_kind", nullable = false, length = 32)
    private TaskKind taskKind = TaskKind.FILTER;

    @Column(name = "parent_task_id")
    private UUID parentTaskId;

    @Column(name = "derived_method", length = 64)
    private String derivedMethod;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "derived_params_json", columnDefinition = "jsonb")
    private Map<String, Object> derivedParamsJson;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "derived_metrics_json", columnDefinition = "jsonb")
    private Map<String, Object> derivedMetricsJson;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt = Instant.now();

    protected FilterTask() {
    }

    public FilterTask(UUID id, UserAccount owner, String inputLasPath, String outputBasePath) {
        this.id = id;
        this.owner = owner;
        this.inputLasPath = inputLasPath;
        this.outputBasePath = outputBasePath;
    }

    public UUID getId() {
        return id;
    }

    public Long getVersion() {
        return version;
    }

    public UserAccount getOwner() {
        return owner;
    }

    public TaskStatus getStatus() {
        return status;
    }

    public void setStatus(TaskStatus status) {
        this.status = status;
        touch();
    }

    public String getInputLasPath() {
        return inputLasPath;
    }

    public String getOutputBasePath() {
        return outputBasePath;
    }

    public String getExternalPythonJobId() {
        return externalPythonJobId;
    }

    public void setExternalPythonJobId(String externalPythonJobId) {
        this.externalPythonJobId = externalPythonJobId;
        touch();
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
        touch();
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public FilterMethod getFilterMethod() {
        return filterMethod;
    }

    public Map<String, Object> getFilterParamsJson() {
        return filterParamsJson;
    }

    /**
     * Persists immutable filter configuration chosen at task creation.
     *
     * @param chosenMethod    non-null algorithm
     * @param paramsJsonMap   non-null merged parameters (snake_case keys)
     */
    public void setFilterConfigurationSnapshot(FilterMethod chosenMethod, Map<String, Object> paramsJsonMap) {
        this.filterMethod = chosenMethod;
        this.filterParamsJson = new LinkedHashMap<>(paramsJsonMap);
        touch();
    }

    public Map<String, Object> getFilterMetricsJson() {
        return filterMetricsJson;
    }

    /**
     * Persists Python-run metrics when the external job reports {@code SUCCEEDED}.
     *
     * @param metricsJsonMap non-null metrics map (defensive copy stored)
     */
    public void setFilterMetricsSnapshot(Map<String, Object> metricsJsonMap) {
        this.filterMetricsJson = new LinkedHashMap<>(metricsJsonMap);
        touch();
    }

    public TaskKind getTaskKind() {
        return taskKind != null ? taskKind : TaskKind.FILTER;
    }

    public UUID getParentTaskId() {
        return parentTaskId;
    }

    public String getDerivedMethod() {
        return derivedMethod;
    }

    public Map<String, Object> getDerivedParamsJson() {
        return derivedParamsJson;
    }

    public Map<String, Object> getDerivedMetricsJson() {
        return derivedMetricsJson;
    }

    /**
     * Persists a segment/classify/semantic-prune child task configuration at creation.
     *
     * @param chosenKind   {@link TaskKind#SEGMENT}, {@link TaskKind#CLASSIFY}, or {@link TaskKind#SEMANTIC_PRUNE}
     * @param parentTaskId parent task id (filter for segment/classify; classify for semantic prune)
     * @param methodToken  algorithm token for Python (e.g. {@code euclidean_cluster}, {@code voxel_drop_ground})
     * @param paramsJsonMap merged parameters
     */
    public void setDerivedConfigurationSnapshot(TaskKind chosenKind, UUID parentTaskId, String methodToken, Map<String, Object> paramsJsonMap) {
        this.taskKind = chosenKind;
        this.parentTaskId = parentTaskId;
        this.derivedMethod = methodToken;
        this.derivedParamsJson = new LinkedHashMap<>(paramsJsonMap);
        touch();
    }

    public void setDerivedMetricsSnapshot(Map<String, Object> metricsJsonMap) {
        this.derivedMetricsJson = new LinkedHashMap<>(metricsJsonMap);
        touch();
    }

    private void touch() {
        this.updatedAt = Instant.now();
    }
}
