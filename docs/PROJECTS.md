# Palette projects

A vColor project is a named group of colors. It is not tied to a document
format: vColor imports and exports the same palette formats that other design
tools use, so a project can move between vColor, Coolors, GIMP, Inkscape,
Adobe apps, and codebases without a conversion step.

The project name comes from the file name. Importing `catppuccin-mocha.css`
creates a project called **Catppuccin Mocha**. File metadata such as
descriptions, source URLs, licenses, and tags is not stored in vColor.

vColor does not bundle a theme catalog. Theme colors change upstream and have
different licenses, so the intended workflow is to fetch the official colors,
write a palette file, and import it. Coding agents can follow the recipes in
[AGENTS.md](../AGENTS.md).

## Supported formats

| Format | Import | Export | Notes |
| --- | --- | --- | --- |
| JSON | Yes | Yes | Coolors array, object, or extended array; also generic JSON. |
| CSS / SCSS | Yes | Yes | Custom properties (`--name`) and SCSS variables (`$name`). |
| Tailwind config | Yes | Yes | Exports a v3 `theme.extend.colors` mapping; flattens shades on import. |
| XML | Yes | Yes | Reads color elements and `name`/`hex`/`r`/`g`/`b` attributes. |
| SVG | Yes | Yes | Exports a labeled swatch sheet; ignores text colors on import. |
| ASE | Yes | Yes | Adobe Swatch Exchange. Imports RGB, CMYK, LAB, and Gray. |
| GPL | Yes | Yes | GIMP palette. |
| CSV | Yes | Yes | Flat comma-separated hex, matching Coolors. |
| TXT | Yes | Yes | Plain hex values, or `#rrggbb<TAB>Name` when names exist. |
| Coolors link | Yes | Yes | `https://coolors.co/...` palette URLs. |

PDF and PNG are not supported because they cannot be imported back into a
palette.

## JSON format

Exports use an array of objects:

```json
[
  { "name": "background", "hex": "#101014" },
  { "name": "foreground", "hex": "#f2f2f7" }
]
```

The reader also accepts the shapes Coolors produces:

- an array of `{"name", "hex"}` objects, with extra fields ignored;
- an array of hex strings;
- a `{"name": "#hex"}` object;
- an extended array of objects with `hex`/`value` fields;
- a wrapper object such as `{"colors": [...]}`.

Hex values are normalized to lowercase `#rrggbb`. Invalid entries are skipped;
a file with no valid colors is rejected.

The old custom `vcolor.palette` JSON document is no longer supported. Files
that use it are rejected; use a standard palette format instead.

## Project names

The file name becomes the project name: separators become spaces and words are
title-cased.

| File | Project |
| --- | --- |
| `catppuccin-mocha.json` | Catppuccin Mocha |
| `TokyoNight.css` | Tokyo Night |
| `my_theme.v2.txt` | My Theme V2 |

Duplicate names get a numbered copy: `Catppuccin Mocha`, then
`Catppuccin Mocha (2)`, `Catppuccin Mocha (3)`, and so on. Existing projects
are never overwritten.

## Importing a project

Use **Import project** at the bottom of the sidebar, just above **Settings**,
and choose one or more palette files. You can also drag palette files onto the
vColor window. vColor does not watch folders.

- Every valid file creates a **new project** and becomes the active project.
- The original file is not moved or modified.
- Invalid files are skipped with a notification.
- The toast notification offers **Undo**, which removes the imported projects
  and restores the previously active project.

## Importing colors into a project

Right-click a project in the sidebar and choose **Import colors...**, or press
`Ctrl/Cmd+I` to import into the active project. This appends colors from any
supported palette file to that project instead of creating a new one.

## Exporting a project

Right-click a project and choose **Export project...**, or press `Ctrl/Cmd+E`
to export the active project. Pick a format in the save dialog. The extension
you type selects the format when it is recognized, so `theme.ase` exports ASE
even if the JSON filter is selected. If you omit the extension, vColor appends
the selected format's extension. Both plain text formats use `.txt`, so the
selected filter chooses between a hex list and a Coolors link.

Formats that carry color names preserve them. CSV and Coolors links contain
only hex values, so imported colors get generated names like **Color 1**.

## Licensing

Palette colors remain under their upstream project's license. vColor stores only
project names, colors, and app settings. If you redistribute a palette, keep its
license and source information alongside the file.
