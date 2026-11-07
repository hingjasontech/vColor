"""Color conversion helpers used by the UI and by import/export."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
DISPLAY_FORMATS = ("HEX", "RGB", "HSL", "OKLCH")


class ColorError(ValueError):
    """Raised when a color string cannot be parsed."""


@dataclass(frozen=True, slots=True)
class RGB:
    r: int
    g: int
    b: int

    @property
    def clamped(self) -> "RGB":
        return RGB(
            max(0, min(255, self.r)),
            max(0, min(255, self.g)),
            max(0, min(255, self.b)),
        )

    def as_tuple(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)


@dataclass(frozen=True, slots=True)
class HSL:
    h: float
    s: float
    l: float


@dataclass(frozen=True, slots=True)
class OKLCH:
    l: float
    c: float
    h: float


def normalize_hex(value: str) -> str:
    """Return a lowercase ``#rrggbb`` string, or raise :class:`ColorError`."""
    match = HEX_RE.match(value.strip())
    if not match:
        raise ColorError(f"Not a valid hex color: {value!r}")
    raw = match.group(1).lower()
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    return f"#{raw}"


def is_hex(value: str) -> bool:
    try:
        normalize_hex(value)
    except ColorError:
        return False
    return True


CSS_NAMED_COLORS = {
    "aliceblue": "#f0f8ff",
    "antiquewhite": "#faebd7",
    "aqua": "#00ffff",
    "aquamarine": "#7fffd4",
    "azure": "#f0ffff",
    "beige": "#f5f5dc",
    "bisque": "#ffe4c4",
    "black": "#000000",
    "blanchedalmond": "#ffebcd",
    "blue": "#0000ff",
    "blueviolet": "#8a2be2",
    "brown": "#a52a2a",
    "burlywood": "#deb887",
    "cadetblue": "#5f9ea0",
    "chartreuse": "#7fff00",
    "chocolate": "#d2691e",
    "coral": "#ff7f50",
    "cornflowerblue": "#6495ed",
    "cornsilk": "#fff8dc",
    "crimson": "#dc143c",
    "cyan": "#00ffff",
    "darkblue": "#00008b",
    "darkcyan": "#008b8b",
    "darkgoldenrod": "#b8860b",
    "darkgray": "#a9a9a9",
    "darkgreen": "#006400",
    "darkgrey": "#a9a9a9",
    "darkkhaki": "#bdb76b",
    "darkmagenta": "#8b008b",
    "darkolivegreen": "#556b2f",
    "darkorange": "#ff8c00",
    "darkorchid": "#9932cc",
    "darkred": "#8b0000",
    "darksalmon": "#e9967a",
    "darkseagreen": "#8fbc8f",
    "darkslateblue": "#483d8b",
    "darkslategray": "#2f4f4f",
    "darkslategrey": "#2f4f4f",
    "darkturquoise": "#00ced1",
    "darkviolet": "#9400d3",
    "deeppink": "#ff1493",
    "deepskyblue": "#00bfff",
    "dimgray": "#696969",
    "dimgrey": "#696969",
    "dodgerblue": "#1e90ff",
    "firebrick": "#b22222",
    "floralwhite": "#fffaf0",
    "forestgreen": "#228b22",
    "fuchsia": "#ff00ff",
    "gainsboro": "#dcdcdc",
    "ghostwhite": "#f8f8ff",
    "gold": "#ffd700",
    "goldenrod": "#daa520",
    "gray": "#808080",
    "green": "#008000",
    "greenyellow": "#adff2f",
    "grey": "#808080",
    "honeydew": "#f0fff0",
    "hotpink": "#ff69b4",
    "indianred": "#cd5c5c",
    "indigo": "#4b0082",
    "ivory": "#fffff0",
    "khaki": "#f0e68c",
    "lavender": "#e6e6fa",
    "lavenderblush": "#fff0f5",
    "lawngreen": "#7cfc00",
    "lemonchiffon": "#fffacd",
    "lightblue": "#add8e6",
    "lightcoral": "#f08080",
    "lightcyan": "#e0ffff",
    "lightgoldenrodyellow": "#fafad2",
    "lightgray": "#d3d3d3",
    "lightgreen": "#90ee90",
    "lightgrey": "#d3d3d3",
    "lightpink": "#ffb6c1",
    "lightsalmon": "#ffa07a",
    "lightseagreen": "#20b2aa",
    "lightskyblue": "#87cefa",
    "lightslategray": "#778899",
    "lightslategrey": "#778899",
    "lightsteelblue": "#b0c4de",
    "lightyellow": "#ffffe0",
    "lime": "#00ff00",
    "limegreen": "#32cd32",
    "linen": "#faf0e6",
    "magenta": "#ff00ff",
    "maroon": "#800000",
    "mediumaquamarine": "#66cdaa",
    "mediumblue": "#0000cd",
    "mediumorchid": "#ba55d3",
    "mediumpurple": "#9370db",
    "mediumseagreen": "#3cb371",
    "mediumslateblue": "#7b68ee",
    "mediumspringgreen": "#00fa9a",
    "mediumturquoise": "#48d1cc",
    "mediumvioletred": "#c71585",
    "midnightblue": "#191970",
    "mintcream": "#f5fffa",
    "mistyrose": "#ffe4e1",
    "moccasin": "#ffe4b5",
    "navajowhite": "#ffdead",
    "navy": "#000080",
    "oldlace": "#fdf5e6",
    "olive": "#808000",
    "olivedrab": "#6b8e23",
    "orange": "#ffa500",
    "orangered": "#ff4500",
    "orchid": "#da70d6",
    "palegoldenrod": "#eee8aa",
    "palegreen": "#98fb98",
    "paleturquoise": "#afeeee",
    "palevioletred": "#db7093",
    "papayawhip": "#ffefd5",
    "peachpuff": "#ffdab9",
    "peru": "#cd853f",
    "pink": "#ffc0cb",
    "plum": "#dda0dd",
    "powderblue": "#b0e0e6",
    "purple": "#800080",
    "rebeccapurple": "#663399",
    "red": "#ff0000",
    "rosybrown": "#bc8f8f",
    "royalblue": "#4169e1",
    "saddlebrown": "#8b4513",
    "salmon": "#fa8072",
    "sandybrown": "#f4a460",
    "seagreen": "#2e8b57",
    "seashell": "#fff5ee",
    "sienna": "#a0522d",
    "silver": "#c0c0c0",
    "skyblue": "#87ceeb",
    "slateblue": "#6a5acd",
    "slategray": "#708090",
    "slategrey": "#708090",
    "snow": "#fffafa",
    "springgreen": "#00ff7f",
    "steelblue": "#4682b4",
    "tan": "#d2b48c",
    "teal": "#008080",
    "thistle": "#d8bfd8",
    "tomato": "#ff6347",
    "turquoise": "#40e0d0",
    "violet": "#ee82ee",
    "wheat": "#f5deb3",
    "white": "#ffffff",
    "whitesmoke": "#f5f5f5",
    "yellow": "#ffff00",
    "yellowgreen": "#9acd32",
}

