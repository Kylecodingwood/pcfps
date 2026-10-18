"""
派生点云处理：分割、分类、语义精简。

论文附录 B/C 对应本模块：
- 分割：欧式聚类（DBSCAN）、区域生长
- 分类：PMF-lite / CSF-lite 地面、校园规则四类语义、RF 有监督语义
- 语义精简：删除植被(3)/其它(4)，建筑(2)全保留，地面(1) XY 体素抽稀

输入通常为父任务滤波后的 LAS；整文件 laspy.read 进内存后写 classification 或子集。
Web 预览通过 classification / user_data 伪彩色展示。

@author PCFPS
@date 2026-05
"""

from __future__ import annotations

import logging
import math
import time
from collections import deque
from pathlib import Path
from typing import Any, Mapping

import laspy
import numpy as np
from scipy import ndimage
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

_LOGGER = logging.getLogger(__name__)

# LAS classification 字段常见仅 0..31；簇号超过 31 时用取模映射，完整 id 写入 user_data
_LAS_CLASSIFICATION_MODULO = 30


def _clear_user_data_if_present(las: laspy.LasData, point_count: int) -> None:
    dimension_name_set = {dimension.name for dimension in las.header.point_format.dimensions}
    if "user_data" in dimension_name_set:
        try:
            las.user_data = np.zeros(point_count, dtype=np.uint8)
        except (AttributeError, ValueError) as exception:
            _LOGGER.warning("Could not clear user_data for classify output: %s", exception)


def _neighbor_planarity_and_z_std(xyz: np.ndarray, neighbor_count: int) -> tuple[np.ndarray, np.ndarray]:
    """
    局部 k 邻域 PCA：平面度 = λ_min/λ_max（越小越像平面），以及邻域 Z 标准差。

    用于校园规则语义分类区分建筑（较平）与植被（较糙）。
    """
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


def _run_rule_semantic_campus(
    las: laspy.LasData,
    xyz: np.ndarray,
    params: dict[str, Any],
    wall_start: float,
    point_count: int,
) -> dict[str, float | int | str]:
    """
    校园规则伪语义四类：1 地面 / 2 建筑 / 3 植被 / 4 其它。

    先 PMF 提地面，再对非地面点用平面度与 Z 标准差阈值划分建/植/其它。
    """
    ground_mask = _run_pmf_ground(xyz, params)
    neighbor_k = int(params.get("semantic_neighbor_count", 24))
    planarity_building_max = float(params.get("semantic_planarity_building_max", 0.12))
    z_std_vegetation_min = float(params.get("semantic_z_std_vegetation_min", 0.28))
    z_std_flat_max = float(params.get("semantic_z_std_flat_max", 0.30))
    planarity_vegetation_min = float(params.get("semantic_planarity_vegetation_min", 0.38))

    planarity_per_point, z_std_per_point = _neighbor_planarity_and_z_std(xyz, neighbor_k)

    label_per_point = np.zeros(point_count, dtype=np.uint8)
    label_per_point[ground_mask] = 1
    non_ground_mask = ~ground_mask
    # 建筑：低平面度 + 邻域 Z 变化小（近似大平面）
    building_mask = non_ground_mask & (planarity_per_point < planarity_building_max) & (z_std_per_point < z_std_flat_max)
    # 植被：Z 起伏大或平面度较高（冠层、枝叶）
    vegetation_mask = non_ground_mask & ~building_mask & (
        (z_std_per_point >= z_std_vegetation_min) | (planarity_per_point >= planarity_vegetation_min)
    )
    other_mask = non_ground_mask & ~building_mask & ~vegetation_mask
    label_per_point[building_mask] = 2
    label_per_point[vegetation_mask] = 3
    label_per_point[other_mask] = 4

    las.classification = label_per_point
    _clear_user_data_if_present(las, point_count)

    marker_token = "PCFPS_RULE_SEMANTIC_v1"
    try:
        existing_software = str(las.header.generating_software or "")
        merged_software = (existing_software + " " + marker_token).strip()
        las.header.generating_software = merged_software[:256]
    except (AttributeError, ValueError) as exception:
        _LOGGER.warning("Could not set generating_software marker: %s", exception)

    ground_point_count = int(np.sum(ground_mask))
    building_point_count = int(np.sum(building_mask))
    vegetation_point_count = int(np.sum(vegetation_mask))
    other_point_count = int(np.sum(other_mask))
    return {
        "n_input": point_count,
        "n_output": point_count,
        "algorithm_code": "rule_semantic_campus",
        "n_ground": ground_point_count,
        "n_building": building_point_count,
        "n_vegetation": vegetation_point_count,
        "n_other": other_point_count,
        "ground_ratio": float(ground_point_count / point_count) if point_count > 0 else 0.0,
        "wall_time_sec": time.perf_counter() - wall_start,
    }


