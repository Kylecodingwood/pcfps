"""
Spatial tiling with overlap for LAS SOR/ROR: extended regions feed kNN context; core regions own mask writes.

@author PCFPS
@date 2026-05
"""

from __future__ import annotations

import logging
import math
import struct
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

import laspy
import numpy as np

from python_filter.las_io import _DEFAULT_READ_CHUNK_POINTS, save_las_subset_by_mask_from_source

_LOGGER = logging.getLogger(__name__)

_RECORD_STRUCT = struct.Struct("<qddd")

_DEFAULT_BOUNDS_PADDING_ABSOLUTE = 1e-3
_DEFAULT_BOUNDS_PADDING_RELATIVE = 1e-9


def _validate_tiling_params(tile_size: float, tile_overlap: float) -> None:
    if tile_size <= 0:
        raise ValueError("tile_size must be positive.")
    if tile_overlap < 0:
        raise ValueError("tile_overlap must be non-negative.")
    if tile_overlap >= tile_size / 2:
        raise ValueError(
            "tile_overlap must be strictly less than tile_size / 2 so each tile core has positive width/height."
        )


def _compute_grid_extent(
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    tile_size: float,
) -> tuple[int, int]:
    span_x = xmax - xmin
    span_y = ymax - ymin
    numeric_epsilon = 1e-9
    if span_x <= numeric_epsilon and span_y <= numeric_epsilon:
        return 1, 1
    nx = max(1, int(math.ceil(span_x / tile_size))) if span_x > numeric_epsilon else 1
    ny = max(1, int(math.ceil(span_y / tile_size))) if span_y > numeric_epsilon else 1
    return nx, ny


def _core_axis_limits(
    axis_min: float,
    axis_max: float,
    tile_index: int,
    tile_count_along_axis: int,
    tile_size: float,
) -> tuple[float, float]:
    core_lo = axis_min + tile_index * tile_size
    core_hi = min(axis_max, axis_min + (tile_index + 1) * tile_size)
    return core_lo, core_hi


def _vectorized_points_in_core_xy(
    x_column: np.ndarray,
    y_column: np.ndarray,
    tile_ix: int,
    tile_iy: int,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    tile_size: float,
    nx: int,
    ny: int,
) -> np.ndarray:
    core_x_lo, core_x_hi = _core_axis_limits(xmin, xmax, tile_ix, nx, tile_size)
    core_y_lo, core_y_hi = _core_axis_limits(ymin, ymax, tile_iy, ny, tile_size)
    last_column_x = tile_ix == nx - 1
    last_row_y = tile_iy == ny - 1
    x_inside_core = (
        (core_x_lo <= x_column) & (x_column <= core_x_hi)
        if last_column_x
        else (core_x_lo <= x_column) & (x_column < core_x_hi)
    )
    y_inside_core = (
        (core_y_lo <= y_column) & (y_column <= core_y_hi)
        if last_row_y
        else (core_y_lo <= y_column) & (y_column < core_y_hi)
    )
    return x_inside_core & y_inside_core


def _extended_xy_bounds(
    tile_ix: int,
    tile_iy: int,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    tile_size: float,
    nx: int,
    ny: int,
    overlap: float,
) -> tuple[float, float, float, float]:
    core_x_lo, core_x_hi = _core_axis_limits(xmin, xmax, tile_ix, nx, tile_size)
    core_y_lo, core_y_hi = _core_axis_limits(ymin, ymax, tile_iy, ny, tile_size)
    ext_x_lo = max(xmin, core_x_lo - overlap)
    ext_x_hi = min(xmax, core_x_hi + overlap)
    ext_y_lo = max(ymin, core_y_lo - overlap)
    ext_y_hi = min(ymax, core_y_hi + overlap)
    return ext_x_lo, ext_x_hi, ext_y_lo, ext_y_hi


def _point_in_extended_tile(
    x: float,
    y: float,
    tile_ix: int,
    tile_iy: int,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    tile_size: float,
    nx: int,
    ny: int,
    overlap: float,
) -> bool:
    ext_x_lo, ext_x_hi, ext_y_lo, ext_y_hi = _extended_xy_bounds(
        tile_ix, tile_iy, xmin, ymin, xmax, ymax, tile_size, nx, ny, overlap
    )
    return ext_x_lo <= x <= ext_x_hi and ext_y_lo <= y <= ext_y_hi


