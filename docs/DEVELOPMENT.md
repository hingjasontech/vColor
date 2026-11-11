# Developing vColor

## Why it starts fast

vColor uses Qt Widgets directly instead of a browser runtime. The window is
shown first, then the project data is loaded on the first event-loop tick.
Dialogs and import/export code are imported only when used.

Measured on the development machine (Linux, Wayland, Python 3.14, PySide6 6.12):

| Build | Time to first event-loop tick |
| --- | ---: |
| Source checkout | ~200 ms |
| PyInstaller onedir bundle | ~240 ms |

These numbers come from `python -m vcolor --benchmark-startup` (which includes
a 60 ms settle period) on Linux/Wayland. The bundled app is a **onedir** build
rather than a one-file executable, so startup does not pay the cost of unpacking
an archive.

## Run from source

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python run.py
```

`uv sync` creates `.venv`, installs the locked dependencies from `uv.lock`, and
installs vColor in editable mode. The `dev` dependency group (including
PyInstaller) is installed by default. Commit `uv.lock` so builds use the same
dependency versions everywhere.

To add or upgrade a dependency, edit `pyproject.toml`, then run:

```bash
uv lock
uv sync
```

### pip fallback

The `requirements*.txt` files remain for environments without uv. Keep them in
sync when dependencies change.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python run.py
```

If your Python installation cannot create virtual environments, install into a
local folder and use the launcher:

```bash
python3 -m pip install --target .deps -r requirements.txt
./run.py
```

`run.py` automatically adds a local `.deps` folder to `sys.path` when present.

## Tests

```bash
QT_QPA_PLATFORM=offscreen uv run python -m unittest discover -s tests -v
```

On Windows PowerShell:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
uv run python -m unittest discover -s tests -v
```

The suite covers color conversion, contrast, persistence, corrupt-file recovery,
project file import/export, system accent detection, update version comparison,
and a headless UI smoke test.

## README screenshot

`docs/screenshot.png` is embedded in `README.md`. Regenerate it after any UI
change so the README stays in sync:

```bash
uv run python scripts/screenshot.py
```

The script renders the current interface with Qt's offscreen platform.

## Build a desktop bundle

```bash
uv run python scripts/build.py
```

`scripts/build.py` runs the test suite first unless `--skip-tests` is passed.

Outputs:

- Linux/Windows: `dist/vColor/`
- macOS: `dist/vColor.app/`

The PyInstaller spec is in `packaging/vcolor.spec`. Builds are platform-specific,
so each bundle must be produced on its target operating system (or in CI).
PyInstaller cannot cross-compile, which means a Windows machine cannot produce
Linux or macOS bundles.

To create release archives for the current platform:

```bash
uv run python scripts/package.py
```

It always writes the portable
`dist/vColor-<version>-<platform>-portable.(zip|tar.gz)` archive. Installer
formats share the same `vColor-<version>-<platform>` base name:

- Linux: `.deb` and `.rpm` when `dpkg-deb` and `rpmbuild` are installed, and
  `.AppImage` when `appimagetool` is on `PATH` (or `APPIMAGETOOL` points at it).
- Windows: `-setup.exe` when Inno Setup (`ISCC.exe`) is installed.
- macOS: `.dmg` plus the portable `.zip`.

The package layout is:

| Format | Installs |
| --- | --- |
| `.deb` / `.rpm` | `/opt/vcolor`, a `vColor` command in `/usr/bin`, desktop entry, and icon |
| `.AppImage` | Single self-contained executable; no install step |
| `-setup.exe` | Per-user install with Start Menu shortcut and uninstaller |
| `.dmg` | `vColor.app` plus an `Applications` shortcut for drag-to-install |
| `-portable.zip` / `-portable.tar.gz` | Portable bundle; extract anywhere and run |

The `-portable` suffix means the archive needs no installer. The `.deb` and
`.rpm` filenames use the shared `vColor-...` release name, but their internal
package name stays lowercase (`vcolor`) because Debian and RPM policies require
it.

### Build all targets with CI

`.github/workflows/build.yml` builds and uploads bundles for Windows x64,
Windows arm64, Linux x86_64, Linux arm64, and macOS arm64 on every push to
`main`, every pull request, and on demand. Pushing the repository to GitHub and
opening the **Actions** tab is enough; the archives are attached to the workflow
run. The arm64 jobs use the public-repository-only `windows-11-arm` and
`ubuntu-24.04-arm` runners.

Windows arm64 builds need an arm64 Python and arm64 PySide6/PyInstaller wheels;
the `windows-11-arm` runner provides both, and the installer is compiled with
Inno's `arm64` architecture mode. Run the manual Windows steps below from an
arm64 Python to produce `vColor-<version>-windows-arm64-*`.

The equivalent manual builds are:

```bash
# Windows (produces the portable zip and, with Inno Setup, -setup.exe)
choco install innosetup   # or install Inno Setup 6 manually
uv sync
uv run python scripts/build.py
uv run python scripts/package.py

