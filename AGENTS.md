# AGENTS.md

vColor is a PySide6/Qt Widgets desktop color project manager for Linux, macOS,
and Windows. It deliberately ships **no theme catalog**. This file covers both
work on the app and generating portable theme projects for users.

## Commands

```powershell
uv sync                    # creates .venv and installs locked deps + dev group
uv run python run.py       # run from source
uv run python -m vcolor    # equivalent entry point
```

- After changing dependencies in `pyproject.toml`, run `uv lock` and `uv sync`.
  Keep `requirements.txt` / `requirements-dev.txt` in sync for the pip fallback.
- Tests (PowerShell):
  ```powershell
  $env:QT_QPA_PLATFORM='offscreen'; uv run python scripts/run_tests.py
  ```
  On macOS/Linux: `QT_QPA_PLATFORM=offscreen uv run python scripts/run_tests.py`.
  Use `scripts/run_tests.py`, not raw `python -m unittest`: it force-exits
  before Qt's platform-plugin teardown, which can crash after a passing run.
- Single test:
  ```powershell
  $env:QT_QPA_PLATFORM='offscreen'; uv run python -m unittest tests.test_models.ModelTests.test_serialization_round_trip -v
  ```
  The suite is stdlib `unittest`, not pytest. It includes headless Qt UI tests,
  so prefer a single test or module while iterating. Ruff is configured in
  `pyproject.toml` (line length 100) but is not a project dependency; CI runs
  tests then builds, so do not invent lint/typecheck steps.
- After any UI change, regenerate the README image:
  `uv run python scripts/screenshot.py` (writes `docs/screenshot.png` offscreen).
- Build and package:
  ```powershell
  uv run python scripts/build.py      # runs tests unless --skip-tests
  uv run python scripts/package.py    # release archives for this platform
  ```
  PyInstaller cannot cross-compile; build each platform on its target OS.
  See `docs/DEVELOPMENT.md` for installers, CI, and release details.
- Do not push, tag, or publish releases unless the user asks.

## Architecture

- Entry point is `vcolor/app.py:main`; `run.py` adds a local `.deps` fallback,
  and `python -m vcolor` calls the same `main`. `app.py` sets Fusion style, the
  dark palette, bundled Inter font, then constructs `MainWindow` and loads data
  on the first event-loop tick (`MainWindow.bootstrap`).
- `vcolor/models.py` holds `AppData`, `Project`, `ColorEntry`, and
  `PaletteStore`. The store writes `palettes.json` atomically and moves corrupt
  files aside. Never hand-edit the application data directory.
- `vcolor/main_window.py` owns the window, project list/rendering, autosave,
  shortcuts, drag-and-drop, import/export, and update banner. Persistence is
  gated by `MainWindow._loaded`; UI tests set it before calling `set_data`.
- Project import flow: `import_project_files` -> `project_files.read_project_file`
  (2 MB cap) -> `palette_format.load_palette` -> `PortablePalette.to_project`.
  Imports append and select the last new project; duplicate names become
  `Name (2)`, `Name (3)`, etc. Invalid files are skipped with a toast. Undo
  removes the imported projects.
- `vcolor/palette_format.py` defines the portable `vcolor.palette` format and
  `PALETTE_SCHEMA`. `vcolor/palette_io.py` handles CSS/GPL/JSON color import and
  export. `vcolor/project_files.py` handles project-file import and copy naming.
- UI is custom-painted Qt widgets (`widgets.py`, `dialogs.py`,
  `settings_page.py`, `shortcuts_page.py`) with runtime tokens and accent colors
  in `theme.py`; `system_accent.py` detects the OS accent.
- The version is duplicated. A release bump must update `vcolor/__init__.py`,
  `pyproject.toml`, `uv.lock` (run `uv lock`), and the macOS
  `CFBundleShortVersionString` / `CFBundleVersion` values in
  `packaging/vcolor.spec`. CI reads `__init__.py` and runs `uv sync --locked`.
  The release workflow runs on `v*` tags and on `main` pushes touching
  `__init__.py` or `pyproject.toml`.

## Portable projects

A vColor project is one standalone `.json` file. Users import it explicitly with
**Import project** in the sidebar, by dragging files onto the window, or with a
project's **Import colors** action. The app does not watch folders. Every valid
file becomes a new project; existing projects are never overwritten. Invalid
files are rejected with a notification.

Write the file somewhere the user can reach (the workspace, downloads, or a path
they choose). Never write into the vColor application data directory, and never
create `AGENTS.md`, schema files, or inbox folders there.

Canonical format:

```json
{
  "format": "vcolor.palette",
  "version": 1,
  "id": "my-theme",
  "name": "My Theme",
  "description": "One-line summary.",
  "source": "https://example.com/my-theme",
  "license": "MIT",
  "tags": ["dark"],
  "colors": [
    { "name": "background", "hex": "#101014" },
    { "name": "foreground", "hex": "#f2f2f7" }
  ]
}
```

- `name` and at least one valid color are required; everything else is optional.
- Always write `"format": "vcolor.palette"`; reading also accepts files without it.
- `id` defaults to a slug of `name`. Keep it stable and file/URL friendly.
- Write `colors` as an array of `{"name", "hex"}` objects. The reader also accepts
  a name-to-hex object or an array of hex strings, but exports use the array form.
- Hex values are normalized to lowercase `#rrggbb`; invalid colors are skipped.
- Record the upstream `source` URL and `license` when they exist.
- `source`, `license`, `description`, and `tags` live only in the project file.
  `palettes.json` stores project names, colors, and app settings, not this metadata.
  Exporting from the GUI therefore omits those fields.

## Generating themes

1. **Fetch official colors** from the upstream project, repository, or docs.
   Do not invent or approximate hex values. Preserve the project's color names
   and intended order, and note the license and source URL.
2. **Write a portable file** in the format above and tell the user which file to
   import.
3. **Ask the user to import it** with **Import project** or by dragging it onto
   the window.
4. **Verify** that the file is valid JSON with a name and at least one `#rrggbb`
   color.

Theme notes:

- **Material 3** is seed-based. If the user supplies a seed color, use the
  official Material color utilities or generator to produce the tonal roles;
  otherwise use the published baseline scheme.
- **libadwaita** uses the named GNOME palette (Blue, Green, Yellow, Orange, Red,
  Purple, Brown, Light, and Dark steps).
- **Catppuccin** publishes all four flavors in its official palette repository.
- **Editor themes** such as Tokyo Night, Nord, and Dracula should come from the
  project's own color definitions, not third-party approximations.
- If the upstream source cannot be found, say which values are missing rather
  than guessing.

## Repository rules

- Do not add theme projects to the repository unless the user explicitly asks.
  Theme projects are user data, not source code.
- Do not hand-edit `palettes.json`; use the GUI.
- Keep `source` and `license` metadata accurate when converting a theme.