def _run_ml_rf_semantic(
    las: laspy.LasData,
    params: dict[str, Any],
    wall_start: float,
) -> dict[str, float | int | str]:
    """Supervised RF semantic labels 1–4 using a persisted model directory."""
    from pathlib import Path as PathLib

    from python_rf_semantic.infer_core import apply_rf_semantic_to_las

    model_dir_raw = params.get("model_dir")
    if model_dir_raw is None or str(model_dir_raw).strip() == "":
        raise ValueError("ml_rf_semantic requires model_dir in algorithm parameters")
    model_directory = PathLib(str(model_dir_raw)).expanduser().resolve()
    if not model_directory.is_dir():
        raise FileNotFoundError(f"RF model directory not found: {model_directory}")
    metrics = apply_rf_semantic_to_las(las, model_directory)
    metrics["wall_time_sec"] = time.perf_counter() - wall_start
    return metrics


def _run_semantic_prune(
    las: laspy.LasData,
    xyz: np.ndarray,
    params: dict[str, Any],
    wall_start: float,
    point_count: int,
) -> tuple[laspy.LasData, dict[str, float | int | str]]:
    """
    语义精简（测绘交付向）：删 3 植被、4 其它；2 建筑全保留；1 地面 XY 体素抽稀（每格留最低 Z）。

    compression_ratio = n_input / n_output。其它 classification 码保留且不抽稀。
    """
    ground_voxel_m = float(params.get("ground_voxel_size_m", 0.5))
    if ground_voxel_m <= 0.0:
        raise ValueError("ground_voxel_size_m must be positive")

    classification_array = np.asarray(las.classification, dtype=np.int32)
    # 第一步：删除时相地物（植被、其它）
    drop_mask = np.isin(classification_array, (3, 4))
    kept_after_drop_mask = ~drop_mask
    after_drop_indices = np.flatnonzero(kept_after_drop_mask)
    if after_drop_indices.size == 0:
        raise ValueError("semantic_prune: no points left after removing classes 3 and 4")

    classification_after_drop = classification_array[after_drop_indices]
    xyz_after_drop = xyz[after_drop_indices]

    non_ground_mask = classification_after_drop != 1
    ground_mask = classification_after_drop == 1
    non_ground_after_drop_indices = np.flatnonzero(non_ground_mask)
    ground_after_drop_indices = np.flatnonzero(ground_mask)

    ground_in_count = int(ground_after_drop_indices.size)
    removed_34_count = int(np.sum(drop_mask))

    if ground_in_count == 0:
        thin_ground_after_drop_indices = ground_after_drop_indices
    else:
        ground_coordinate_x = xyz_after_drop[ground_after_drop_indices, 0]
        ground_coordinate_y = xyz_after_drop[ground_after_drop_indices, 1]
        ground_coordinate_z = xyz_after_drop[ground_after_drop_indices, 2]
        global_x_min = float(np.min(xyz[:, 0]))
        global_y_min = float(np.min(xyz[:, 1]))
        voxel_index_x = np.floor((ground_coordinate_x - global_x_min) / ground_voxel_m).astype(np.int64)
        voxel_index_y = np.floor((ground_coordinate_y - global_y_min) / ground_voxel_m).astype(np.int64)
        # 按体素格排序后，每格第一个点即为该格最低 Z（lexsort 末键 Z 升序）
        sort_order = np.lexsort((ground_coordinate_z, voxel_index_y, voxel_index_x))
        sorted_ground_after_drop = ground_after_drop_indices[sort_order]
        voxel_index_x_sorted = voxel_index_x[sort_order]
        voxel_index_y_sorted = voxel_index_y[sort_order]
        cell_boundary_mask = np.ones(voxel_index_x_sorted.shape[0], dtype=bool)
        cell_boundary_mask[1:] = (voxel_index_x_sorted[1:] != voxel_index_x_sorted[:-1]) | (
            voxel_index_y_sorted[1:] != voxel_index_y_sorted[:-1]
        )
        thin_ground_after_drop_indices = sorted_ground_after_drop[cell_boundary_mask]

    merged_after_drop_indices = np.unique(
        np.concatenate([non_ground_after_drop_indices, thin_ground_after_drop_indices])
    )
    final_original_indices = after_drop_indices[merged_after_drop_indices]
    las_subset = las[final_original_indices]

    output_point_count = int(final_original_indices.size)
    ground_out_count = int(thin_ground_after_drop_indices.size)
    compression_ratio = float(point_count / output_point_count) if output_point_count > 0 else 0.0

    metrics: dict[str, float | int | str] = {
        "n_input": point_count,
        "n_output": output_point_count,
        "n_removed_34": removed_34_count,
        "n_ground_in": ground_in_count,
        "n_ground_out": ground_out_count,
        "ground_voxel_size_m": ground_voxel_m,
        "compression_ratio": compression_ratio,
        "algorithm_code": "voxel_drop_ground",
        "wall_time_sec": time.perf_counter() - wall_start,
    }
    return las_subset, metrics


