"""Headless palette commands.

These commands never start Qt. They validate portable palette files, convert
other palette files, and install projects into the same ``palettes.json`` used
by the GUI. Run them through ``python -m vcolor palette ...`` or ``vcolor-cli``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .color_utils import ColorError, normalize_hex, slugify
from .models import ColorEntry, PaletteStore, StoreError, default_data_dir
from .palette_format import (
    FORMAT,
    PALETTE_SCHEMA,
    PortablePalette,
    save_palette,
)
from .palette_io import export_palette, import_palette

_FORMATS = {"json": "json", "css": "css", "gpl": "gpl"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vcolor palette",
        description="Validate, convert, export, and install portable palettes.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    show_parser = subparsers.add_parser(
        "show",
        help="Validate and display a palette file.",
    )
    show_parser.add_argument(
        "input",
        type=Path,
        help="Palette file (portable JSON, legacy JSON, CSS, or GPL).",
    )
    show_parser.add_argument("--json", action="store_true", help="Print JSON.")
    show_parser.set_defaults(func=_cmd_show)

    create_parser = subparsers.add_parser(
        "create",
        parents=[_metadata_parser(include_name=False)],
        help="Create a portable palette from NAME=HEX pairs.",
    )
    create_parser.add_argument("name", help="Palette name.")
    create_parser.add_argument(
        "--color",
        action="append",
        default=[],
        metavar="NAME=HEX",
        help="Color entry, repeatable.",
    )
    create_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write the palette here; otherwise print it to stdout.",
    )
    create_parser.set_defaults(func=_cmd_create)

    convert_parser = subparsers.add_parser(
        "convert",
        parents=[_metadata_parser(include_name=True)],
        help="Convert JSON, CSS, or GPL input to portable palette JSON.",
    )
    convert_parser.add_argument(
        "input",
        type=Path,
        help="Palette file (portable JSON, legacy JSON, CSS, or GPL).",
    )
    convert_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write the palette here; otherwise print it to stdout.",
    )
    convert_parser.set_defaults(func=_cmd_convert)

    export_parser = subparsers.add_parser(
        "export",
        help="Export a palette file as JSON, CSS, or GPL.",
    )
    export_parser.add_argument(
        "input",
        type=Path,
        help="Palette file (portable JSON, legacy JSON, CSS, or GPL).",
    )
    export_parser.add_argument("output", type=Path, help="Output file.")
    export_parser.add_argument(
        "--format",
        choices=sorted(_FORMATS),
        help="Output format; defaults to the output file extension.",
    )
    export_parser.set_defaults(func=_cmd_export)

    install_parser = subparsers.add_parser(
        "install",
        aliases=["import"],
        help="Add a palette file to vColor as a project.",
    )
    install_parser.add_argument(
        "input",
        type=Path,
        help="Palette file (portable JSON, legacy JSON, CSS, or GPL).",
    )
    install_parser.add_argument("--name", help="Project name to use in the app.")
    install_parser.add_argument(
        "--replace",
        action="store_true",
        help="Overwrite an existing project with the same name.",
    )
    install_parser.add_argument(
        "--data-dir",
        type=Path,
        help="Override the application data directory.",
    )
    install_parser.set_defaults(func=_cmd_install)

    list_parser = subparsers.add_parser(
        "list",
        help="List projects installed in the app.",
    )
    list_parser.add_argument(
        "--data-dir",
        type=Path,
        help="Override the application data directory.",
    )
    list_parser.add_argument("--json", action="store_true", help="Print JSON.")
    list_parser.set_defaults(func=_cmd_list)

    schema_parser = subparsers.add_parser(
        "schema",
        help="Print the portable palette JSON Schema.",
    )
    schema_parser.set_defaults(func=_cmd_schema)

    return parser


def _metadata_parser(*, include_name: bool) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    if include_name:
        parser.add_argument(
            "--name",
            help="Palette name; defaults to the input file's name.",
        )
    parser.add_argument("--id", dest="palette_id", help="Palette id (slug).")
    parser.add_argument("--description", help="One-line description.")
    parser.add_argument("--source", help="Upstream project or documentation URL.")
    parser.add_argument("--license", dest="license_name", help="License name.")
    parser.add_argument(
        "--tag",
        action="append",
        help="Tag such as dark or light, repeatable.",
    )
    return parser


def _cmd_show(args: argparse.Namespace) -> int:
    palette = _read_palette(args.input)
    if args.json:
        print(json.dumps(palette.to_dict(), indent=2, ensure_ascii=False))
        return 0

    print(f"{palette.name}  ({palette.id})")
    meta = [f"{len(palette.colors)} colors"]
    if palette.tags:
        meta.append(", ".join(palette.tags))
    if palette.license:
        meta.append(palette.license)
    print(" | ".join(meta))
    if palette.description:
        print(palette.description)
    if palette.source:
        print(palette.source)
    print()
    width = max((len(color.name) for color in palette.colors), default=0)
    for color in palette.colors:
        print(f"{color.name.ljust(width)}  {color.hex}")
    return 0


def _cmd_create(args: argparse.Namespace) -> int:
    colors: list[ColorEntry] = []
    for raw in args.color:
        name, separator, value = raw.partition("=")
        if not separator:
            raise ValueError(f"Expected NAME=HEX, got {raw!r}")
        name = name.strip()
        if not name:
            raise ValueError(f"Expected a color name before '=' in {raw!r}")
        try:
            hex_value = normalize_hex(value.strip())
        except ColorError as exc:
            raise ValueError(f"Invalid color {value!r}: {exc}") from exc
        colors.append(ColorEntry(name=name, hex=hex_value))

    if not colors:
        raise ValueError("Provide at least one --color NAME=HEX entry")

    palette = PortablePalette(
        id=slugify(args.palette_id or args.name, "palette"),
        name=args.name,
        colors=colors,
        description=args.description or "",
        source=args.source or "",
        license=args.license_name or "",
        tags=list(args.tag or []),
    )
    if args.output is None:
        print(json.dumps(palette.to_dict(), indent=2, ensure_ascii=False))
        return 0

    save_palette(palette, args.output)
    print(f"Wrote {palette.name!r} to {args.output} ({len(colors)} colors).")
    return 0


def _cmd_convert(args: argparse.Namespace) -> int:
    palette, portable = _read_palette_file(args.input)
    palette = _apply_metadata(palette, args)
    if not portable and args.name and not args.palette_id:
        palette.id = slugify(palette.name, "palette")
    if args.output is None:
        print(json.dumps(palette.to_dict(), indent=2, ensure_ascii=False))
        return 0

    save_palette(palette, args.output)
    print(
        f"Wrote {palette.name!r} to {args.output} "
        f"({len(palette.colors)} colors, {FORMAT})."
    )
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    palette = _read_palette(args.input)
    kind = args.format or _FORMATS.get(args.output.suffix.lower().lstrip("."))
    if kind is None:
        raise ValueError(
            f"Cannot infer a format from {args.output.suffix!r}; pass --format."
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if kind == "json":
        save_palette(palette, args.output)
    else:
        export_palette(palette.to_project(), args.output, kind)
    print(
        f"Exported {palette.name!r} to {args.output} "
        f"({len(palette.colors)} colors, {kind})."
    )
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    palette = _read_palette(args.input)
    name = args.name or palette.name
    data_dir = args.data_dir or default_data_dir()
    store = PaletteStore(Path(data_dir) / "palettes.json")
    data = store.load()

    existing = next(
        (project for project in data.projects if project.name.lower() == name.lower()),
        None,
    )
    if existing is not None and not args.replace:
        raise ValueError(
            f"A project named {name!r} already exists; pass --replace to overwrite it."
        )

    project = palette.to_project(name=name)
    if existing is not None:
        existing.colors = project.colors
        existing.touch()
        target = existing
    else:
        data.projects.append(project)
        target = project

    data.active_project_id = target.id
    store.save(data)
    print(
        f"Installed {name!r} ({len(target.colors)} colors) "
        f"into {store.path}."
    )
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    data_dir = args.data_dir or default_data_dir()
    store = PaletteStore(Path(data_dir) / "palettes.json")
    data = store.load()

    if args.json:
        payload = [
            {
                "id": project.id,
                "name": project.name,
                "colors": len(project.colors),
                "active": project.id == data.active_project_id,
            }
            for project in data.projects
        ]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if not data.projects:
        print("No projects installed.")
        return 0

    rows = [
        (
            project.name,
            str(len(project.colors)),
            "yes" if project.id == data.active_project_id else "",
        )
        for project in data.projects
    ]
    headers = ("NAME", "COLORS", "ACTIVE")
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
    return 0


def _cmd_schema(args: argparse.Namespace) -> int:
    print(json.dumps(PALETTE_SCHEMA, indent=2, ensure_ascii=False))
    return 0


def _read_palette(path: Path) -> PortablePalette:
    """Read any supported palette file."""
    palette, _portable = _read_palette_file(path)
    return palette


def _read_palette_file(path: Path) -> tuple[PortablePalette, bool]:
    """Read a palette and report whether it used the portable format."""
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"Palette file not found: {path}")

    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")

    raw: object = None
    if path.suffix.lower() == ".json" or text.lstrip().startswith(("{", "[")):
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            raw = None

    fallback_name = _name_from_path(path)
    if isinstance(raw, dict):
        raw_format = raw.get("format")
        if (
            isinstance(raw_format, str)
            and raw_format.startswith("vcolor.")
            and raw_format != FORMAT
        ):
            raise ValueError(
                f"Unsupported palette format {raw_format!r}; expected {FORMAT!r}."
            )
        if raw_format in (None, FORMAT):
            try:
                return PortablePalette.from_dict(raw), True
            except ValueError:
                pass
        candidate_name = raw.get("name")
        if isinstance(candidate_name, str) and candidate_name.strip():
            fallback_name = candidate_name.strip()

    colors = import_palette(path)
    return (
        PortablePalette(
            id=slugify(fallback_name, "palette"),
            name=fallback_name,
            colors=colors,
        ),
        False,
    )


def _name_from_path(path: Path) -> str:
    stem = path.stem.replace("-", " ").replace("_", " ").strip()
    return stem.title() or "Palette"


def _apply_metadata(
    palette: PortablePalette, args: argparse.Namespace
) -> PortablePalette:
    if getattr(args, "name", None):
        palette.name = args.name
    if getattr(args, "palette_id", None):
        palette.id = slugify(args.palette_id, "palette")
    for attribute, target in (
        ("description", "description"),
        ("source", "source"),
        ("license_name", "license"),
    ):
        value = getattr(args, attribute, None)
        if value is not None:
            setattr(palette, target, value)
    tags = getattr(args, "tag", None)
    if tags is not None:
        palette.tags = list(tags)
    return palette


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, OSError, StoreError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def console_main(argv: list[str] | None = None) -> int:
    """Entry point for the ``vcolor-cli`` console script."""
    return main(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(console_main())
