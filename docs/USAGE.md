# Using vColor

## Features

- Multiple projects with rename, delete, and undo.
- Add, edit, copy, and delete colors.
- Enter colors as hex, `rgb()`, `hsl()`, `oklch()`, or CSS names like `tomato` —
  vColor normalizes them to hex automatically. Names are optional; unnamed colors
  are saved as “Untitled color”.
- Live color picker plus HEX, RGB, HSL, OKLCH, and Display P3 conversions.
- WCAG contrast checks against white and black.
- Format selector updates the values shown and copied in the list, and remembers
  your choice between sessions.
- Automatic saving with atomic JSON writes — no Save button needed.
- Import colors from JSON, CSS, or GIMP `.gpl` palettes.
- Export palettes as portable JSON, CSS custom properties, or GIMP `.gpl`.
- Portable JSON palette files with a headless CLI for validating, converting,
  exporting, and importing palettes.
- No built-in theme catalog: fetch a theme's official colors and import them as
  a project.
- Starts with an empty workspace so you can create your own projects.
- Bundled Inter font and custom-painted icons — no icon theme dependency.
- Keyboard shortcuts and project context menus.
- Native file dialogs and native color picker on each platform.
- Automatic update checks against GitHub Releases, with a download banner when
  a newer version exists.

## Installing

| Platform | Recommended download |
| --- | --- |
| Windows x64 | `vColor-<version>-windows-x64-setup.exe` — per-user install, no admin prompt |
| Windows arm64 | `vColor-<version>-windows-arm64-setup.exe` |
| macOS | `vColor-<version>-macos-arm64.dmg` — drag `vColor.app` to Applications |
| Linux | `vColor-<version>-linux-x86_64.AppImage` or `-linux-arm64.AppImage` — no install needed |
| Linux (system package) | `vColor-<version>-linux-<arch>.deb` or `.rpm` |
| Any | `-portable.zip` / `-portable.tar.gz` — extract and run |

Windows installers are unsigned, so SmartScreen may show a warning; choose
**More info → Run anyway**. macOS builds are also unsigned: right-click the app
and choose **Open** the first time.

## Update checks

On launch, vColor asks the public GitHub API for the latest release at most once
every 24 hours. If the release is newer, a banner appears above the color list
with a **Download** button that opens the release page in your browser. Dismiss
the banner to hide that version until the next one is published.

Click the `vColor <version>` label at the bottom of the sidebar to check
manually. It shows a short confirmation toast.

vColor never downloads or installs updates by itself; it only opens the release
page. To opt out, set `"update_check": false` in `palettes.json`, or start the
app with `--no-update-check`.

## Keyboard shortcuts

| Action | Shortcut |
| --- | --- |
| New color | `Ctrl/Cmd+N` |
| New project | `Ctrl/Cmd+Shift+N` |
| Export active palette | `Ctrl/Cmd+E` |
| Import colors into active palette | `Ctrl/Cmd+I` |

Double-click a project to rename it. Right-click a project for export/import.
Click a color tile to copy its value in the current display format; use the
pencil button on the tile to edit it, or the trash button to delete it.

## Portable palettes and the CLI

Palettes can live outside the app as standalone JSON files such as
`catppuccin-mocha.json`. The same format is used by **Export → JSON** in the
GUI. vColor does not bundle a theme catalog; get the official colors from the
upstream project and write the JSON file first.

```bash
# From a source checkout
uv run python -m vcolor palette show catppuccin-mocha.json
uv run python -m vcolor palette install catppuccin-mocha.json
uv run python -m vcolor palette export catppuccin-mocha.json catppuccin-mocha.css

# Installed package
vcolor-cli install catppuccin-mocha.json
```

See [Portable palettes](PALETTES.md) for the format, the JSON Schema, and every
command.

## Where data lives

| Platform | Path |
| --- | --- |
| Linux | `$XDG_DATA_HOME/vColor/palettes.json` (usually `~/.local/share/vColor/`) |
| macOS | `~/Library/Application Support/vColor/palettes.json` |
| Windows | `%APPDATA%\vColor\palettes.json` |

Pass `--data-dir /some/path` to use a different location.

Saves are atomic: data is written to a temporary file, flushed to disk, and
then moved into place. If the JSON file is corrupt, vColor moves it aside as
`palettes.corrupt-<timestamp>.json` and starts with an empty workspace.
