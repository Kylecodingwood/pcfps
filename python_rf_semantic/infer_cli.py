"""CLI: infer RF semantic labels and write output LAS."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import laspy

from python_rf_semantic.infer_core import apply_rf_semantic_to_las

_LOGGER = logging.getLogger(__name__)


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Infer RF semantic classification on LAS.")
    parser.add_argument("--input-las", required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--output-las", required=True)
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    arguments = _parse_arguments()
    input_las_path = Path(arguments.input_las).expanduser().resolve()
    model_directory = Path(arguments.model_dir).expanduser().resolve()
    output_las_path = Path(arguments.output_las).expanduser().resolve()
    if not input_las_path.is_file():
        _LOGGER.error("Input LAS not found: %s", input_las_path)
        return 2
    if not model_directory.is_dir():
        _LOGGER.error("Model directory not found: %s", model_directory)
        return 2
    las = laspy.read(str(input_las_path))
    metrics_mapping = apply_rf_semantic_to_las(las, model_directory)
    output_las_path.parent.mkdir(parents=True, exist_ok=True)
    compress_output = output_las_path.suffix.lower() == ".laz"
    las.write(str(output_las_path), do_compress=compress_output)
    _LOGGER.info("Wrote %s metrics=%s", output_las_path, metrics_mapping)
    return 0


if __name__ == "__main__":
    sys.exit(main())
