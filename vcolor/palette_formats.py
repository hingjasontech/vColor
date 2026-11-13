"""Import and export for common palette file formats.

vColor treats a palette file as a list of colors, not as a project document.
The project name always comes from the file name, so the file formats stay
interchangeable with tools such as Coolors, GIMP, Inkscape, and Adobe apps.

Supported formats: Coolors links, CSS/SCSS variables, JSON, CSV, plain text,
XML, SVG, Adobe Swatch Exchange (ASE), Tailwind configs, and GIMP palettes.
"""

from __future__ import annotations

import csv
import io
import json
import re
import struct
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .color_utils import (
    CMYK,
    LAB,
    RGB,
    ColorError,
    cmyk_to_rgb,
    hex_to_rgb,
    lab_to_rgb,
    normalize_hex,
    parse_color,
    readable_text_color,
    rgb_to_hex,
    slugify,
)
from .models import ColorEntry, Project


@dataclass(frozen=True, slots=True)
class ExportFormat:
    id: str
    label: str
    suffix: str

    @property
    def filter(self) -> str:
        return f"{self.label} (*{self.suffix})"


EXPORT_FORMATS: tuple[ExportFormat, ...] = (
    ExportFormat("json", "JSON palette", ".json"),
    ExportFormat("css", "CSS variables", ".css"),
    ExportFormat("scss", "SCSS variables", ".scss"),
    ExportFormat("tailwind", "Tailwind config", ".js"),
    ExportFormat("xml", "XML palette", ".xml"),
    ExportFormat("svg", "SVG swatches", ".svg"),
    ExportFormat("ase", "Adobe Swatch Exchange", ".ase"),
    ExportFormat("gpl", "GIMP palette", ".gpl"),
    ExportFormat("csv", "CSV palette", ".csv"),
    ExportFormat("txt", "Hex list", ".txt"),
    ExportFormat("coolors", "Coolors link", ".txt"),
)

DEFAULT_EXPORT_FORMAT = EXPORT_FORMATS[0]

IMPORT_SUFFIXES: frozenset[str] = frozenset(
    {
        ".json",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".styl",
        ".txt",
        ".text",
        ".csv",
        ".xml",
        ".svg",
        ".ase",
        ".js",
        ".cjs",
        ".mjs",
        ".ts",
        ".gpl",
        ".hex",
        ".colors",
        ".url",
        ".coolors",
    }
)

IMPORT_FILTER = (
    "Palette files (*.json *.css *.scss *.sass *.less *.styl *.txt *.text "
    "*.csv *.xml *.svg *.ase *.js *.cjs *.mjs *.ts *.gpl *.hex *.colors "
    "*.url *.coolors);;All files (*)"
)

_SVG_NS = "http://www.w3.org/2000/svg"
_HEX_TOKEN_RE = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
_FUNCTION_TOKEN_RE = re.compile(
    r"\b(?:rgba?|hsla?|hsb|hsv|device-cmyk|cmyk|lab|oklch)\([^)]*\)",
    re.IGNORECASE,
)
_COLOR_TOKEN_RE = re.compile(
    f"(?:{_HEX_TOKEN_RE.pattern})|(?:{_FUNCTION_TOKEN_RE.pattern})",
    re.IGNORECASE,
)
_BARE_HEX_RE = re.compile(r"(?<![\w#])(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![\w])")
_VAR_DECL_RE = re.compile(
    r"(?P<prefix>--|\$)(?P<name>[A-Za-z_][\w-]*)\s*:\s*(?P<value>[^;{}]+)"
)
_CSS_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_CSS_LINE_COMMENT_RE = re.compile(r"(?m)^\s*//.*$")
_COOLORS_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?coolors\.co/(?:palette/)?"
    r"(?P<tokens>[0-9a-fA-F]{3,6}(?:-[0-9a-fA-F]{3,6})*)",
    re.IGNORECASE,
)
_HEADER_WORDS = {
    "name",
    "color",
    "colors",
    "colour",
    "hex",
    "value",
    "swatch",
    "palette",
    "red",
    "green",
    "blue",
    "alpha",
    "r",
    "g",
    "b",
    "a",
    "h",
    "s",
    "l",
    "c",
    "m",
    "y",
    "k",
}

_KIND_ALIASES = {
    "coolors-url": "coolors",
    "coolors_link": "coolors",
    "url": "coolors",
    "hex": "txt",
    "text": "txt",
    "tailwindcss": "tailwind",
    "js": "tailwind",
    "javascript": "tailwind",
    "gimp": "gpl",
    "adobe-ase": "ase",
    "asef": "ase",
    "sass": "scss",
    "less": "css",
    "styl": "css",
}

