from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QFont, QFontDatabase, QKeySequence  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialog  # noqa: E402

from vcolor import theme  # noqa: E402
from vcolor.main_window import MainWindow  # noqa: E402
from vcolor.models import AppData, PaletteStore  # noqa: E402
from vcolor.settings_page import SettingsRow  # noqa: E402
from vcolor.shortcuts import (  # noqa: E402
    SHORTCUT_ACTIONS,
    normalize_shortcut,
    resolve_shortcuts,
    sanitize_overrides,
    shortcut_keycaps,
)
from vcolor.shortcuts_page import ShortcutDialog  # noqa: E402


class ShortcutHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_normalize_shortcut(self) -> None:
        self.assertEqual(normalize_shortcut("Ctrl+Shift+N"), "Ctrl+Shift+N")
        self.assertEqual(normalize_shortcut(""), "")
        self.assertEqual(normalize_shortcut("Ctrl+N, Ctrl+C"), "")

    def test_keycaps_split_modifiers(self) -> None:
        if sys.platform == "darwin":
            expected = ["⌘", "⇧", "N"]
        else:
            expected = ["Ctrl", "Shift", "N"]
        self.assertEqual(shortcut_keycaps("Ctrl+Shift+N"), expected)
        self.assertEqual(shortcut_keycaps(""), [])

    def test_sanitize_drops_unknown_and_conflicting_overrides(self) -> None:
        self.assertEqual(
            sanitize_overrides(
                {"add_color": "Ctrl+Shift+A", "unknown": "Ctrl+U"}
            ),
            {"add_color": "Ctrl+Shift+A"},
        )
        self.assertEqual(sanitize_overrides({"new_project": "Ctrl+N"}), {})
        self.assertEqual(
            sanitize_overrides(
                {"add_color": "Ctrl+Shift+N", "new_project": "Ctrl+N"}
            ),
            {"add_color": "Ctrl+Shift+N", "new_project": "Ctrl+N"},
        )
        self.assertEqual(sanitize_overrides({"add_color": "Ctrl+N"}), {})
        self.assertEqual(sanitize_overrides({"add_color": ""}), {"add_color": ""})
        self.assertEqual(sanitize_overrides({"add_color": "A"}), {})

    def test_resolve_shortcuts_uses_defaults_and_overrides(self) -> None:
        resolved = resolve_shortcuts({"add_color": "Ctrl+Shift+A"})
        self.assertEqual(resolved["add_color"], "Ctrl+Shift+A")
        self.assertEqual(resolved["open_settings"], "Ctrl+,")
        self.assertEqual(resolve_shortcuts({"add_color": ""})["add_color"], "")

    def test_app_data_round_trips_shortcut_overrides(self) -> None:
        data = AppData(shortcut_overrides={"add_color": "Ctrl+Shift+A"})
        restored = AppData.from_dict(data.to_dict())
        self.assertEqual(
            restored.shortcut_overrides, {"add_color": "Ctrl+Shift+A"}
        )


class ShortcutUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle("Fusion")
        font_id = QFontDatabase.addApplicationFont(
            str(
                Path(__file__).resolve().parents[1]
                / "vcolor/resources/fonts/InterVariable.ttf"
            )
        )
        families = QFontDatabase.applicationFontFamilies(font_id)
        family = families[0] if families else "Noto Sans"
        font = QFont(family)
        font.setPixelSize(14)
        cls.app.setFont(font)
        cls.app.setStyleSheet(theme.build_stylesheet(family))

    def setUp(self) -> None:
        theme.set_accent(theme.DEFAULT_ACCENT)
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "palettes.json"
        self.window = MainWindow(PaletteStore(self.path))
        self.window._loaded = True
        self.window.set_data(AppData())
        self.window.resize(1280, 800)
        self.window.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def test_shortcuts_page_opens_from_settings_and_returns(self) -> None:
        self.window.show_settings_page()
        rows = [
            row
            for row in self.window.settings_page.findChildren(SettingsRow)
            if row.title_label.text() == "Keyboard shortcuts"
        ]
        self.assertEqual(len(rows), 1)
        QTest.mouseClick(rows[0], Qt.MouseButton.LeftButton)
        self.app.processEvents()
        self.assertIs(
            self.window.page_stack.currentWidget(), self.window.shortcuts_page
        )

        self.window.shortcuts_page.back_button.click()
        self.app.processEvents()
        self.assertIs(
            self.window.page_stack.currentWidget(), self.window.settings_page
        )

    def test_shortcuts_page_shows_current_keycaps(self) -> None:
        self.window.show_shortcuts_page()
        self.assertEqual(
            self.window.shortcuts_page._keycaps["add_color"].sequence(),
            "Ctrl+N",
        )
        self.assertEqual(
            self.window.shortcuts_page._keycaps["open_settings"].sequence(),
            "Ctrl+,",
        )
        self.assertEqual(
            self.window._shortcut_objects["open_settings"]
            .key()
            .toString(QKeySequence.SequenceFormat.PortableText),
            "Ctrl+,",
        )

    def test_changing_shortcut_reinstalls_and_persists(self) -> None:
        self.window._shortcuts_changed({"add_color": "Ctrl+Shift+A"})
        self.app.processEvents()
        self.assertEqual(
            self.window.data.shortcut_overrides,
            {"add_color": "Ctrl+Shift+A"},
        )
        self.assertEqual(
            self.window._shortcut_objects["add_color"]
            .key()
            .toString(QKeySequence.SequenceFormat.PortableText),
            "Ctrl+Shift+A",
        )
        self.assertEqual(
            self.window.shortcuts_page._keycaps["add_color"].sequence(),
            "Ctrl+Shift+A",
        )
        loaded = PaletteStore(self.path).load()
        self.assertEqual(
            loaded.shortcut_overrides, {"add_color": "Ctrl+Shift+A"}
        )

    def test_dialog_captures_and_clears_shortcut(self) -> None:
        dialog = ShortcutDialog(
            self.window,
            action=SHORTCUT_ACTIONS[0],
            sequence="Ctrl+N",
            is_custom=False,
            taken={"Ctrl+Shift+N": "New project"},
        )
        try:
            dialog.show()
            self.app.processEvents()
            QTest.keyClick(
                dialog, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier
            )
            self.assertEqual(dialog.sequence(), "Ctrl+A")

            QTest.keyClick(dialog, Qt.Key.Key_Backspace)
            self.assertEqual(dialog.sequence(), "")

            QTest.keyClick(
                dialog,
                Qt.Key.Key_N,
                Qt.KeyboardModifier.ControlModifier
                | Qt.KeyboardModifier.ShiftModifier,
            )
            self.assertEqual(dialog.sequence(), "Ctrl+Shift+N")
            dialog._accept_if_valid()
            self.assertNotEqual(
                dialog.result(), QDialog.DialogCode.Accepted
            )
            self.assertTrue(dialog.error_label.isVisible())
        finally:
            dialog.close()
            dialog.deleteLater()

    def test_dialog_reset_restores_default(self) -> None:
        dialog = ShortcutDialog(
            self.window,
            action=SHORTCUT_ACTIONS[0],
            sequence="Ctrl+Shift+A",
            is_custom=True,
            taken={},
        )
        try:
            dialog.reset_button.click()
            self.assertEqual(dialog.sequence(), "Ctrl+N")
        finally:
            dialog.deleteLater()

    def test_dialog_rejects_bare_letters(self) -> None:
        dialog = ShortcutDialog(
            self.window,
            action=SHORTCUT_ACTIONS[0],
            sequence="",
            is_custom=False,
            taken={},
        )
        try:
            dialog.show()
            self.app.processEvents()
            QTest.keyClick(dialog, Qt.Key.Key_A)
            self.assertEqual(dialog.sequence(), "")
            self.assertTrue(dialog.error_label.isVisible())
        finally:
            dialog.close()
            dialog.deleteLater()
