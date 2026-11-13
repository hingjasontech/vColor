from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QFontDatabase  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialog, QPushButton  # noqa: E402

from vcolor import theme  # noqa: E402
from vcolor.main_window import MainWindow  # noqa: E402
from vcolor.models import AppData, ColorEntry, PaletteStore, Project  # noqa: E402
from vcolor.palette_formats import export_palette, import_palette  # noqa: E402
from vcolor.widgets import ColorListCard, ColorRow, EmptyState  # noqa: E402


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
        font = QFont(family)
        font.setPixelSize(14)
        cls.app.setFont(font)
        cls.app.setStyleSheet(theme.build_stylesheet(family))

    def setUp(self) -> None:
        theme.set_accent(theme.DEFAULT_ACCENT)
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
        rows = self.window.body.findChildren(ColorRow)
        self.assertEqual(len(rows), 2)
        self.assertEqual(self.window.format_combo.currentText(), "HEX")
        self.assertEqual(len(self.window.body.findChildren(ColorListCard)), 1)
        self.assertIs(rows[0].copy_button.parentWidget(), rows[0])
        self.assertEqual(self.window.page_title.full_text(), "Website")

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
        row = self.window.body.findChildren(ColorRow)[0]
        row.copy_button.click()
        self.assertIn("hsl(", QApplication.clipboard().text())

    def test_clicking_row_copies_value(self) -> None:
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

    def test_add_dialog_starts_with_empty_color_value(self) -> None:
        from vcolor.dialogs import ColorDialog

        dialog = ColorDialog(self.window)
        try:
            dialog.show()
            self.app.processEvents()
            self.assertEqual(dialog.color_input.text(), "")
            self.assertEqual(dialog.name_input.text(), "")
            self.assertTrue(dialog.color_input.hasFocus())
            self.assertEqual(dialog.color_name(), "Untitled color")
        finally:
            dialog.close()
            dialog.deleteLater()

    def test_color_dialog_accepts_any_format(self) -> None:
        from vcolor.dialogs import ColorDialog

        dialog = ColorDialog(self.window)
        try:
            for entered, expected in (
                ("rgb(10, 132, 255)", "#0a84ff"),
                ("hsl(210 100% 50%)", "#0080ff"),
                ("red", "#ff0000"),
                ("0a84ff", "#0a84ff"),
            ):
                with self.subTest(entered=entered):
                    dialog.color_input.setText(entered)
                    self.app.processEvents()
                    self.assertEqual(dialog.color_hex(), expected)
        finally:
            dialog.deleteLater()

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
        states = self.window.body.findChildren(EmptyState)
        self.assertEqual(len(states), 1)
        self.assertIsNone(states[0].action_button)
        self.assertTrue(self.window.add_button.isVisible())
        self.assertEqual(self.window.page_title.full_text(), empty.name)

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

    def test_project_context_menu_has_duplicate_action(self) -> None:
        item = next(iter(self.window._project_items.values()))
        duplicate_ids: list[str] = []
        item.duplicateRequested.connect(duplicate_ids.append)
        menu = item.build_context_menu()
        try:
            actions = {action.text(): action for action in menu.actions()}
            self.assertIn("Duplicate project", actions)
            actions["Duplicate project"].trigger()
            self.assertEqual(duplicate_ids, [item.project_id])
        finally:
            menu.deleteLater()

    def test_duplicate_project_copies_colors_and_selects_copy(self) -> None:
        original = self.window.active_project
        original_color_ids = {color.id for color in original.colors}
        self.window.duplicate_project(original.id)
        self.app.processEvents()

        projects = self.window.data.projects
        self.assertEqual(
            [project.name for project in projects],
            ["Website", "Website (2)", "Mobile app", "Brand"],
        )
        duplicate = projects[1]
        self.assertNotEqual(duplicate.id, original.id)
        self.assertEqual(
            [color.name for color in duplicate.colors],
            [color.name for color in original.colors],
        )
        self.assertEqual(
            [color.hex for color in duplicate.colors],
            [color.hex for color in original.colors],
        )
        self.assertTrue(
            original_color_ids.isdisjoint(color.id for color in duplicate.colors)
        )
        self.assertEqual(self.window.data.active_project_id, duplicate.id)
        self.assertTrue(self.window._project_items[duplicate.id].property("selected"))

        loaded = PaletteStore(self.path).load()
        self.assertEqual(loaded.active_project_id, duplicate.id)
        self.assertEqual(len(loaded.projects), 4)

    def test_duplicating_twice_keeps_numbered_names(self) -> None:
        original = self.window.active_project
        self.window.duplicate_project(original.id)
        self.window.duplicate_project(original.id)
        self.app.processEvents()

        names = [project.name for project in self.window.data.projects]
        self.assertEqual(names[:3], ["Website", "Website (3)", "Website (2)"])

    def test_update_banner_is_hidden_at_start(self) -> None:
        self.assertFalse(self.window.update_banner.isVisible())

    def test_sidebar_has_no_version_label(self) -> None:
        labels = [
            button.text()
            for button in self.window.sidebar.findChildren(QPushButton)
        ]
        self.assertNotIn("vColor 0.0.0", labels)
        self.assertEqual(self.window.findChildren(QPushButton, "VersionButton"), [])

    def test_available_update_shows_banner(self) -> None:
        self.window._on_update_available(self.release("9.9.9"))
        self.app.processEvents()
        self.assertTrue(self.window.update_banner.isVisible())
        self.assertIn("9.9.9", self.window.update_banner._label.text())

    def test_dismissing_update_remembers_version(self) -> None:
        self.window._on_update_available(self.release("9.9.9"))
        self.window._dismiss_update()
        self.app.processEvents()
        self.assertFalse(self.window.update_banner.isVisible())
        self.assertEqual(self.window.data.skipped_version, "9.9.9")

    def test_skipped_version_stays_hidden_on_auto_check(self) -> None:
        self.window.data.skipped_version = "9.9.9"
        self.window._manual_update_check = False
        self.window._on_update_available(self.release("9.9.9"))
        self.app.processEvents()
        self.assertFalse(self.window.update_banner.isVisible())

    def test_manual_check_shows_skipped_version(self) -> None:
        self.window.data.skipped_version = "9.9.9"
        self.window._manual_update_check = True
        self.window._on_update_available(self.release("9.9.9"))
        self.app.processEvents()
        self.assertTrue(self.window.update_banner.isVisible())

    def test_import_button_sits_above_settings(self) -> None:
        self.assertEqual(self.window.import_button.text(), "Import project")
        self.assertTrue(self.window.import_button.isVisible())
        self.assertIn("project", self.window.import_button.toolTip().lower())
        footer = self.window.import_button.parentWidget()
        layout = footer.layout()
        self.assertLess(
            layout.indexOf(self.window.import_button),
            layout.indexOf(self.window.settings_button),
        )

    def test_import_project_files_adds_project_and_supports_undo(self) -> None:
        previous_active_id = self.window.data.active_project_id
        source = export_palette(
            self.project_palette(),
            self.path.parent / "imported-theme.json",
            "json",
        )

        self.window.import_project_files([source])
        self.app.processEvents()

        self.assertEqual(len(self.window.data.projects), 4)
        imported = self.window.active_project
        self.assertEqual(imported.name, "Imported Theme")
        self.assertEqual(len(self.window.body.findChildren(ColorRow)), 2)
        self.assertTrue(source.exists())
        self.assertIsNotNone(self.window.toast._action)

        self.window.toast._action()
        self.app.processEvents()

        self.assertEqual(len(self.window.data.projects), 3)
        self.assertEqual(self.window.data.active_project_id, previous_active_id)

    def test_import_project_duplicate_name_gets_numbered_copy(self) -> None:
        source = export_palette(
            self.project_palette("Website"),
            self.path.parent / "website.json",
            "json",
        )

        self.window.import_project_files([source])
        self.app.processEvents()

        self.assertEqual(self.window.active_project.name, "Website (2)")

    def test_import_project_reports_invalid_file(self) -> None:
        source = self.path.parent / "broken.json"
        source.write_text('{"name": "Broken"}\n', encoding="utf-8")

        self.window.import_project_files([source])
        self.app.processEvents()

        self.assertEqual(len(self.window.data.projects), 3)
        self.assertTrue(self.window.toast.isVisible())
        self.assertIn("Could not import", self.window.toast._label.text())

    def test_import_project_dialog_reads_selected_files(self) -> None:
        from unittest.mock import patch

        source = export_palette(
            self.project_palette("Picked Theme"),
            self.path.parent / "picked-theme.json",
            "json",
        )
        with patch(
            "vcolor.main_window.QFileDialog.getOpenFileNames",
            return_value=([str(source)], "Palette files (*.json *.css)"),
        ):
            self.window.import_project()
        self.app.processEvents()

        self.assertEqual(self.window.active_project.name, "Picked Theme")

    def test_import_colors_appends_to_the_active_project(self) -> None:
        from unittest.mock import patch

        source = self.path.parent / "extra-colors.css"
        source.write_text(":root { --extra: #abcdef; }\n", encoding="utf-8")
        with patch(
            "vcolor.main_window.QFileDialog.getOpenFileName",
            return_value=(str(source), "Palette files (*.css)"),
        ):
            self.window.import_colors(self.window.active_project.id)
        self.app.processEvents()

        self.assertEqual(len(self.window.active_project.colors), 3)
        self.assertEqual(self.window.active_project.colors[-1].hex, "#abcdef")

    def test_export_project_uses_selected_filter_and_appends_suffix(self) -> None:
        from unittest.mock import patch

        target = self.path.parent / "exported-theme"
        with patch(
            "vcolor.main_window.QFileDialog.getSaveFileName",
            return_value=(str(target), "CSS variables (*.css)"),
        ):
            self.window.export_project(self.window.active_project.id)
        self.app.processEvents()

        written = target.with_suffix(".css")
        self.assertTrue(written.exists())
        self.assertIn("--apple-blue: #0a84ff;", written.read_text(encoding="utf-8"))

    def test_export_project_prefers_typed_suffix(self) -> None:
        from unittest.mock import patch

        target = self.path.parent / "exported-theme.ase"
        with patch(
            "vcolor.main_window.QFileDialog.getSaveFileName",
            return_value=(str(target), "JSON palette (*.json)"),
        ):
            self.window.export_project(self.window.active_project.id)
        self.app.processEvents()

        self.assertEqual(
            [color.hex for color in import_palette(target)],
            ["#0a84ff", "#123123"],
        )

    def test_dropped_json_file_creates_a_project(self) -> None:
        from PySide6.QtCore import QMimeData, QUrl

        source = self.path.parent / "dropped-theme.json"
        export_palette(self.project_palette("Dropped Theme"), source, "json")
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(source))])

        paths = self.window._project_paths(mime)
        self.assertEqual(paths, [source])
        self.window.import_project_files(paths)
        self.app.processEvents()

        self.assertEqual(self.window.active_project.name, "Dropped Theme")
        self.assertTrue(source.exists())

    @staticmethod
    def project_palette(name: str = "Imported Theme") -> Project:
        return Project(
            name=name,
            colors=[
                ColorEntry(name="Background", hex="#101014"),
                ColorEntry(name="Accent", hex="#0a84ff"),
            ],
        )

    def test_settings_page_opens_from_sidebar(self) -> None:
        self.window.settings_button.click()
        self.app.processEvents()
        self.assertIs(
            self.window.page_stack.currentWidget(), self.window.settings_page
        )
        self.assertTrue(self.window.settings_page.isVisible())
        self.assertTrue(self.window.settings_button._selected)

    def test_settings_page_back_returns_to_projects(self) -> None:
        self.window.show_settings_page()
        self.window.settings_page.back_button.click()
        self.app.processEvents()
        self.assertIs(
            self.window.page_stack.currentWidget(), self.window.main_content
        )
        self.assertFalse(self.window.settings_button._selected)

    def test_settings_format_choice_updates_header_and_rows(self) -> None:
        self.window.show_settings_page()
        self.window.settings_page.format_combo.setCurrentText("RGB")
        self.app.processEvents()

        self.assertEqual(self.window.format_combo.currentText(), "RGB")
        self.assertEqual(self.window.data.display_format, "RGB")
        rows = self.window.body.findChildren(ColorRow)
        self.assertEqual(rows[0].value_label.text(), "rgb(10, 132, 255)")
        self.assertEqual(PaletteStore(self.path).load().display_format, "RGB")

    def test_hex_values_can_be_shown_without_hash(self) -> None:
        self.window.show_settings_page()
        self.window.settings_page.hex_hash_switch.setChecked(False)
        self.app.processEvents()

        rows = self.window.body.findChildren(ColorRow)
        self.assertEqual(rows[0].value_label.text(), "0a84ff")

        color_id = self.window.active_project.colors[0].id
        self.window.copy_color(color_id)
        self.assertEqual(QApplication.clipboard().text(), "0a84ff")
        self.assertFalse(PaletteStore(self.path).load().show_hex_hash)

        self.window.format_combo.setCurrentText("RGB")
        self.app.processEvents()
        rows = self.window.body.findChildren(ColorRow)
        self.assertEqual(rows[0].value_label.text(), "rgb(10, 132, 255)")

    def test_hex_hash_setting_is_restored(self) -> None:
        self.window.show_settings_page()
        self.window.settings_page.hex_hash_switch.setChecked(False)
        self.app.processEvents()
        self.window.close()

        restored = MainWindow(PaletteStore(self.path))
        restored._loaded = True
        restored.set_data(restored.store.load())
        self.assertFalse(restored.data.show_hex_hash)
        self.assertFalse(restored.settings_page.hex_hash_switch.isChecked())
        self.assertEqual(
            restored.body.findChildren(ColorRow)[0].value_label.text(), "0a84ff"
        )
        restored.deleteLater()
        self.app.processEvents()

    def test_sidebar_project_spacing_is_compact(self) -> None:
        self.assertEqual(self.window.project_list_layout.spacing(), 6)

    def test_settings_update_toggle_persists(self) -> None:
        self.window.show_settings_page()
        switch = self.window.settings_page.update_switch
        self.assertTrue(switch.isChecked())

        switch.setChecked(False)
        self.app.processEvents()

        self.assertFalse(self.window.data.update_check)
        self.assertFalse(PaletteStore(self.path).load().update_check)

    def test_accent_follows_the_system_by_default(self) -> None:
        from unittest.mock import patch

        with patch(
            "vcolor.main_window.system_accent_color", return_value="#abcdef"
        ):
            self.window.set_data(sample_data())

        self.window.show_settings_page()
        self.assertTrue(self.window.data.use_system_accent)
        self.assertTrue(self.window.settings_page.system_accent_switch.isChecked())
        self.assertEqual(theme.ACCENT, "#abcdef")
        self.assertEqual(self.window.settings_page.accent_button.color(), "#abcdef")

    def test_follow_system_accent_switch_applies_detected_color(self) -> None:
        from unittest.mock import patch

        self.window.show_settings_page()
        self.window.settings_page.system_accent_switch.setChecked(False)
        self.app.processEvents()
        self.assertFalse(self.window.data.use_system_accent)

        with patch(
            "vcolor.main_window.system_accent_color", return_value="#aabbcc"
        ):
            self.window.settings_page.system_accent_switch.setChecked(True)
        self.app.processEvents()

        self.assertTrue(self.window.data.use_system_accent)
        self.assertEqual(theme.ACCENT, "#aabbcc")
        self.assertEqual(self.window.settings_page.accent_button.color(), "#aabbcc")

    def test_choosing_an_accent_color_turns_off_system_follow(self) -> None:
        from unittest.mock import patch

        class Picker:
            def __init__(self, *args, **kwargs) -> None:
                pass

            def setWindowTitle(self, title: str) -> None:
                pass

            def selectedColor(self) -> QColor:
                return QColor("#123456")

        self.window.show_settings_page()
        self.assertTrue(self.window.data.use_system_accent)
        with patch("vcolor.settings_page.QColorDialog", Picker), patch(
            "vcolor.dialogs.run_dialog",
            return_value=QDialog.DialogCode.Accepted,
        ):
            self.window.settings_page.accent_button.click()
        self.app.processEvents()

        self.assertFalse(self.window.data.use_system_accent)
        self.assertFalse(self.window.settings_page.system_accent_switch.isChecked())
        self.assertEqual(self.window.data.accent_color, "#123456")
        self.assertEqual(theme.ACCENT, "#123456")
        loaded = PaletteStore(self.path).load()
        self.assertFalse(loaded.use_system_accent)
        self.assertEqual(loaded.accent_color, "#123456")

    def test_settings_source_button_opens_github(self) -> None:
        from unittest.mock import patch

        from PySide6.QtCore import QUrl

        opened: list[QUrl] = []
        with patch(
            "vcolor.main_window.QDesktopServices.openUrl",
            side_effect=opened.append,
        ):
            self.window.show_settings_page()
            self.window.settings_page.source_button.click()
        self.app.processEvents()

        self.assertEqual(opened, [QUrl("https://github.com/hingjasontech/vColor")])

    def test_color_context_menu_has_adwaita_labels(self) -> None:
        row = ColorRow("color-id", "Apple blue", "#0a84ff", "#0a84ff")
        menu = row.build_context_menu()
        events = []
        row.editRequested.connect(lambda color_id: events.append(("edit", color_id)))
        row.copyRequested.connect(lambda color_id: events.append(("copy", color_id)))
        row.deleteRequested.connect(lambda color_id: events.append(("delete", color_id)))
        try:
            self.assertEqual(
                [action.text() for action in menu.actions()],
                ["Edit", "Copy", "", "Delete"],
            )
            self.assertTrue(menu.actions()[2].isSeparator())
            menu.actions()[0].trigger()
            menu.actions()[1].trigger()
            menu.actions()[3].trigger()
            self.assertEqual(
                events,
                [("edit", "color-id"), ("copy", "color-id"), ("delete", "color-id")],
            )
        finally:
            menu.deleteLater()

    @staticmethod
    def release(version: str):
        from vcolor.updater import ReleaseInfo

        return ReleaseInfo(
            version=version,
            tag=f"v{version}",
            url=f"https://example.com/{version}",
            name=f"vColor {version}",
        )


if __name__ == "__main__":
    unittest.main()
