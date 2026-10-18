"""CLI entry for offline LAS filtering (`python -m python_filter`)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from python_filter.pipeline import process

_EXIT_FAILURE = 1


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Statistical (SOR) or radius (ROR) outlier removal on LAS/LAZ using laspy + KDTree/BallTree."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input LAS/LAZ file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path: must use suffix .las or .laz (streaming subset preserves header dimensions).",
    )
    parser.add_argument(
        "--method",
        default="sor",
        choices=("sor", "ror"),
        help="Filter method.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=20,
        help="SOR: number of nearest neighbours (excluding self).",
    )
    parser.add_argument(
        "--std_ratio",
        type=float,
        default=1.0,
        help="SOR: threshold multiplier on global std of per-point mean neighbour distances.",
    )
    parser.add_argument(
        "--radius",
        type=float,
        default=1.0,
        help="ROR: search radius in LAS coordinate units.",
    )
    parser.add_argument(
        "--min_neighbors",
        type=int,
        default=5,
        help="ROR: minimum neighbour count within radius, after excluding the query point itself.",
    )
    parser.add_argument(
        "--tile_size",
        type=float,
        default=None,
        help=(
            "Optional XY core tile length (same units as LAS X/Y). When set, enables spatial tiling instead of "
            "loading the entire cloud into RAM; requires --tile_overlap."
        ),
    )
    parser.add_argument(
        "--tile_overlap",
        type=float,
        default=None,
        help="Halo width around each core tile when --tile_size is set; must be < tile_size / 2.",
    )
    parser.add_argument(
        "--temp_dir",
        default=None,
        help="Optional workspace directory for tile spill files when tiling (default: system temp).",
    )
    parser.add_argument(
        "--bounds_pad_abs",
        type=float,
        default=1e-3,
        help="When tiling: minimum symmetric pad on streamed XY bounds (same units as LAS X/Y).",
    )
    parser.add_argument(
        "--bounds_pad_rel",
        type=float,
        default=1e-9,
        help="When tiling: pad as fraction of max(span_x, span_y), combined with bounds_pad_abs.",
    )
    parser.add_argument(
        "--orphan_drop",
        action="store_true",
        help="When tiling: if orphan fallback runs, mark orphans as drop (False) instead of keep (True).",
    )
    return parser


def run_cli_main(argv: list[str] | None) -> int:
    """Returns POSIX exit code (0 success)."""
    try:
        parser = build_argument_parser()
        parsed_arguments = parser.parse_args(argv)

        output_suffix_lower = Path(parsed_arguments.output).suffix.lower()
        if output_suffix_lower not in {".las", ".laz"}:
            print(
                "Unsupported output suffix; only .las or .laz outputs are supported.",
                file=sys.stderr,
            )
            return _EXIT_FAILURE

        uses_tiling = parsed_arguments.tile_size is not None
        if uses_tiling:
            if parsed_arguments.tile_overlap is None:
                print("[las-filter] ERROR: --tile_overlap is required when --tile_size is set.", file=sys.stderr)
                return _EXIT_FAILURE
        elif parsed_arguments.tile_overlap is not None:
            print("[las-filter] ERROR: --tile_overlap is only valid together with --tile_size.", file=sys.stderr)
            return _EXIT_FAILURE

        extra_parameters: dict[str, Any] = {}
        if parsed_arguments.method == "sor":
            extra_parameters = {"k": parsed_arguments.k, "std_ratio": parsed_arguments.std_ratio}
        elif parsed_arguments.method == "ror":
            extra_parameters = {"radius": parsed_arguments.radius, "min_neighbors": parsed_arguments.min_neighbors}

        if uses_tiling:
            extra_parameters["tile_size"] = parsed_arguments.tile_size
            extra_parameters["tile_overlap"] = parsed_arguments.tile_overlap
            extra_parameters["bounds_padding_absolute"] = parsed_arguments.bounds_pad_abs
            extra_parameters["bounds_padding_relative"] = parsed_arguments.bounds_pad_rel
            extra_parameters["orphan_points_keep"] = not parsed_arguments.orphan_drop
            if parsed_arguments.temp_dir is not None:
                extra_parameters["scratch_workspace_directory"] = Path(parsed_arguments.temp_dir)

        process(
            parsed_arguments.input,
            parsed_arguments.output,
            filtering_method_keyword=parsed_arguments.method,
            **extra_parameters,
        )
        return 0
    except Exception as error:
        print(f"[las-filter] ERROR: {error}", file=sys.stderr)
        return _EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(run_cli_main(sys.argv[1:]))
