# AGENTS.md

vColor is a desktop palette manager with a portable JSON palette format and a
Qt-free CLI. It deliberately does **not** ship a theme catalog: when a user asks
for Catppuccin Mocha, Material 3, libadwaita, Tokyo Night, or any other theme,
fetch the current official colors from the internet and turn them into a vColor
palette.

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
- `format` may be omitted when reading; exported files always include
  `"format": "vcolor.palette"` and `"version": 1`.
- `id` defaults to a slug of `name`. Keep it stable and URL/file friendly.
- `tags` are lowercase labels such as `dark`, `light`, `pastel`, `material`.
- The canonical `colors` form is an array of `{"name", "hex"}` objects. The
  reader also accepts an object (`{"background": "#101014"}`) or an array of
  hex strings, but always write the canonical form.
- Hex values are normalized to lowercase `#rrggbb`.
- Record the upstream `source` URL and `license` when they exist.

Print the JSON Schema at any time:

```bash
uv run python -m vcolor palette schema
```

## Workflow: generate a theme

1. **Fetch the official colors.** Use web search/fetch tools to get the named
   colors from the upstream project (its repository or documentation). Do not
   invent or approximate hex values. Preserve the project's color names and
   intended order. Note the license and source URL.
2. **Write a portable file.** Create `my-theme.json` in the format above.
3. **Validate it.** `show` parses and normalizes the file, so any bad hex value
   or missing name fails here:

   ```bash
   uv run python -m vcolor palette show my-theme.json
   ```

4. **Install it into vColor.** This creates a project in the same
   `palettes.json` the GUI uses and makes it active. Restart vColor if it is
   already open:

   ```bash
   uv run python -m vcolor palette install my-theme.json
   ```

5. **Export other formats if needed.**

   ```bash
   uv run python -m vcolor palette export my-theme.json my-theme.css
   uv run python -m vcolor palette export my-theme.json my-theme.gpl
   ```

If the upstream data is already a simple JSON object, CSS custom-property file,
or GIMP `.gpl`, `install` and `convert` can read it directly. For complex
upstream files, extract the hex values and write the portable JSON yourself.

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

Examples:

```bash
# Upstream CSS with --accent: #0a84ff; and --surface: #101014;
uv run python -m vcolor palette convert upstream.css \
  --name "Libadwaita" \
  --source "https://gitlab.gnome.org/GNOME/libadwaita" \
  --license "LGPL-2.1-or-later" \
  --tag dark \
  --output libadwaita.json

# Material 3 baseline roles from an upstream JSON file
uv run python -m vcolor palette convert material3.json \
  --name "Material 3" \
  --source "https://m3.material.io" \
  --license "Apache-2.0" \
  --output material-3.json
```

## CLI reference

From a source checkout, prefix commands with `uv run python -m vcolor palette`.
If the package is installed, use `vcolor-cli` instead (no `palette` word):

| Command | Purpose |
| --- | --- |
| `show FILE [--json]` | Validate and display a palette file |
| `create NAME --color NAME=HEX ... [-o FILE]` | Build a palette from explicit colors |
| `convert FILE [-o FILE]` | Normalize JSON/CSS/GPL input to portable JSON |
| `export FILE OUTPUT [--format json\|css\|gpl]` | Convert a palette file to another format |
| `install FILE [--name NAME] [--replace]` | Add a project to vColor; alias: `import` |
| `list [--json]` | List projects installed in vColor |
| `schema` | Print the portable palette JSON Schema |

All commands are file-based and never start Qt. `install` writes to the normal
application data directory; pass `--data-dir <path>` to use a test profile.
`install` refuses to overwrite an existing project unless `--replace` is given.

Metadata flags accepted by `create` and `convert`: `--id`, `--description`,
`--source`, `--license`, and repeatable `--tag`. `convert` also accepts
`--name`. With no `--output`, both commands print JSON to stdout.

## Rules for this repository

- Do not add theme palettes to the repository unless the user explicitly asks.
  Palettes are user data, not source code.
- Do not hand-edit the application database (`palettes.json`); use
  `vcolor palette install` or the GUI.
- Do not guess official theme colors. If the upstream source cannot be found,
  tell the user which values are missing.
- Keep `source` and `license` metadata accurate when converting someone
  else's palette.

## Repository map

| Path | Purpose |
| --- | --- |
| `vcolor/palette_format.py` | Portable palette load/save and JSON Schema |
| `vcolor/cli.py` | Headless `vcolor palette` commands |
| `vcolor/palette_io.py` | CSS/GPL/JSON import and export |
| `vcolor/models.py` | Application data (`palettes.json`) |
| `vcolor/app.py` | Qt application entry point |
| `tests/` | `unittest` suite |

## Development

```powershell
uv lock
$env:QT_QPA_PLATFORM='offscreen'; uv run python -m unittest discover -s tests -q
```

Builds and release details are in `docs/DEVELOPMENT.md`. Do not push, tag, or
publish releases unless the user asks.
