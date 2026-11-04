"""vColor application entry point."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPalette
from PySide6.QtWidgets import QApplication

from . import theme
from .main_window import MainWindow
from .models import PaletteStore, default_data_dir

__version__ = "1.0.0"


def _resource_path(*parts: str) -> Path:
    return Path(__file__).resolve().parent.joinpath("resources", *parts)


def _apply_dark_palette(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(theme.APP_BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(theme.TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(theme.SURFACE_INPUT))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme.SURFACE))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#111111"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(theme.TEXT))
    palette.setColor(QPalette.ColorRole.Text, QColor(theme.TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(theme.SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme.TEXT))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Link, QColor(theme.ACCENT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(theme.ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(theme.TEXT_DIM))
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor(theme.TEXT_DIM),
    )
    app.setPalette(palette)


def _load_font(app: QApplication) -> str:
    path = _resource_path("fonts", "InterVariable.ttf")
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vcolor",
        description="A fast, focused desktop color palette manager.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        help="Override the application data directory (useful for testing).",
    )
    parser.add_argument(
        "--benchmark-startup",
        action="store_true",
        help="Print time to first event-loop tick and exit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"vColor {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    started = time.perf_counter()
    args = build_parser().parse_args(argv)

    QApplication.setApplicationName("vColor")
    QApplication.setApplicationDisplayName("vColor")
    QApplication.setOrganizationName("vColor")
    app = QApplication([sys.argv[0]])
    app.setStyle("Fusion")
    _apply_dark_palette(app)
    family = _load_font(app)
    app.setStyleSheet(theme.build_stylesheet(family))

    icon_path = _resource_path("icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    data_dir = args.data_dir or default_data_dir()
    store = PaletteStore(data_dir / "palettes.json")
    window = MainWindow(store)
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    QTimer.singleShot(0, window.bootstrap)

    if args.benchmark_startup:
        def finish_benchmark() -> None:
            app.processEvents()
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            print(f"startup_ms={elapsed_ms:.1f}")
            app.quit()

        QTimer.singleShot(60, finish_benchmark)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
