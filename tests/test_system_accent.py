from __future__ import annotations

import unittest
from unittest.mock import patch

from vcolor import system_accent
from vcolor.color_utils import DEFAULT_ACCENT


class SystemAccentTests(unittest.TestCase):
    def test_windows_colorization_is_converted_to_rgb(self) -> None:
        self.assertEqual(
            system_accent._windows_colorization(0xC46B69D6), "#6b69d6"
        )

    def test_windows_black_is_treated_as_missing(self) -> None:
        self.assertIsNone(system_accent._windows_colorization(0xFF000000))

    def test_macos_highlight_color_is_parsed(self) -> None:
        self.assertEqual(
            system_accent._macos_highlight("0.0 0.501960784 1.0 Blue"),
            "#0080ff",
        )

    def test_macos_highlight_rejects_garbage(self) -> None:
        self.assertIsNone(system_accent._macos_highlight("not a color"))

    def test_channel_lists_are_converted(self) -> None:
        self.assertEqual(
            system_accent._channels_to_hex(["255", "0", "10"]), "#ff000a"
        )

    def test_channel_lists_reject_out_of_range_values(self) -> None:
        self.assertIsNone(system_accent._channels_to_hex(["255", "300", "0"]))
        self.assertIsNone(system_accent._channels_to_hex(["255", "0"]))

    def test_detection_failure_uses_the_fallback(self) -> None:
        with patch.object(system_accent, "_detect", side_effect=OSError("missing")):
            self.assertEqual(system_accent.system_accent_color(), DEFAULT_ACCENT)

    def test_invalid_detected_value_uses_the_fallback(self) -> None:
        with patch.object(system_accent, "_detect", return_value="not-a-color"):
            self.assertEqual(system_accent.system_accent_color(), DEFAULT_ACCENT)

    def test_detected_value_is_normalized(self) -> None:
        with patch.object(system_accent, "_detect", return_value="ABC"):
            self.assertEqual(system_accent.system_accent_color(), "#aabbcc")


if __name__ == "__main__":
    unittest.main()
