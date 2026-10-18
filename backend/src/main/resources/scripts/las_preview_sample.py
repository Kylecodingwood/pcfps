#!/usr/bin/env python3
"""
Streams a LAS/LAZ file and prints a single JSON line with uniformly subsampled XYZ points.

When the file's point format includes red, green, and blue dimensions, each emitted point
also carries r, g, b as floats in [0, 1] (16-bit LAS colour divided by 65535), matching
Java Point3dDto. When ``classification`` is present but RGB is not, r,g,b are filled from
pseudo-colour without changing the Three.js payload shape:

- **Ground / non-ground (values in {0,1,2})**: fixed greys / green / orange.
- **Segmentation (otherwise)**: prefer ``user_data`` as colour key when it is non-zero
  (full cluster id up to 255); else ``classification``. Hue spread on a circle using a
  constant step for adjacent-id separation; class 0 = low-saturation neutral.

Usage: las_preview_sample.py <las_path> <max_points> [native|classification] [default|semantic_campus]

Optional 3rd argument ``color_mode`` (default ``native``):

- ``native``: prefer LAS RGB when red/green/blue dimensions exist.
- ``classification`` (alias ``label``): prefer pseudo-colour from ``classification`` /
  ``user_data`` and do not use LAS RGB for display even when RGB dimensions exist.

Optional 4th argument ``palette`` (default ``default``):

- ``semantic_campus``: fixed RGB for rule_semantic_campus classes 1–4 (ground / building / vegetation / other).
  **Keep in sync** with ``frontend/src/preview/DualPreviewLegends.tsx`` swatch hex values.

Stdout: one JSON object with keys points, sourcePointCountEstimate, pointCountReturned,
truncated, maxPointsRequested. Stderr: human-readable errors on failure (non-zero exit).
"""

from __future__ import annotations

import colorsys
import json
import math
import sys
from pathlib import Path

try:
    import laspy
except ImportError:
    laspy = None  # type: ignore[misc, assignment]


