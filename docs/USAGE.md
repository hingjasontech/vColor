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
- Optional HEX display and copy without the leading `#`.
- Accent color that follows your operating system by default, with a custom
  color picker in Settings.
- Automatic saving with atomic JSON writes — no Save button needed.
- Import a project from a portable `.json` file with **Import project**.
- Import colors from JSON, CSS, or GIMP `.gpl` files into an existing project.
- Export projects as portable JSON, CSS custom properties, or GIMP `.gpl` files.
- Drag one or more `.json` project files onto the window to add them as projects.
- No built-in theme catalog: ask your AI assistant for a theme, or supply the
  official colors yourself.
- Starts with an empty workspace so you can create your own projects.
- Bundled Inter font and custom-painted icons — no icon theme dependency.
- Keyboard shortcuts and project context menus.
- Native file dialogs and native color picker on each platform.
- Automatic update checks against GitHub Releases, with a download banner when
  a newer version exists.
- A Settings page for accent color, color format, HEX prefix, updates, and the
  project's GitHub source.

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

Open **Settings** and click **Check now** to check manually. It shows a short
confirmation toast.

vColor never downloads or installs updates by itself; it only opens the release
page. To opt out, set `"update_check": false` in `palettes.json`.

## Settings

Click **Settings** at the bottom of the sidebar to change the accent color, the
color format, whether HEX values show a leading `#`, automatic update checks, or
to check for updates now. Click the back arrow to return to your projects.

Under **Appearance**, vColor follows your operating system's accent color by
default. Turn off **Follow system accent color**, or click the color swatch, to
pick a custom accent. If the system color cannot be detected, vColor uses
`#477eeb`.

Under **About**, **Open GitHub** opens
[the vColor source code](https://github.com/hingjasontech/vColor).

## Keyboard shortcuts

| Action | Shortcut |
| --- | --- |
| New color | `Ctrl/Cmd+N` |
| New project | `Ctrl/Cmd+Shift+N` |
| Import project file | `Ctrl/Cmd+O` |
| Export active project | `Ctrl/Cmd+E` |
| Import colors into active project | `Ctrl/Cmd+I` |

Double-click a project to rename it. Right-click a project to duplicate it,
export it, or import colors into it.
Click a color row to copy its value in the current display format; use the
copy, pencil, or trash buttons on the row to copy, edit, or delete it. You can
also right-click a color for **Edit**, **Copy**, and **Delete**.

## Projects from an AI assistant

Ask your AI assistant for a theme, for example “generate a Catppuccin Mocha
theme using vColor.” The assistant should use the instructions in this
repository's [AGENTS.md](../AGENTS.md) and write a portable `.json` project
file.

Then import it with **Import project** at the bottom of the sidebar, or drag the
file onto the vColor window. The project appears immediately. Duplicate names
are added as numbered copies, and a toast offers **Undo** after an import.

See [Portable projects](PROJECTS.md) for the file format and import rules.

## Where data lives

| Platform | Path |
| --- | --- |
| Linux | `$XDG_DATA_HOME/vColor/` (usually `~/.local/share/vColor/`) |
| macOS | `~/Library/Application Support/vColor/` |
| Windows | `%APPDATA%\vColor\` |

`palettes.json` stores your projects (the filename is kept for compatibility
with earlier versions). Project files themselves stay wherever you saved them;
vColor only reads them when you import or drag them in.

Saves are atomic: data is written to a temporary file, flushed to disk, and
then moved into place. If the JSON file is corrupt, vColor moves it aside as
`palettes.corrupt-<timestamp>.json` and starts with an empty workspace.
