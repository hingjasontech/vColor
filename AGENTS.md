# AGENTS.md

vColor is a desktop project manager for Linux, macOS, and Windows. It
deliberately does **not** ship a theme catalog: when a user asks for Catppuccin
Mocha, Material 3, libadwaita, Tokyo Night, or any other theme, fetch the
current official colors from the upstream project and deliver them as a
portable vColor project.

This file is the only source of instructions for AI assistants working with
vColor projects. vColor does not install a copy of this file, a schema, or any
other documentation on the user's machine, and it does not watch a folder for
projects. Do not create `AGENTS.md`, schema files, or inbox folders in the
user's application data directory.

## How projects reach the app

A vColor project is a single portable `.json` file. The user imports it
explicitly:

- **Import project** at the bottom of the sidebar (above **Settings**).
- Drag one or more `.json` project files onto the vColor window.
- A project's context menu can **Import colors** into that existing project.

Every imported file becomes a **new project** and becomes the active project.
If a project with the same name already exists, the new project is named
`Name (2)`, `Name (3)`, and so on. Existing projects are never overwritten.
Invalid files are rejected with a notification and are not modified.

Write the file wherever the user can reach it (the current workspace, a
downloads folder, or a path the user chooses). Never write into the vColor
application data directory.

## Portable project format

A project is one standalone JSON file, for example `my-theme.json`:

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
- `format` may be omitted when reading; always write `"vcolor.palette"`. The
  identifier is kept for compatibility with existing files.
- `id` defaults to a slug of `name`. Keep it stable and URL/file friendly.
- `tags` are lowercase labels such as `dark`, `light`, `pastel`, `material`.
- The canonical `colors` form is an array of `{"name", "hex"}` objects. The
  reader also accepts an object (`{"background": "#101014"}`) or an array of
  hex strings, but always write the canonical form.
- Hex values are normalized to lowercase `#rrggbb`.
- Record the upstream `source` URL and `license` when they exist.

The JSON Schema lives in this repository in `vcolor/palette_format.py` as
`PALETTE_SCHEMA`. It is not shipped to the user's machine.

## What the app stores

The app stores only the project name and colors in `palettes.json`. Keep
`source`, `license`, `description`, and `tags` in the project `.json` file as
the source of truth. If the user exports a project from vColor, the export
contains the name and colors in the same portable format.

Do not edit `palettes.json` directly, and do not write anywhere in the
application data directory.

## Workflow: generate a theme

1. **Fetch the official colors.** Use web search/fetch tools to get the named
   colors from the upstream project, its repository, or its documentation. Do
   not invent or approximate hex values. Preserve the project's color names and
   intended order. Note the license and source URL.
2. **Write a portable file.** Create the JSON document in the format above and
   tell the user which file to import.
3. **Ask the user to import it.** They can use **Import project** in the
   sidebar or drag the file onto the vColor window.
4. **Verify if possible.** Re-read the file and confirm it is valid JSON with a
   name and at least one `#rrggbb` color.

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

- Do not add theme projects to the repository unless the user explicitly asks.
  Theme projects are user data, not source code.
- Do not hand-edit the application database (`palettes.json`); use the GUI.
- Do not guess official theme colors. If the upstream source cannot be found,
  tell the user which values are missing.
- Keep `source` and `license` metadata accurate when converting someone else's
  theme.
- Regenerate `docs/screenshot.png` whenever the interface changes. The README
  embeds this file, so a UI change is not complete until the screenshot is
  updated with `uv run python scripts/screenshot.py`.

## Repository map

| Path | Purpose |
| --- | --- |
| `vcolor/project_files.py` | Project-file import helpers and copy naming |
| `vcolor/settings_page.py` | Libadwaita-style settings page |
| `vcolor/palette_format.py` | Portable project load/save and JSON Schema |
| `vcolor/palette_io.py` | CSS/GPL/JSON import and export |
| `vcolor/models.py` | Application data (`palettes.json`) |
| `vcolor/main_window.py` | Window, project import/export, drag-and-drop, persistence |
| `vcolor/app.py` | Qt application entry point |
| `tests/` | `unittest` suite |

## Development

```powershell
uv lock
$env:QT_QPA_PLATFORM='offscreen'; uv run python -m unittest discover -s tests -q
```

Builds and release details are in `docs/DEVELOPMENT.md`. Do not push, tag, or
publish releases unless the user asks.