def _iter_candidate_tile_indices(
    x: float,
    y: float,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    tile_size: float,
    nx: int,
    ny: int,
    overlap: float,
) -> Iterator[tuple[int, int]]:
    total_tiles = nx * ny
    if total_tiles <= 4096:
        for tile_ix in range(nx):
            for tile_iy in range(ny):
                if _point_in_extended_tile(
                    x, y, tile_ix, tile_iy, xmin, ymin, xmax, ymax, tile_size, nx, ny, overlap
                ):
                    yield tile_ix, tile_iy
        return

    span_x = xmax - xmin
    span_y = ymax - ymin
    raw_ix = int((x - xmin) / tile_size) if span_x > 1e-9 else 0
    raw_iy = int((y - ymin) / tile_size) if span_y > 1e-9 else 0
    ix_center = min(nx - 1, max(0, raw_ix))
    iy_center = min(ny - 1, max(0, raw_iy))
    tile_stride_in_overlap_units = int(math.ceil(overlap / tile_size)) + 2 if tile_size > 1e-12 else nx

    ix_lo = max(0, ix_center - tile_stride_in_overlap_units)
    ix_hi_exclusive = min(nx, ix_center + tile_stride_in_overlap_units + 1)
    iy_lo = max(0, iy_center - tile_stride_in_overlap_units)
    iy_hi_exclusive = min(ny, iy_center + tile_stride_in_overlap_units + 1)

    if ix_hi_exclusive - ix_lo >= nx:
        ix_range = range(nx)
    else:
        ix_range = range(ix_lo, ix_hi_exclusive)
    if iy_hi_exclusive - iy_lo >= ny:
        iy_range = range(ny)
    else:
        iy_range = range(iy_lo, iy_hi_exclusive)

    for tile_ix in ix_range:
        for tile_iy in iy_range:
            if _point_in_extended_tile(
                x, y, tile_ix, tile_iy, xmin, ymin, xmax, ymax, tile_size, nx, ny, overlap
            ):
                yield tile_ix, tile_iy


def _scan_xy_bounds_from_las_stream(
    las_file_path: Path,
    *,
    chunk_point_count: int,
) -> tuple[float, float, float, float, int, int]:
    """
    Streams the LAS once and returns actual XY extrema plus streamed point count.

    :param las_file_path: Readable LAS/LAZ path.
    :param chunk_point_count: laspy chunk_iterator size.
    :return: Tuple ``(xmin, xmax, ymin, ymax, header_point_count, streamed_point_count)``.
    """
    streamed_point_count = 0
    data_xmin = math.inf
    data_xmax = -math.inf
    data_ymin = math.inf
    data_ymax = -math.inf

    with laspy.open(las_file_path.as_posix()) as las_reader:
        header_point_count = int(las_reader.header.point_count)
        header_xmin = float(las_reader.header.x_min)
        header_xmax = float(las_reader.header.x_max)
        header_ymin = float(las_reader.header.y_min)
        header_ymax = float(las_reader.header.y_max)

        for chunk_point_record in las_reader.chunk_iterator(chunk_point_count):
            chunk_x = np.asarray(chunk_point_record.x, dtype=np.float64)
            chunk_y = np.asarray(chunk_point_record.y, dtype=np.float64)
            chunk_x_min = float(np.min(chunk_x))
            chunk_x_max = float(np.max(chunk_x))
            chunk_y_min = float(np.min(chunk_y))
            chunk_y_max = float(np.max(chunk_y))
            data_xmin = min(data_xmin, chunk_x_min)
            data_xmax = max(data_xmax, chunk_x_max)
            data_ymin = min(data_ymin, chunk_y_min)
            data_ymax = max(data_ymax, chunk_y_max)
            streamed_point_count += int(chunk_x.shape[0])

    if streamed_point_count == 0:
        raise ValueError("LAS stream produced zero points; cannot compute XY bounds.")

    if streamed_point_count != header_point_count:
        _LOGGER.warning(
            "LAS streamed point count differs from header point_count: streamed=%d header=%d path=%s",
            streamed_point_count,
            header_point_count,
            las_file_path,
        )

    _LOGGER.info(
        "XY bounds header vs streamed-data path=%s header_xy=(%s,%s,%s,%s) data_xy=(%s,%s,%s,%s)",
        las_file_path,
        header_xmin,
        header_xmax,
        header_ymin,
        header_ymax,
        data_xmin,
        data_xmax,
        data_ymin,
        data_ymax,
    )

    return data_xmin, data_xmax, data_ymin, data_ymax, header_point_count, streamed_point_count


