"""
点云离群点滤波核心：统计离群点去除（SOR）与半径离群点去除（ROR）。

- SOR：SciPy cKDTree 求 k 近邻，全局均值+标准差阈值。
- ROR：sklearn BallTree 半径邻域计数阈值。

论文附录 A 对应本模块；上层 pipeline 用 keep_mask 写 LAS 子集，见 las_io.save_las_subset_by_mask_from_source。

@author PCFPS
@date 2026-05
"""

from __future__ import annotations

import warnings

import numpy as np
from scipy.spatial import cKDTree
from sklearn.neighbors import BallTree


def sor_keep_mask(points: np.ndarray, neighbor_count: int, std_ratio: float) -> np.ndarray:
    """
    统计离群点去除（SOR）：返回长度为 N 的布尔掩码，True 表示保留该点。

    算法步骤：
    1. 对每个点求 k 个最近邻（查询 k+1 个，去掉自身）。
    2. 计算每点平均邻距 d̄_i。
    3. 全云 d̄ 的均值 μ 与标准差 σ，阈值 T = μ + std_ratio × σ。
    4. d̄_i ≤ T 的点保留，否则剔除。

    :param points: 形状 (N, >=3)，前三列为 XYZ（LAS 解码后的真实坐标，单位与源文件一致）。
    :param neighbor_count: 邻域点数 k（CLI 参数 --k）。
    :param std_ratio: 标准差倍数（CLI 参数 --std_ratio），越大越保守。
    :return: 布尔掩码，长度 N。
    """
    if neighbor_count < 1:
        raise ValueError("neighbor_count (k in CLI) must be >= 1.")

    if points.ndim != 2 or points.shape[1] < 3:
        raise ValueError("SOR expects coordinate matrix shaped (N, >=3); first triple are XYZ.")

    coordinate_xyz_float64_matrix = np.ascontiguousarray(points[:, :3], dtype=np.float64)

    observation_row_count = coordinate_xyz_float64_matrix.shape[0]
    if observation_row_count == 0:
        return np.zeros((0,), dtype=bool)
    if observation_row_count <= neighbor_count:
        # 点数不足以构造 k 邻域时，保持原有点云不做剔除
        warnings.warn(
            "SOR degenerate dataset: observation_count <= neighbour_count keeps all scanned points untouched.",
            stacklevel=2,
        )
        return np.ones((observation_row_count,), dtype=bool)

    # 三维 KD 树加速 k 近邻查询
    spatial_index_structure = cKDTree(coordinate_xyz_float64_matrix)
    queried_neighbor_dimensions = neighbor_count + 1
    neighbour_distance_matrix_square, _ = spatial_index_structure.query(
        coordinate_xyz_float64_matrix,
        k=queried_neighbor_dimensions,
        workers=-1,
    )

    # 第 0 列是自身（距离 0），从第 1 列起为 k 个邻点距离
    trimmed_distance_matrix_exclude_self_origin = neighbour_distance_matrix_square[:, 1:]
    mean_neighbor_distance_per_point_vector = np.mean(trimmed_distance_matrix_exclude_self_origin, axis=1)
    pooled_mean_scalar = float(np.mean(mean_neighbor_distance_per_point_vector))
    pooled_standard_dev_scalar = float(np.std(mean_neighbor_distance_per_point_vector))

    cutoff_threshold_scalar_value = pooled_mean_scalar + std_ratio * pooled_standard_dev_scalar
    keep_point_row_mask_vector = mean_neighbor_distance_per_point_vector <= cutoff_threshold_scalar_value
    return np.asarray(keep_point_row_mask_vector, dtype=bool)


def sor_filter(points: np.ndarray, k: int = 20, std_ratio: float = 1.0) -> np.ndarray:
    """应用 SOR 并返回保留点的坐标行（库调用便捷接口）。"""
    keep_point_row_mask_vector = sor_keep_mask(points, neighbor_count=k, std_ratio=std_ratio)
    return points[keep_point_row_mask_vector]


def ror_keep_mask(points: np.ndarray, radius: float, min_neighbors: int) -> np.ndarray:
    """
    半径离群点去除（ROR）：返回布尔掩码，True 表示保留。

    算法步骤：
    1. BallTree 统计每个点半径 radius 内的点数（含自身）。
    2. 计数减 1 得到除自身外的邻点数。
    3. 邻点数 >= min_neighbors 则保留，否则视为稀疏离群点剔除。

    :param radius: 搜索半径，单位与 LAS XYZ 一致（米）。
    :param min_neighbors: 半径内最少邻点数（不含自身）。
    """
    if radius <= 0:
        raise ValueError("radius must be positive.")
    if min_neighbors < 0:
        raise ValueError("min_neighbors must not be negative.")

    if points.ndim != 2 or points.shape[1] < 3:
        raise ValueError("ROR expects coordinate matrix shaped (N,>=3); first triple are XYZ.")

    coordinate_xyz_float64_matrix = np.ascontiguousarray(points[:, :3], dtype=np.float64)
    spatial_ball_tree_structure = BallTree(coordinate_xyz_float64_matrix, metric="euclidean")

    aggregated_radius_hit_counts_numpy_array = spatial_ball_tree_structure.query_radius(
        coordinate_xyz_float64_matrix,
        radius,
        count_only=True,
        return_distance=False,
        sort_results=False,
    )
    # 半径球内包含查询点自身，需减 1
    neighbouring_peer_count_exclusive_self_numpy_array = np.maximum(
        aggregated_radius_hit_counts_numpy_array.astype(np.int64) - 1,
        0,
    )

    surviving_point_boolean_mask_numpy_array = (
        neighbouring_peer_count_exclusive_self_numpy_array >= min_neighbors
    )

    return np.asarray(surviving_point_boolean_mask_numpy_array, dtype=bool)


def ror_filter(points: np.ndarray, radius: float = 1.0, min_neighbors: int = 5) -> np.ndarray:
    """应用 ROR 并返回保留点的坐标行。"""
    surviving_point_boolean_mask_numpy_array = ror_keep_mask(
        points, radius=radius, min_neighbors=min_neighbors
    )
    return points[surviving_point_boolean_mask_numpy_array]
