package com.pcfps.job;

/**
 * Request body to create a semantic-prune child task from a succeeded {@link TaskKind#CLASSIFY} task.
 *
 * @param groundVoxelSizeM optional horizontal voxel size in metres for thinning class 1 (ground); default 0.5
 * @author PCFPS
 * @date 2026-05-15
 */
public record CreateSemanticPruneTaskRequest(Double groundVoxelSizeM) {
}
