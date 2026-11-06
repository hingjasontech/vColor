# Using vColor

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
- Starts with an empty workspace so you can create your own projects.
- Bundled Inter font and custom-painted icons — no icon theme dependency.
- Keyboard shortcuts and project context menus.
- Native file dialogs and native color picker on each platform.

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
