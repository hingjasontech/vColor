#!/usr/bin/env python3
"""Build a native onedir bundle with PyInstaller."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    if not args.skip_tests:
        subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
            cwd=ROOT,
            check=True,
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        )

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "packaging/vcolor.spec",
            "--noconfirm",
        ],
        cwd=ROOT,
        check=True,
    )

    if sys.platform == "darwin":
        target = ROOT / "dist" / "vColor.app"
    else:
        target = ROOT / "dist" / "vColor"
    print(f"Built {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
