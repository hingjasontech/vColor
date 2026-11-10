#!/usr/bin/env python3
"""Package the built bundle into release archives for this platform."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
HOMEPAGE = "https://github.com/hingjasontech/vColor"
MAINTAINER = "vColor contributors <noreply@example.com>"

DEB_DEPENDS = (
    "libc6",
    "libegl1",
    "libgl1",
    "libxkbcommon0",
    "libxkbcommon-x11-0",
    "libxcb-cursor0",
    "libxcb-icccm4",
    "libxcb-image0",
    "libxcb-keysyms1",
    "libxcb-randr0",
    "libxcb-render-util0",
    "libxcb-shape0",
    "libxcb-xkb1",
    "libxcb-xinerama0",
    "libx11-xcb1",
    "libfontconfig1",
    "libfreetype6",
)

RPM_DEPENDS = (
    "glibc",
    "libxkbcommon",
    "libxkbcommon-x11",
    "mesa-libGL",
    "mesa-libEGL",
    "xcb-util",
    "xcb-util-cursor",
    "xcb-util-image",
    "xcb-util-keysyms",
    "xcb-util-renderutil",
    "xcb-util-wm",
    "libX11-xcb",
    "fontconfig",
    "freetype",
)


def project_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if match is None:
        raise SystemExit("Could not find project version in pyproject.toml")
    return match.group(1)


def windows_arch() -> str:
    """Return ``arm64`` or ``x64`` for the running Windows interpreter.

    ``platform.machine()`` reports ``ARM64`` even for an emulated x64 Python, so
    the interpreter's own platform tag is the reliable source here.
    """
    return "arm64" if "arm" in sysconfig.get_platform().lower() else "x64"


def platform_tag() -> str:
    machine = platform.machine().lower()
    if sys.platform == "win32":
        return f"windows-{windows_arch()}"
    if sys.platform == "darwin":
        arch = "arm64" if machine == "arm64" else "x64"
        return f"macos-{arch}"
    arch = "arm64" if machine in {"aarch64", "arm64"} else "x86_64"
    return f"linux-{arch}"


def inno_arch() -> str:
    return "arm64" if windows_arch() == "arm64" else "x64compatible"


def deb_arch() -> str:
    return {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(
        platform.machine().lower(), platform.machine().lower()
    )


def rpm_arch() -> str:
    return {"x86_64": "x86_64", "amd64": "x86_64", "aarch64": "aarch64", "arm64": "aarch64"}.get(
        platform.machine().lower(), platform.machine().lower()
    )


def appimage_arch() -> str:
    return "aarch64" if platform.machine().lower() in {"aarch64", "arm64"} else "x86_64"


def find_appimagetool() -> str | None:
    override = os.environ.get("APPIMAGETOOL")
    if override:
        return override if Path(override).is_file() else None
    return shutil.which("appimagetool")


def find_iscc() -> str | None:
    override = os.environ.get("ISCC")
    if override and Path(override).is_file():
        return override
    found = shutil.which("iscc") or shutil.which("ISCC")
    if found:
        return found
    roots = [os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")]
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        roots.append(str(Path(local_appdata) / "Programs"))
    for root in roots:
        if not root:
            continue
        for directory in sorted(Path(root).glob("Inno Setup *")):
            candidate = directory / "ISCC.exe"
            if candidate.is_file():
                return str(candidate)
    return None


def write_file(path: Path, text: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    if executable:
        path.chmod(0o755)


def linux_install_tree(stage: Path, source: Path) -> None:
    """Build an FHS-like tree for .deb and .rpm packages."""
    bundle = stage / "opt" / "vcolor"
    shutil.copytree(source, bundle)

    bin_dir = stage / "usr" / "bin"
    bin_dir.mkdir(parents=True)
    write_file(
        bin_dir / "vColor",
        "#!/bin/sh\nexec /opt/vcolor/vColor \"$@\"\n",
        executable=True,
    )
    (bin_dir / "vcolor").symlink_to("vColor")

    applications = stage / "usr" / "share" / "applications"
    applications.mkdir(parents=True)
    shutil.copy2(
        ROOT / "packaging" / "linux" / "vcolor.desktop",
        applications / "vcolor.desktop",
    )

    resources = ROOT / "vcolor" / "resources"
    png_dir = stage / "usr" / "share" / "icons" / "hicolor" / "512x512" / "apps"
    png_dir.mkdir(parents=True)
    shutil.copy2(resources / "icon.png", png_dir / "vColor.png")
    svg_dir = stage / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps"
    svg_dir.mkdir(parents=True)
    shutil.copy2(resources / "icon.svg", svg_dir / "vColor.svg")

    doc_dir = stage / "usr" / "share" / "doc" / "vcolor"
    doc_dir.mkdir(parents=True)
    shutil.copy2(ROOT / "LICENSE", doc_dir / "copyright")


def build_deb(stage: Path, root: Path, version: str, archive: Path) -> None:
    deb_root = root / "vcolor"
    shutil.copytree(stage, deb_root, symlinks=True)

    installed_kb = max(
        1,
        sum(path.stat().st_size for path in deb_root.rglob("*") if path.is_file()) // 1024,
    )
    control = f"""Package: vcolor
