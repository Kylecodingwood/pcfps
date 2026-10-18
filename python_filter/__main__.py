"""Run as: python -m python_filter --input ... --output ..."""

from __future__ import annotations

import sys

from python_filter.filter import run_cli_main

if __name__ == "__main__":
    raise SystemExit(run_cli_main(sys.argv[1:]))