def _pad_xy_bounds_symmetric(
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    *,
    padding_absolute: float,
    padding_relative: float,
) -> tuple[float, float, float, float]:
    """
    Expands XY bounds symmetrically for numeric tolerance at tile edges.

    padding = max(padding_absolute, padding_relative * max(span_x, span_y)).
    """
    span_x = xmax - xmin
    span_y = ymax - ymin
    span_reference = max(span_x, span_y, 1e-30)
    padding_half_width = max(padding_absolute, padding_relative * span_reference)
    return (
        xmin - padding_half_width,
        xmax + padding_half_width,
        ymin - padding_half_width,
        ymax + padding_half_width,
    )


def _apply_orphan_point_fallback_stream(
    las_file_path: Path,
    *,
    chunk_point_count: int,
    total_point_count: int,
    global_assigned_buffer: np.memmap,
    global_keep_buffer: np.memmap,
    orphan_points_keep: bool,
) -> int:
    """
    Third LAS pass: assign any still-unassigned indices (keep/drop only; does not re-run tile SOR).

    :return: Number of indices repaired.
    """
    repaired_orphan_count = 0
    global_point_index = 0

    with laspy.open(las_file_path.as_posix()) as las_reader:
        for chunk_point_record in las_reader.chunk_iterator(chunk_point_count):
            chunk_x = np.asarray(chunk_point_record.x, dtype=np.float64)
            chunk_y = np.asarray(chunk_point_record.y, dtype=np.float64)
            chunk_length = len(chunk_x)
            for offset_within_chunk in range(chunk_length):
                if not bool(global_assigned_buffer[global_point_index]):
                    global_assigned_buffer[global_point_index] = True
                    global_keep_buffer[global_point_index] = bool(orphan_points_keep)
                    repaired_orphan_count += 1
                global_point_index += 1

    if global_point_index != total_point_count:
        raise ValueError(
            "Orphan fallback stream length mismatch: "
            f"expected={total_point_count}, streamed={global_point_index}."
        )

    return repaired_orphan_count


def _clear_workspace_spill_files(scratch_workspace_directory: Path) -> None:
    for spill_pattern in ("tile_*.bin", "global_assigned.mmap", "global_keep.mmap"):
        for spill_file_path in scratch_workspace_directory.glob(spill_pattern):
            spill_file_path.unlink(missing_ok=True)


def _flush_tile_byte_buffers(
    tile_record_buffers: dict[tuple[int, int], bytearray],
    tile_output_paths: dict[tuple[int, int], Path],
    scratch_workspace_directory: Path,
) -> None:
    for tile_key, byte_buffer in tile_record_buffers.items():
        if not byte_buffer:
            continue
        destination_tile_path = tile_output_paths.setdefault(
            tile_key,
            scratch_workspace_directory / f"tile_{tile_key[0]}_{tile_key[1]}.bin",
        )
        with destination_tile_path.open("ab") as append_binary_stream:
            append_binary_stream.write(byte_buffer)
        byte_buffer.clear()