# Linux (install Qt runtime libraries, rpmbuild, and appimagetool first)
sudo apt-get install -y libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 rpm
curl -fsSL https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage \
  -o ~/.local/bin/appimagetool && chmod +x ~/.local/bin/appimagetool
uv sync
uv run python scripts/build.py
uv run python scripts/package.py

# macOS (produces dist/vColor.app, -portable.zip, and .dmg)
uv sync
uv run python scripts/build.py
uv run python scripts/package.py
```

Install the Linux packages with `sudo apt install ./vColor-*.deb` or
`sudo dnf install ./vColor-*.rpm`, or run `chmod +x vColor-*.AppImage` and
execute the AppImage directly. The RPM metadata targets Fedora/RHEL package
names; on other RPM distributions you may need to adapt the `Requires:` lines in
`scripts/package.py`.

macOS builds are unsigned. For local use, right-click the app and choose **Open**
the first time, or remove the quarantine flag:

```bash
xattr -dr com.apple.quarantine dist/vColor.app
```

Distribution to other Macs requires a Developer ID certificate, code signing,
and notarization on a macOS machine.

### Publishing a release

A push to `main` publishes a release when the version in `vcolor/__init__.py`
does not have a release yet. Bump the version in `vcolor/__init__.py` and
`pyproject.toml`, then commit and push:

```bash
git commit -am "chore(release): bump version to 1.3.1"
git push origin main
```

The workflow only runs for `main` pushes that touch `vcolor/__init__.py` or
`pyproject.toml`, so README or source-only changes do not start a build. A
lightweight check job then reads the version, creates the matching `v` tag if
needed, downloads the CI artifacts, writes `SHA256SUMS.txt`, and publishes
everything with generated release notes. If a release for the current version
already exists, the check job stops before the build matrix starts.

Pushing a tag that starts with `v` also builds every target and publishes the
release, which is useful for manual or historical releases:

```bash
git tag v1.0.0
git push origin main v1.0.0
```

For a manual release, download the artifacts from the workflow run and attach
the inner archives (not the artifact zips) in
**Releases → Draft a new release**.

Artifacts from a workflow run are at the bottom of the run summary under
**Artifacts**. GitHub wraps each artifact in a zip, so extract twice.

## App icon

The icon source is `vcolor/resources/icon.svg`. After editing it, regenerate the
PNG, ICO, and ICNS files:

```bash
uv run python scripts/make_icon.py
```

Rebuild the desktop bundle afterward so the new icon is embedded in the EXE.

## Project layout

```text
vcolor/
  app.py            application bootstrap, command-line flags, theme setup
  main_window.py    window, projects, rows, import/export, persistence wiring
  settings_page.py  libadwaita-style preferences page
  shortcuts.py      shortcut definitions, validation, and override resolution
  shortcuts_page.py keyboard shortcuts page and Set Shortcut dialog
  system_accent.py  Windows/macOS/Linux accent-color detection with a fallback
  theme.py          dark theme tokens and the runtime accent stylesheet
  project_files.py  project-file import helpers and copy naming
  widgets.py        custom-painted buttons, rows, toast, empty state
  dialogs.py        project/color/confirm dialogs
  color_utils.py    conversions, contrast, formatting
  models.py         data model and atomic JSON store
  palette_format.py portable project load/save and JSON Schema
  palette_io.py     JSON/CSS/GPL color import and export
  updater.py        GitHub release lookup and version comparison
  resources/        Inter font and app icons
packaging/          PyInstaller spec, Inno Setup script, Linux desktop entry
scripts/            icon generation, screenshot, and build helpers
tests/              unit and headless UI tests
```
