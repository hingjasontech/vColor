from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from vcolor import cli
from vcolor.models import ColorEntry, PaletteStore
from vcolor.palette_format import PortablePalette, load_palette, save_palette


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cli.main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class CliTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.palette_path = self.directory / "test-theme.json"
        self.palette = PortablePalette(
            id="test-theme",
            name="Test Theme",
            description="A test palette.",
            source="https://example.com/test-theme",
            license="MIT",
            tags=["dark", "test"],
            colors=[
                ColorEntry(name="Base", hex="#101014"),
                ColorEntry(name="Accent Blue", hex="#0a84ff"),
                ColorEntry(name="Text", hex="#f2f2f7"),
            ],
        )
        save_palette(self.palette, self.palette_path)

    def tearDown(self) -> None:
        self.temp.cleanup()


class ShowTests(CliTestBase):
    def test_show_prints_metadata_and_colors(self) -> None:
        code, stdout, stderr = run_cli("show", str(self.palette_path))
        self.assertEqual(code, 0, stderr)
        self.assertIn("Test Theme", stdout)
        self.assertIn("test-theme", stdout)
        self.assertIn("3 colors", stdout)
        self.assertIn("MIT", stdout)
        self.assertIn("#0a84ff", stdout)

    def test_show_json_returns_canonical_document(self) -> None:
        code, stdout, stderr = run_cli("show", str(self.palette_path), "--json")
        self.assertEqual(code, 0, stderr)
        raw = json.loads(stdout)
        self.assertEqual(raw["format"], "vcolor.palette")
        self.assertEqual(raw["id"], "test-theme")
        self.assertEqual(raw["colors"][0], {"name": "Base", "hex": "#101014"})

    def test_show_missing_file_fails(self) -> None:
        code, stdout, stderr = run_cli("show", str(self.directory / "missing.json"))
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("not found", stderr)

    def test_show_invalid_palette_fails(self) -> None:
        path = self.directory / "broken.json"
        path.write_text(
            json.dumps({"name": "Broken", "colors": ["nope"]}), encoding="utf-8"
        )
        code, stdout, stderr = run_cli("show", str(path))
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("No colors", stderr)