_SUFFIX_ALIASES = {
    ".sass": "scss",
    ".less": "css",
    ".styl": "css",
    ".cjs": "tailwind",
    ".mjs": "tailwind",
    ".ts": "tailwind",
    ".hex": "txt",
    ".text": "txt",
    ".colors": "txt",
    ".url": "coolors",
    ".coolors": "coolors",
}


def export_filter_string() -> str:
    return ";;".join(fmt.filter for fmt in EXPORT_FORMATS)


def export_format_for_filter(selected: str) -> ExportFormat | None:
    for fmt in EXPORT_FORMATS:
        if selected == fmt.filter:
            return fmt
    selected = selected.casefold()
    for fmt in EXPORT_FORMATS:
        if fmt.label.casefold() in selected:
            return fmt
    return None


def export_format_for_suffix(suffix: str) -> ExportFormat | None:
    suffix = suffix.casefold()
    kind = _SUFFIX_ALIASES.get(suffix, suffix.lstrip("."))
    for fmt in EXPORT_FORMATS:
        if fmt.id == kind or fmt.suffix == suffix:
            return fmt
    return None


def is_supported_palette_file(path: str | Path) -> bool:
    return Path(path).suffix.casefold() in IMPORT_SUFFIXES


def resolve_export_target(
    path: str | Path, selected_filter: str
) -> tuple[Path, ExportFormat]:
    """Resolve the output path and format chosen in a save dialog.

    A recognized suffix wins, so typing ``theme.ase`` exports ASE even when the
    JSON filter is selected. Both plain text formats use ``.txt``, so the chosen
    filter decides between them. When no suffix is typed, the selected format's
    suffix is appended.
    """
    path = Path(path)
    selected = export_format_for_filter(selected_filter) or DEFAULT_EXPORT_FORMAT
    suffix = path.suffix.casefold()
    if not suffix:
        return path.with_suffix(selected.suffix), selected

    fmt = export_format_for_suffix(suffix)
    if fmt is None:
        return path.with_name(path.name + selected.suffix), selected
    if suffix == ".txt" and selected.suffix == ".txt":
        return path, selected
    return path, fmt


def export_palette(project: Project, path: Path, kind: str) -> Path:
    """Write ``project`` in ``kind`` format and return the written path."""
    kind = _normalize_kind(kind)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if kind == "ase":
        path.write_bytes(_to_ase(project))
        return path

    writers = {
        "json": _to_json,
        "css": _to_css,
        "scss": _to_scss,
        "tailwind": _to_tailwind,
        "xml": _to_xml,
        "svg": _to_svg,
        "gpl": _to_gpl,
        "csv": _to_csv,
        "txt": _to_txt,
        "coolors": _to_coolors,
    }
    writer = writers.get(kind)
    if writer is None:
        raise ValueError(f"Unsupported export format: {kind}")
    path.write_text(writer(project), encoding="utf-8")
    return path


def import_palette(path: Path) -> list[ColorEntry]:
    """Read colors from any supported palette file."""
    path = Path(path)
    return import_palette_bytes(path.read_bytes(), path)


def import_palette_bytes(data: bytes, path: Path) -> list[ColorEntry]:
    path = Path(path)
    if data.startswith(b"ASEF"):
        colors = _parse_ase(data)
    else:
        text = _decode_text(data)
        kind = _detect_kind(path.suffix.casefold(), text)
        colors = _parse_by_kind(kind, text)
    if not colors:
        raise ValueError("No colors were found in this file.")
    return colors


def _normalize_kind(kind: str) -> str:
    kind = kind.casefold().lstrip(".")
    return _KIND_ALIASES.get(kind, kind)


