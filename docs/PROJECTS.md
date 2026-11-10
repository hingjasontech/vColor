# Portable projects

A vColor project is a small JSON document that can be stored, shared, and
version-controlled on its own — `catppuccin-mocha.json`, `libadwaita.json`,
`material-3.json`, and so on. The same format is used by the GUI's
**Export → JSON** action and by the watched project inbox.

vColor does not bundle a theme catalog. Theme colors change upstream and have
different licenses, so the intended workflow is: fetch the official colors,
write a portable project file, then let vColor import it. Coding agents can
follow the recipes in [AGENTS.md](../AGENTS.md).

## File format

```json
{
  "format": "vcolor.palette",
  "version": 1,
  "id": "my-project",
  "name": "My Project",
  "description": "One-line summary.",
  "source": "https://example.com/my-project",
  "license": "MIT",
  "tags": ["dark"],
  "colors": [
    { "name": "background", "hex": "#101014" },
    { "name": "foreground", "hex": "#f2f2f7" }
  ]
}
```

| Field | Required | Purpose |
| --- | --- | --- |
| `format` | No | Always `vcolor.palette` when written. Omitted files are still readable. |
| `version` | No | Format version; currently `1`. |
| `id` | No | Stable slug. Defaults to a slug of `name`. |
| `name` | Yes | Display name. |
| `description` | No | One-line summary. |
| `source` | No | Upstream project URL. |
| `license` | No | SPDX identifier or short license name. |
| `tags` | No | Lowercase search labels, e.g. `dark`, `light`, `material`. |
| `colors` | Yes | Array of `{"name", "hex"}` objects; at least one valid color. |

The `vcolor.palette` format identifier is kept for compatibility with existing
files. Internally, an imported file becomes a vColor **project**.

For convenience, the reader also accepts `colors` as an object
(`{"base": "#101014"}`) or a bare array of hex strings. Exports always use the
canonical array form. Hex values are normalized to lowercase `#rrggbb`;
invalid entries are skipped when reading, and a project with no valid colors is
rejected.

The machine-readable JSON Schema is written into the project inbox as
`project-schema.json` and lives in the source tree in
[`vcolor/palette_format.py`](../vcolor/palette_format.py) as `PALETTE_SCHEMA`.

## The project inbox

vColor watches an inbox folder inside its application data directory. A valid
JSON file placed there becomes a new project automatically and is made active.
The file is then moved into `inbox/imported/`; invalid files are moved into
`inbox/failed/`.

| Platform | Project inbox path |
| --- | --- |
| Windows | `%APPDATA%\vColor\inbox` |
| macOS | `~/Library/Application Support/vColor/inbox` |
| Linux | `${XDG_DATA_HOME:-$HOME/.local/share}/vColor/inbox` |

The app creates the folder, `AGENTS.md`, and `project-schema.json` on first
launch. Click **Project inbox** at the bottom of the app sidebar to open it.

### Delivering a project

1. Write the complete JSON document to a temporary file in the inbox.
2. Rename the temporary file to a `.json` name, for example
   `catppuccin-mocha.json`. This atomic rename prevents vColor from reading a
   half-written file.
3. Leave the file there. vColor scans at startup and every couple of seconds
   while it is running.

Files whose names start with `.` are ignored. `AGENTS.md` and
`project-schema.json` are reserved documentation and are never imported.

### Import rules

- Every valid file creates a **new project** and becomes the active project.
- A duplicate name gets a numbered copy: `Catppuccin Mocha`, then
  `Catppuccin Mocha (2)`, `Catppuccin Mocha (3)`, and so on. Existing projects
  are never overwritten.
- The app stores only the project name and colors. `source`, `license`, and
  `tags` stay in the JSON file as the source of truth.
- Imported files are archived in `inbox/imported/`; failed files are kept in
  `inbox/failed/`.
- The toast notification offers **Undo**, which removes the imported project
  and restores the previously active project.

## Drag and drop

Dropping one or more `.json` project files onto the vColor window creates new
projects with the same naming and duplicate rules. This is the fallback for
web-based AI assistants that can provide a file download but cannot write to
the local inbox. The original file is not moved or modified.

## GUI integration

- **Export → JSON** writes the full portable document, including the `format`,
  `version`, and `id` fields, but without `source`, `license`, or `tags`
  because the app does not store that metadata.
- **Import colors** in a project's context menu appends colors from JSON, CSS,
  or GIMP files to that project. To create a separate project named after the
  theme, use the project inbox or drag-and-drop instead.

## Licensing

The project data remains under its upstream project's license. Put that in the
`license` field and keep the `source` URL. vColor itself is MIT-licensed; see
the repository `LICENSE`.