def collect_las_preview_heuristic(
    las_path_string: str,
    dimension_name_set: set[str],
    header_point_count: int,
) -> tuple[set[int], int]:
    """Subsamples the file once to infer unique ``classification`` values and max ``user_data``."""
    unique_classification_values: set[int] = set()
    max_user_data_value = 0
    sample_stride = max(1, header_point_count // 30000)
    global_row_index = 0
    with laspy.open(las_path_string) as las_reader:
        for chunk in las_reader.chunk_iterator(1_000_000):
            chunk_point_count = len(chunk.x)
            for row_index in range(chunk_point_count):
                if global_row_index % sample_stride == 0:
                    unique_classification_values.add(int(chunk.classification[row_index]) & 0xFF)
                    if "user_data" in dimension_name_set:
                        max_user_data_value = max(max_user_data_value, int(chunk.user_data[row_index]) & 0xFF)
                global_row_index += 1
    return unique_classification_values, max_user_data_value


def rgb_for_binary_classification(class_id: int) -> tuple[float, float, float]:
    """Fixed colours for PMF/CSF-style labels: 0 unknown, 1 ground, 2 non-ground."""
    if class_id <= 0:
        return colorsys.hsv_to_rgb(0.0, 0.02, 0.72)
    if class_id == 1:
        return (0.22, 0.75, 0.38)
    if class_id == 2:
        return (0.92, 0.42, 0.18)
    hue = (class_id * 0.17) % 1.0
    return colorsys.hsv_to_rgb(hue, 0.75, 0.92)


def rgb_for_segment_color_key(color_key: int) -> tuple[float, float, float]:
    """Spread hues on the circle; key 0 = noise / background."""
    if color_key <= 0:
        return colorsys.hsv_to_rgb(0.55, 0.06, 0.78)
    hue = (color_key * 0.3819660112501051) % 1.0
    return colorsys.hsv_to_rgb(hue, 0.82, 0.94)


def rgb_for_semantic_campus(class_id: int) -> tuple[float, float, float]:
    """
    rule_semantic_campus output: 1 ground, 2 building, 3 vegetation, 4 other.

    Linear RGB in [0,1] — must match ``DualPreviewLegends.tsx`` hex swatches.
    """
    if class_id <= 0:
        return colorsys.hsv_to_rgb(0.0, 0.02, 0.72)
    if class_id == 1:
        return (0.22, 0.75, 0.38)
    if class_id == 2:
        return (0.20, 0.42, 0.92)
    if class_id == 3:
        return (0.55, 0.82, 0.22)
    if class_id == 4:
        return (0.92, 0.62, 0.18)
    return rgb_for_segment_color_key(class_id)


def main() -> int:
    if len(sys.argv) < 3:
        sys.stderr.write(
            "usage: las_preview_sample.py <las_path> <max_points> [native|classification] [default|semantic_campus]\n"
        )
        return 2
    las_path = Path(sys.argv[1]).expanduser().resolve()
    max_points = int(sys.argv[2])
    if max_points < 1:
        sys.stderr.write("max_points must be >= 1\n")
        return 2
    color_mode_raw = sys.argv[3].strip().lower() if len(sys.argv) > 3 else "native"
    if color_mode_raw in ("classification", "label"):
        color_mode_normalized = "classification"
    elif color_mode_raw == "native":
        color_mode_normalized = "native"
    else:
        sys.stderr.write(
            f"invalid color_mode: {color_mode_raw!r}; expected native or classification\n"
        )
        return 2
    palette_raw = sys.argv[4].strip().lower() if len(sys.argv) > 4 else "default"
    if palette_raw in ("default", "semantic_campus"):
        palette_normalized = palette_raw
    else:
        sys.stderr.write(
            f"invalid palette: {palette_raw!r}; expected default or semantic_campus\n"
        )
        return 2
    force_classification_color = color_mode_normalized == "classification"
    if not las_path.is_file():
        sys.stderr.write(f"LAS path is not a file: {las_path}\n")
        return 2

    if laspy is None:
        sys.stderr.write("laspy not available; install laspy for LAS preview.\n")
        return 3

    points_output: list[dict[str, float]] = []
    try:
        with laspy.open(las_path.as_posix()) as header_reader:
            dimension_name_set = {
                dimension.name for dimension in header_reader.header.point_format.dimensions
            }
            header_point_count = int(header_reader.header.point_count)

        if header_point_count <= 0:
            payload = {
                "points": [],
                "sourcePointCountEstimate": 0,
                "pointCountReturned": 0,
                "truncated": False,
                "maxPointsRequested": max_points,
            }
            print(json.dumps(payload))
            return 0

        has_rgb_dimensions = {"red", "green", "blue"} <= dimension_name_set
        has_classification_dimension = "classification" in dimension_name_set
        has_user_data_dimension = "user_data" in dimension_name_set

        use_binary_ground_palette = False
        prefer_user_data_for_segment_color = False
        if has_classification_dimension and (force_classification_color or not has_rgb_dimensions):
            unique_class_values, max_user_data_seen = collect_las_preview_heuristic(
                las_path.as_posix(),
                dimension_name_set,
                header_point_count,
            )
            use_binary_ground_palette = unique_class_values.issubset({0, 1, 2}) and len(unique_class_values) <= 3
            prefer_user_data_for_segment_color = (
                has_user_data_dimension and max_user_data_seen > 0 and not use_binary_ground_palette
            )

        stride = max(1, math.ceil(header_point_count / max_points))
        global_index = 0
        with laspy.open(las_path.as_posix()) as las_reader:
            for chunk in las_reader.chunk_iterator(1_000_000):
                chunk_length = len(chunk.x)
                for row_index in range(chunk_length):
                    if global_index % stride == 0 and len(points_output) < max_points:
                        point_row: dict[str, float] = {
                            "x": float(chunk.x[row_index]),
                            "y": float(chunk.y[row_index]),
                            "z": float(chunk.z[row_index]),
                        }
                        if has_rgb_dimensions and not force_classification_color:
                            point_row["r"] = float(chunk.red[row_index]) / 65535.0
                            point_row["g"] = float(chunk.green[row_index]) / 65535.0
                            point_row["b"] = float(chunk.blue[row_index]) / 65535.0
                        elif has_classification_dimension and (
                            force_classification_color or not has_rgb_dimensions
                        ):
                            class_id = int(chunk.classification[row_index]) & 0xFF
                            if palette_normalized == "semantic_campus" and force_classification_color:
                                red_linear, green_linear, blue_linear = rgb_for_semantic_campus(class_id)
                            elif use_binary_ground_palette:
                                red_linear, green_linear, blue_linear = rgb_for_binary_classification(class_id)
                            elif prefer_user_data_for_segment_color and has_user_data_dimension:
                                color_key = int(chunk.user_data[row_index]) & 0xFF
                                red_linear, green_linear, blue_linear = rgb_for_segment_color_key(color_key)
                            else:
                                red_linear, green_linear, blue_linear = rgb_for_segment_color_key(class_id)
                            point_row["r"] = float(red_linear)
                            point_row["g"] = float(green_linear)
                            point_row["b"] = float(blue_linear)
                        elif has_rgb_dimensions:
                            point_row["r"] = float(chunk.red[row_index]) / 65535.0
                            point_row["g"] = float(chunk.green[row_index]) / 65535.0
                            point_row["b"] = float(chunk.blue[row_index]) / 65535.0
                        points_output.append(point_row)
                    global_index += 1
                    if len(points_output) >= max_points:
                        break
                if len(points_output) >= max_points:
                    break

        point_count_returned = len(points_output)
        truncated = header_point_count > point_count_returned
        payload = {
            "points": points_output,
            "sourcePointCountEstimate": header_point_count,
            "pointCountReturned": point_count_returned,
            "truncated": truncated,
            "maxPointsRequested": max_points,
        }
        print(json.dumps(payload))
        return 0
    except Exception as exception:
        sys.stderr.write(f"LAS preview failed: {exception}\n")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