_FUNCTION_RE = re.compile(r"^(rgba?|hsla?|oklch)\(\s*(.*?)\s*\)$", re.IGNORECASE)


def parse_color(value: str) -> str:
    """Parse common CSS color notations and return ``#rrggbb``.

    Accepts hex (with or without ``#``, including alpha variants), ``rgb()``,
    ``hsl()``, ``oklch()``, and CSS color names. Alpha values are ignored.
    """
    text = value.strip()
    if not text:
        raise ColorError("Enter a color value")

    match = _FUNCTION_RE.match(text)
    if match:
        function = match.group(1).lower()
        arguments = match.group(2)
        if function.startswith("rgb"):
            return rgb_to_hex(_parse_rgb_args(arguments))
        if function.startswith("hsl"):
            return rgb_to_hex(hsl_to_rgb(_parse_hsl_args(arguments)))
        return rgb_to_hex(oklch_to_rgb(_parse_oklch_args(arguments)))

    body = text.lstrip("#")
    if re.fullmatch(r"[0-9a-fA-F]{4}", body):
        body = body[:3]
    elif re.fullmatch(r"[0-9a-fA-F]{8}", body):
        body = body[:6]
    if re.fullmatch(r"[0-9a-fA-F]{3}|[0-9a-fA-F]{6}", body):
        return normalize_hex(f"#{body}")

    named = CSS_NAMED_COLORS.get(text.lower())
    if named is not None:
        return named

    raise ColorError(f"Unrecognized color: {value!r}")


