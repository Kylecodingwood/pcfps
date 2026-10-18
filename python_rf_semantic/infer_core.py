"""
RF 有监督语义分类推断：加载 model.joblib，逐点预测 1～4 类并写回 LAS classification。

论文附录 C-4；训练见 train_cli.py（CloudCompare 标注 LAS → RandomForest）。

@author PCFPS
@date 2026-05
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import laspy
import numpy as np

from python_rf_semantic.geometry_features import build_feature_matrix
from python_rf_semantic.model_io import load_model_bundle

_LOGGER = logging.getLogger(__name__)

# 写入 LAS header.generating_software，标识 RF 语义产物
RF_SEMANTIC_MARKER = "PCFPS_RF_SEMANTIC_v1"


def read_xyz_from_las(las: laspy.LasData) -> np.ndarray:
    """从 LasData 读取解码后的真实坐标 XYZ（laspy 已应用 scale/offset）。"""
    coordinate_x = np.asarray(las.x, dtype=np.float64)
    coordinate_y = np.asarray(las.y, dtype=np.float64)
    coordinate_z = np.asarray(las.z, dtype=np.float64)
    return np.column_stack([coordinate_x, coordinate_y, coordinate_z])


def read_intensity_normalized(las: laspy.LasData) -> np.ndarray | None:
    """强度归一化到 [0,1]；无 intensity 维度时返回 None（特征维数 F=4）。"""
    dimension_name_set = {dimension.name for dimension in las.header.point_format.dimensions}
    if "intensity" not in dimension_name_set:
        return None
    intensity_array = np.asarray(las.intensity, dtype=np.float64)
    intensity_max = float(np.max(intensity_array)) if intensity_array.size > 0 else 0.0
    if intensity_max <= 0.0:
        return np.zeros(intensity_array.shape[0], dtype=np.float64)
    return intensity_array / intensity_max


def predict_labels_for_xyz(
    xyz: np.ndarray,
    model_directory: Path,
    intensity_normalized: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """
    对每点预测 uint8 标签 1～4。

    特征须与训练时 feature_config.json 一致，否则抛出 ValueError。
    """
    classifier, config_payload = load_model_bundle(model_directory)
    pmf_params = dict(config_payload.get("pmf_params", {}))
    neighbor_k = int(config_payload.get("semantic_neighbor_count", 24))
    saved_feature_names = list(config_payload.get("feature_names", []))
    feature_matrix, built_feature_names = build_feature_matrix(
        xyz, pmf_params, neighbor_k, intensity_normalized
    )
    if saved_feature_names and saved_feature_names != built_feature_names:
        raise ValueError(
            f"Feature name mismatch: model expects {saved_feature_names}, built {built_feature_names}"
        )
    predicted_labels = classifier.predict(feature_matrix)
    return predicted_labels.astype(np.uint8), config_payload


def apply_rf_semantic_to_las(
    las: laspy.LasData,
    model_directory: Path,
) -> dict[str, float | int | str]:
    """
    将 RF 预测标签写入 las.classification，并返回与 rule_semantic_campus 对齐的 metrics。

    标签含义：1 地面 / 2 建筑 / 3 植被 / 4 其它。
    """
    xyz = read_xyz_from_las(las)
    point_count = xyz.shape[0]
    intensity_normalized = read_intensity_normalized(las)
    label_per_point, _config_payload = predict_labels_for_xyz(xyz, model_directory, intensity_normalized)
    las.classification = label_per_point
    dimension_name_set = {dimension.name for dimension in las.header.point_format.dimensions}
    if "user_data" in dimension_name_set:
        try:
            las.user_data = np.zeros(point_count, dtype=np.uint8)
        except (AttributeError, ValueError) as exception:
            _LOGGER.warning("Could not clear user_data for RF semantic output: %s", exception)
    try:
        existing_software = str(las.header.generating_software or "")
        merged_software = (existing_software + " " + RF_SEMANTIC_MARKER).strip()
        las.header.generating_software = merged_software[:256]
    except (AttributeError, ValueError) as exception:
        _LOGGER.warning("Could not set generating_software marker: %s", exception)
    ground_point_count = int(np.sum(label_per_point == 1))
    building_point_count = int(np.sum(label_per_point == 2))
    vegetation_point_count = int(np.sum(label_per_point == 3))
    other_point_count = int(np.sum(label_per_point == 4))
    return {
        "n_input": point_count,
        "n_output": point_count,
        "algorithm_code": "ml_rf_semantic",
        "n_ground": ground_point_count,
        "n_building": building_point_count,
        "n_vegetation": vegetation_point_count,
        "n_other": other_point_count,
        "ground_ratio": float(ground_point_count / point_count) if point_count > 0 else 0.0,
    }


def count_semantic_metrics(label_per_point: np.ndarray) -> dict[str, float | int | str]:
    """按 classification 统计各类点数（工具函数）。"""
    point_count = int(label_per_point.shape[0])
    ground_point_count = int(np.sum(label_per_point == 1))
    building_point_count = int(np.sum(label_per_point == 2))
    vegetation_point_count = int(np.sum(label_per_point == 3))
    other_point_count = int(np.sum(label_per_point == 4))
    return {
        "n_input": point_count,
        "n_output": point_count,
        "algorithm_code": "ml_rf_semantic",
        "n_ground": ground_point_count,
        "n_building": building_point_count,
        "n_vegetation": vegetation_point_count,
        "n_other": other_point_count,
        "ground_ratio": float(ground_point_count / point_count) if point_count > 0 else 0.0,
    }
