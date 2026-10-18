"""CLI: train RandomForest on labeled LAS (classification 1–4)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import laspy
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from python_rf_semantic.geometry_features import build_feature_matrix
from python_rf_semantic.infer_core import read_intensity_normalized, read_xyz_from_las
from python_rf_semantic.model_io import default_pmf_params, save_model_bundle

_LOGGER = logging.getLogger(__name__)


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train RF semantic classifier on labeled LAS.")
    parser.add_argument("--labeled-las", required=True, help="LAS with classification 1–4 (0 ignored).")
    parser.add_argument("--output-dir", required=True, help="Directory for model.joblib and feature_config.json.")
    parser.add_argument("--neighbor-k", type=int, default=24, help="kNN size for planarity / z_std features.")
    parser.add_argument("--cell-size-m", type=float, default=0.6)
    parser.add_argument("--max-window-size", type=int, default=8)
    parser.add_argument("--slope-threshold", type=float, default=0.15)
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    arguments = _parse_arguments()
    labeled_las_path = Path(arguments.labeled_las).expanduser().resolve()
    output_directory = Path(arguments.output_dir).expanduser().resolve()
    if not labeled_las_path.is_file():
        _LOGGER.error("Labeled LAS not found: %s", labeled_las_path)
        return 2
    las = laspy.read(str(labeled_las_path))
    xyz = read_xyz_from_las(las)
    label_array = np.asarray(las.classification, dtype=np.int64)
    labeled_mask = (label_array >= 1) & (label_array <= 4)
    if not np.any(labeled_mask):
        _LOGGER.error("No points with classification in 1..4")
        return 2
    pmf_params = default_pmf_params()
    pmf_params["cell_size_m"] = arguments.cell_size_m
    pmf_params["max_window_size"] = arguments.max_window_size
    pmf_params["slope_threshold"] = arguments.slope_threshold
    neighbor_k = int(arguments.neighbor_k)
    intensity_normalized = read_intensity_normalized(las)
    feature_matrix_full, feature_name_list = build_feature_matrix(
        xyz, pmf_params, neighbor_k, intensity_normalized
    )
    feature_matrix = feature_matrix_full[labeled_mask]
    target_labels = label_array[labeled_mask]
    _LOGGER.info(
        "Training on %s labeled points (total %s) features=%s",
        feature_matrix.shape[0],
        xyz.shape[0],
        feature_name_list,
    )
    train_features, test_features, train_labels, test_labels = train_test_split(
        feature_matrix,
        target_labels,
        test_size=arguments.test_fraction,
        random_state=arguments.random_state,
        stratify=target_labels,
    )
    classifier = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=arguments.random_state,
        n_jobs=-1,
    )
    classifier.fit(train_features, train_labels)
    test_predictions = classifier.predict(test_features)
    report_text = classification_report(test_labels, test_predictions, digits=4)
    _LOGGER.info("Hold-out classification report:\n%s", report_text)
    save_model_bundle(
        output_directory,
        classifier,
        feature_name_list,
        pmf_params,
        neighbor_k,
    )
    metrics_payload = {
        "labeled_las": str(labeled_las_path),
        "n_labeled": int(feature_matrix.shape[0]),
        "n_total": int(xyz.shape[0]),
        "feature_names": feature_name_list,
        "holdout_classification_report": report_text,
    }
    (output_directory / "metrics.json").write_text(
        json.dumps(metrics_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _LOGGER.info("Saved model to %s", output_directory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
