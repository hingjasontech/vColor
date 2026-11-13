"""Render the README screenshot from the current UI.

Run from the repository root:

    uv run python scripts/screenshot.py

The script uses Qt's offscreen platform, so it works without opening a window.
Regenerate ``docs/screenshot.png`` whenever the interface changes.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QFont, QFontDatabase  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from vcolor import theme  # noqa: E402
from vcolor.color_utils import DEFAULT_ACCENT  # noqa: E402
from vcolor.main_window import MainWindow  # noqa: E402
from vcolor.models import AppData, ColorEntry, PaletteStore, Project  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "screenshot.png"
WIDTH = 1920
HEIGHT = 1080

COLORS = [
    ("Background", "#0b0d12"),
    ("Surface", "#151a23"),
    ("Foreground", "#e6edf7"),
    ("Muted", "#8b98ab"),
    ("Accent", DEFAULT_ACCENT),
    ("Success", "#3dd68c"),
    ("Warning", "#f5a524"),
    ("Danger", "#ff7b84"),
]


def build_data() -> AppData:
    website = Project(
        name="Website",
        colors=[ColorEntry(name=name, hex=hex_value) for name, hex_value in COLORS],
        favorite=True,
    )
    mobile = Project(
        name="Mobile app",
        colors=[ColorEntry(name=name, hex=hex_value) for name, hex_value in COLORS[:4]],
    )
    brand = Project(
        name="Brand",
        colors=[ColorEntry(name="Accent", hex=DEFAULT_ACCENT)],
    )
    return AppData(
        projects=[website, mobile, brand],
        active_project_id=website.id,
        use_system_accent=False,
        accent_color=DEFAULT_ACCENT,
    )


def load_font(app: QApplication) -> str:
    path = ROOT / "vcolor" / "resources" / "fonts" / "InterVariable.ttf"
    family = "Inter Variable"
    if path.exists():
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id >= 0:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                family = families[0]
    font = QFont(family)
    font.setPixelSize(14)
    app.setFont(font)
    return family


def main() -> int:
    import tempfile

    app = QApplication([])
    app.setStyle("Fusion")
    family = load_font(app)
    app.setStyleSheet(theme.build_stylesheet(family))

    with tempfile.TemporaryDirectory() as directory:
        store = PaletteStore(Path(directory) / "palettes.json")
        window = MainWindow(store)
        window._loaded = True
        window.set_data(build_data())
        window.resize(WIDTH, HEIGHT)
        window.show()
        app.processEvents()

    if not window.grab().save(str(OUTPUT)):
        raise SystemExit(f"Could not write {OUTPUT}")
    window.close()
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
