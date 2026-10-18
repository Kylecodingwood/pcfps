"""
LAS/LAZ 读写辅助：分块流式读入；按掩码写子集时复制源 header（含 scale/offset）。

论文附录 A-2：save_las_subset_by_mask_from_source 保证滤波前后 LAS 比例尺与平移量不变。

@author PCFPS
@date 2026-05
"""

from __future__ import annotations

from pathlib import Path

import laspy
import numpy as np

_DEFAULT_READ_CHUNK_POINTS = 1_000_000


def load_las(file_path: str | Path, *, chunk_point_count: int = _DEFAULT_READ_CHUNK_POINTS) -> np.ndarray:
    """
    Streams LAS/LAZ XYZ into contiguous memory shaped (N, 3).

    Uses header.point_count to preallocate and chunk_iterator for bounded peak allocations.

    :param file_path: Path to LAS or LAZ on disk readable by laspy backends.
    :param chunk_point_count: Number of LAS records fetched per iterator step.
    :return: float64 XYZ matrix shaped (N, 3) in CRS units from LAS scale/offset fields.
    """
    resolved_source_path = Path(file_path).expanduser().resolve()
    normalized_path_string = str(resolved_source_path)

    with laspy.open(normalized_path_string) as las_reader:
        total_point_count = int(las_reader.header.point_count)
        coordinate_xyz_buffer = np.empty((total_point_count, 3), dtype=np.float64)
        cumulative_rows_appended = 0
        for chunk_point_record in las_reader.chunk_iterator(chunk_point_count):
            chunk_length = len(chunk_point_record)
            row_slice_range = slice(cumulative_rows_appended, cumulative_rows_appended + chunk_length)
            coordinate_xyz_buffer[row_slice_range, 0] = np.asarray(chunk_point_record.x, dtype=np.float64)
            coordinate_xyz_buffer[row_slice_range, 1] = np.asarray(chunk_point_record.y, dtype=np.float64)
            coordinate_xyz_buffer[row_slice_range, 2] = np.asarray(chunk_point_record.z, dtype=np.float64)
            cumulative_rows_appended += chunk_length

        if cumulative_rows_appended != total_point_count:
            raise ValueError(
                "LAS header point_count does not equal streamed chunk total: "
                f"header_point_count={total_point_count}, streamed_points={cumulative_rows_appended}."
            )

    return coordinate_xyz_buffer


def save_las(points_xyz: np.ndarray, output_path: str | Path, *, laz_backend=None) -> None:
    """Writes XYZ-only LAS 1.2 / point_format=3."""

    xyz_matrix = np.asarray(points_xyz[:, :3], dtype=np.float64)
    destination_file_path = Path(output_path).expanduser().resolve()

    synthetic_header = laspy.LasHeader(point_format=3, version="1.2")
    las_destination = laspy.LasData(synthetic_header)
    las_destination.x = xyz_matrix[:, 0].copy()
    las_destination.y = xyz_matrix[:, 1].copy()
    las_destination.z = xyz_matrix[:, 2].copy()

    compressed_output = destination_file_path.suffix.lower() == ".laz"
    las_destination.write(destination_file_path.as_posix(), do_compress=compressed_output, laz_backend=laz_backend)


def save_las_subset_by_mask_from_source(
    *,
    source_las_file_path: str | Path,
    output_las_file_path: str | Path,
    retention_mask: np.ndarray,
    chunk_point_count: int = _DEFAULT_READ_CHUNK_POINTS,
) -> None:
    """
    按布尔掩码从源 LAS 流式写出子集，保留源文件 header（scale/offset、点格式、维度定义）。

    retention_mask[j] 与 laspy chunk_iterator 顺序读入的第 j 条点记录一一对应。
    laspy 读写时使用 header 中的比例尺与偏移，无需手工 int×scale+offset。
    """
    resolved_source_file_path = Path(source_las_file_path).expanduser().resolve()
    resolved_output_file_path = Path(output_las_file_path).expanduser().resolve()

    if retention_mask.ndim != 1:
        raise ValueError("Retention mask must be shaped (N,).")

    bool_retention_mask = np.asarray(retention_mask, dtype=bool)

    with laspy.open(resolved_source_file_path.as_posix()) as las_reader_source:
        if bool_retention_mask.shape[0] != int(las_reader_source.header.point_count):
            raise ValueError(
                "Retention mask length must equal source LAS point_count "
                f"({bool_retention_mask.shape[0]} != {las_reader_source.header.point_count})."
            )

        # 复制 header → 输出 LAS 与源文件坐标系、比例尺一致，仅减少点数
        duplicated_header_structure = las_reader_source.header.copy()
        incremental_source_offset_records = 0
        compressed_destination = resolved_output_file_path.suffix.lower() == ".laz"

        with laspy.open(
            resolved_output_file_path.as_posix(),
            mode="w",
            header=duplicated_header_structure,
            do_compress=compressed_destination,
        ) as las_destination_writer:
            for source_chunk_records in las_reader_source.chunk_iterator(chunk_point_count):
                chunk_point_length = len(source_chunk_records)
                chunk_aligned_mask_segment = bool_retention_mask[
                    incremental_source_offset_records : incremental_source_offset_records + chunk_point_length
                ]
                if chunk_aligned_mask_segment.shape[0] != chunk_point_length:
                    raise ValueError("Aligned mask slicing produced unexpected chunk length.")

                if np.any(chunk_aligned_mask_segment):
                    retained_chunk_records = source_chunk_records[chunk_aligned_mask_segment]
                    las_destination_writer.write_points(retained_chunk_records)

                incremental_source_offset_records += chunk_point_length

