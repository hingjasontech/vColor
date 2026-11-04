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
