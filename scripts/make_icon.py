#!/usr/bin/env python3
"""Generate the application icon (PNG + multi-resolution ICO/ICNS) from icon.svg."""

from __future__ import annotations

import struct
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "vcolor" / "resources"
SVG_SOURCE = RESOURCES / "icon.svg"


def render(size: int) -> QImage:
    renderer = QSvgRenderer(str(SVG_SOURCE))
    if not renderer.isValid():
        raise RuntimeError(f"Could not load {SVG_SOURCE}")

    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # Leave a small transparent margin so platform icon masks do not clip the tile.
    margin = size * 0.04
    rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    renderer.render(painter, rect)

    painter.end()
    return image


def write_icns(path: Path, entries: list[tuple[str, int]]) -> None:
    payloads: list[bytes] = []
    for kind, size in entries:
        image = render(size)
        temp = path.with_suffix(f".{kind}.png")
        image.save(str(temp), "PNG")
        payload = temp.read_bytes()
        temp.unlink()
        payloads.append(
            kind.encode("ascii") + struct.pack(">I", len(payload) + 8) + payload
        )
    total_size = 8 + sum(len(payload) for payload in payloads)
    path.write_bytes(b"icns" + struct.pack(">I", total_size) + b"".join(payloads))


def write_ico(path: Path, sizes: list[int]) -> None:
    images = [render(size) for size in sizes]
    payloads: list[bytes] = []
    for image in images:
        temp = path.with_suffix(f".{image.width()}.png")
        image.save(str(temp), "PNG")
        payloads.append(temp.read_bytes())
        temp.unlink()

    header = struct.pack("<HHH", 0, 1, len(images))
    directory = bytearray()
    offset = 6 + 16 * len(images)
    for image, payload in zip(images, payloads, strict=True):
        size = image.width()
        directory.extend(
            struct.pack(
                "<BBBBHHII",
                0 if size >= 256 else size,
                0 if size >= 256 else size,
                0,
                0,
                1,
                32,
                len(payload),
                offset,
            )
        )
        offset += len(payload)
    path.write_bytes(header + directory + b"".join(payloads))


def main() -> None:
    app = QApplication([])  # required for QImage painting
    RESOURCES.mkdir(parents=True, exist_ok=True)
    large = render(512)
    large.save(str(RESOURCES / "icon.png"), "PNG")
    write_ico(RESOURCES / "icon.ico", [16, 24, 32, 48, 64, 128, 256])
    write_icns(
        RESOURCES / "icon.icns",
        [
            ("icp4", 16),
            ("icp5", 32),
            ("icp6", 64),
            ("ic07", 128),
            ("ic08", 256),
            ("ic09", 512),
            ("ic10", 1024),
        ],
    )
    print(f"Wrote {RESOURCES / 'icon.png'}")
    print(f"Wrote {RESOURCES / 'icon.ico'}")
    print(f"Wrote {RESOURCES / 'icon.icns'}")
    app.quit()


if __name__ == "__main__":
    main()