def process_tiled_spatial(
    las_input_path: str,
    result_output_path: str,
    *,
    tile_size: float,
    tile_overlap: float,
    filtering_method_keyword: str,
    mask_functor: Callable[..., np.ndarray],
    chunk_point_count: int = _DEFAULT_READ_CHUNK_POINTS,
    scratch_parent_directory: Path | str | None = None,
    bounds_padding_absolute: float = _DEFAULT_BOUNDS_PADDING_ABSOLUTE,
    bounds_padding_relative: float = _DEFAULT_BOUNDS_PADDING_RELATIVE,
    orphan_points_keep: bool = True,
    **filter_parameter_mapping: Any,
) -> Mapping[str, float | int | str]:
    """
    Stream LAS into XY tiles with overlap, run SOR/ROR per extended tile, merge masks by core ownership, write LAS/LAZ.

    :param las_input_path: Source LAS/LAZ path.
    :param result_output_path: Destination .las or .laz path.
    :param tile_size: Core tile extent along X and Y (same units as LAS XY).
    :param tile_overlap: Halo added around each core for neighbourhood context.
    :param filtering_method_keyword: ``sor`` or ``ror`` (for metrics/logging).
    :param mask_functor: ``sor_keep_mask`` or ``ror_keep_mask`` from filters module.
    :param chunk_point_count: laspy chunk_iterator size.
    :param scratch_parent_directory: Optional directory for temp tiles and memmaps; otherwise system temp.
    :param bounds_padding_absolute: Minimum half-width pad applied symmetrically to streamed XY bounds.
    :param bounds_padding_relative: Pad as a fraction of max(span_x, span_y) combined with absolute pad.
    :param orphan_points_keep: When orphan fallback runs, set ``keep`` to True (preserve) or False (drop).
    :param filter_parameter_mapping: k/std_ratio for SOR or radius/min_neighbors for ROR.
    :return: Metrics mapping including timing_pass0_bounds_scan_sec, timing_pass1_bucket_sec, timing_pass2_tiles_sec.
    """
    _validate_tiling_params(tile_size, tile_overlap)
    resolved_input_path = Path(las_input_path).expanduser().resolve()
    resolved_output_path = Path(result_output_path).expanduser().resolve()

    method_token_lower = filtering_method_keyword.lower().strip()
    clock_pipeline_start = time.perf_counter()

    if scratch_parent_directory is not None:
        scratch_workspace_directory = Path(scratch_parent_directory).expanduser().resolve()
        scratch_workspace_directory.mkdir(parents=True, exist_ok=True)
        temp_directory_handle = None
    else:
        temp_directory_handle = tempfile.TemporaryDirectory(prefix="pcfps_tiled_")
        scratch_workspace_directory = Path(temp_directory_handle.name)

    try:
        _clear_workspace_spill_files(scratch_workspace_directory)

        clock_pass0_start = time.perf_counter()
        data_xmin, data_xmax, data_ymin, data_ymax, header_point_count, streamed_point_count = (
            _scan_xy_bounds_from_las_stream(resolved_input_path, chunk_point_count=chunk_point_count)
        )
        xmin, xmax, ymin, ymax = _pad_xy_bounds_symmetric(
            data_xmin,
            data_xmax,
            data_ymin,
            data_ymax,
            padding_absolute=float(bounds_padding_absolute),
            padding_relative=float(bounds_padding_relative),
        )
        clock_pass0_end = time.perf_counter()

        total_point_count = int(header_point_count)
        nx, ny = _compute_grid_extent(xmin, xmax, ymin, ymax, tile_size)
        _LOGGER.info(
            "Tiled LAS filter starting path=%s point_count=%d streamed_count=%d grid_nx=%d grid_ny=%d "
            "tile_size=%s overlap=%s bounds_pad_abs=%s bounds_pad_rel=%s",
            resolved_input_path,
            total_point_count,
            streamed_point_count,
            nx,
            ny,
            tile_size,
            tile_overlap,
            bounds_padding_absolute,
            bounds_padding_relative,
        )

        tile_output_paths: dict[tuple[int, int], Path] = {}
        tile_record_buffers: dict[tuple[int, int], bytearray] = {}

        with laspy.open(resolved_input_path.as_posix()) as las_reader:
            clock_pass1_start = time.perf_counter()
            global_point_index = 0
            for chunk_point_record in las_reader.chunk_iterator(chunk_point_count):
                chunk_x = np.asarray(chunk_point_record.x, dtype=np.float64)
                chunk_y = np.asarray(chunk_point_record.y, dtype=np.float64)
                chunk_z = np.asarray(chunk_point_record.z, dtype=np.float64)
                chunk_length = len(chunk_x)
                for offset_within_chunk in range(chunk_length):
                    sample_x = float(chunk_x[offset_within_chunk])
                    sample_y = float(chunk_y[offset_within_chunk])
                    sample_z = float(chunk_z[offset_within_chunk])
                    for tile_ix, tile_iy in _iter_candidate_tile_indices(
                        sample_x,
                        sample_y,
                        xmin,
                        ymin,
                        xmax,
                        ymax,
                        tile_size,
                        nx,
                        ny,
                        tile_overlap,
                    ):
                        tile_key = (tile_ix, tile_iy)
                        if tile_key not in tile_record_buffers:
                            tile_record_buffers[tile_key] = bytearray()
                        packed_record_bytes = _RECORD_STRUCT.pack(
                            global_point_index,
                            sample_x,
                            sample_y,
                            sample_z,
                        )
                        tile_record_buffers[tile_key].extend(packed_record_bytes)
                    global_point_index += 1

                _flush_tile_byte_buffers(
                    tile_record_buffers,
                    tile_output_paths,
                    scratch_workspace_directory,
                )

            if global_point_index != total_point_count:
                raise ValueError(
                    "Streamed point index count does not match LAS header point_count: "
                    f"expected={total_point_count}, streamed={global_point_index}."
                )

            clock_pass1_end = time.perf_counter()

        assigned_mask_path = scratch_workspace_directory / "global_assigned.mmap"
        retention_mask_path = scratch_workspace_directory / "global_keep.mmap"

        global_assigned_buffer = np.memmap(
            assigned_mask_path,
            dtype=np.bool_,
            mode="w+",
            shape=(total_point_count,),
        )
        global_keep_buffer = np.memmap(
            retention_mask_path,
            dtype=np.bool_,
            mode="w+",
            shape=(total_point_count,),
        )
        global_assigned_buffer[:] = False
        global_keep_buffer[:] = False

        clock_pass2_start = time.perf_counter()

        dtype_tile_record = np.dtype(
            [
                ("global_index", np.int64),
                ("x", np.float64),
                ("y", np.float64),
                ("z", np.float64),
            ]
        )

        sorted_tile_keys = sorted(tile_output_paths.keys())

        for tile_key in sorted_tile_keys:
            tile_binary_path = tile_output_paths[tile_key]
            tile_ix, tile_iy = tile_key
            tile_table = np.fromfile(tile_binary_path, dtype=dtype_tile_record)
            if tile_table.size == 0:
                _LOGGER.warning("Empty tile buffer tile_ix=%s tile_iy=%s path=%s", tile_ix, tile_iy, tile_binary_path)
                continue

            coordinate_xyz_matrix = np.empty((tile_table.shape[0], 3), dtype=np.float64)
            coordinate_xyz_matrix[:, 0] = tile_table["x"]
            coordinate_xyz_matrix[:, 1] = tile_table["y"]
            coordinate_xyz_matrix[:, 2] = tile_table["z"]

            if method_token_lower == "sor":
                neighbour_count_requested = int(
                    filter_parameter_mapping.get("k", filter_parameter_mapping.get("neighbor_count", 20))
                )
                pooled_std_multiplier_ratio = float(filter_parameter_mapping.get("std_ratio", 1.0))
                local_keep_mask = mask_functor(
                    coordinate_xyz_matrix,
                    neighbor_count=neighbour_count_requested,
                    std_ratio=pooled_std_multiplier_ratio,
                )
            elif method_token_lower == "ror":
                spherical_search_radius_measurement = float(
                    filter_parameter_mapping.get("radius", filter_parameter_mapping.get("search_radius_metric", 1.0))
                )
                minimum_peer_count_exclusive_self = int(filter_parameter_mapping.get("min_neighbors", 5))
                local_keep_mask = mask_functor(
                    coordinate_xyz_matrix,
                    radius=spherical_search_radius_measurement,
                    min_neighbors=minimum_peer_count_exclusive_self,
                )
            else:
                raise ValueError(f"Unsupported tiled method '{filtering_method_keyword}'.")

            global_index_column = tile_table["global_index"]
            x_column = tile_table["x"]
            y_column = tile_table["y"]

            owns_core_row_mask = _vectorized_points_in_core_xy(
                x_column,
                y_column,
                tile_ix,
                tile_iy,
                xmin,
                ymin,
                xmax,
                ymax,
                tile_size,
                nx,
                ny,
            )
            global_indices_for_core_rows = global_index_column[owns_core_row_mask].astype(np.int64, copy=False)
            if global_indices_for_core_rows.size > 1:
                sorted_global_indices = np.sort(global_indices_for_core_rows)
                if np.any(sorted_global_indices[1:] == sorted_global_indices[:-1]):
                    raise RuntimeError(
                        "Duplicate global indices within one tile core slice; tiling spill logic is inconsistent."
                    )
            if np.any(global_assigned_buffer[global_indices_for_core_rows]):
                raise RuntimeError(
                    "Overlapping core ownership for at least one global index; check tile overlap and partition rules."
                )
            global_assigned_buffer[global_indices_for_core_rows] = True
            global_keep_buffer[global_indices_for_core_rows] = local_keep_mask[owns_core_row_mask]

        clock_pass2_end = time.perf_counter()

        global_assigned_buffer.flush()
        global_keep_buffer.flush()

        elapsed_orphan_seconds = 0.0
        orphan_repaired_count = 0
        if not bool(np.all(global_assigned_buffer)):
            unassigned_before_fallback = int(total_point_count - int(np.count_nonzero(global_assigned_buffer)))
            _LOGGER.warning(
                "Tiled pipeline has %d unassigned points before orphan fallback; applying stream repair path=%s",
                unassigned_before_fallback,
                resolved_input_path,
            )
            clock_orphan_start = time.perf_counter()
            orphan_repaired_count = _apply_orphan_point_fallback_stream(
                resolved_input_path,
                chunk_point_count=chunk_point_count,
                total_point_count=total_point_count,
                global_assigned_buffer=global_assigned_buffer,
                global_keep_buffer=global_keep_buffer,
                orphan_points_keep=bool(orphan_points_keep),
            )
            elapsed_orphan_seconds = time.perf_counter() - clock_orphan_start
            global_assigned_buffer.flush()
            global_keep_buffer.flush()
            _LOGGER.info(
                "Orphan fallback repaired %d point indices (orphan_points_keep=%s) path=%s",
                orphan_repaired_count,
                orphan_points_keep,
                resolved_input_path,
            )

        if not bool(np.all(global_assigned_buffer)):
            unassigned_remaining = int(total_point_count - int(np.count_nonzero(global_assigned_buffer)))
            raise RuntimeError(
                f"Tiled pipeline still left {unassigned_remaining} points without assignment after orphan fallback; "
                "check tiling implementation or LAS integrity."
            )

        filtered_point_row_count_integer = int(np.count_nonzero(global_keep_buffer))
        clock_write_start = time.perf_counter()

        save_las_subset_by_mask_from_source(
            source_las_file_path=resolved_input_path,
            output_las_file_path=resolved_output_path,
            retention_mask=np.asarray(global_keep_buffer, dtype=bool),
            chunk_point_count=chunk_point_count,
        )

        clock_write_end = time.perf_counter()
        clock_pipeline_end = time.perf_counter()

        elapsed_pass0_seconds = clock_pass0_end - clock_pass0_start
        elapsed_pass1_seconds = clock_pass1_end - clock_pass1_start
        elapsed_pass2_seconds = clock_pass2_end - clock_pass2_start
        elapsed_write_seconds = clock_write_end - clock_write_start
        elapsed_total_seconds = clock_pipeline_end - clock_pipeline_start

        metrics_payload_mapping: dict[str, float | int | str] = {
            "input_path": str(resolved_input_path),
            "output_path": str(resolved_output_path),
            "method": method_token_lower,
            "N_before": total_point_count,
            "N_after": filtered_point_row_count_integer,
            "timing_pass0_bounds_scan_sec": elapsed_pass0_seconds,
            "timing_decode_sec": elapsed_pass0_seconds + elapsed_pass1_seconds,
            "timing_filter_sec": elapsed_pass2_seconds + elapsed_orphan_seconds,
            "timing_pass1_bucket_sec": elapsed_pass1_seconds,
            "timing_pass2_tiles_sec": elapsed_pass2_seconds,
            "timing_orphan_fallback_sec": elapsed_orphan_seconds,
            "timing_write_sec": elapsed_write_seconds,
            "timing_total_sec": elapsed_total_seconds,
            "tile_grid_nx": nx,
            "tile_grid_ny": ny,
            "orphan_repaired_count": orphan_repaired_count,
        }

        _LOGGER.info(
            "Tiled LAS filter finished method=%s N_before=%d N_after=%d total_sec=%.6f pass1=%.6f pass2=%.6f write=%.6f %s -> %s",
            method_token_lower,
            total_point_count,
            filtered_point_row_count_integer,
            elapsed_total_seconds,
            elapsed_pass1_seconds,
            elapsed_pass2_seconds,
            elapsed_write_seconds,
            resolved_input_path,
            resolved_output_path,
        )

        for progress_line in (
            f"[las-filter] tiled timing_total_sec={elapsed_total_seconds:.6f}",
            (
                "[las-filter] tiled timing_breakdown pass0_bounds_scan_sec="
                f"{elapsed_pass0_seconds:.6f} pass1_bucket_sec={elapsed_pass1_seconds:.6f} "
                f"pass2_tiles_sec={elapsed_pass2_seconds:.6f} orphan_fallback_sec={elapsed_orphan_seconds:.6f} "
                f"write_sec={elapsed_write_seconds:.6f}"
            ),
            f"[las-filter] N_before={total_point_count} N_after={filtered_point_row_count_integer}",
            f"[las-filter] tile_grid_nx={nx} tile_grid_ny={ny} orphan_repaired_count={orphan_repaired_count}",
            f"[las-filter] output_written_path={resolved_output_path}",
        ):
            print(progress_line)

        return metrics_payload_mapping

    finally:
        if temp_directory_handle is not None:
            temp_directory_handle.cleanup()
