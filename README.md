# vColor

A fast, native desktop color palette manager for Linux, macOS, and Windows.
Built with Python and Qt/PySide6 — no Electron, no bundled browser, no splash
screen.

![vColor screenshot](docs/screenshot.png)

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

## Features

- Multiple projects with rename, delete, and undo.
- Add, edit, copy, and delete colors.
- Live color picker plus HEX, RGB, HSL, OKLCH, and Display P3 conversions.
- WCAG contrast checks against white and black.
- Format selector updates the values shown and copied in the list, and remembers
  your choice between sessions.
- Automatic saving with atomic JSON writes — no Save button needed.
- Import colors from JSON, CSS, or GIMP `.gpl` palettes.
- Export palettes as JSON, CSS custom properties, or GIMP `.gpl`.
- First-run sample palette so the app is immediately explorable.
- Bundled Inter font and custom-painted icons — no icon theme dependency.
- Keyboard shortcuts and project context menus.
- Native file dialogs and native color picker on each platform.

## Run from source

Requires Python 3.10+.

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

## Keyboard shortcuts

| Action | Shortcut |
| --- | --- |
| New color | `Ctrl/Cmd+N` |
| New project | `Ctrl/Cmd+Shift+N` |
| Export active palette | `Ctrl/Cmd+E` |
| Import colors into active palette | `Ctrl/Cmd+I` |

Double-click a project to rename it. Right-click a project for export/import.
Click a color row to edit it; the Copy button copies the current display format.

## Where data lives

| Platform | Path |
| --- | --- |
| Linux | `$XDG_DATA_HOME/vColor/palettes.json` (usually `~/.local/share/vColor/`) |
| macOS | `~/Library/Application Support/vColor/palettes.json` |
| Windows | `%APPDATA%\vColor\palettes.json` |

Pass `--data-dir /some/path` to use a different location.

Saves are atomic: data is written to a temporary file, flushed to disk, and
then moved into place. If the JSON file is corrupt, vColor moves it aside as
`palettes.corrupt-<timestamp>.json` and starts from the sample palette.

## Tests

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -v
```

The suite covers color conversion, contrast, persistence, corrupt-file recovery,
palette import/export, and a headless UI smoke test.

## Build a desktop bundle

```bash
python3 scripts/build.py
```

Outputs:

- Linux/Windows: `dist/vColor/`
- macOS: `dist/vColor.app/`

The PyInstaller spec is in `packaging/vcolor.spec`. A GitHub Actions workflow
(`.github/workflows/build.yml`) runs the tests and builds zipped bundles on all
three platforms.

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

## License

MIT. The bundled Inter font is licensed under the SIL Open Font License; see
`vcolor/resources/fonts/OFL.txt`.
