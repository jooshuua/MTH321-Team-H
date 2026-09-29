#!/usr/bin/env python3
"""Single entry point that regenerates every report figure and result file."""

from pathlib import Path
import runpy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_SCRIPT = PROJECT_ROOT / "financial_sde_project.py"

if not MAIN_SCRIPT.is_file():
    raise FileNotFoundError(f"Main experiment script not found: {MAIN_SCRIPT}")

runpy.run_path(str(MAIN_SCRIPT), run_name="__main__")