def _write_segment_labels_to_las(las: laspy.LasData, raw_cluster_labels: np.ndarray) -> None:
    """
    分割簇号写回 LAS：classification 0=噪声，1..31 为簇（大 id 取模）；user_data 存 0..255 完整簇号供预览分色。
    """
    raw = np.asarray(raw_cluster_labels, dtype=np.int64)
    noise_mask = raw == 0
    mapped_classification = np.zeros(raw.shape[0], dtype=np.uint8)
    positive_mask = ~noise_mask
    if np.any(positive_mask):
        mapped_classification[positive_mask] = (
            1 + ((raw[positive_mask] - 1) % _LAS_CLASSIFICATION_MODULO)
        ).astype(np.uint8)
    las.classification = mapped_classification

    dimension_name_set = {dimension.name for dimension in las.header.point_format.dimensions}
    if "user_data" in dimension_name_set:
        try:
            # Point format 3 ``user_data`` is typically one byte (0..255).
            capped_user = np.clip(raw, 0, 255).astype(np.uint8)
            las.user_data = capped_user
            _LOGGER.debug("Wrote cluster id (capped 0..255) to user_data for segment output")
        except (AttributeError, ValueError) as exception:
            _LOGGER.warning("Could not write user_data for segment labels: %s", exception)


def process_derived(
    las_input_path: str,
    result_output_path: str,
    *,
    job_kind: str,
    algorithm: str,
    algorithm_parameter_mapping: Mapping[str, Any],
) -> dict[str, float | int | str]:
    """
    Run one derived algorithm and write ``result_output_path`` (LAS/LAZ).

    :param las_input_path: Readable LAS/LAZ path (typically filtered parent output).
    :param result_output_path: Output path ending in .las or .laz.
    :param job_kind: ``segment``, ``classify``, or ``semantic_prune``.
    :param algorithm: e.g. ``euclidean_cluster``, ``region_growing``, ``pmf``, ``csf``, ``rule_semantic_campus``, ``ml_rf_semantic``, ``voxel_drop_ground``.
    :param algorithm_parameter_mapping: Merged snake_case parameters from the gateway.
    :return: Metrics bundle (JSON-serializable scalars).
    """
    wall_start = time.perf_counter()
    input_path = Path(las_input_path).expanduser().resolve()
    output_path = Path(result_output_path).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input LAS not found: {input_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix_lower = output_path.suffix.lower()
    if suffix_lower not in {".las", ".laz"}:
        raise ValueError("Output must be .las or .laz")

    las = laspy.read(str(input_path))
    coordinate_x = np.asarray(las.x, dtype=np.float64)
    coordinate_y = np.asarray(las.y, dtype=np.float64)
    coordinate_z = np.asarray(las.z, dtype=np.float64)
    point_count = coordinate_x.shape[0]
    xyz = np.column_stack([coordinate_x, coordinate_y, coordinate_z])

    job_token = job_kind.lower().strip()
    algo_token = algorithm.lower().strip()
    params = dict(algorithm_parameter_mapping)

    if job_token == "segment":
        if algo_token == "euclidean_cluster":
            labels = _run_euclidean_clustering(xyz, params)
        elif algo_token == "region_growing":
            labels = _run_region_growing(xyz, params)
        else:
            raise ValueError(f"Unknown segment algorithm: {algorithm}")
        _write_segment_labels_to_las(las, labels)
        unique_labels = np.unique(labels)
        noise_mask = labels == 0
        num_clusters = int(np.sum(unique_labels > 0))
        metrics: dict[str, float | int | str] = {
            "n_input": point_count,
            "n_output": point_count,
            "algorithm_code": algo_token,
            "num_clusters": num_clusters,
            "noise_point_count": int(np.sum(noise_mask)),
            "noise_ratio": float(np.mean(noise_mask)) if point_count > 0 else 0.0,
            "wall_time_sec": time.perf_counter() - wall_start,
        }
    elif job_token == "classify":
        if algo_token == "rule_semantic_campus":
            metrics = _run_rule_semantic_campus(las, xyz, params, wall_start, point_count)
        elif algo_token == "ml_rf_semantic":
            metrics = _run_ml_rf_semantic(las, params, wall_start)
        elif algo_token == "pmf":
            ground_mask = _run_pmf_ground(xyz, params)
            classified = np.where(ground_mask, np.uint8(1), np.uint8(2))
            las.classification = classified
            _clear_user_data_if_present(las, point_count)
            ground_count = int(np.sum(ground_mask))
            non_ground_count = point_count - ground_count
            metrics = {
                "n_input": point_count,
                "n_output": point_count,
                "algorithm_code": algo_token,
                "n_ground": ground_count,
                "n_non_ground": non_ground_count,
                "ground_ratio": float(ground_count / point_count) if point_count > 0 else 0.0,
                "wall_time_sec": time.perf_counter() - wall_start,
            }
        elif algo_token == "csf":
            ground_mask = _run_csf_ground(xyz, params)
            classified = np.where(ground_mask, np.uint8(1), np.uint8(2))
            las.classification = classified
            _clear_user_data_if_present(las, point_count)
            ground_count = int(np.sum(ground_mask))
            non_ground_count = point_count - ground_count
            metrics = {
                "n_input": point_count,
                "n_output": point_count,
                "algorithm_code": algo_token,
                "n_ground": ground_count,
                "n_non_ground": non_ground_count,
                "ground_ratio": float(ground_count / point_count) if point_count > 0 else 0.0,
                "wall_time_sec": time.perf_counter() - wall_start,
            }
        else:
            raise ValueError(f"Unknown classify algorithm: {algorithm}")
    elif job_token == "semantic_prune":
        if algo_token != "voxel_drop_ground":
            raise ValueError(f"Unknown semantic_prune algorithm: {algorithm}")
        las, metrics = _run_semantic_prune(las, xyz, params, wall_start, point_count)
        output_point_count = int(las.header.point_count)
        algo_token = "voxel_drop_ground"
    else:
        raise ValueError(f"Unknown job_kind: {job_kind}")

    if job_token != "semantic_prune":
        output_point_count = point_count

    las.write(str(output_path), do_compress=(suffix_lower == ".laz"))
    _LOGGER.info(
        "Derived job finished algorithm=%s n_input=%s n_output=%s path=%s",
        algo_token,
        point_count,
        output_point_count,
        output_path,
    )
    return metrics


def _run_euclidean_clustering(xyz: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    """欧式聚类：sklearn DBSCAN，eps=cluster_tolerance，min_samples=min_cluster_points。"""
    tolerance = float(params.get("cluster_tolerance", 0.5))
    min_cluster_points = int(params.get("min_cluster_points", 50))
    use_xy_only = bool(params.get("use_xy_only", False))
    coords = xyz[:, :2] if use_xy_only else xyz
    clustering = DBSCAN(eps=tolerance, min_samples=min_cluster_points, metric="euclidean").fit(coords)
    raw_labels = clustering.labels_
    output = np.zeros(raw_labels.shape[0], dtype=np.int32)
    sequential_cluster_id = 0
    for label_value in np.unique(raw_labels):
        if label_value < 0:
            continue
        sequential_cluster_id += 1
        output[raw_labels == label_value] = sequential_cluster_id
    return output


def _run_region_growing(xyz: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    """
    区域生长：kNN 估法向 → 从低到高取种子 → BFS 扩张（距离+法向夹角约束）→ 过小区域剔除。
    """
    normal_neighbor_count = int(params.get("normal_neighbor_count", 30))
    angle_threshold_deg = float(params.get("angle_threshold_deg", 30.0))
    distance_threshold = float(params.get("distance_threshold", 0.3))
    min_region_points = int(params.get("min_region_points", 100))
    max_seeds = int(params.get("max_seeds", 50))
    point_count = xyz.shape[0]
    neighbor_count = min(normal_neighbor_count + 1, point_count)
    neighbor_search = NearestNeighbors(n_neighbors=neighbor_count, algorithm="kd_tree")
    neighbor_search.fit(xyz)
    _, neighbor_indices = neighbor_search.kneighbors(xyz)
    neighbor_indices_only = neighbor_indices[:, 1:]
    normals = np.zeros((point_count, 3), dtype=np.float64)
    chunk_size = 2048
    for start_row in range(0, point_count, chunk_size):
        end_row = min(start_row + chunk_size, point_count)
        neighbor_points = xyz[neighbor_indices_only[start_row:end_row]]
        centered = neighbor_points - xyz[start_row:end_row, None, :]
        _, _, right_singular = np.linalg.svd(centered, full_matrices=False)
        normals[start_row:end_row] = right_singular[:, -1, :]
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    norms = np.where(norms < 1e-9, 1.0, norms)
    normals = normals / norms
    angle_limit_rad = math.radians(angle_threshold_deg)

    # 从低处取种子，利于从地面/结构面向外生长
    sorted_by_height = np.argsort(xyz[:, 2])
    seed_stride = max(1, point_count // max(1, max_seeds))
    seed_index_list = sorted_by_height[::seed_stride][:max_seeds]
    region_labels = np.zeros(point_count, dtype=np.int32)
    next_region_id = 0
    visited_global = np.zeros(point_count, dtype=bool)
    for seed_index in seed_index_list:
        if visited_global[seed_index]:
            continue
        next_region_id += 1
        if next_region_id >= 255:
            break
        queue = deque([seed_index])
        visited_global[seed_index] = True
        region_labels[seed_index] = next_region_id
        region_size = 1
        while queue:
            current_index = queue.popleft()
            for neighbor_index in neighbor_indices_only[current_index]:
                if visited_global[neighbor_index]:
                    continue
                step_distance = float(np.linalg.norm(xyz[current_index] - xyz[neighbor_index]))
                if step_distance > distance_threshold:
                    continue
                cos_angle = float(
                    np.clip(
                        np.dot(normals[current_index], normals[neighbor_index]),
                        -1.0,
                        1.0,
                    )
                )
                angle_between = math.acos(cos_angle)
                if angle_between > angle_limit_rad:
                    continue
                visited_global[neighbor_index] = True
                region_labels[neighbor_index] = next_region_id
                region_size += 1
                queue.append(neighbor_index)
        if region_size < min_region_points:
            region_labels[region_labels == next_region_id] = 0
            next_region_id -= 1
    return region_labels


def _xy_grid_min_z_and_point_bins(
    xyz: np.ndarray, cell_size_m: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int, int]:
    """XY 规则格网：每格记录最低 Z，并返回每点所在格索引（PMF/CSF/体素抽稀共用）。"""
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


def _run_pmf_ground(xyz: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    """PMF-lite 地面：格网 min-Z 面经形态学最小值滤波，点高程残差小于坡度带则判为地面。"""
    cell_size_m = float(params.get("cell_size_m", 0.6))
    max_window_size = int(params.get("max_window_size", 8))
    slope_threshold = float(params.get("slope_threshold", 0.15))
    min_z_grid, grid_ix, grid_iy, n_bins_x, n_bins_y = _xy_grid_min_z_and_point_bins(xyz, cell_size_m)
    max_height = float(np.max(xyz[:, 2]))
    min_z_grid[~np.isfinite(min_z_grid)] = max_height + 1.0
    surface = min_z_grid.copy()
    window_radius = max(1, min(max_window_size, max(n_bins_x, n_bins_y)))
    for _ in range(max_window_size):
        surface = ndimage.minimum_filter(surface, size=window_radius, mode="nearest")
    surface_at_points = surface[grid_ix, grid_iy]
    delta_allowed = slope_threshold * cell_size_m * max(1, max_window_size)
    return (xyz[:, 2] - surface_at_points) <= delta_allowed


def _run_csf_ground(xyz: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    """CSF-lite 地面：简化布料模拟下沉至格网 min-Z，点与布高度差小于阈值则为地面。"""
    cloth_resolution = float(params.get("cloth_resolution", 0.5))
    rigidness = int(params.get("rigidness", 2))
    iterations = int(params.get("iterations", 500))
    classify_threshold = float(params.get("classify_threshold", 0.5))
    min_z_grid, grid_ix, grid_iy, _, _ = _xy_grid_min_z_and_point_bins(xyz, cloth_resolution)
    max_height = float(np.max(xyz[:, 2]))
    min_z_grid[~np.isfinite(min_z_grid)] = max_height
    cloth_heights = np.full_like(min_z_grid, float(np.percentile(xyz[:, 2], 95)))
    stiffness = 1.0 / max(1, rigidness)
    time_step = 0.5 / max(1, iterations // 100)
    for _ in range(iterations):
        cloth_heights = (1.0 - time_step * stiffness) * cloth_heights + time_step * stiffness * min_z_grid
        cloth_heights = ndimage.uniform_filter(cloth_heights, size=3, mode="nearest")
    cloth_at_points = cloth_heights[grid_ix, grid_iy]
    return np.abs(xyz[:, 2] - cloth_at_points) < classify_threshold