class CreateTests(CliTestBase):
    def test_create_writes_portable_file(self) -> None:
        output = self.directory / "brand.json"
        code, _stdout, stderr = run_cli(
            "create",
            "Brand Colors",
            "--id",
            "brand",
            "--color",
            "Primary=#0A84FF",
            "--color",
            "Surface=#101014",
            "--description",
            "Brand palette.",
            "--source",
            "https://example.com/brand",
            "--license",
            "MIT",
            "--tag",
            "dark",
            "--output",
            str(output),
        )
        self.assertEqual(code, 0, stderr)
        palette = load_palette(output)
        self.assertEqual(palette.id, "brand")
        self.assertEqual(palette.name, "Brand Colors")
        self.assertEqual(palette.description, "Brand palette.")
        self.assertEqual(palette.source, "https://example.com/brand")
        self.assertEqual(palette.license, "MIT")
        self.assertEqual(palette.tags, ["dark"])
        self.assertEqual(palette.colors[0].hex, "#0a84ff")

    def test_create_defaults_id_to_slug(self) -> None:
        output = self.directory / "brand.json"
        code, _, stderr = run_cli(
            "create",
            "Brand Colors",
            "--color",
            "Ink=#123123",
            "--output",
            str(output),
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(load_palette(output).id, "brand-colors")

    def test_create_without_output_prints_json(self) -> None:
        code, stdout, stderr = run_cli(
            "create", "Brand", "--color", "Ink=#123123"
        )
        self.assertEqual(code, 0, stderr)
        raw = json.loads(stdout)
        self.assertEqual(raw["format"], "vcolor.palette")
        self.assertEqual(raw["colors"], [{"name": "Ink", "hex": "#123123"}])

    def test_create_requires_colors(self) -> None:
        code, _, stderr = run_cli("create", "Empty")
        self.assertEqual(code, 1)
        self.assertIn("at least one --color", stderr)

    def test_create_rejects_invalid_color(self) -> None:
        code, _, stderr = run_cli("create", "Bad", "--color", "Ink=nope")
        self.assertEqual(code, 1)
        self.assertIn("Invalid color", stderr)


class ConvertTests(CliTestBase):
    def test_convert_css_with_metadata(self) -> None:
        source = self.directory / "upstream.css"
        source.write_text(
            ":root {\n"
            "  --accent-blue: #0A84FF;\n"
            "  --surface: #101014;\n"
            "}\n",
            encoding="utf-8",
        )
        output = self.directory / "converted.json"
        code, _, stderr = run_cli(
            "convert",
            str(source),
            "--name",
            "My Theme",
            "--id",
            "my-theme",
            "--source",
            "https://example.com/my-theme",
            "--license",
            "MIT",
            "--tag",
            "dark",
            "--output",
            str(output),
        )
        self.assertEqual(code, 0, stderr)
        palette = load_palette(output)
        self.assertEqual(palette.id, "my-theme")
        self.assertEqual(palette.name, "My Theme")
        self.assertEqual(palette.source, "https://example.com/my-theme")
        self.assertEqual(palette.license, "MIT")
        self.assertEqual(palette.tags, ["dark"])
        self.assertEqual([color.name for color in palette.colors], ["Accent Blue", "Surface"])
        self.assertEqual(palette.colors[0].hex, "#0a84ff")

    def test_convert_without_output_prints_json(self) -> None:
        source = self.directory / "upstream.css"
        source.write_text(":root { --surface: #101014; }", encoding="utf-8")
        code, stdout, stderr = run_cli("convert", str(source), "--name", "My Theme")
        self.assertEqual(code, 0, stderr)
        raw = json.loads(stdout)
        self.assertEqual(raw["name"], "My Theme")
        self.assertEqual(raw["colors"], [{"name": "Surface", "hex": "#101014"}])

    def test_convert_portable_preserves_metadata(self) -> None:
        output = self.directory / "copy.json"
        code, _, stderr = run_cli(
            "convert", str(self.palette_path), "--output", str(output)
        )
        self.assertEqual(code, 0, stderr)
        palette = load_palette(output)
        self.assertEqual(palette.description, "A test palette.")
        self.assertEqual(palette.source, "https://example.com/test-theme")
        self.assertEqual(palette.tags, ["dark", "test"])

    def test_convert_derives_id_from_name_for_imported_input(self) -> None:
        source = self.directory / "upstream.css"
        source.write_text(":root { --surface: #101014; }", encoding="utf-8")
        code, stdout, stderr = run_cli("convert", str(source), "--name", "My Theme")
        self.assertEqual(code, 0, stderr)
        self.assertEqual(json.loads(stdout)["id"], "my-theme")

    def test_convert_preserves_portable_id_when_renaming(self) -> None:
        code, stdout, stderr = run_cli(
            "convert", str(self.palette_path), "--name", "Renamed Theme"
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(json.loads(stdout)["id"], "test-theme")


class ExportTests(CliTestBase):
    def test_export_css(self) -> None:
        output = self.directory / "theme.css"
        code, _, stderr = run_cli("export", str(self.palette_path), str(output))
        self.assertEqual(code, 0, stderr)
        text = output.read_text(encoding="utf-8")
        self.assertIn("--base: #101014;", text)
        self.assertIn("--accent-blue: #0a84ff;", text)

    def test_export_gpl(self) -> None:
        output = self.directory / "theme.gpl"
        code, _, stderr = run_cli("export", str(self.palette_path), str(output))
        self.assertEqual(code, 0, stderr)
        self.assertTrue(output.read_text(encoding="utf-8").startswith("GIMP Palette"))

    def test_export_json_preserves_metadata(self) -> None:
        output = self.directory / "copy.json"
        code, _, stderr = run_cli("export", str(self.palette_path), str(output))
        self.assertEqual(code, 0, stderr)
        palette = load_palette(output)
        self.assertEqual(palette.description, "A test palette.")
        self.assertEqual(palette.source, "https://example.com/test-theme")
        self.assertEqual(palette.license, "MIT")
        self.assertEqual(palette.tags, ["dark", "test"])

    def test_export_infers_format_from_extension(self) -> None:
        output = self.directory / "theme.gpl"
        code, _, _ = run_cli("export", str(self.palette_path), str(output))
        self.assertEqual(code, 0)
        self.assertTrue(output.exists())

    def test_export_rejects_unknown_extension(self) -> None:
        code, _, stderr = run_cli(
            "export", str(self.palette_path), str(self.directory / "theme.txt")
        )
        self.assertEqual(code, 1)
        self.assertIn("Cannot infer", stderr)


class InstallTests(CliTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.data_dir = self.directory / "data"

    def _load_store(self) -> PaletteStore:
        return PaletteStore(self.data_dir / "palettes.json")

    def test_install_creates_project_and_sets_active(self) -> None:
        code, stdout, stderr = run_cli(
            "install", str(self.palette_path), "--data-dir", str(self.data_dir)
        )
        self.assertEqual(code, 0, stderr)
        self.assertIn("Installed", stdout)
        data = self._load_store().load()
        self.assertEqual(len(data.projects), 1)
        project = data.projects[0]
        self.assertEqual(project.name, "Test Theme")
        self.assertEqual(len(project.colors), 3)
        self.assertEqual(data.active_project_id, project.id)

    def test_install_duplicate_requires_replace(self) -> None:
        run_cli("install", str(self.palette_path), "--data-dir", str(self.data_dir))
        code, _, stderr = run_cli(
            "install", str(self.palette_path), "--data-dir", str(self.data_dir)
        )
        self.assertEqual(code, 1)
        self.assertIn("already exists", stderr)

        replacement = PortablePalette(
            id="test-theme",
            name="Test Theme",
            colors=[ColorEntry(name="Only", hex="#ffffff")],
        )
        save_palette(replacement, self.palette_path)
        code, _, stderr = run_cli(
            "install",
            str(self.palette_path),
            "--data-dir",
            str(self.data_dir),
            "--replace",
        )
        self.assertEqual(code, 0, stderr)
        data = self._load_store().load()
        self.assertEqual(len(data.projects), 1)
        self.assertEqual(len(data.projects[0].colors), 1)
        self.assertEqual(data.active_project_id, data.projects[0].id)

    def test_install_accepts_css_and_custom_name(self) -> None:
        source = self.directory / "upstream.css"
        source.write_text(":root { --surface: #101014; }", encoding="utf-8")
        code, _, stderr = run_cli(
            "install",
            str(source),
            "--name",
            "Imported",
            "--data-dir",
            str(self.data_dir),
        )
        self.assertEqual(code, 0, stderr)
        data = self._load_store().load()
        self.assertEqual(data.projects[0].name, "Imported")
        self.assertEqual(len(data.projects[0].colors), 1)

    def test_install_import_alias(self) -> None:
        code, _, stderr = run_cli(
            "import", str(self.palette_path), "--data-dir", str(self.data_dir)
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(len(self._load_store().load().projects), 1)


class ListTests(CliTestBase):
    def test_list_empty(self) -> None:
        data_dir = self.directory / "data"
        code, stdout, _ = run_cli("list", "--data-dir", str(data_dir))
        self.assertEqual(code, 0)
        self.assertIn("No projects installed.", stdout)

        code, stdout, _ = run_cli("list", "--data-dir", str(data_dir), "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout), [])

    def test_list_reports_installed_projects(self) -> None:
        data_dir = self.directory / "data"
        run_cli("install", str(self.palette_path), "--data-dir", str(data_dir))
        code, stdout, stderr = run_cli("list", "--data-dir", str(data_dir), "--json")
        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["name"], "Test Theme")
        self.assertEqual(payload[0]["colors"], 3)
        self.assertTrue(payload[0]["active"])

        code, stdout, _ = run_cli("list", "--data-dir", str(data_dir))
        self.assertEqual(code, 0)
        self.assertIn("Test Theme", stdout)
        self.assertIn("yes", stdout)


class SchemaAndEntryPointTests(CliTestBase):
    def test_schema_is_valid_json(self) -> None:
        code, stdout, stderr = run_cli("schema")
        self.assertEqual(code, 0, stderr)
        schema = json.loads(stdout)
        self.assertEqual(schema["properties"]["format"]["const"], "vcolor.palette")
        self.assertEqual(schema["required"], ["name", "colors"])

    def test_console_main_uses_command_arguments_directly(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cli.console_main(["schema"])
        self.assertEqual(code, 0, stderr.getvalue())
        self.assertIn('"vcolor.palette"', stdout.getvalue())

    def test_python_m_palette_dispatch_is_qt_free(self) -> None:
        script = (
            "import sys\n"
            "sys.argv = ['vcolor', 'palette', 'schema']\n"
            "from vcolor.__main__ import main\n"
            "assert main() == 0\n"
            "assert 'PySide6' not in sys.modules\n"
            "assert 'vcolor.app' not in sys.modules\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"vcolor.palette"', result.stdout)


if __name__ == "__main__":
    unittest.main()
