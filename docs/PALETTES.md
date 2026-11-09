# Portable palettes

A vColor palette is a small JSON document that can be stored, shared, and
version-controlled on its own — `catppuccin-mocha.json`, `libadwaita.json`,
`material-3.json`, and so on. The same file works with the GUI, the headless
CLI, and any script that can read JSON.

vColor does not bundle a theme catalog. Theme colors change upstream and have
different licenses, so the intended workflow is: fetch the official palette,
write a portable file, then import it. Coding agents can follow the recipes in
[AGENTS.md](../AGENTS.md).

## File format

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

For convenience, the reader also accepts `colors` as an object
(`{"base": "#101014"}`) or a bare array of hex strings. Exports always use the
canonical array form. Hex values are normalized to lowercase `#rrggbb`;
invalid entries are skipped when reading, and a palette with no valid colors is
rejected.

The machine-readable JSON Schema is available with:

```bash
uv run python -m vcolor palette schema
```

## Preparing a palette

1. Find the official colors on the upstream project's website or repository.
   Record the source URL and license.
2. Write a JSON file using the format above.
3. Validate it:

   ```bash
   uv run python -m vcolor palette show my-theme.json
   ```

4. Install it into vColor:

   ```bash
   uv run python -m vcolor palette install my-theme.json
   ```

`install` creates a project in the same `palettes.json` the GUI uses and makes
it active. Restart vColor if it is already open. It refuses to overwrite an
existing project unless you pass `--replace`. The app stores the palette name
and colors; keep the JSON file as the source of truth for `source`, `license`,
and `tags`.

## Command line

The `vcolor palette` commands work without Qt. From a source checkout, prefix
them with `uv run python -m`; when the package is installed, use `vcolor-cli`
without the `palette` word.

```bash
# Validate and inspect a portable file
uv run python -m vcolor palette show catppuccin-mocha.json
uv run python -m vcolor palette show catppuccin-mocha.json --json

# Create a palette from explicit colors
uv run python -m vcolor palette create "Brand" \
  --id brand \
  --color primary=#0a84ff \
  --color surface=#101014 \
  --tag dark \
  --output brand.json

# Normalize an upstream JSON, CSS, or GPL file
uv run python -m vcolor palette convert upstream.css \
  --name "My Theme" \
  --source "https://example.com/my-theme" \
  --license MIT \
  --tag dark \
  --output my-theme.json

# Export a portable file to another format
uv run python -m vcolor palette export my-theme.json my-theme.css
uv run python -m vcolor palette export my-theme.json my-theme.gpl

# Add it to the app and inspect installed projects
uv run python -m vcolor palette install my-theme.json
uv run python -m vcolor palette list
```

`export` infers the format from the file extension; pass `--format` to override
it. When the output is `.json`, the full portable document is preserved,
including metadata. Use `--data-dir` with `install` or `list` to target a test
profile instead of the real one.

### Metadata flags

`create` and `convert` accept `--id`, `--description`, `--source`, `--license`,
and repeatable `--tag`. `convert` also accepts `--name`. With no `--output`,
both commands print the portable JSON to stdout.

### Supported input files

`show`, `convert`, `export`, and `install` accept:

- vColor portable JSON (the canonical format)
- simple legacy JSON such as `{"name": "...", "colors": [{"name": ..., "hex": ...}]}`
- JSON arrays of hex strings or `{name, hex}` objects
- CSS files with `--variable: #rrggbb` declarations or plain hex values
- GIMP `.gpl` palettes

Complex upstream theme files (nested JSON, Lua, SCSS) should be reduced to
named hex values first, then written as portable JSON.

## GUI integration

- **Export → JSON** writes the full portable document, including the
  `format`, `version`, and `id` fields.
- **Import colors** in the GUI appends the file's colors to the active project.
  To create a separate project named after the palette, use
  `vcolor palette install` instead.
- Installing with the CLI is equivalent to creating the project in the GUI and
  marks it active.

## Licensing

The palette *data* remains under its upstream project's license. Put that in
the `license` field and keep the `source` URL. vColor itself is MIT-licensed;
see the repository `LICENSE`.
