from __future__ import annotations

import unittest

from vcolor.color_utils import (
    ColorError,
    contrast_grade,
    contrast_ratio,
    format_color,
    hex_to_rgb,
    hsl_to_rgb,
    normalize_hex,
    oklch_to_rgb,
    rgb_to_hex,
    rgb_to_hsl,
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


class ConversionTests(unittest.TestCase):
    def test_hsl_round_trip(self) -> None:
        for value in ("#0a84ff", "#123123", "#f05252", "#a78bfa"):
            rgb = hex_to_rgb(value)
            self.assertEqual(rgb_to_hex(hsl_to_rgb(rgb_to_hsl(rgb))), value)

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
