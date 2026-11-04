#!/usr/bin/env python3
"""Convenience launcher for running vColor from a source checkout."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow a local dependency folder created with:
#   python3 -m pip install --target .deps PySide6-Essentials
local_deps = Path(__file__).resolve().parent / ".deps"
if local_deps.exists():
    sys.path.insert(0, str(local_deps))

from vcolor.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
