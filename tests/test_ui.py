from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer, Qt  # noqa: E402
from PySide6.QtGui import QFontDatabase  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from vcolor import theme  # noqa: E402
from vcolor.main_window import MainWindow  # noqa: E402
from vcolor.models import AppData, ColorEntry, PaletteStore, Project  # noqa: E402
from vcolor.widgets import ColorItem, ColorRow, EmptyState  # noqa: E402


def sample_data() -> AppData:
    website = Project(
        name="Website",
        colors=[
            ColorEntry(name="Apple blue", hex="#0a84ff"),
            ColorEntry(name="Ink", hex="#123123"),
        ],
    )
    mobile = Project(name="Mobile app")
    brand = Project(name="Brand")
    return AppData(
        projects=[website, mobile, brand],
        active_project_id=website.id,
    )


class WindowSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle("Fusion")
        font_id = QFontDatabase.addApplicationFont(
            str(Path(__file__).resolve().parents[1] / "vcolor/resources/fonts/InterVariable.ttf")
        )
        families = QFontDatabase.applicationFontFamilies(font_id)
        family = families[0] if families else "Noto Sans"
        cls.app.setStyleSheet(theme.build_stylesheet(family))

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "palettes.json"
        self.store = PaletteStore(self.path)
        self.window = MainWindow(self.store)
        self.window._loaded = True
        self.window.set_data(sample_data())
        self.window.resize(1280, 800)
        self.window.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def test_initial_render(self) -> None:
        self.assertTrue(self.window.format_combo.isEnabled())
        self.assertEqual(len(self.window.body.findChildren(ColorRow)), 2)
        self.assertEqual(self.window.format_combo.currentText(), "HEX")
        items = self.window.body.findChildren(ColorItem)
        self.assertEqual(items[0].copy_button.text(), "Copy")
        self.assertIs(items[0].copy_button.parentWidget(), items[0])
        self.assertIs(items[0].row.parentWidget(), items[0])

    def test_first_run_is_empty(self) -> None:
        self.window.set_data(AppData())
        self.app.processEvents()
        self.assertEqual(self.window.data.projects, [])
        self.assertEqual(self.window.body.findChildren(ColorRow), [])
        self.assertEqual(len(self.window.body.findChildren(EmptyState)), 1)
        self.assertFalse(self.window.format_combo.isEnabled())
        self.assertFalse(self.window.add_button.isVisible())

    def test_format_change_updates_rows(self) -> None:
        self.window.format_combo.setCurrentText("RGB")
        self.app.processEvents()
        rows = self.window.body.findChildren(ColorRow)
        self.assertEqual(rows[0].value_label.text(), "rgb(10, 132, 255)")

    def test_format_choice_is_persisted(self) -> None:
        self.window.format_combo.setCurrentText("OKLCH")
        self.app.processEvents()
        loaded = PaletteStore(self.path).load()
        self.assertEqual(loaded.display_format, "OKLCH")

    def test_saved_format_is_restored(self) -> None:
        self.window.format_combo.setCurrentText("HSL")
        self.app.processEvents()
        self.window.close()

        restored = MainWindow(PaletteStore(self.path))
        restored._loaded = True
        restored.set_data(restored.store.load())
        self.assertEqual(restored.format_combo.currentText(), "HSL")
        self.assertEqual(restored.current_format, "HSL")
        restored.deleteLater()
        self.app.processEvents()

    def test_copy_uses_selected_format(self) -> None:
        self.window.format_combo.setCurrentText("HSL")
        self.app.processEvents()
        color_id = self.window.active_project.colors[0].id
        self.window.copy_color(color_id)
        self.assertIn("hsl(", QApplication.clipboard().text())

    def test_copy_button_uses_selected_format(self) -> None:
        self.window.format_combo.setCurrentText("HSL")
        self.app.processEvents()
        item = self.window.body.findChildren(ColorItem)[0]
        item.copy_button.click()
        self.assertIn("hsl(", QApplication.clipboard().text())

    def test_clicking_tile_copies_value(self) -> None:
        self.window.format_combo.setCurrentText("RGB")
        self.app.processEvents()
        row = self.window.body.findChildren(ColorRow)[0]
        QApplication.clipboard().clear()
        QTest.mouseClick(
            row,
            Qt.MouseButton.LeftButton,
            pos=row.rect().center(),
        )
        self.assertEqual(QApplication.clipboard().text(), "rgb(10, 132, 255)")

    def test_edit_button_requests_edit(self) -> None:
        row = ColorRow("color-id", "Apple blue", "#0a84ff", "#0a84ff")
        requested: list[str] = []
        row.editRequested.connect(requested.append)
        QTest.mouseClick(row.edit_button, Qt.MouseButton.LeftButton)
        self.assertEqual(requested, ["color-id"])

    def test_add_button_sits_in_header(self) -> None:
        self.assertTrue(self.window.add_button.isVisible())
        self.assertEqual(self.window.add_button.text(), "Add color")
        self.assertIsNot(self.window.add_button.parentWidget(), self.window.main_content)

    def test_add_dialog_hides_conversions(self) -> None:
        from vcolor.dialogs import ColorDialog

        add_dialog = ColorDialog(self.window, show_conversions=False)
        edit_dialog = ColorDialog(self.window)
        try:
            self.assertEqual(add_dialog._conversion_values, {})
            self.assertEqual(len(edit_dialog._conversion_values), 4)
        finally:
            add_dialog.deleteLater()
            edit_dialog.deleteLater()

    def test_delete_and_undo(self) -> None:
        project = self.window.active_project
        color_id = project.colors[0].id
        self.window.delete_color(color_id)
        self.assertEqual(len(project.colors), 1)
        self.assertTrue(self.window.toast.isVisible())
        self.assertIsNotNone(self.window.toast._action)
        self.window.toast._action()
        self.assertEqual(len(project.colors), 2)

    def test_empty_project_renders_empty_state(self) -> None:
        empty = next(project for project in self.window.data.projects if not project.colors)
        self.window.select_project(empty.id)
        self.app.processEvents()
        self.assertEqual(len(self.window.body.findChildren(ColorRow)), 0)
        self.assertEqual(len(self.window.body.findChildren(EmptyState)), 1)

    def test_autosave_writes_file(self) -> None:
        second = self.window.data.projects[1]
        self.window.select_project(second.id)
        self.assertTrue(self.path.exists())
        self.assertIn('"projects"', self.path.read_text(encoding="utf-8"))

    def test_dialog_is_modal_and_detached_from_parent_on_linux(self) -> None:
        import sys

        from vcolor.dialogs import ProjectDialog, run_dialog

        dialog = ProjectDialog(self.window)
        seen: list[object] = []

        def accept() -> None:
            seen.append(dialog.parentWidget())
            seen.append(dialog.isModal())
            seen.append(dialog.windowType())
            dialog.name_input.setText("Test project")
            dialog.accept()

        QTimer.singleShot(0, accept)
        result = run_dialog(dialog)

        self.assertEqual(result, ProjectDialog.DialogCode.Accepted)
        self.assertTrue(seen[1])
        if sys.platform.startswith("linux"):
            self.assertIsNone(seen[0])
            self.assertEqual(seen[2], Qt.WindowType.Dialog)

    def test_switching_project_persists_active_id(self) -> None:
        second = self.window.data.projects[1]
        self.window.select_project(second.id)
        loaded = PaletteStore(self.path).load()
        self.assertEqual(loaded.active_project_id, second.id)


if __name__ == "__main__":
    unittest.main()
