# python_filter — LAS Statistical / Radius Outlier Removal

Standalone Python module callable from CLI or imported by a future FastAPI wrapper. **Input and output are LAS/LAZ only** (no PCD).

## Dependency install

From repository root:

```bash
pip install -r python_filter/requirements.txt
```

## CLI examples

LAS → LAS (streaming subset write preserves LAS dimensions):

```bash
PYTHONPATH=. python -m python_filter \
  --input /path/input.las \
  --output /path/output.las \
  --method sor \
  --k 20 \
  --std_ratio 1.0
```

### Large files — spatial tiling with overlap

Default behaviour loads all XYZ into RAM before building the KD-tree/Ball-tree, which can exceed available memory on dense tiles.

With **tiling**, the pipeline first does a **full pass over the LAS** to compute **actual** XY min/max from point data (LAS header bounds are only logged for comparison), then **symmetrically pads** that box using `--bounds_pad_abs` and `--bounds_pad_rel` (defaults `1e-3` and `1e-9`) to absorb header/rounding drift. A **second full pass** buckets points into **extended** XY tiles (core size = `--tile_size`, halo = `--tile_overlap`), runs SOR/ROR per tile, and merges masks so **only points whose XY falls in a tile’s core** receive their mask from that tile. If anything is still unassigned (rare after padding), a **third pass** applies orphan fallback: mark those indices assigned with keep `True` unless `--orphan_drop` is set. Require `0 ≤ tile_overlap < tile_size / 2`.

```bash
PYTHONPATH=. python -m python_filter \
  --input /path/input.las \
  --output /path/output.las \
  --method sor \
  --k 20 \
  --std_ratio 1.0 \
  --tile_size 80.0 \
  --tile_overlap 12.0 \
  --temp_dir /path/to/scratch_workspace
```

`--temp_dir` is optional; when omitted, tile spill files and mask memory maps use the system temp directory (removed after a successful run).

Optional tiling flags: `--bounds_pad_abs`, `--bounds_pad_rel`, `--orphan_drop` (see `--help`).

Metrics printed to stdout include `timing_total_sec`, `N_before`, `N_after`; tiled runs also report `tile_grid_nx`, `tile_grid_ny`, `timing_pass0_bounds_scan_sec`, `timing_pass1_bucket_sec`, `timing_pass2_tiles_sec`, `timing_orphan_fallback_sec`, and `orphan_repaired_count` (zero when every point was covered by the bucket pass).

## Library imports

Public symbols re-exported from `python_filter` package `__init__.py`: `load_las`, `save_las`, `save_las_subset_by_mask_from_source`, `sor_filter`, `ror_filter`, `process`.

`process(..., tile_size=..., tile_overlap=..., scratch_workspace_directory=..., bounds_padding_absolute=..., bounds_padding_relative=..., orphan_points_keep=...)` matches the tiled CLI options.

## Note on vs global SOR

Tiled SOR/ROR is not bit-identical to a single global pass on the full cloud; boundary behaviour is determined by the overlap halos. For evaluation, compare on a small in-memory crop if needed.

## 与仓库内「Web 预览 JSON」的关系（必读）

- **`python_filter`**：离线 **滤波** 真值（CLI / 未来 FastAPI 封装 `process`），**不负责** Spring 的 HTTP 预览响应。
- **后端 LAS 预览**：Spring Boot 在 `POST /api/v1/files/{fileId}/preview-points` 遇到 `.las`/`.laz` 时，会单独起一个 **子进程**，执行 **`backend/src/main/resources/scripts/las_preview_sample.py`**（classpath 资源，与 `python_filter` 目录无关）。该脚本同样依赖 **`laspy`**（及 LAZ 所需后端）。
- **在线滤波任务**：调度用的 HTTP 服务见 **[`../python_gateway/`](../python_gateway/)**，其内部直接 `import` 并调用本包的 **`process`**，写出任务目录下的 **`filtered.las`**（与 CLI 同一算法路径）。
- **部署建议**：运行后端且需预览 LAS 的机器上执行 `pip install laspy`（版本可与 `python_filter/requirements.txt` 对齐）；仅跑 **ASCII PLY** 预览时不需要该脚本成功，由 Java 解析即可。详见 [`../backend/README.md`](../backend/README.md)。
