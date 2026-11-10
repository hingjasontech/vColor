"""Custom-painted widgets used throughout vColor."""

from __future__ import annotations

import math
from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from . import theme


def _repolish(widget: QWidget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


class ElidedLabel(QLabel):
    """QLabel that truncates gracefully while keeping the full text in a tooltip."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__("", parent)
        self._full_text = text
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setToolTip(text)
        self._update_elided()

    def setText(self, text: str) -> None:
        self._full_text = text
        self.setToolTip(text)
        self._update_elided()

    def full_text(self) -> str:
        return self._full_text

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self) -> None:
        width = max(0, self.width())
        if width <= 0:
            super().setText(self._full_text)
            return
        metrics = QFontMetrics(self.font())
        super().setText(metrics.elidedText(self._full_text, Qt.TextElideMode.ElideRight, width))


def draw_icon(
    painter: QPainter,
    kind: str,
    rect: QRectF,
    color: QColor,
    pen_width: float = 1.7,
) -> None:
    """Draw a small, consistent line icon in ``rect``."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(color, pen_width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    cx, cy = x + w / 2.0, y + h / 2.0
    s = min(w, h)

    if kind == "copy":
        back = QRectF(cx - s * 0.31, cy - s * 0.39, s * 0.53, s * 0.53)
        front = QRectF(cx - s * 0.22, cy - s * 0.22, s * 0.53, s * 0.53)
        painter.drawRoundedRect(back, s * 0.09, s * 0.09)
        painter.drawRoundedRect(front, s * 0.09, s * 0.09)
    elif kind == "trash":
        painter.drawLine(QPointF(cx - s * 0.36, cy - s * 0.27), QPointF(cx + s * 0.36, cy - s * 0.27))
        painter.drawLine(QPointF(cx - s * 0.15, cy - s * 0.39), QPointF(cx + s * 0.15, cy - s * 0.39))
        body = QPainterPath()
        body.moveTo(cx - s * 0.29, cy - s * 0.20)
        body.lineTo(cx - s * 0.23, cy + s * 0.33)
        body.quadTo(cx - s * 0.21, cy + s * 0.41, cx - s * 0.11, cy + s * 0.41)
        body.lineTo(cx + s * 0.11, cy + s * 0.41)
        body.quadTo(cx + s * 0.21, cy + s * 0.41, cx + s * 0.23, cy + s * 0.33)
        body.lineTo(cx + s * 0.29, cy - s * 0.20)
        painter.drawPath(body)
        painter.drawLine(QPointF(cx - s * 0.11, cy - s * 0.06), QPointF(cx - s * 0.08, cy + s * 0.24))
        painter.drawLine(QPointF(cx + s * 0.11, cy - s * 0.06), QPointF(cx + s * 0.08, cy + s * 0.24))
    elif kind == "plus":
        painter.drawLine(QPointF(cx - s * 0.33, cy), QPointF(cx + s * 0.33, cy))
        painter.drawLine(QPointF(cx, cy - s * 0.33), QPointF(cx, cy + s * 0.33))
    elif kind == "chevron-down":
        path = QPainterPath()
        path.moveTo(cx - s * 0.24, cy - s * 0.09)
        path.lineTo(cx, cy + s * 0.15)
        path.lineTo(cx + s * 0.24, cy - s * 0.09)
        painter.drawPath(path)
    elif kind == "chevron-right":
        path = QPainterPath()
        path.moveTo(cx - s * 0.09, cy - s * 0.24)
        path.lineTo(cx + s * 0.15, cy)
        path.lineTo(cx - s * 0.09, cy + s * 0.24)
        painter.drawPath(path)
    elif kind == "check":
        path = QPainterPath()
        path.moveTo(cx - s * 0.34, cy + s * 0.01)
        path.lineTo(cx - s * 0.09, cy + s * 0.25)
        path.lineTo(cx + s * 0.35, cy - s * 0.26)
        painter.drawPath(path)
    elif kind == "close":
        painter.drawLine(QPointF(cx - s * 0.28, cy - s * 0.28), QPointF(cx + s * 0.28, cy + s * 0.28))
        painter.drawLine(QPointF(cx + s * 0.28, cy - s * 0.28), QPointF(cx - s * 0.28, cy + s * 0.28))
    elif kind == "eyedropper":
        path = QPainterPath()
        path.moveTo(cx - s * 0.32, cy + s * 0.32)
        path.lineTo(cx - s * 0.28, cy + s * 0.14)
        path.lineTo(cx + s * 0.14, cy - s * 0.28)
        path.lineTo(cx + s * 0.31, cy - s * 0.11)
        path.lineTo(cx - s * 0.11, cy + s * 0.31)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(cx + s * 0.18, cy - s * 0.22), QPointF(cx + s * 0.34, cy - s * 0.38))
    elif kind == "pencil":
        path = QPainterPath()
        path.moveTo(cx - s * 0.34, cy + s * 0.34)
        path.lineTo(cx - s * 0.24, cy + s * 0.08)
        path.lineTo(cx + s * 0.18, cy - s * 0.34)
        path.lineTo(cx + s * 0.34, cy - s * 0.18)
        path.lineTo(cx - s * 0.08, cy + s * 0.24)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(
            QPointF(cx - s * 0.24, cy + s * 0.08),
            QPointF(cx - s * 0.08, cy + s * 0.24),
        )
    elif kind == "external":
        painter.drawRoundedRect(QRectF(cx - s * 0.34, cy - s * 0.26, s * 0.46, s * 0.46), 2, 2)
        painter.drawLine(QPointF(cx - s * 0.02, cy - s * 0.30), QPointF(cx + s * 0.34, cy - s * 0.30))
        painter.drawLine(QPointF(cx + s * 0.34, cy - s * 0.30), QPointF(cx + s * 0.34, cy + s * 0.05))
        painter.drawLine(QPointF(cx + s * 0.08, cy - s * 0.04), QPointF(cx + s * 0.34, cy - s * 0.30))
    elif kind == "arrow-left":
        painter.drawLine(QPointF(cx - s * 0.26, cy), QPointF(cx + s * 0.30, cy))
        arrow = QPainterPath()
        arrow.moveTo(cx - s * 0.08, cy - s * 0.20)
        arrow.lineTo(cx - s * 0.28, cy)
        arrow.lineTo(cx - s * 0.08, cy + s * 0.20)
        painter.drawPath(arrow)
    elif kind == "import":
        left = cx - s * 0.34
        right = cx + s * 0.34
        bottom = cy + s * 0.30
        path = QPainterPath()
        path.moveTo(left, cy - s * 0.02)
        path.lineTo(left, bottom)
        path.lineTo(right, bottom)
        path.lineTo(right, cy - s * 0.02)
        painter.drawPath(path)
        painter.drawLine(
            QPointF(cx, cy - s * 0.38),
            QPointF(cx, cy + s * 0.10),
        )
        arrow = QPainterPath()
        arrow.moveTo(cx - s * 0.16, cy - s * 0.06)
        arrow.lineTo(cx, cy + s * 0.12)
        arrow.lineTo(cx + s * 0.16, cy - s * 0.06)
        painter.drawPath(arrow)
    elif kind == "settings":
        painter.drawEllipse(
            QRectF(cx - s * 0.27, cy - s * 0.27, s * 0.54, s * 0.54)
        )
        painter.drawEllipse(
            QRectF(cx - s * 0.10, cy - s * 0.10, s * 0.20, s * 0.20)
        )
        for index in range(8):
            angle = math.pi * index / 4.0 + math.pi / 8.0
            painter.drawLine(
                QPointF(cx + math.cos(angle) * s * 0.27, cy + math.sin(angle) * s * 0.27),
                QPointF(cx + math.cos(angle) * s * 0.41, cy + math.sin(angle) * s * 0.41),
            )
    else:
        painter.drawEllipse(QRectF(cx - s * 0.25, cy - s * 0.25, s * 0.5, s * 0.5))

    painter.restore()


