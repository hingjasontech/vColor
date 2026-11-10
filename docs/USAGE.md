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
- Watched palette inbox: palettes from an AI assistant appear automatically.
- Drag a `.json` palette file onto the window to add it as a project.
- No built-in theme catalog: ask your AI assistant for a theme, or supply the
  official colors yourself.
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
page. To opt out, set `"update_check": false` in `palettes.json`.

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

## Palettes from an AI assistant

Ask your AI assistant for a vColor palette, for example “generate a Catppuccin
Mocha theme using vColor.” The assistant writes a portable `.json` palette into
vColor's palette inbox, and the project appears in the app automatically — even
if vColor is already open. If it was closed, the project is added the next time
you launch it.

You can also drag one or more `.json` palette files onto the vColor window, or
use **Export → JSON** to save a project in the same portable format.

Click **Palette inbox** at the bottom of the sidebar to open the folder where
palettes arrive. Duplicate names are added as numbered copies, and a toast
offers **Undo** after an import.

See [Portable palettes](PALETTES.md) for the file format and import rules.

## Where data lives

| Platform | Path |
| --- | --- |
| Linux | `$XDG_DATA_HOME/vColor/` (usually `~/.local/share/vColor/`) |
| macOS | `~/Library/Application Support/vColor/` |
| Windows | `%APPDATA%\vColor\` |

`palettes.json` stores your projects. `inbox/` is the watched palette inbox,
with `imported/` and `failed/` subfolders for archived files.

Saves are atomic: data is written to a temporary file, flushed to disk, and
then moved into place. If the JSON file is corrupt, vColor moves it aside as
`palettes.corrupt-<timestamp>.json` and starts with an empty workspace.
