package com.pcfps.job;

/**
 * High-level pipeline kind stored on {@code filter_task.task_kind}.
 *
 * @author PCFPS
 * @date 2026-05-10
 */
public enum TaskKind {

    /**
     * LAS outlier filtering (SOR/ROR).
     */
    FILTER,

    /**
     * Segmentation on a parent's {@code FILTERED_LAS}.
     */
    SEGMENT,

    /**
     * Ground / non-ground classification on a parent's {@code FILTERED_LAS}.
     */
    CLASSIFY,

    /**
     * Post-classify semantic reduction on a parent's {@code CLASSIFIED_LAS} (drop 3/4, voxel-thin ground).
     */
    SEMANTIC_PRUNE
}