def _split_components(arguments: str) -> list[str]:
    cleaned = arguments.replace(",", " ").replace("/", " ")
    parts = [part for part in cleaned.split() if part]
    if len(parts) < 3:
        raise ColorError(f"Expected three color components: {arguments!r}")
    return parts


def _parse_number(token: str) -> float:
    try:
        return float(token.rstrip("%"))
    except ValueError as exc:
        raise ColorError(f"Invalid color component: {token!r}") from exc


def _rgb_channel(token: str) -> int:
    value = _parse_number(token)
    if token.endswith("%"):
        value = value * 255.0 / 100.0
    return round(value)


def _parse_rgb_args(arguments: str) -> RGB:
    parts = _split_components(arguments)
    return RGB(*(_rgb_channel(part) for part in parts[:3])).clamped


def _parse_angle(token: str) -> float:
    text = token.lower()
    for suffix, factor in (
        ("deg", 1.0),
        ("grad", 0.9),
        ("turn", 360.0),
        ("rad", 180.0 / math.pi),
    ):
        if text.endswith(suffix):
            return float(text[: -len(suffix)]) * factor
    return _parse_number(text)


def _parse_percentage(token: str) -> float:
    value = _parse_number(token)
    if token.endswith("%") or value > 1.0:
        value /= 100.0
    return max(0.0, min(1.0, value))


def _parse_hsl_args(arguments: str) -> HSL:
    parts = _split_components(arguments)
    return HSL(
        _parse_angle(parts[0]),
        _parse_percentage(parts[1]),
        _parse_percentage(parts[2]),
    )


def _parse_oklch_args(arguments: str) -> OKLCH:
    parts = _split_components(arguments)
    lightness = _parse_number(parts[0])
    if parts[0].endswith("%") or lightness > 1.0:
        lightness /= 100.0
    chroma = _parse_number(parts[1])
    if parts[1].endswith("%"):
        chroma = chroma * 0.4 / 100.0
    hue = _parse_angle(parts[2])
    return OKLCH(max(0.0, min(1.0, lightness)), max(0.0, chroma), hue)


def hex_to_rgb(value: str) -> RGB:
    raw = normalize_hex(value)[1:]
    return RGB(int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))


def rgb_to_hex(rgb: RGB) -> str:
    rgb = rgb.clamped
    return f"#{rgb.r:02x}{rgb.g:02x}{rgb.b:02x}"


def rgb_to_hsl(rgb: RGB) -> HSL:
    r, g, b = (channel / 255.0 for channel in rgb.clamped.as_tuple())
    high = max(r, g, b)
    low = min(r, g, b)
    lightness = (high + low) / 2.0

    if high == low:
        return HSL(0.0, 0.0, lightness)

    delta = high - low
    saturation = delta / (2.0 - high - low) if lightness > 0.5 else delta / (high + low)

    if high == r:
        hue = ((g - b) / delta) % 6.0
    elif high == g:
        hue = (b - r) / delta + 2.0
    else:
        hue = (r - g) / delta + 4.0

    return HSL(hue * 60.0, saturation, lightness)


def hsl_to_rgb(hsl: HSL) -> RGB:
    hue = hsl.h % 360.0
    saturation = max(0.0, min(1.0, hsl.s))
    lightness = max(0.0, min(1.0, hsl.l))

    chroma = (1.0 - abs(2.0 * lightness - 1.0)) * saturation
    x = chroma * (1.0 - abs((hue / 60.0) % 2.0 - 1.0))
    m = lightness - chroma / 2.0

    if hue < 60:
        r, g, b = chroma, x, 0.0
    elif hue < 120:
        r, g, b = x, chroma, 0.0
    elif hue < 180:
        r, g, b = 0.0, chroma, x
    elif hue < 240:
        r, g, b = 0.0, x, chroma
    elif hue < 300:
        r, g, b = x, 0.0, chroma
    else:
        r, g, b = chroma, 0.0, x

    return RGB(
        round((r + m) * 255.0),
        round((g + m) * 255.0),
        round((b + m) * 255.0),
    ).clamped


def _srgb_to_linear(channel: int) -> float:
    value = channel / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(value: float) -> int:
    value = max(0.0, min(1.0, value))
    if value <= 0.0031308:
        encoded = value * 12.92
    else:
        encoded = 1.055 * (value ** (1.0 / 2.4)) - 0.055
    return round(max(0.0, min(1.0, encoded)) * 255.0)