def _decode_text(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def _detect_kind(suffix: str, text: str) -> str:
    direct = {
        ".json": "json",
        ".css": "css",
        ".scss": "scss",
        ".csv": "csv",
        ".xml": "xml",
        ".svg": "svg",
        ".ase": "ase",
        ".gpl": "gpl",
    }
    if suffix in direct:
        return direct[suffix]
    if suffix in _SUFFIX_ALIASES:
        return _SUFFIX_ALIASES[suffix]

    stripped = text.lstrip()
    if stripped.startswith(("{", "[")):
        return "json"
    if stripped.startswith("<"):
        if re.search(r"<svg\b", text, re.IGNORECASE):
            return "svg"
        return "xml"
    if "coolors.co/" in text.casefold():
        return "coolors"
    if text.startswith("GIMP Palette"):
        return "gpl"
    if re.search(r"\bcolors\s*:\s*\{", text) or (
        "module.exports" in text and "theme" in text
    ):
        return "tailwind"
    if _VAR_DECL_RE.search(text) or re.search(r"--[\w-]+\s*:", text):
        return "css"
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    if first_line.count(",") >= 2:
        return "csv"
    return "txt"


def _parse_by_kind(kind: str, text: str) -> list[ColorEntry]:
    parsers = {
        "json": _parse_json,
        "css": _parse_css,
        "scss": _parse_css,
        "tailwind": _parse_tailwind,
        "xml": _parse_xml,
        "svg": _parse_svg,
        "gpl": _parse_gpl,
        "csv": _parse_csv,
        "txt": _parse_text,
        "coolors": _parse_coolors,
    }
    parser = parsers.get(kind)
    if parser is None:
        parser = _parse_text
    return parser(text)


# --------------------------------------------------------------------- helpers


def _humanize(value: str) -> str:
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    text = re.sub(r"[-_.]+", " ", text)
    words = []
    for word in text.split():
        if word.isdigit() or (word.isupper() and len(word) <= 4):
            words.append(word)
        else:
            words.append(word[:1].upper() + word[1:].lower())
    return " ".join(words).strip()


def _unique_name(name: str, used: set[str]) -> str:
    base = name.strip() or "Color"
    candidate = base
    index = 2
    while candidate.casefold() in used:
        candidate = f"{base} {index}"
        index += 1
    used.add(candidate.casefold())
    return candidate


def _clean_value(value: str) -> str:
    value = re.sub(r"!default|!important", "", value, flags=re.IGNORECASE)
    return value.strip().strip(";,").strip()


def _color_value(value: str) -> str | None:
    value = _clean_value(value)
    if not value:
        return None
    try:
        return parse_color(value)
    except ColorError:
        return None


def _token_color(value: str) -> str | None:
    match = _COLOR_TOKEN_RE.fullmatch(_clean_value(value))
    if match is None:
        return None
    return _color_value(match.group(0))


def _bare_color_value(value: str) -> str | None:
    value = value.strip().strip("\"'")
    if re.fullmatch(r"[0-9a-fA-F]{3}|[0-9a-fA-F]{6}", value):
        return normalize_hex(value)
    return None


def _scan_colors(text: str) -> list[ColorEntry]:
    colors: list[ColorEntry] = []
    seen: set[str] = set()
    for match in _COLOR_TOKEN_RE.finditer(text):
        value = _color_value(match.group(0))
        if value is None or value in seen:
            continue
        seen.add(value)
        colors.append(ColorEntry(name=f"Color {len(colors) + 1}", hex=value))
    return colors


def _mask_spans(text: str, spans: Iterable[tuple[int, int]]) -> str:
    chars = list(text)
    for start, end in spans:
        for index in range(start, min(end, len(chars))):
            chars[index] = " "
    return "".join(chars)


def _variable_entries(colors: Iterable[ColorEntry]) -> list[tuple[str, ColorEntry]]:
    entries: list[tuple[str, ColorEntry]] = []
    used: set[str] = set()
    for index, color in enumerate(colors, start=1):
        base = slugify(color.name, f"color-{index}")
        name = base
        suffix = 2
        while name in used:
            name = f"{base}-{suffix}"
            suffix += 1
        used.add(name)
        entries.append((name, color))
    return entries


def _safe_comment(value: str) -> str:
    return value.replace("*/", "* /").replace("\r", " ").replace("\n", " ")


# ------------------------------------------------------------------------ CSS


def _parse_css(text: str) -> list[ColorEntry]:
    text = _CSS_BLOCK_COMMENT_RE.sub(" ", text)
    text = _CSS_LINE_COMMENT_RE.sub("", text)

    colors: list[ColorEntry] = []
    used_names: set[str] = set()
    spans: list[tuple[int, int]] = []
    for match in _VAR_DECL_RE.finditer(text):
        value = _token_color(match.group("value"))
        if value is None:
            continue
        name = _humanize(match.group("name")) or f"Color {len(colors) + 1}"
        colors.append(
            ColorEntry(name=_unique_name(name, used_names), hex=value)
        )
        spans.append(match.span())

    present = {color.hex for color in colors}
    for match in _COLOR_TOKEN_RE.finditer(_mask_spans(text, spans)):
        value = _color_value(match.group(0))
        if value is None or value in present:
            continue
        present.add(value)
        colors.append(ColorEntry(name=f"Color {len(colors) + 1}", hex=value))
    return colors


def _to_css(project: Project) -> str:
    lines = [f"/* {_safe_comment(project.name)} */", ":root {"]
    for name, color in _variable_entries(project.colors):
        lines.append(f"  --{name}: {color.hex};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _to_scss(project: Project) -> str:
    lines = [f"// {_safe_comment(project.name)}"]
    for name, color in _variable_entries(project.colors):
        lines.append(f"${name}: {color.hex};")
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------- JSON


def _parse_json(text: str) -> list[ColorEntry]:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(raw, (dict, list)):
        raise ValueError("JSON palette must be an object or an array")
    if isinstance(raw, dict):
        palette_format = raw.get("format")
        if isinstance(palette_format, str) and palette_format.startswith(
            "vcolor.palette"
        ):
            raise ValueError(
                "vcolor.palette files are no longer supported; "
                "use a standard palette format instead"
            )
        for key in ("colors", "palette", "swatches", "entries"):
            if key in raw and isinstance(raw[key], (dict, list)):
                return _parse_json_items(raw[key])
    return _parse_json_items(raw)


def _parse_json_items(items: Any) -> list[ColorEntry]:
    colors: list[ColorEntry] = []
    if isinstance(items, dict):
        used_names: set[str] = set()
        for key, value in items.items():
            key_text = str(key)
            if _token_color(key_text) and isinstance(value, str):
                value_text = _color_value(value)
                if value_text is None:
                    hex_value = _token_color(key_text)
                    name = value
                else:
                    hex_value = value_text
                    name = key_text
            else:
                hex_value = _json_color(value)
                name = _json_name(value) or key_text
            if hex_value is None:
                continue
            name = name if name and not name.isdigit() else ""
            colors.append(
                ColorEntry(
                    name=_unique_name(name or f"Color {len(colors) + 1}", used_names),
                    hex=hex_value,
                )
            )
        return colors

    if not isinstance(items, list):
        return colors
    used_names: set[str] = set()
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            hex_value = _json_color(item)
            name = _json_name(item)
        else:
            hex_value = _json_color(item)
            name = ""
        if hex_value is None:
            continue
        colors.append(
            ColorEntry(
                name=_unique_name(name or f"Color {index}", used_names),
                hex=hex_value,
            )
        )
    return colors


def _json_name(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    for key in ("name", "title", "label"):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def _json_color(value: Any) -> str | None:
    if isinstance(value, str):
        return _color_value(value)
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        if all(isinstance(part, (int, float)) for part in value[:3]):
            return rgb_to_hex(
                RGB(round(value[0]), round(value[1]), round(value[2]))
            )
        return None
    if not isinstance(value, dict):
        return None
    for key in ("hex", "color", "value", "hexcode"):
        candidate = value.get(key)
        if isinstance(candidate, str):
            color = _color_value(candidate)
            if color is not None:
                return color
    rgb = value.get("rgb")
    if isinstance(rgb, (list, tuple)) and len(rgb) >= 3:
        return _json_color(list(rgb[:3]))
    if all(key in value for key in ("r", "g", "b")):
        try:
            return rgb_to_hex(
                RGB(int(value["r"]), int(value["g"]), int(value["b"]))
            )
        except (TypeError, ValueError):
            return None
    return None


def _to_json(project: Project) -> str:
    payload = [{"name": color.name, "hex": color.hex} for color in project.colors]
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


# ------------------------------------------------------------------ CSV / text


def _parse_csv(text: str) -> list[ColorEntry]:
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return _parse_text(text)
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        return []
    if _is_header_row(rows[0]):
        rows = rows[1:]

    colors: list[ColorEntry] = []
    used_names: set[str] = set()
    seen: set[str] = set()
    for row in rows:
        entries: list[tuple[str, str]] = []
        labels: list[str] = []
        for cell in row:
            cell = cell.strip()
            if not cell:
                continue
            value = _token_color(cell) or _bare_color_value(cell)
            if value is not None:
                entries.append(("", value))
                continue
            match = _COLOR_TOKEN_RE.search(cell)
            if match is not None:
                value = _color_value(match.group(0))
                if value is not None:
                    label = (cell[: match.start()] + " " + cell[match.end() :]).strip(
                        " \t,:;|"
                    )
                    entries.append((label, value))
                    continue
            labels.append(cell)

        if not entries:
            continue
        if len(entries) == 1:
            label = entries[0][0] or (labels[0] if labels else "")
            entries = [(label, entries[0][1])]

        for label, value in entries:
            if value in seen:
                continue
            seen.add(value)
            name = _humanize(label) if label else f"Color {len(colors) + 1}"
            colors.append(
                ColorEntry(name=_unique_name(name, used_names), hex=value)
            )
    return colors


def _is_header_row(row: list[str]) -> bool:
    cells = [cell.strip().casefold() for cell in row if cell.strip()]
    if not cells:
        return False
    if any(_token_color(cell) or _bare_color_value(cell) for cell in cells):
        return False
    return all(cell in _HEADER_WORDS or cell.isdigit() for cell in cells)


def _parse_text(text: str) -> list[ColorEntry]:
    if "coolors.co/" in text.casefold():
        colors = _parse_coolors(text)
        if colors:
            return colors
    if _VAR_DECL_RE.search(text):
        colors = _parse_css(text)
        if colors:
            return colors

    colors: list[ColorEntry] = []
    used_names: set[str] = set()
    seen: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("//", ";")):
            continue
        line = re.sub(r"^#\s+", "", line)
        matches = list(_COLOR_TOKEN_RE.finditer(line))
        if not matches:
            bare = list(_BARE_HEX_RE.finditer(line))
            remainder = _BARE_HEX_RE.sub("", line)
            if bare and not remainder.strip(" \t,;|"):
                matches = bare
        if not matches:
            continue
        if len(matches) == 1:
            match = matches[0]
            value = _color_value(match.group(0))
            if value is None:
                continue
            label = (line[: match.start()] + " " + line[match.end() :]).strip(
                " \t,-—:|"
            )
            if label and value not in seen:
                seen.add(value)
                colors.append(
                    ColorEntry(name=_unique_name(_humanize(label), used_names), hex=value)
                )
                continue
        for match in matches:
            value = _color_value(match.group(0))
            if value is None or value in seen:
                continue
            seen.add(value)
            colors.append(
                ColorEntry(
                    name=_unique_name(f"Color {len(colors) + 1}", used_names),
                    hex=value,
                )
            )
    return colors


def _parse_coolors(text: str) -> list[ColorEntry]:
    colors: list[ColorEntry] = []
    seen: set[str] = set()
    for match in _COOLORS_URL_RE.finditer(text):
        for index, token in enumerate(match.group("tokens").split("-"), start=1):
            if not re.fullmatch(r"[0-9a-fA-F]{3}|[0-9a-fA-F]{6}", token):
                continue
            value = normalize_hex(token)
            if value in seen:
                continue
            seen.add(value)
            colors.append(ColorEntry(name=f"Color {len(colors) + 1}", hex=value))
    return colors


def _to_csv(project: Project) -> str:
    return ",".join(color.hex.lstrip("#") for color in project.colors) + "\n"


def _to_txt(project: Project) -> str:
    lines: list[str] = []
    for color in project.colors:
        if color.name and not color.name.startswith("Color "):
            lines.append(f"{color.hex}\t{color.name}")
        else:
            lines.append(color.hex)
    return "\n".join(lines) + ("\n" if lines else "")


def _to_coolors(project: Project) -> str:
    tokens = "-".join(color.hex.lstrip("#") for color in project.colors)
    return f"https://coolors.co/{tokens}\n"


# ------------------------------------------------------------------------ XML


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _element_name(element: ET.Element) -> str:
    for key in ("name", "aria-label", "data-name", "title", "id"):
        value = element.get(key)
        if value and value.strip():
            return _humanize(value)
    for child in element:
        if (
            _local_name(child.tag).casefold() in ("title", "name", "label")
            and child.text
        ):
            return _humanize(child.text)
    return ""


def _parse_xml(text: str) -> list[ColorEntry]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML: {exc}") from exc

    colors: list[ColorEntry] = []
    used_names: set[str] = set()
    seen: set[str] = set()
    for element in root.iter():
        name = _element_name(element)
        values: list[str] = []
        for key, value in element.attrib.items():
            key_lower = key.casefold()
            if key_lower in ("hex", "color", "rgb", "value"):
                color = _color_value(value)
                if color is not None:
                    values.append(color)
            elif key_lower in ("r", "g", "b"):
                continue
            else:
                values.extend(
                    color
                    for color in (
                        _color_value(match.group(0))
                        for match in _COLOR_TOKEN_RE.finditer(value)
                    )
                    if color is not None
                )
        if all(key in element.attrib for key in ("r", "g", "b")):
            try:
                values.append(
                    rgb_to_hex(
                        RGB(
                            int(element.attrib["r"]),
                            int(element.attrib["g"]),
                            int(element.attrib["b"]),
                        )
                    )
                )
            except ValueError:
                pass
        texts = [element.text or ""]
        texts.extend(child.tail or "" for child in element)
        for text in texts:
            values.extend(
                color
                for color in (
                    _color_value(match.group(0))
                    for match in _COLOR_TOKEN_RE.finditer(text)
                )
                if color is not None
            )
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            colors.append(
                ColorEntry(
                    name=_unique_name(
                        name or f"Color {len(colors) + 1}", used_names
                    ),
                    hex=value,
                )
            )
    return colors or _scan_colors(text)


def _parse_svg(text: str) -> list[ColorEntry]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return _scan_colors(text)

    shape_tags = {
        "rect",
        "circle",
        "ellipse",
        "path",
        "polygon",
        "polyline",
        "line",
        "stop",
        "use",
        "g",
    }
    color_attrs = ("fill", "stroke", "stop-color", "color", "flood-color", "lighting-color")
    colors: list[ColorEntry] = []
    used_names: set[str] = set()
    seen: set[str] = set()
    for element in root.iter():
        tag = _local_name(element.tag).casefold()
        if tag == "style" and element.text:
            for match in _COLOR_TOKEN_RE.finditer(element.text):
                value = _color_value(match.group(0))
                if value is None or value in seen:
                    continue
                seen.add(value)
                colors.append(
                    ColorEntry(
                        name=_unique_name(f"Color {len(colors) + 1}", used_names),
                        hex=value,
                    )
                )
            continue
        if tag not in shape_tags:
            continue
        name = _element_name(element)
        values: list[str] = []
        for attr in color_attrs:
            value = element.get(attr)
            if value:
                color = _color_value(value)
                if color is not None:
                    values.append(color)
        style = element.get("style")
        if style:
            values.extend(
                color
                for color in (
                    _color_value(match.group(0))
                    for match in _COLOR_TOKEN_RE.finditer(style)
                )
                if color is not None
            )
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            colors.append(
                ColorEntry(
                    name=_unique_name(
                        name or f"Color {len(colors) + 1}", used_names
                    ),
                    hex=value,
                )
            )
    return colors or _scan_colors(text)


def _to_xml(project: Project) -> str:
    root = ET.Element("palette")
    for color in project.colors:
        rgb = hex_to_rgb(color.hex)
        ET.SubElement(
            root,
            "color",
            {
                "name": color.name,
                "hex": color.hex.lstrip("#"),
                "r": str(rgb.r),
                "g": str(rgb.g),
                "b": str(rgb.b),
            },
        )
    ET.indent(root, space="  ")
    body = ET.tostring(root, encoding="unicode")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + body + "\n"


# ------------------------------------------------------------------------ SVG


def _ellipsize(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _to_svg(project: Project) -> str:
    swatch_width = 128
    swatch_height = 156
    count = max(1, len(project.colors))
    root = ET.Element(
        "svg",
        {
            "xmlns": _SVG_NS,
            "width": str(swatch_width * count),
            "height": str(swatch_height),
            "viewBox": f"0 0 {swatch_width * count} {swatch_height}",
        },
    )
    ET.SubElement(root, "title").text = project.name
    for index, color in enumerate(project.colors):
        x = index * swatch_width
        rect = ET.SubElement(
            root,
            "rect",
            {
                "x": str(x),
                "y": "0",
                "width": str(swatch_width),
                "height": str(swatch_height),
                "fill": color.hex,
                "data-name": color.name,
            },
        )
        ET.SubElement(rect, "title").text = f"{color.name} {color.hex}"
        text_color = readable_text_color(color.hex)
        name = ET.SubElement(
            root,
            "text",
            {
                "x": str(x + swatch_width // 2),
                "y": str(swatch_height - 42),
                "fill": text_color,
                "font-family": "sans-serif",
                "font-size": "12",
                "font-weight": "600",
                "text-anchor": "middle",
            },
        )
        name.text = _ellipsize(color.name, 18)
        value = ET.SubElement(
            root,
            "text",
            {
                "x": str(x + swatch_width // 2),
                "y": str(swatch_height - 22),
                "fill": text_color,
                "font-family": "monospace",
                "font-size": "11",
                "text-anchor": "middle",
            },
        )
        value.text = color.hex
    ET.indent(root, space="  ")
    body = ET.tostring(root, encoding="unicode")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + body + "\n"


# ------------------------------------------------------------------------ ASE


def _ase_name_field(name: str) -> bytes:
    name = name.strip()[:255]
    encoded = name.encode("utf-16-be")
    units = len(encoded) // 2 + 1
    return struct.pack(">H", units) + encoded + b"\x00\x00"


def _read_ase_name(block: bytes, offset: int = 0) -> tuple[str, int]:
    if offset + 2 > len(block):
        return "", offset
    units = struct.unpack_from(">H", block, offset)[0]
    offset += 2
    length = units * 2
    if offset + length > len(block):
        return "", offset
    raw = block[offset : offset + length]
    offset += length
    return (
        raw.decode("utf-16-be", "replace").rstrip("\x00").strip(),
        offset,
    )


def _parse_ase(data: bytes) -> list[ColorEntry]:
    if not data.startswith(b"ASEF"):
        raise ValueError("Not an Adobe Swatch Exchange file")
    if len(data) < 12:
        raise ValueError("ASE file is truncated")
    count = struct.unpack_from(">I", data, 8)[0]
    offset = 12
    colors: list[ColorEntry] = []
    for _ in range(count):
        if offset + 6 > len(data):
            break
        block_type, length = struct.unpack_from(">HI", data, offset)
        offset += 6
        if offset + length > len(data):
            break
        block = data[offset : offset + length]
        offset += length
        if block_type != 0x0001:
            continue

        name, position = _read_ase_name(block)
        if position + 4 > len(block):
            continue
        model = block[position : position + 4].decode("ascii", "replace")
        position += 4
        values: tuple[float, ...]
        if model == "RGB ":
            if position + 12 > len(block):
                continue
            values = struct.unpack_from(">fff", block, position)
            rgb = RGB(*(round(value * 255.0) for value in values))
        elif model == "CMYK":
            if position + 16 > len(block):
                continue
            values = struct.unpack_from(">ffff", block, position)
            rgb = cmyk_to_rgb(CMYK(*values))
        elif model == "LAB ":
            if position + 12 > len(block):
                continue
            values = struct.unpack_from(">fff", block, position)
            rgb = lab_to_rgb(LAB(*values))
        elif model == "Gray":
            if position + 4 > len(block):
                continue
            value = struct.unpack_from(">f", block, position)[0]
            channel = round(value * 255.0)
            rgb = RGB(channel, channel, channel)
        else:
            continue
        colors.append(
            ColorEntry(
                name=name or f"Color {len(colors) + 1}",
                hex=rgb_to_hex(rgb),
            )
        )
    return colors


def _to_ase(project: Project) -> bytes:
    blocks: list[bytes] = []
    group = _ase_name_field(project.name or "vColor")
    blocks.append(struct.pack(">HI", 0xC001, len(group)) + group)
    for color in project.colors:
        rgb = hex_to_rgb(color.hex)
        data = (
            _ase_name_field(color.name or "Color")
            + b"RGB "
            + struct.pack(">fff", rgb.r / 255.0, rgb.g / 255.0, rgb.b / 255.0)
            + struct.pack(">H", 2)
        )
        blocks.append(struct.pack(">HI", 0x0001, len(data)) + data)
    blocks.append(struct.pack(">HI", 0xC002, 0))
    return (
        b"ASEF"
        + struct.pack(">HHI", 1, 0, len(blocks))
        + b"".join(blocks)
    )


# ------------------------------------------------------------------------ GPL


def _parse_gpl(text: str) -> list[ColorEntry]:
    colors: list[ColorEntry] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.casefold().startswith(
            ("gimp", "name:", "columns:")
        ):
            continue
        parts = line.split(None, 3)
        if len(parts) < 3:
            continue
        try:
            r, g, b = (int(part) for part in parts[:3])
        except ValueError:
            continue
        if not all(0 <= channel <= 255 for channel in (r, g, b)):
            continue
        name = parts[3].strip() if len(parts) > 3 else f"Color {len(colors) + 1}"
        colors.append(ColorEntry(name=name, hex=f"#{r:02x}{g:02x}{b:02x}"))
    return colors


def _to_gpl(project: Project) -> str:
    lines = [
        "GIMP Palette",
        f"Name: {project.name}",
        "Columns: 4",
        "#",
    ]
    for color in project.colors:
        raw = color.hex.lstrip("#")
        r, g, b = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
        lines.append(f"{r:3d} {g:3d} {b:3d}\t{color.name}")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------- Tailwind


def _parse_tailwind(text: str) -> list[ColorEntry]:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        raw = None
    if isinstance(raw, (dict, list)):
        return _parse_json_items(raw)

    match = re.search(r"\bcolors\s*:\s*\{", text)
    start = match.end() - 1 if match else text.find("{")
    if start >= 0:
        try:
            value, _ = _parse_js_value(text, start)
        except ValueError:
            value = None
        if isinstance(value, dict):
            colors: list[ColorEntry] = []
            used_names: set[str] = set()
            _flatten_js_colors(value, [], colors, used_names)
            if colors:
                return colors
    return _scan_colors(text)


def _parse_js_value(text: str, offset: int) -> tuple[Any, int]:
    offset = _skip_js_space(text, offset)
    if offset >= len(text):
        raise ValueError("Unexpected end of JavaScript")
    char = text[offset]
    if char == "{":
        return _parse_js_object(text, offset)
    if char in "\"'`":
        return _parse_js_string(text, offset)
    if char == "[":
        return _parse_js_array(text, offset)
    end = offset
    while end < len(text) and text[end] not in ",}]\n":
        end += 1
    return text[offset:end].strip(), end


def _parse_js_object(text: str, offset: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    offset += 1
    while True:
        offset = _skip_js_space(text, offset)
        if offset >= len(text):
            raise ValueError("Unterminated JavaScript object")
        if text[offset] == "}":
            return result, offset + 1
        if text[offset] == ",":
            offset += 1
            continue
        if text[offset] in "\"'`":
            key, offset = _parse_js_string(text, offset)
        else:
            start = offset
            while offset < len(text) and text[offset] not in ":,}":
                offset += 1
            key = text[start:offset].strip()
        offset = _skip_js_space(text, offset)
        if offset >= len(text) or text[offset] != ":":
            raise ValueError("Expected ':' in JavaScript object")
        value, offset = _parse_js_value(text, offset + 1)
        if key:
            result[key] = value


def _parse_js_array(text: str, offset: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    offset += 1
    while True:
        offset = _skip_js_space(text, offset)
        if offset >= len(text):
            raise ValueError("Unterminated JavaScript array")
        if text[offset] == "]":
            return result, offset + 1
        if text[offset] == ",":
            offset += 1
            continue
        value, offset = _parse_js_value(text, offset)
        result.append(value)


def _parse_js_string(text: str, offset: int) -> tuple[str, int]:
    quote = text[offset]
    offset += 1
    chars: list[str] = []
    while offset < len(text):
        char = text[offset]
        if char == "\\" and offset + 1 < len(text):
            chars.append(text[offset + 1])
            offset += 2
            continue
        if char == quote:
            return "".join(chars), offset + 1
        chars.append(char)
        offset += 1
    raise ValueError("Unterminated JavaScript string")


def _skip_js_space(text: str, offset: int) -> int:
    while offset < len(text):
        if text[offset].isspace():
            offset += 1
            continue
        if text.startswith("//", offset):
            end = text.find("\n", offset)
            offset = len(text) if end < 0 else end + 1
            continue
        if text.startswith("/*", offset):
            end = text.find("*/", offset + 2)
            offset = len(text) if end < 0 else end + 2
            continue
        break
    return offset


def _flatten_js_colors(
    value: dict[str, Any],
    path: list[str],
    colors: list[ColorEntry],
    used_names: set[str],
) -> None:
    for key, child in value.items():
        child_path = [*path, str(key)]
        if isinstance(child, dict):
            _flatten_js_colors(child, child_path, colors, used_names)
            continue
        color = _json_color(child)
        if color is None:
            continue
        name = " ".join(
            part if part.isdigit() else _humanize(part) for part in child_path
        )
        colors.append(
            ColorEntry(
                name=_unique_name(name or f"Color {len(colors) + 1}", used_names),
                hex=color,
            )
        )


def _to_tailwind(project: Project) -> str:
    entries = []
    for name, color in _variable_entries(project.colors):
        entries.append(f'        "{name}": "{color.hex}"')
    body = ",\n".join(entries)
    lines = [
        "/** @type {import('tailwindcss').Config} */",
        "module.exports = {",
        "  theme: {",
        "    extend: {",
        "      colors: {",
    ]
    if body:
        lines.append(body)
    lines.extend(
        [
            "      },",
            "    },",
            "  },",
            "};",
        ]
    )
    return "\n".join(lines) + "\n"
