from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vcolor.models import (
    AppData,
    ColorEntry,
    PaletteStore,
    Project,
)


class ModelTests(unittest.TestCase):
    def test_active_project_falls_back_to_first(self) -> None:
        data = AppData(
            projects=[Project(name="One"), Project(name="Two")],
            active_project_id="missing",
        )
        self.assertEqual(data.ensure_active_project().name, "One")
        self.assertEqual(data.active_project_id, data.projects[0].id)

    def test_serialization_round_trip(self) -> None:
        data = AppData(
            projects=[
                Project(
                    name="One",
                    colors=[ColorEntry(name="Blue", hex="#0a84ff")],
                )
            ]
        )
        restored = AppData.from_dict(json.loads(json.dumps(data.to_dict())))
        self.assertEqual(len(restored.projects), len(data.projects))
        self.assertEqual(restored.projects[0].colors[0].hex, "#0a84ff")

    def test_invalid_stored_hex_is_sanitized(self) -> None:
        color = ColorEntry.from_dict({"name": "Broken", "hex": "not-a-color"})
        self.assertEqual(color.hex, "#000000")

    def test_display_format_round_trip(self) -> None:
        data = AppData(display_format="OKLCH")
        restored = AppData.from_dict(json.loads(json.dumps(data.to_dict())))
        self.assertEqual(restored.display_format, "OKLCH")

    def test_invalid_display_format_falls_back_to_hex(self) -> None:
        restored = AppData.from_dict({"display_format": "CMYK", "projects": []})
        self.assertEqual(restored.display_format, "HEX")

    def test_show_hex_hash_defaults_to_true(self) -> None:
        self.assertTrue(AppData().show_hex_hash)
        self.assertTrue(AppData.from_dict({"projects": []}).show_hex_hash)

    def test_show_hex_hash_round_trip(self) -> None:
        data = AppData(show_hex_hash=False)
        restored = AppData.from_dict(json.loads(json.dumps(data.to_dict())))
        self.assertFalse(restored.show_hex_hash)

    def test_malformed_show_hex_hash_is_sanitized(self) -> None:
        restored = AppData.from_dict({"projects": [], "show_hex_hash": "no"})
        self.assertTrue(restored.show_hex_hash)

    def test_update_settings_round_trip(self) -> None:
        data = AppData(
            update_check=False,
            last_update_check="2026-05-01T12:00:00+00:00",
            skipped_version="1.2.0",
        )
        restored = AppData.from_dict(json.loads(json.dumps(data.to_dict())))
        self.assertFalse(restored.update_check)
        self.assertEqual(restored.last_update_check, "2026-05-01T12:00:00+00:00")
        self.assertEqual(restored.skipped_version, "1.2.0")

    def test_missing_update_settings_use_defaults(self) -> None:
        restored = AppData.from_dict({"projects": []})
        self.assertTrue(restored.update_check)
        self.assertIsNone(restored.last_update_check)
        self.assertIsNone(restored.skipped_version)

    def test_malformed_update_settings_are_sanitized(self) -> None:
        restored = AppData.from_dict(
            {"projects": [], "update_check": "yes", "skipped_version": 5}
        )
        self.assertTrue(restored.update_check)
        self.assertEqual(restored.skipped_version, "5")


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "palettes.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_save_and_load(self) -> None:
        store = PaletteStore(self.path)
        data = AppData(
            projects=[
                Project(
                    name="One",
                    colors=[ColorEntry(name="Test", hex="#abcdef")],
                )
            ]
        )
        store.save(data)

        loaded = PaletteStore(self.path).load()
        self.assertEqual(loaded.projects[0].colors[0].name, "Test")
        self.assertEqual(loaded.projects[0].colors[0].hex, "#abcdef")

    def test_missing_file_starts_empty(self) -> None:
        data = PaletteStore(self.path).load()
        self.assertEqual(data.projects, [])
        self.assertIsNone(data.active_project)

    def test_corrupt_file_is_backed_up(self) -> None:
        self.path.write_text("{not json", encoding="utf-8")
        store = PaletteStore(self.path)
        data = store.load()
        self.assertEqual(data.projects, [])
        self.assertIsNone(data.active_project)
        self.assertIsNotNone(store.last_backup_path)
        self.assertTrue(store.last_backup_path.exists())
        self.assertFalse(self.path.exists())

    def test_saved_file_is_valid_json(self) -> None:
        store = PaletteStore(self.path)
        store.save(AppData())
        parsed = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(parsed["version"], 1)
        self.assertEqual(parsed["projects"], [])


if __name__ == "__main__":
    unittest.main()