Version: {version}
Section: graphics
Priority: optional
Architecture: {deb_arch()}
Maintainer: {MAINTAINER}
Installed-Size: {installed_kb}
Depends: {", ".join(DEB_DEPENDS)}
Homepage: {HOMEPAGE}
Description: A fast, focused desktop color project manager
 vColor is a desktop color project manager built with Qt.
"""
    write_file(deb_root / "DEBIAN" / "control", control)
    write_file(
        deb_root / "DEBIAN" / "postinst",
        """#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t /usr/share/icons/hicolor || true
fi
exit 0
""",
        executable=True,
    )

    archive.unlink(missing_ok=True)
    subprocess.run(
        ["dpkg-deb", "--build", "--root-owner-group", str(deb_root), str(archive)],
        check=True,
    )


def build_rpm(stage: Path, root: Path, version: str, archive: Path) -> None:
    topdir = root / "rpmbuild"
    for name in ("BUILD", "BUILDROOT", "RPMS", "SOURCES", "SPECS", "SRPMS"):
        (topdir / name).mkdir(parents=True, exist_ok=True)

    requires = "\n".join(f"Requires: {name}" for name in RPM_DEPENDS)
    spec = f"""Name: vcolor
Version: {version}
Release: 1
Summary: A fast, focused desktop color project manager
License: MIT
URL: {HOMEPAGE}
BuildArch: {rpm_arch()}
AutoReqProv: no
{requires}

%description
vColor is a desktop color project manager built with Qt.

%install
rm -rf %{{buildroot}}
mkdir -p %{{buildroot}}
cp -a {stage.as_posix()}/. %{{buildroot}}/

%files
/opt/vcolor
/usr/bin/vColor
/usr/bin/vcolor
/usr/share/applications/vcolor.desktop
/usr/share/icons/hicolor/512x512/apps/vColor.png
/usr/share/icons/hicolor/scalable/apps/vColor.svg
/usr/share/doc/vcolor/copyright

%changelog
"""
    spec_path = topdir / "SPECS" / "vcolor.spec"
    spec_path.write_text(spec, encoding="utf-8", newline="\n")
    subprocess.run(
        [
            "rpmbuild",
            "-bb",
            "--define",
            f"_topdir {topdir.as_posix()}",
            str(spec_path),
        ],
        check=True,
    )

    built = next((topdir / "RPMS").rglob("*.rpm"))
    archive.unlink(missing_ok=True)
    shutil.copy2(built, archive)


def build_appimage(source: Path, archive: Path) -> bool:
    tool = find_appimagetool()
    if tool is None:
        print("Skipping .AppImage: appimagetool was not found")
        return False

    with tempfile.TemporaryDirectory() as temporary:
        appdir = Path(temporary) / "vColor.AppDir"
        bundle = appdir / "usr" / "lib" / "vcolor"
        shutil.copytree(source, bundle)

        bin_dir = appdir / "usr" / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "vColor").symlink_to("../lib/vcolor/vColor")
        (bin_dir / "vcolor").symlink_to("vColor")

        desktop = ROOT / "packaging" / "linux" / "vcolor.desktop"
        applications = appdir / "usr" / "share" / "applications"
        applications.mkdir(parents=True)
        shutil.copy2(desktop, applications / "vColor.desktop")
        shutil.copy2(desktop, appdir / "vColor.desktop")

        resources = ROOT / "vcolor" / "resources"
        shutil.copy2(resources / "icon.png", appdir / "vColor.png")
        png_dir = appdir / "usr" / "share" / "icons" / "hicolor" / "512x512" / "apps"
        png_dir.mkdir(parents=True)
        shutil.copy2(resources / "icon.png", png_dir / "vColor.png")
        svg_dir = appdir / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps"
        svg_dir.mkdir(parents=True)
        shutil.copy2(resources / "icon.svg", svg_dir / "vColor.svg")

        write_file(
            appdir / "AppRun",
            """#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/lib/vcolor/vColor" "$@"
