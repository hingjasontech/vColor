from __future__ import annotations

import unittest

from vcolor.color_utils import (
    ColorError,
    cmyk_to_rgb,
    contrast_grade,
    contrast_ratio,
    format_color,
    hex_to_rgb,
    hsl_to_rgb,
    hsb_to_rgb,
    lab_to_rgb,
    normalize_hex,
    oklch_to_rgb,
    parse_color,
    rgb_to_cmyk,
    rgb_to_hex,
    rgb_to_hsl,
    rgb_to_hsb,
    rgb_to_lab,
    rgb_to_oklch,
    srgb_to_display_p3,
)


class HexTests(unittest.TestCase):
    def test_normalizes_short_and_long_hex(self) -> None:
        self.assertEqual(normalize_hex("#ABC"), "#aabbcc")
        self.assertEqual(normalize_hex("0A84FF"), "#0a84ff")

    def test_rejects_invalid_values(self) -> None:
        for value in ("", "#12", "blue", "#gggggg", "#1234567"):
            with self.subTest(value=value), self.assertRaises(ColorError):
                normalize_hex(value)

    def test_rgb_round_trip(self) -> None:
        for value in ("#000000", "#ffffff", "#0a84ff", "#123123"):
            self.assertEqual(rgb_to_hex(hex_to_rgb(value)), value)


class ParseColorTests(unittest.TestCase):
    def test_hex_variants(self) -> None:
        self.assertEqual(parse_color("#ABC"), "#aabbcc")
        self.assertEqual(parse_color("0a84ff"), "#0a84ff")
        self.assertEqual(parse_color("#0a84ffcc"), "#0a84ff")
        self.assertEqual(parse_color("#abc8"), "#aabbcc")

    def test_rgb_notation(self) -> None:
        self.assertEqual(parse_color("rgb(10, 132, 255)"), "#0a84ff")
        self.assertEqual(parse_color("rgba(10 132 255 / 0.5)"), "#0a84ff")
        self.assertEqual(parse_color("rgb(100%, 0%, 0%)"), "#ff0000")

    def test_hsl_notation(self) -> None:
        self.assertEqual(parse_color("hsl(0, 100%, 50%)"), "#ff0000")
        self.assertEqual(parse_color("hsl(120deg 100% 50%)"), "#00ff00")
        self.assertEqual(parse_color("hsl(240, 100, 50)"), "#0000ff")
        self.assertEqual(parse_color("hsla(210deg 100% 50% / 0.5)"), "#0080ff")

    def test_oklch_notation(self) -> None:
        for value in ("#0a84ff", "#123123", "#f05252", "#a78bfa"):
            text = format_color(value, "OKLCH")
            parsed = hex_to_rgb(parse_color(text))
            expected = hex_to_rgb(value)
            for first, second in zip(
                parsed.as_tuple(), expected.as_tuple(), strict=True
            ):
                self.assertLessEqual(abs(first - second), 2)

    def test_hsb_notation(self) -> None:
        self.assertEqual(parse_color("hsb(120, 100%, 100%)"), "#00ff00")
        self.assertEqual(parse_color("hsv(0, 100%, 50%)"), "#800000")

    def test_cmyk_notation(self) -> None:
        self.assertEqual(parse_color("cmyk(0%, 100%, 100%, 0%)"), "#ff0000")
        self.assertEqual(
            parse_color("device-cmyk(100%, 0%, 0%, 0%)"), "#00ffff"
        )

    def test_lab_notation(self) -> None:
        for value in ("#0a84ff", "#123123", "#f05252", "#a78bfa"):
            lab = rgb_to_lab(hex_to_rgb(value))
            parsed = hex_to_rgb(
                parse_color(f"lab({lab.l:.4f} {lab.a:.4f} {lab.b:.4f})")
            )
            for first, second in zip(
                parsed.as_tuple(), hex_to_rgb(value).as_tuple(), strict=True
            ):
                self.assertLessEqual(abs(first - second), 2)

    def test_named_colors(self) -> None:
        self.assertEqual(parse_color("Red"), "#ff0000")
        self.assertEqual(parse_color("steelblue"), "#4682b4")
        self.assertEqual(parse_color("RebeccaPurple"), "#663399")

    def test_rejects_invalid_values(self) -> None:
        for value in (
            "",
            "notacolor",
            "rgb(1, 2)",
            "hsl(x, 50%, 50%)",
            "oklch(0.5 0.1)",
        ):
            with self.subTest(value=value), self.assertRaises(ColorError):
                parse_color(value)


class ConversionTests(unittest.TestCase):
    def test_hsl_round_trip(self) -> None:
        for value in ("#0a84ff", "#123123", "#f05252", "#a78bfa"):
            rgb = hex_to_rgb(value)
            self.assertEqual(rgb_to_hex(hsl_to_rgb(rgb_to_hsl(rgb))), value)

    def test_hsb_round_trip(self) -> None:
        for value in ("#0a84ff", "#123123", "#f05252", "#a78bfa"):
            rgb = hex_to_rgb(value)
            self.assertEqual(rgb_to_hex(hsb_to_rgb(rgb_to_hsb(rgb))), value)

    def test_cmyk_round_trip(self) -> None:
        for value in ("#000000", "#ffffff", "#0a84ff", "#123123"):
            rgb = hex_to_rgb(value)
            self.assertEqual(rgb_to_hex(cmyk_to_rgb(rgb_to_cmyk(rgb))), value)

    def test_lab_round_trip_is_close(self) -> None:
        for value in ("#000000", "#ffffff", "#0a84ff", "#123123", "#f05252"):
            rgb = hex_to_rgb(value)
            converted = lab_to_rgb(rgb_to_lab(rgb))
            for first, second in zip(
                rgb.as_tuple(), converted.as_tuple(), strict=True
            ):
                self.assertLessEqual(abs(first - second), 1)

    def test_oklch_round_trip_is_close(self) -> None:
        for value in ("#0a84ff", "#123123", "#f05252", "#a78bfa"):
            rgb = hex_to_rgb(value)
            converted = oklch_to_rgb(rgb_to_oklch(rgb))
            for first, second in zip(rgb.as_tuple(), converted.as_tuple(), strict=True):
                self.assertLessEqual(abs(first - second), 1)

    def test_formatting(self) -> None:
        self.assertEqual(format_color("#0a84ff", "HEX"), "#0a84ff")
        self.assertEqual(format_color("#0a84ff", "RGB"), "rgb(10, 132, 255)")
        self.assertIn("hsl(", format_color("#0a84ff", "HSL"))
        self.assertIn("oklch(", format_color("#0a84ff", "OKLCH"))

    def test_contrast(self) -> None:
        self.assertAlmostEqual(contrast_ratio("#000000", "#ffffff"), 21.0, places=2)
        self.assertEqual(contrast_grade(21.0), "AAA")
        self.assertEqual(contrast_grade(1.2), "Fail")

    def test_display_p3_is_reported(self) -> None:
        self.assertRegex(srgb_to_display_p3("#0a84ff"), r"^#[0-9a-f]{6}( \*)?$")


if __name__ == "__main__":
    unittest.main()
