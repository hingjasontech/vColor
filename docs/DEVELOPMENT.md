# Developing vColor

## Why it starts fast

vColor uses Qt Widgets directly instead of a browser runtime. The window is
shown first, then the palette data is loaded on the first event-loop tick.
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
palette import/export, and a headless UI smoke test.

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

For Linux desktop integration, copy the bundled folder somewhere stable and
install `packaging/linux/vcolor.desktop` as `vcolor.desktop` in your applications
directory, pointing `Exec=` at the `vColor` executable.

## Project layout

```text
vcolor/
  app.py            application bootstrap, CLI, theme setup
  main_window.py    window, projects, rows, persistence wiring
  widgets.py        custom-painted buttons, rows, toast, empty state
  dialogs.py        project/color/confirm dialogs
  color_utils.py    conversions, contrast, formatting
  models.py         data model and atomic JSON store
  palette_io.py     JSON/CSS/GPL import and export
  resources/        Inter font and app icons
packaging/          PyInstaller spec and Linux desktop entry
scripts/            icon generation and build helper
tests/              unit and headless UI tests
```
