#!/usr/bin/env python3
"""Package the built bundle into a release archive for this platform."""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def project_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if match is None:
        raise SystemExit("Could not find project version in pyproject.toml")
    return match.group(1)


def platform_tag() -> str:
    machine = platform.machine().lower()
    if sys.platform == "win32":
        arch = "x64" if machine in {"amd64", "x86_64"} else machine
        return f"windows-{arch}"
    if sys.platform == "darwin":
        arch = "arm64" if machine == "arm64" else "x64"
        return f"macos-{arch}"
    arch = "aarch64" if machine in {"aarch64", "arm64"} else "x86_64"
    return f"linux-{arch}"


def main() -> int:
    version = project_version()
    stem = f"vColor-{version}-{platform_tag()}"

    if sys.platform == "darwin":
        source = DIST / "vColor.app"
        if not source.is_dir():
            raise SystemExit(f"Missing bundle: {source}. Run scripts/build.py first.")
        archive = DIST / f"{stem}.zip"
        archive.unlink(missing_ok=True)
        # ditto keeps symlinks, permissions, and extended attributes intact, which
        # a plain zip does not preserve inside a macOS .app bundle.
        subprocess.run(
            [
                "ditto",
                "-c",
                "-k",
                "--sequesterRsrc",
                "--keepParent",
                str(source),
                str(archive),
            ],
            check=True,
        )
    elif sys.platform == "win32":
        source = DIST / "vColor"
        if not source.is_dir():
            raise SystemExit(f"Missing bundle: {source}. Run scripts/build.py first.")
        archive = DIST / f"{stem}.zip"
        archive.unlink(missing_ok=True)
        shutil.make_archive(str(DIST / stem), "zip", root_dir=DIST, base_dir="vColor")
    else:
        source = DIST / "vColor"
        if not source.is_dir():
            raise SystemExit(f"Missing bundle: {source}. Run scripts/build.py first.")
        archive = DIST / f"{stem}.tar.gz"
        archive.unlink(missing_ok=True)
        with tempfile.TemporaryDirectory() as temporary:
            staging = Path(temporary)
            shutil.copytree(source, staging / "vColor")
            desktop = ROOT / "packaging" / "linux" / "vcolor.desktop"
            if desktop.is_file():
                shutil.copy2(desktop, staging / "vcolor.desktop")
            shutil.make_archive(str(DIST / stem), "gztar", root_dir=staging)

    print(f"Packaged {archive} ({archive.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
