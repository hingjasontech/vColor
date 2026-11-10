# AGENTS.md

vColor is a desktop palette manager for Linux, macOS, and Windows. It
deliberately does **not** ship a theme catalog: when a user asks for Catppuccin
Mocha, Material 3, libadwaita, Tokyo Night, or any other theme, fetch the
current official colors from the upstream project and deliver them as a
portable vColor palette.

## How palettes reach the app

vColor watches a **palette inbox** inside its application data directory. Write
a complete `.json` file into the inbox. The app notices it while running, or on
the next launch, validates it, creates a new project, and makes it active.

| Platform | Inbox path |
| --- | --- |
| Windows | `%APPDATA%\vColor\inbox` |
| macOS | `~/Library/Application Support/vColor/inbox` |
| Linux | `${XDG_DATA_HOME:-$HOME/.local/share}/vColor/inbox` |

If you cannot determine the path, ask the user to click **Palette inbox** at the
bottom of the app sidebar. That opens the watched folder. If you cannot write
files at all (for example, a web chat), give the user the JSON file and ask
them to drag it onto the vColor window.

### Deliver the file safely

Write the complete JSON to a temporary file in the inbox, then rename it to a
`.json` name. Do not write directly to the final name: vColor may read the file
while it is incomplete. Names starting with `.` are ignored.

## Portable palette format

A palette is one standalone JSON file, for example `my-theme.json`:

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

Rules:

- `name` and at least one valid color are required. Everything else is optional.
- `format` may be omitted when reading; always write `"vcolor.palette"`.
- `id` defaults to a slug of `name`. Keep it stable and URL/file friendly.
- `tags` are lowercase labels such as `dark`, `light`, `pastel`, `material`.
- The canonical `colors` form is an array of `{"name", "hex"}` objects. The
  reader also accepts an object (`{"background": "#101014"}`) or an array of
  hex strings, but always write the canonical form.
- Hex values are normalized to lowercase `#rrggbb`.
- Record the upstream `source` URL and `license` when they exist.

The JSON Schema is available at `<inbox>/palette-schema.json`, and in the
repository at `vcolor/palette_format.py` as `PALETTE_SCHEMA`.

## What the app does with a file

- Every valid file becomes a **new project** and becomes the active project.
- If a project with the same name exists, the new project is named
  `Name (2)`, `Name (3)`, and so on. Existing projects are never overwritten.
- The app stores only the project name and colors. Keep `source`, `license`, and
  `tags` in the JSON file as the source of truth.
- Invalid files are moved into `<inbox>/failed/`.
- Valid files are archived into `<inbox>/imported/`.
- `AGENTS.md` and `palette-schema.json` are reserved and never imported.

Do not edit `palettes.json` directly, and do not write anywhere else in the
application data directory.

## Workflow: generate a theme

1. **Fetch the official colors.** Use web search/fetch tools to get the named
   colors from the upstream project, its repository, or its documentation. Do
   not invent or approximate hex values. Preserve the project's color names and
   intended order. Note the license and source URL.
2. **Write a portable file.** Create the JSON document in the format above.
3. **Deliver it atomically.** Write a temporary file in the inbox, then rename
   it to `my-theme.json`. The app does the rest; no app launch or command is
   required.
4. **Verify if possible.** Re-read the file and confirm it is valid JSON with a
   name and at least one `#rrggbb` color. If the app is open, the project should
   appear within a couple of seconds.

Theme notes:

- **Material 3** is seed-based. If the user supplies a seed color, use the
  official Material color utilities or an official generator to produce the
  tonal roles, then write those roles as colors. Otherwise use the published
  baseline scheme.
- **libadwaita** uses the named GNOME palette (Blue, Green, Yellow, Orange,
  Red, Purple, Brown, Light, and Dark steps).
- **Catppuccin** publishes all four flavors in its official palette repository.
- **Editor themes** such as Tokyo Night, Nord, and Dracula should come from the
  project's own color definitions, not from third-party approximations.

## Rules for this repository

- Do not add theme palettes to the repository unless the user explicitly asks.
  Palettes are user data, not source code.
- Do not hand-edit the application database (`palettes.json`); use the palette
  inbox or the GUI.
- Do not guess official theme colors. If the upstream source cannot be found,
  tell the user which values are missing.
- Keep `source` and `license` metadata accurate when converting someone else's
  palette.

## Repository map

| Path | Purpose |
| --- | --- |
| `vcolor/inbox.py` | Watched palette inbox, validation, copy naming, archiving |
| `vcolor/palette_format.py` | Portable palette load/save and JSON Schema |
| `vcolor/palette_io.py` | CSS/GPL/JSON import and export |
| `vcolor/models.py` | Application data (`palettes.json`) |
| `vcolor/main_window.py` | Window, inbox polling, drag-and-drop, persistence |
| `vcolor/app.py` | Qt application entry point |
| `tests/` | `unittest` suite |

## Development

```powershell
uv lock
$env:QT_QPA_PLATFORM='offscreen'; uv run python -m unittest discover -s tests -q
```

Builds and release details are in `docs/DEVELOPMENT.md`. Do not push, tag, or
publish releases unless the user asks.
