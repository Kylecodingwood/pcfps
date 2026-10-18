"""
RF 语义分类几何特征：与校园规则语义共用 PMF 地面 + 局部 PCA 平面度思路。

论文附录 C-4：build_feature_matrix 构造 4～5 维特征供 RandomForest 训练/推断。

@author PCFPS
@date 2026-05
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import ndimage
from sklearn.neighbors import NearestNeighbors


def _xy_grid_min_z_and_point_bins(
    xyz: np.ndarray, cell_size_m: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int, int]:
    """XY 格网最低 Z 与每点格索引（与 python_derived.pipeline 中 PMF 格网逻辑一致）。"""
    xmin = float(np.min(xyz[:, 0]))
    xmax = float(np.max(xyz[:, 0]))
    ymin = float(np.min(xyz[:, 1]))
    ymax = float(np.max(xyz[:, 1]))
    n_bins_x = max(1, int(math.ceil((xmax - xmin) / cell_size_m)))
    n_bins_y = max(1, int(math.ceil((ymax - ymin) / cell_size_m)))
    x_edges = np.linspace(xmin, xmax, n_bins_x + 1)
    y_edges = np.linspace(ymin, ymax, n_bins_y + 1)
    grid_ix = np.searchsorted(x_edges, xyz[:, 0], side="right") - 1
    grid_iy = np.searchsorted(y_edges, xyz[:, 1], side="right") - 1
    grid_ix = np.clip(grid_ix, 0, n_bins_x - 1)
    grid_iy = np.clip(grid_iy, 0, n_bins_y - 1)
    min_z_grid = np.full((n_bins_x, n_bins_y), np.inf, dtype=np.float64)
    flat_index = grid_ix * n_bins_y + grid_iy
    z_flat = min_z_grid.reshape(-1)
    np.minimum.at(z_flat, flat_index, xyz[:, 2])
    min_z_grid = z_flat.reshape(n_bins_x, n_bins_y)
    return min_z_grid, grid_ix, grid_iy, n_bins_x, n_bins_y


def pmf_height_residual_and_ground_mask(
    xyz: np.ndarray,
    cell_size_m: float,
    max_window_size: int,
    slope_threshold: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    PMF 风格地面面与高度残差。

    :return: (height_residual, ground_mask) 供 RF 特征 pmf_height_residual 与 pmf_ground_flag_float。
    """
    min_z_grid, grid_ix, grid_iy, n_bins_x, n_bins_y = _xy_grid_min_z_and_point_bins(xyz, cell_size_m)
    max_height = float(np.max(xyz[:, 2]))
    min_z_grid_copy = min_z_grid.copy()
    min_z_grid_copy[~np.isfinite(min_z_grid_copy)] = max_height + 1.0
    surface = min_z_grid_copy.copy()
    window_radius = max(1, min(max_window_size, max(n_bins_x, n_bins_y)))
    for _ in range(max_window_size):
        surface = ndimage.minimum_filter(surface, size=window_radius, mode="nearest")
    surface_at_points = surface[grid_ix, grid_iy]
    delta_allowed = slope_threshold * cell_size_m * max(1, max_window_size)
    height_residual = xyz[:, 2] - surface_at_points
    ground_mask = height_residual <= delta_allowed
    return height_residual.astype(np.float64), ground_mask


def neighbor_planarity_and_z_std(xyz: np.ndarray, neighbor_count: int) -> tuple[np.ndarray, np.ndarray]:
    """k 邻域 PCA 平面度与 Z 标准差（与派生 pipeline 中规则语义相同）。"""
    point_count = xyz.shape[0]
    neighborhood_size = min(neighbor_count + 1, point_count)
    if neighborhood_size < 4:
        return np.full(point_count, 0.5, dtype=np.float64), np.zeros(point_count, dtype=np.float64)
    neighbor_search = NearestNeighbors(n_neighbors=neighborhood_size, algorithm="kd_tree")
    neighbor_search.fit(xyz)
    _, neighbor_indices = neighbor_search.kneighbors(xyz)
    neighbor_indices_only = neighbor_indices[:, 1:]
    actual_neighbor_count = neighbor_indices_only.shape[1]
    planarity_output = np.zeros(point_count, dtype=np.float64)
    z_std_output = np.zeros(point_count, dtype=np.float64)
    batch_row_count = 2048
    for batch_start in range(0, point_count, batch_row_count):
        batch_end = min(batch_start + batch_row_count, point_count)
        neighbor_coordinates = xyz[neighbor_indices_only[batch_start:batch_end]]
        centered_neighbor_offsets = neighbor_coordinates - xyz[batch_start:batch_end, None, :]
        for local_row_index in range(batch_end - batch_start):
            neighbor_offset_matrix = centered_neighbor_offsets[local_row_index]
            covariance_matrix = (neighbor_offset_matrix.T @ neighbor_offset_matrix) / float(actual_neighbor_count)
            eigenvalues_ascending = np.linalg.eigvalsh(covariance_matrix)
            eigenvalues_descending = eigenvalues_ascending[::-1]
            largest_eigenvalue = float(eigenvalues_descending[0])
            smallest_eigenvalue = float(eigenvalues_descending[2]) if eigenvalues_descending.size >= 3 else 0.0
            global_row_index = batch_start + local_row_index
            planarity_output[global_row_index] = smallest_eigenvalue / (largest_eigenvalue + 1e-9)
            z_std_output[global_row_index] = float(np.std(neighbor_coordinates[local_row_index, :, 2]))
    return planarity_output, z_std_output


def build_feature_matrix(
    xyz: np.ndarray,
    pmf_params: dict[str, Any],
    neighbor_k: int,
    intensity_normalized: np.ndarray | None,
) -> tuple[np.ndarray, list[str]]:
    """
    构造 (N, F) 特征矩阵，训练标签为 classification 1～4（CloudCompare 人工标注）。

    特征列（F=4 或 5）：
    - pmf_height_residual：相对 PMF 地面高度残差
    - planarity：局部平面度
    - z_std_knn：邻域 Z 标准差
    - pmf_ground_flag_float：PMF 是否地面 (0/1)
    - intensity_01（可选）：归一化强度
    """
    cell_size_m = float(pmf_params.get("cell_size_m", 0.6))
    max_window_size = int(pmf_params.get("max_window_size", 8))
    slope_threshold = float(pmf_params.get("slope_threshold", 0.15))
    height_residual, ground_flag_float = pmf_height_residual_and_ground_mask(
        xyz, cell_size_m, max_window_size, slope_threshold
    )
    planarity_per_point, z_std_per_point = neighbor_planarity_and_z_std(xyz, neighbor_k)
    column_list: list[np.ndarray] = [
        height_residual,
        planarity_per_point,
        z_std_per_point,
        ground_flag_float.astype(np.float64),
    ]
    name_list = ["pmf_height_residual", "planarity", "z_std_knn", "pmf_ground_flag_float"]
    if intensity_normalized is not None:
        column_list.append(intensity_normalized.astype(np.float64))
        name_list.append("intensity_01")
    feature_matrix = np.column_stack(column_list)
    return feature_matrix.astype(np.float64), name_list