def rgb_to_oklch(rgb: RGB) -> OKLCH:
    r, g, b = (_srgb_to_linear(channel) for channel in rgb.clamped.as_tuple())

    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

    l_ = _cbrt(l)
    m_ = _cbrt(m)
    s_ = _cbrt(s)

    lightness = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    bb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_

    chroma = math.hypot(a, bb)
    hue = math.degrees(math.atan2(bb, a)) % 360.0
    return OKLCH(lightness, chroma, hue)


def _cbrt(value: float) -> float:
    return math.copysign(abs(value) ** (1.0 / 3.0), value)


def oklch_to_rgb(oklch: OKLCH) -> RGB:
    chroma = max(0.0, oklch.c)
    hue = math.radians(oklch.h % 360.0)
    a = chroma * math.cos(hue)
    b = chroma * math.sin(hue)

    l_ = oklch.l + 0.3963377774 * a + 0.2158037573 * b
    m_ = oklch.l - 0.1055613458 * a - 0.0638541728 * b
    s_ = oklch.l - 0.0894841775 * a - 1.2914855480 * b

    l = l_**3
    m = m_**3
    s = s_**3

    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

    return RGB(
        _linear_to_srgb(r),
        _linear_to_srgb(g),
        _linear_to_srgb(bb),
    )


def format_color(value: str, mode: str = "HEX") -> str:
    """Format a color for display/copy in one of the supported notations."""
    normalized = normalize_hex(value)
    mode = mode.upper()
    rgb = hex_to_rgb(normalized)

    if mode == "HEX":
        return normalized
    if mode == "RGB":
        return f"rgb({rgb.r}, {rgb.g}, {rgb.b})"
    if mode == "HSL":
        hsl = rgb_to_hsl(rgb)
        return (
            f"hsl({round(hsl.h)}deg, {round(hsl.s * 100)}%, "
            f"{round(hsl.l * 100)}%)"
        )
    if mode == "OKLCH":
        oklch = rgb_to_oklch(rgb)
        return (
            f"oklch({oklch.l * 100:.1f}% {oklch.c:.3f} "
            f"{oklch.h:.1f})"
        )
    raise ColorError(f"Unknown color format: {mode}")


def relative_luminance(value: str) -> float:
    rgb = hex_to_rgb(value)
    r, g, b = (_srgb_to_linear(channel) for channel in rgb.as_tuple())
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(foreground: str, background: str) -> float:
    first = relative_luminance(foreground)
    second = relative_luminance(background)
    lighter = max(first, second)
    darker = min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def contrast_grade(ratio: float) -> str:
    if ratio >= 7.0:
        return "AAA"
    if ratio >= 4.5:
        return "AA"
    if ratio >= 3.0:
        return "AA Large"
    return "Fail"


def readable_text_color(background: str) -> str:
    """Pick near-black or near-white text with the strongest contrast."""
    if contrast_ratio("#111111", background) >= contrast_ratio("#ffffff", background):
        return "#111111"
    return "#ffffff"


def srgb_to_display_p3(value: str) -> str:
    """Approximate sRGB -> Display P3 conversion for informational display."""
    rgb = hex_to_rgb(value)
    r, g, b = (_srgb_to_linear(channel) for channel in rgb.as_tuple())

    x = 0.4123907993 * r + 0.3575843394 * g + 0.1804807884 * b
    y = 0.2126390059 * r + 0.7151686788 * g + 0.0721923154 * b
    z = 0.0193308187 * r + 0.1191947798 * g + 0.9505321522 * b

    p3_r = 2.4934969119 * x - 0.9313836179 * y - 0.4027107845 * z
    p3_g = -0.8294889696 * x + 1.7626640603 * y + 0.0236246858 * z
    p3_b = 0.0358458302 * x - 0.0761723893 * y + 0.9568845240 * z

    in_gamut = all(-0.0001 <= channel <= 1.0001 for channel in (p3_r, p3_g, p3_b))
    converted = RGB(
        _linear_to_srgb(p3_r),
        _linear_to_srgb(p3_g),
        _linear_to_srgb(p3_b),
    ).clamped
    suffix = "" if in_gamut else " *"
    return f"{rgb_to_hex(converted)}{suffix}"


def slugify(value: str, fallback: str = "color") -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return slug or fallback
