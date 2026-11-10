# Portable projects

A vColor project is a small JSON document that can be stored, shared, and
version-controlled on its own — `catppuccin-mocha.json`, `libadwaita.json`,
`material-3.json`, and so on. The same format is used by the GUI's **Import
project** and **Export project** actions.

vColor does not bundle a theme catalog. Theme colors change upstream and have
different licenses, so the intended workflow is: fetch the official colors,
write a portable project file, then import it. Coding agents can follow the
recipes in [AGENTS.md](../AGENTS.md) in this repository.

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

The machine-readable JSON Schema lives in the source tree in
[`vcolor/palette_format.py`](../vcolor/palette_format.py) as `PALETTE_SCHEMA`.
It is not copied to the user's machine.

## Importing a project

Use **Import project** at the bottom of the sidebar, just above **Settings**,
and choose one or more `.json` project files. You can also drag one or more
`.json` project files onto the vColor window.

- Every valid file creates a **new project** and becomes the active project.
- A duplicate name gets a numbered copy: `Catppuccin Mocha`, then
  `Catppuccin Mocha (2)`, `Catppuccin Mocha (3)`, and so on. Existing projects
  are never overwritten.
- The app stores only the project name and colors. `source`, `license`, and
  `tags` stay in the JSON file as the source of truth.
- The original file is not moved or modified.
- The toast notification offers **Undo**, which removes the imported project
  and restores the previously active project.

## Importing colors into a project

Right-click a project in the sidebar and choose **Import colors...**, or press
`Ctrl/Cmd+I` to import into the active project. This appends colors from JSON,
CSS, or GIMP `.gpl` files to that project instead of creating a new one.

## Exporting a project

Right-click a project and choose **Export project...**, or press `Ctrl/Cmd+E`
to export the active project. Choose:

- **JSON project** — the portable `vcolor.palette` document.
- **CSS variables** — a `:root` block of custom properties.
- **GIMP palette** — a `.gpl` file.

A JSON export contains the project name and colors, plus the `format`,
`version`, and `id` fields. It does not contain `source`, `license`, or `tags`
because the app does not store that metadata.

## Licensing

The project data remains under its upstream project's license. Put that in the
`license` field and keep the `source` URL. vColor itself is MIT-licensed; see
the repository `LICENSE`.