""",
            executable=True,
        )

        archive.unlink(missing_ok=True)
        subprocess.run(
            [tool, "--no-appstream", str(appdir), str(archive)],
            check=True,
            env={
                **os.environ,
                "ARCH": appimage_arch(),
                # Lets appimagetool run on runners without FUSE (Ubuntu 24.04).
                "APPIMAGE_EXTRACT_AND_RUN": "1",
            },
        )
    return archive.is_file()


def build_windows_installer(version: str, archive: Path) -> bool:
    compiler = find_iscc()
    if compiler is None:
        print("Skipping Windows installer: Inno Setup (ISCC.exe) was not found")
        return False

    subprocess.run(
        [
            compiler,
            f"/DMyAppVersion={version}",
            f"/DMyArch={inno_arch()}",
            f"/DSourceDir={DIST / 'vColor'}",
            f"/DOutputDir={DIST}",
            f"/DOutputBaseFilename={archive.stem}",
            str(ROOT / "packaging" / "windows" / "vcolor.iss"),
        ],
        check=True,
    )
    return archive.is_file()


def package_macos(source: Path, version: str) -> list[Path]:
    base = f"vColor-{version}-{platform_tag()}"
    archives: list[Path] = []

    archive = DIST / f"{base}-portable.zip"
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
    archives.append(archive)

    dmg = DIST / f"{base}.dmg"
    with tempfile.TemporaryDirectory() as temporary:
        stage = Path(temporary) / "vColor"
        stage.mkdir()
        subprocess.run(["ditto", str(source), str(stage / "vColor.app")], check=True)
        (stage / "Applications").symlink_to("/Applications")
        dmg.unlink(missing_ok=True)
        subprocess.run(
            [
                "hdiutil",
                "create",
                "-volname",
                "vColor",
                "-srcfolder",
                str(stage),
                "-ov",
                "-format",
                "UDZO",
                str(dmg),
            ],
            check=True,
        )
    archives.append(dmg)
    return archives


def package_windows(source: Path, version: str) -> list[Path]:
    base = f"vColor-{version}-{platform_tag()}"
    archives: list[Path] = []

    archive = DIST / f"{base}-portable.zip"
    archive.unlink(missing_ok=True)
    shutil.make_archive(
        str(DIST / f"{base}-portable"), "zip", root_dir=DIST, base_dir="vColor"
    )
    archives.append(archive)

    setup = DIST / f"{base}-setup.exe"
    if build_windows_installer(version, setup):
        archives.append(setup)
    return archives


def package_linux(source: Path, version: str) -> list[Path]:
    base = f"vColor-{version}-{platform_tag()}"
    archives: list[Path] = []

    archive = DIST / f"{base}-portable.tar.gz"
    archive.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        staging = Path(temporary)
        shutil.copytree(source, staging / "vColor")
        desktop = ROOT / "packaging" / "linux" / "vcolor.desktop"
        if desktop.is_file():
            shutil.copy2(desktop, staging / "vcolor.desktop")
        shutil.make_archive(str(DIST / f"{base}-portable"), "gztar", root_dir=staging)
    archives.append(archive)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        stage = root / "stage"
        linux_install_tree(stage, source)

        if shutil.which("dpkg-deb"):
            deb = DIST / f"{base}.deb"
            build_deb(stage, root / "deb", version, deb)
            archives.append(deb)
        else:
            print("Skipping .deb: dpkg-deb was not found")

        if shutil.which("rpmbuild"):
            rpm = DIST / f"{base}.rpm"
            build_rpm(stage, root / "rpm", version, rpm)
            archives.append(rpm)
        else:
            print("Skipping .rpm: rpmbuild was not found (install the rpm package)")

    appimage = DIST / f"{base}.AppImage"
    if build_appimage(source, appimage):
        archives.append(appimage)

    return archives


def main() -> int:
    version = project_version()

    if sys.platform == "darwin":
        source = DIST / "vColor.app"
        if not source.is_dir():
            raise SystemExit(f"Missing bundle: {source}. Run scripts/build.py first.")
        archives = package_macos(source, version)
    elif sys.platform == "win32":
        source = DIST / "vColor"
        if not source.is_dir():
            raise SystemExit(f"Missing bundle: {source}. Run scripts/build.py first.")
        archives = package_windows(source, version)
    else:
        source = DIST / "vColor"
        if not source.is_dir():
            raise SystemExit(f"Missing bundle: {source}. Run scripts/build.py first.")
        archives = package_linux(source, version)

    for archive in archives:
        print(f"Packaged {archive} ({archive.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
