"""Orchestration used by CLI and eventual HTTP wrappers."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from python_filter import filters as point_cloud_filters
from python_filter.las_io import load_las, save_las_subset_by_mask_from_source
from python_filter.tiled_pipeline import process_tiled_spatial

_LOGGER = logging.getLogger(__name__)

_FILTER_MASK_CALLABLE_REGISTRY: Mapping[str, Callable[..., np.ndarray]] = {
    "sor": point_cloud_filters.sor_keep_mask,
    "ror": point_cloud_filters.ror_keep_mask,
}


def _raise_unless_las_output_suffix(result_output_path: str) -> None:
    output_suffix_lower = Path(result_output_path).suffix.lower()
    if output_suffix_lower not in {".las", ".laz"}:
        if output_suffix_lower == "":
            raise ValueError("Output path must include a file extension (.las or .laz).")
        raise ValueError(
            f"Unsupported output extension '{output_suffix_lower}'. Only .las and .laz outputs are supported."
        )


def process(
    las_input_path: str,
    result_output_path: str,
    *,
    filtering_method_keyword: str = "sor",
    tile_size: float | None = None,
    tile_overlap: float | None = None,
    scratch_workspace_directory: str | Path | None = None,
    bounds_padding_absolute: float = 1e-3,
    bounds_padding_relative: float = 1e-9,
    orphan_points_keep: bool = True,
    **filter_parameter_mapping: Any,
) -> Mapping[str, float | int | str]:
    """
    Load LAS XYZ, compute SOR or ROR keep-mask, emit LAS/LAZ subset via streaming writer.

    When ``tile_size`` is set (positive), uses spatial tiling with ``tile_overlap`` instead of full in-memory load.

    :param las_input_path: Readable LAS/LAZ path.
    :param result_output_path: Must end with ``.las`` or ``.laz`` (dimensions preserved from source header).
    :param filtering_method_keyword: Either ``sor`` or ``ror``.
    :param tile_size: Optional XY core tile length (same units as LAS). When provided, must be positive and ``tile_overlap`` must be supplied.
    :param tile_overlap: Halo width around each core tile when tiling is enabled.
    :param scratch_workspace_directory: Optional directory for tile spill files and mask memmaps when tiling.
    :param bounds_padding_absolute: When tiling, symmetric pad on streamed XY bounds (same units as LAS XY).
    :param bounds_padding_relative: Pad as a fraction of max(span_x, span_y) combined with absolute pad.
    :param orphan_points_keep: When tiling orphan fallback runs, keep (True) or drop (False) those points.
    """
    _raise_unless_las_output_suffix(result_output_path)

    method_token_lower = filtering_method_keyword.lower().strip()
    mask_functor = _FILTER_MASK_CALLABLE_REGISTRY.get(method_token_lower)
    if mask_functor is None:
        allowed_methods_joined = ",".join(sorted(_FILTER_MASK_CALLABLE_REGISTRY.keys()))
        raise ValueError(f"Unsupported method '{filtering_method_keyword}'. Choose one of: {allowed_methods_joined}.")

    uses_spatial_tiling = tile_size is not None
    if uses_spatial_tiling:
        if float(tile_size) <= 0:
            raise ValueError("tile_size must be positive when spatial tiling is enabled.")
        if tile_overlap is None:
            raise ValueError("tile_overlap is required when tile_size is set (spatial tiling).")
        _LOGGER.info(
            "Requesting spatial tiling tile_size=%s tile_overlap=%s scratch_workspace_directory=%s",
            tile_size,
            tile_overlap,
            scratch_workspace_directory,
        )
        return process_tiled_spatial(
            las_input_path,
            result_output_path,
            tile_size=float(tile_size),
            tile_overlap=float(tile_overlap),
            filtering_method_keyword=method_token_lower,
            mask_functor=mask_functor,
            scratch_parent_directory=scratch_workspace_directory,
            bounds_padding_absolute=float(bounds_padding_absolute),
            bounds_padding_relative=float(bounds_padding_relative),
            orphan_points_keep=bool(orphan_points_keep),
            **filter_parameter_mapping,
        )

    if tile_overlap is not None:
        raise ValueError("tile_overlap is only valid when tile_size is set.")

    clock_decode_start_timestamp = time.perf_counter()

    coordinate_matrix_xyz = load_las(las_input_path)
    original_point_row_count_integer = coordinate_matrix_xyz.shape[0]

    clock_filter_anchor_timestamp = time.perf_counter()

    if method_token_lower == "sor":
        neighbour_count_requested = int(
            filter_parameter_mapping.get("k", filter_parameter_mapping.get("neighbor_count", 20))
        )
        pooled_std_multiplier_ratio = float(filter_parameter_mapping.get("std_ratio", 1.0))
        retained_point_boolean_mask = mask_functor(
            coordinate_matrix_xyz,
            neighbor_count=neighbour_count_requested,
            std_ratio=pooled_std_multiplier_ratio,
        )
    elif method_token_lower == "ror":
        spherical_search_radius_measurement = float(
            filter_parameter_mapping.get("radius", filter_parameter_mapping.get("search_radius_metric", 1.0))
        )
        minimum_peer_count_exclusive_self = int(filter_parameter_mapping.get("min_neighbors", 5))
        retained_point_boolean_mask = mask_functor(
            coordinate_matrix_xyz,
            radius=spherical_search_radius_measurement,
            min_neighbors=minimum_peer_count_exclusive_self,
        )
    else:
        raise AssertionError("Unreachable filter dispatch branch.")

    filtered_point_row_count_integer = int(np.count_nonzero(retained_point_boolean_mask))

    clock_write_anchor_timestamp = time.perf_counter()

    save_las_subset_by_mask_from_source(
        source_las_file_path=las_input_path,
        output_las_file_path=result_output_path,
        retention_mask=retained_point_boolean_mask,
    )

    clock_finished_timestamp = time.perf_counter()

    elapsed_decode_seconds = clock_filter_anchor_timestamp - clock_decode_start_timestamp
    elapsed_filter_seconds = clock_write_anchor_timestamp - clock_filter_anchor_timestamp
    elapsed_write_seconds = clock_finished_timestamp - clock_write_anchor_timestamp
    elapsed_total_seconds = clock_finished_timestamp - clock_decode_start_timestamp

    metrics_payload_mapping: dict[str, float | int | str] = {
        "input_path": las_input_path,
        "output_path": result_output_path,
        "method": method_token_lower,
        "N_before": original_point_row_count_integer,
        "N_after": filtered_point_row_count_integer,
        "timing_decode_sec": elapsed_decode_seconds,
        "timing_filter_sec": elapsed_filter_seconds,
        "timing_write_sec": elapsed_write_seconds,
        "timing_total_sec": elapsed_total_seconds,
    }

    _LOGGER.info(
        "LAS filter method=%s N_before=%d N_after=%d total_sec=%.6f decode=%.6f filter=%.6f write=%.6f %s -> %s",
        method_token_lower,
        original_point_row_count_integer,
        filtered_point_row_count_integer,
        elapsed_total_seconds,
        elapsed_decode_seconds,
        elapsed_filter_seconds,
        elapsed_write_seconds,
        las_input_path,
        result_output_path,
    )

    progress_line_tuple = (
        f"[las-filter] timing_total_sec={elapsed_total_seconds:.6f}",
        (
            "[las-filter] timing_breakdown decode_sec="
            f"{elapsed_decode_seconds:.6f} filter_sec={elapsed_filter_seconds:.6f} write_sec={elapsed_write_seconds:.6f}"
        ),
        f"[las-filter] N_before={original_point_row_count_integer} N_after={filtered_point_row_count_integer}",
        f"[las-filter] output_written_path={Path(result_output_path)}",
    )
    for progress_line in progress_line_tuple:
        print(progress_line)

    return metrics_payload_mapping