class IconButton(QAbstractButton):
    """Square, flat icon button with a circular hover surface."""

    def __init__(
        self,
        kind: str,
        *,
        size: int = 36,
        icon_size: int = 18,
        color: str = theme.TEXT_MUTED,
        hover_color: str | None = None,
        hover_background: str = "#14FFFFFF",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.kind = kind
        self.icon_size = icon_size
        self.color = QColor(color)
        self.hover_color = QColor(hover_color or theme.TEXT)
        self.hover_background = QColor(hover_background)
        self._hover = False
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setIcon(QIcon())
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def enterEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self._hover and self.isEnabled():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.hover_background)
            painter.drawEllipse(self.rect().adjusted(1, 1, -1, -1))

        color = self.hover_color if self._hover and self.isEnabled() else self.color
        if not self.isEnabled():
            color = QColor(theme.TEXT_DIM)
        icon_rect = QRectF(
            (self.width() - self.icon_size) / 2.0,
            (self.height() - self.icon_size) / 2.0,
            self.icon_size,
            self.icon_size,
        )
        draw_icon(painter, self.kind, icon_rect, color)


class SidebarAction(QAbstractButton):
    """Flat libadwaita-style sidebar row with a line icon and label."""

    def __init__(
        self, kind: str, text: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.kind = kind
        self._hover = False
        self._selected = False
        self.setText(text)
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAccessibleName(text)
        font = QFont(self.font())
        font.setPixelSize(14)
        font.setWeight(QFont.Weight.Medium)
        self.setFont(font)

    def set_selected(self, selected: bool) -> None:
        if self._selected == selected:
            return
        self._selected = selected
        self.update()

    def enterEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)

        if self._selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 24))
            painter.drawRoundedRect(rect, 8, 8)
        elif self._hover or self.isDown():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 12 if not self.isDown() else 22))
            painter.drawRoundedRect(rect, 8, 8)

        icon_color = QColor(
            theme.TEXT if self._hover or self._selected else theme.TEXT_MUTED
        )
        draw_icon(
            painter,
            self.kind,
            QRectF(10, (self.height() - 16) / 2.0, 16, 16),
            icon_color,
            pen_width=1.6,
        )

        metrics = QFontMetrics(self.font())
        width = max(0, self.width() - 38)
        text = metrics.elidedText(
            self.text(), Qt.TextElideMode.ElideRight, width
        )
        painter.setPen(
            QColor(theme.TEXT if self._hover or self._selected else "#D7D7D7")
        )
        painter.drawText(
            QRectF(34, 0, width, self.height()),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            text,
        )

        if self.hasFocus():
            painter.setPen(QPen(QColor(theme.ACCENT), 1.2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)

        painter.end()


class ColorSwatch(QWidget):
    def __init__(self, color: str, diameter: int = 38, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(diameter, diameter)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        painter.setPen(QPen(QColor(255, 255, 255, 34), 1.0))
        painter.setBrush(self._color)
        painter.drawEllipse(rect)


class ColorRow(QFrame):
    copyRequested = Signal(str)
    editRequested = Signal(str)
    deleteRequested = Signal(str)

    def __init__(
        self,
        color_id: str,
        name: str,
        value: str,
        color: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.color_id = color_id
        self._color = color
        self._value = value
        self.setObjectName("ColorRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFixedHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to copy this color")
        self.setAccessibleName(f"Color {name}")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(16)

        self.swatch = ColorSwatch(color, 38)
        layout.addWidget(self.swatch)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        self.name_label = ElidedLabel(name)
        self.name_label.setObjectName("ColorName")
        self.name_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom
        )
        self.value_label = ElidedLabel(value)
        self.value_label.setObjectName("ColorValue")
        self.value_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.value_label)
        layout.addLayout(text_layout, 1)

        self.edit_button = IconButton(
            "pencil",
            size=36,
            icon_size=18,
            color=theme.TEXT_MUTED,
            hover_color=theme.TEXT,
        )
        self.edit_button.setToolTip("Edit color")
        self.edit_button.setAccessibleName("Edit color")
        self.edit_button.clicked.connect(lambda: self.editRequested.emit(self.color_id))
        layout.addWidget(self.edit_button)

        self.delete_button = IconButton(
            "trash",
            size=36,
            icon_size=18,
            color=theme.DANGER,
            hover_color=theme.DANGER,
            hover_background=theme.DANGER_BG,
        )
        self.delete_button.setToolTip("Delete color")
        self.delete_button.setAccessibleName("Delete color")
        self.delete_button.clicked.connect(lambda: self.deleteRequested.emit(self.color_id))
        layout.addWidget(self.delete_button)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.copyRequested.emit(self.color_id)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.editRequested.emit(self.color_id)
        super().mouseDoubleClickEvent(event)

    def build_context_menu(self) -> QMenu:
        menu = QMenu(self)
        edit = menu.addAction("Edit")
        copy = menu.addAction("Copy")
        menu.addSeparator()
        delete = menu.addAction("Delete")
        edit.triggered.connect(
            lambda _checked=False: self.editRequested.emit(self.color_id)
        )
        copy.triggered.connect(
            lambda _checked=False: self.copyRequested.emit(self.color_id)
        )
        delete.triggered.connect(
            lambda _checked=False: self.deleteRequested.emit(self.color_id)
        )
        return menu

    def contextMenuEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        menu = self.build_context_menu()
        menu.exec(event.globalPos())
        menu.deleteLater()


class ColorItem(QWidget):
    """A color tile with its copy action placed outside the tile."""

    copyRequested = Signal(str)
    editRequested = Signal(str)
    deleteRequested = Signal(str)

    def __init__(
        self,
        color_id: str,
        name: str,
        value: str,
        color: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.color_id = color_id
        self.setFixedHeight(72)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.copy_button = QPushButton("Copy")
        self.copy_button.setObjectName("CopyButton")
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setFixedSize(72, 34)
        self.copy_button.setToolTip(f"Copy {value}")
        self.copy_button.setAccessibleName("Copy color")
        self.copy_button.clicked.connect(lambda: self.copyRequested.emit(self.color_id))
        layout.addWidget(self.copy_button, 0, Qt.AlignmentFlag.AlignVCenter)

        self.row = ColorRow(color_id, name, value, color)
        self.row.copyRequested.connect(self.copyRequested.emit)
        self.row.editRequested.connect(self.editRequested.emit)
        self.row.deleteRequested.connect(self.deleteRequested.emit)
        layout.addWidget(self.row, 1)


class ProjectItem(QFrame):
    activated = Signal(str)
    renameRequested = Signal(str)
    duplicateRequested = Signal(str)
    deleteRequested = Signal(str)
    exportRequested = Signal(str)
    importRequested = Signal(str)

    def __init__(
        self,
        project_id: str,
        name: str,
        color_count: int,
        *,
        selected: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.project_id = project_id
        self.setObjectName("ProjectItem")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"{color_count} color{'s' if color_count != 1 else ''}")
        self.setAccessibleName(f"Project {name}")
        self.setProperty("selected", selected)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)
        label = ElidedLabel(name)
        label.setObjectName("ProjectName")
        label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(label)

    def set_selected(self, selected: bool) -> None:
        if bool(self.property("selected")) == selected:
            return
        self.setProperty("selected", selected)
        _repolish(self)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(self.project_id)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.renameRequested.emit(self.project_id)
        super().mouseDoubleClickEvent(event)

    def build_context_menu(self) -> QMenu:
        menu = QMenu(self)
        rename = menu.addAction("Rename project")
        duplicate = menu.addAction("Duplicate project")
        export = menu.addAction("Export project...")
        import_action = menu.addAction("Import colors...")
        menu.addSeparator()
        delete = menu.addAction("Delete project")
        rename.triggered.connect(
            lambda _checked=False: self.renameRequested.emit(self.project_id)
        )
        duplicate.triggered.connect(
            lambda _checked=False: self.duplicateRequested.emit(self.project_id)
        )
        export.triggered.connect(
            lambda _checked=False: self.exportRequested.emit(self.project_id)
        )
        import_action.triggered.connect(
            lambda _checked=False: self.importRequested.emit(self.project_id)
        )
        delete.triggered.connect(
            lambda _checked=False: self.deleteRequested.emit(self.project_id)
        )
        return menu

    def contextMenuEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        menu = self.build_context_menu()
        menu.exec(event.globalPos())
        menu.deleteLater()


class _ComboItemDelegate(QStyledItemDelegate):
    """Paint dropdown rows with a rounded accent highlight, menu-style."""

    def paint(self, painter, option, index) -> None:  # type: ignore[no-untyped-def]
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(theme.ACCENT))
            painter.drawRoundedRect(QRectF(option.rect).adjusted(5, 1, -5, -1), 8, 8)
        elif selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(theme.SURFACE_ACTIVE))
            painter.drawRoundedRect(QRectF(option.rect).adjusted(5, 1, -5, -1), 8, 8)
        painter.setPen(QColor("#FFFFFF") if hovered else QColor(theme.TEXT))
        text_rect = option.rect.adjusted(16, 0, -16, 0)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            str(index.data(Qt.ItemDataRole.DisplayRole) or ""),
        )
        painter.restore()

    def sizeHint(self, option, index):  # type: ignore[no-untyped-def]
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), 36))
        return size


class FormatComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("FormatSelect")
        self.setFixedWidth(192)
        self.setFixedHeight(34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setPlaceholderText("Select...")
        self.setAccessibleName("Color format")
        self.setItemDelegate(_ComboItemDelegate(self))
        self.view().setMouseTracking(True)

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color = QColor(theme.TEXT_MUTED if self.isEnabled() else theme.TEXT_DIM)
        draw_icon(
            painter,
            "chevron-down",
            QRectF(self.width() - 27, (self.height() - 14) / 2, 14, 14),
            color,
            pen_width=1.6,
        )


class EmptyState(QWidget):
    actionTriggered = Signal()

    def __init__(
        self,
        title: str,
        body: str,
        action: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 40, 0, 40)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setObjectName("EmptyTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        body_label = QLabel(body)
        body_label.setObjectName("EmptyBody")
        body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_label.setWordWrap(True)
        body_label.setFixedWidth(460)
        layout.addWidget(body_label)

        if action:
            layout.addSpacing(10)
            button = QPushButton(action)
            button.setObjectName("PillButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setAccessibleName(action)
            button.clicked.connect(self.actionTriggered.emit)
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch(1)


class Toast(QFrame):
    """Small transient notification anchored to the bottom of its parent."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(46)
        self.setVisible(False)
        self._action: Callable[[], None] | None = None

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(16, 0, 8, 0)
        self._layout.setSpacing(12)
        self._icon = IconButton("check", size=24, icon_size=15, color=theme.SUCCESS)
        self._icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._layout.addWidget(self._icon)
        self._label = QLabel()
        self._label.setStyleSheet("font-size: 14px; color: #F2F2F2;")
        self._layout.addWidget(self._label)
        self._action_button = QPushButton("Undo")
        self._action_button.setObjectName("ToastAction")
        self._action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._action_button.clicked.connect(self._run_action)
        self._layout.addWidget(self._action_button)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(
        self,
        message: str,
        *,
        action_label: str | None = None,
        action: Callable[[], None] | None = None,
        duration: int = 2400,
        kind: str = "check",
    ) -> None:
        self._label.setText(message)
        self._action = action
        self._icon.kind = kind
        icon_color = QColor(theme.DANGER if kind == "error" else theme.SUCCESS)
        self._icon.color = icon_color
        self._icon.hover_color = icon_color
        self._icon.update()
        self._action_button.setVisible(bool(action_label and action))
        if action_label:
            self._action_button.setText(action_label)
        self._layout.activate()
        self.adjustSize()
        self.setFixedHeight(46)
        self.reposition()
        self.show()
        self.raise_()
        self._timer.start(duration)

    def reposition(self) -> None:
        parent = self.parentWidget()
        if not parent:
            return
        self.move(
            max(16, (parent.width() - self.width()) // 2),
            max(16, parent.height() - self.height() - 30),
        )

    def _run_action(self) -> None:
        self._timer.stop()
        self.hide()
        if self._action:
            self._action()
        self._action = None


class UpdateBanner(QFrame):
    """Non-blocking notice that a newer vColor release exists."""

    downloadRequested = Signal()
    dismissRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("UpdateBanner")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(46)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(10)

        icon = IconButton("external", size=26, icon_size=15, color=theme.ACCENT)
        icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(icon)

        self._label = QLabel()
        self._label.setObjectName("UpdateBannerLabel")
        layout.addWidget(self._label, 1)

        self.download_button = QPushButton("Download")
        self.download_button.setObjectName("UpdateBannerAction")
        self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_button.setFixedHeight(30)
        self.download_button.setAccessibleName("Download update")
        self.download_button.clicked.connect(self.downloadRequested.emit)
        layout.addWidget(self.download_button)

        self.dismiss_button = IconButton(
            "close", size=30, icon_size=14, color=theme.TEXT_DIM
        )
        self.dismiss_button.setToolTip("Dismiss this update")
        self.dismiss_button.setAccessibleName("Dismiss update")
        self.dismiss_button.clicked.connect(self.dismissRequested.emit)
        layout.addWidget(self.dismiss_button)

    def set_version(self, version: str) -> None:
        self._label.setText(f"vColor {version} is available")


class ColorPreview(QWidget):
    """Rounded color preview with a subtle border, used in dialogs."""

    clicked = Signal()

    def __init__(self, color: str = "#3B82F6", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(104, 104)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Open the system color picker")

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor(255, 255, 255, 38), 1.2))
        painter.setBrush(self._color)
        painter.drawRoundedRect(rect, 22, 22)


class ContrastPill(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ContrastPill")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(34)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        self._label = QLabel()
        self._label.setStyleSheet("font-size: 12px; color: #D8D8D8;")
        self._grade = QLabel()
        self._grade.setStyleSheet("font-size: 12px; font-weight: 600; color: #3DD68C;")
        layout.addWidget(self._label)
        layout.addWidget(self._grade)

    def set_values(self, label: str, ratio: float, grade: str) -> None:
        self._label.setText(label)
        self._grade.setText(f"{grade}  {ratio:.1f}:1")
        if grade == "Fail":
            color = theme.DANGER
        elif grade == "AA Large":
            color = theme.WARNING
        else:
            color = theme.SUCCESS
        self._grade.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {color};"
        )
