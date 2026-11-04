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
    seed_data,
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
        data = seed_data()
        restored = AppData.from_dict(json.loads(json.dumps(data.to_dict())))
        self.assertEqual(len(restored.projects), len(data.projects))
        self.assertEqual(restored.projects[0].colors[0].hex, "#0a84ff")

    def test_invalid_stored_hex_is_sanitized(self) -> None:
        color = ColorEntry.from_dict({"name": "Broken", "hex": "not-a-color"})
        self.assertEqual(color.hex, "#000000")

    def test_display_format_round_trip(self) -> None:
        data = seed_data()
        data.display_format = "OKLCH"
        restored = AppData.from_dict(json.loads(json.dumps(data.to_dict())))
        self.assertEqual(restored.display_format, "OKLCH")

    def test_invalid_display_format_falls_back_to_hex(self) -> None:
        restored = AppData.from_dict({"display_format": "CMYK", "projects": []})
        self.assertEqual(restored.display_format, "HEX")


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "palettes.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_save_and_load(self) -> None:
        store = PaletteStore(self.path)
        data = seed_data()
        data.projects[0].colors.append(ColorEntry(name="Test", hex="#abcdef"))
        store.save(data)

        loaded = PaletteStore(self.path).load()
        self.assertEqual(loaded.projects[0].colors[-1].name, "Test")
        self.assertEqual(loaded.projects[0].colors[-1].hex, "#abcdef")

    def test_missing_file_seeds_data(self) -> None:
        data = PaletteStore(self.path).load()
        self.assertEqual(len(data.projects), 3)
        self.assertIsNotNone(data.active_project)

    def test_missing_file_can_be_empty(self) -> None:
        data = PaletteStore(self.path, seed_if_missing=False).load()
        self.assertEqual(data.projects, [])

    def test_corrupt_file_is_backed_up(self) -> None:
        self.path.write_text("{not json", encoding="utf-8")
        store = PaletteStore(self.path)
        data = store.load()
        self.assertEqual(len(data.projects), 3)
        self.assertIsNotNone(store.last_backup_path)
        self.assertTrue(store.last_backup_path.exists())
        self.assertFalse(self.path.exists())

    def test_saved_file_is_valid_json(self) -> None:
        store = PaletteStore(self.path)
        store.save(seed_data())
        parsed = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(parsed["version"], 1)
        self.assertIn("projects", parsed)


if __name__ == "__main__":
    unittest.main()
