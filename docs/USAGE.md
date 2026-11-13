# Using vColor

## Features

- Multiple projects with rename, delete, and undo.
- Drag projects in the sidebar to reorder them. Star a project to mark it as a
  favorite and move it to the top; you can still drag it elsewhere afterward.
  Order and favorites are saved automatically.
- Add, edit, copy, and delete colors.
- Enter colors as hex, `rgb()`, `hsl()`, `hsb()`/`hsv()`, `cmyk()`, `lab()`,
  `oklch()`, or CSS names like `tomato` — vColor normalizes them to hex
  automatically. Names are optional; unnamed colors are saved as “Untitled
  color”.
- Live color picker plus HEX, RGB, HSL, OKLCH, and Display P3 conversions.
- WCAG contrast checks against white and black.
- Format selector updates the values shown and copied in the list, and remembers
  your choice between sessions.
- Optional HEX display and copy without the leading `#`.
- Accent color that follows your operating system by default, with a custom
  color picker in Settings.
- Automatic saving with atomic JSON writes — no Save button needed.
- Import a project from JSON, CSS/SCSS, Tailwind, XML, SVG, ASE, GPL, CSV, TXT,
  or a Coolors link with **Import project**.
- Import colors from any supported palette file into an existing project.
- Export projects as JSON, CSS/SCSS variables, Tailwind config, XML, SVG, ASE,
  GPL, CSV, a hex list, or a Coolors link.
- Drag one or more palette files onto the window to add them as projects.
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
color format, whether HEX values show a leading `#`, keyboard shortcuts,
automatic update checks, or to check for updates now. Click the back arrow to
return to your projects.

Under **Keyboard**, select **Keyboard shortcuts** to view and change every
shortcut. Select a row, press the new key combination, and choose **Set**.
**Reset to Default** restores the built-in combination. Press **Backspace** in
the dialog to disable a shortcut, or **Esc** to cancel. Changes are saved
automatically.

Under **Appearance**, vColor follows your operating system's accent color by
default. Turn off **Follow system accent color**, or click the color swatch, to
pick a custom accent. If the system color cannot be detected, vColor uses
`#477eeb`.

Under **About**, **Open GitHub** opens
[the vColor source code](https://github.com/hingjasontech/vColor).

## Keyboard shortcuts

| Action | Default shortcut |
| --- | --- |
| New color | `Ctrl/Cmd+N` |
| New project | `Ctrl/Cmd+Shift+N` |
| Import palette file | `Ctrl/Cmd+O` |
| Export active project | `Ctrl/Cmd+E` |
| Import colors into active project | `Ctrl/Cmd+I` |
| Open settings | `Ctrl/Cmd+,` |

These are defaults; you can change or disable any shortcut under **Settings →
Keyboard → Keyboard shortcuts**.

Double-click a project to rename it. Drag a project up or down in the sidebar
to reorder it, and click the star on the right of a project row to favorite it.
Favoriting moves the project to the top; drag it elsewhere afterward if you
prefer. Right-click a project to duplicate it, export it, import colors into it,
or toggle its favorite state.
Click a color row to copy its value in the current display format; use the
copy, pencil, or trash buttons on the row to copy, edit, or delete it. You can
also right-click a color for **Edit**, **Copy**, and **Delete**.

## Projects from an AI assistant

Ask your AI assistant for a theme, for example “generate a Catppuccin Mocha
theme using vColor.” The assistant should use the instructions in this
repository's [AGENTS.md](../AGENTS.md) and write a palette file in a supported
format.

Then import it with **Import project** at the bottom of the sidebar, or drag the
file onto the vColor window. The project name comes from the file name. Duplicate
names are added as numbered copies, and a toast offers **Undo** after an import.

See [Palette projects](PROJECTS.md) for the formats and import rules.

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
