"""Persist and load RandomForest model + feature configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
from sklearn.ensemble import RandomForestClassifier

MODEL_FILENAME = "model.joblib"
FEATURE_CONFIG_FILENAME = "feature_config.json"


def default_pmf_params() -> dict[str, Any]:
    return {
        "cell_size_m": 0.6,
        "max_window_size": 8,
        "slope_threshold": 0.15,
    }


def save_model_bundle(
    model_directory: Path,
    classifier: RandomForestClassifier,
    feature_name_list: list[str],
    pmf_params: dict[str, Any],
    neighbor_k: int,
    class_label_map: dict[str, int] | None = None,
) -> None:
    model_directory.mkdir(parents=True, exist_ok=True)
    joblib.dump(classifier, model_directory / MODEL_FILENAME)
    config_payload: dict[str, Any] = {
        "feature_names": feature_name_list,
        "pmf_params": pmf_params,
        "semantic_neighbor_count": neighbor_k,
        "class_labels": class_label_map
        or {"ground": 1, "building": 2, "vegetation": 3, "other": 4},
    }
    (model_directory / FEATURE_CONFIG_FILENAME).write_text(
        json.dumps(config_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_model_bundle(model_directory: Path) -> tuple[RandomForestClassifier, dict[str, Any]]:
    model_path = model_directory / MODEL_FILENAME
    config_path = model_directory / FEATURE_CONFIG_FILENAME
    if not model_path.is_file():
        raise FileNotFoundError(f"Missing model file: {model_path}")
    if not config_path.is_file():
        raise FileNotFoundError(f"Missing feature config: {config_path}")
    classifier = joblib.load(model_path)
    config_payload = json.loads(config_path.read_text(encoding="utf-8"))
    return classifier, config_payload
