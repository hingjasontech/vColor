"""Libadwaita-inspired preferences page."""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QColorDialog,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .color_utils import DEFAULT_ACCENT
from .widgets import FormatComboBox, IconButton, draw_icon


def build_page_header(title: str, back_tooltip: str) -> tuple[QWidget, IconButton]:
    """Build the flat, centered libadwaita-style page header."""
    header = QWidget()
    header.setObjectName("SettingsHeader")
    header.setFixedHeight(56)

    layout = QHBoxLayout(header)
    layout.setContentsMargins(48, 0, 48, 0)
    layout.setSpacing(0)

    back_button = IconButton(
        "arrow-left",
        size=36,
        icon_size=18,
        color=theme.TEXT_MUTED,
        hover_color=theme.TEXT,
    )
    back_button.setToolTip(back_tooltip)
    back_button.setAccessibleName(back_tooltip)
    layout.addWidget(back_button, 0, Qt.AlignmentFlag.AlignVCenter)

    label = QLabel(title)
    label.setObjectName("SettingsHeaderTitle")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label, 1)

    spacer = QWidget()
    spacer.setFixedWidth(36)
    layout.addWidget(spacer)
    return header, back_button


class Chevron(QWidget):
    """A non-interactive trailing chevron for navigation rows."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        draw_icon(
            painter,
            "chevron-right",
            QRectF(self.rect()),
            QColor(theme.TEXT_DIM),
            pen_width=1.6,
        )


class Switch(QAbstractButton):
    """Pill-shaped switch matching the libadwaita dark style."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(48, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._hover = False
        self.toggled.connect(lambda _checked: self.update())

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

        track = QRectF(1, 3, self.width() - 2, self.height() - 6)
        radius = track.height() / 2.0
        if self.isChecked():
            color = QColor(theme.ACCENT_HOVER if self._hover else theme.ACCENT)
        elif self._hover:
            color = QColor(255, 255, 255, 48)
        else:
            color = QColor(255, 255, 255, 32)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(track, radius, radius)

        knob = self.height() - 8
        x = track.right() - knob - 2 if self.isChecked() else track.left() + 2
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QRectF(x, (self.height() - knob) / 2.0, knob, knob))

        if self.hasFocus():
            painter.setPen(QPen(QColor(theme.ACCENT), 1.4))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(track.adjusted(-1, -1, 1, 1), radius + 1, radius + 1)

        painter.end()


class AccentColorButton(QAbstractButton):
    """A round color swatch that opens the system color picker."""

    def __init__(
        self, color: str = DEFAULT_ACCENT, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(34, 34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip("Choose accent color")
        self.setAccessibleName("Accent color")

    def color(self) -> str:
        return self._color.name()

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        painter.setPen(QPen(QColor(255, 255, 255, 46), 1.2))
        painter.setBrush(self._color)
        painter.drawEllipse(rect)

        if self.hasFocus():
            painter.setPen(QPen(QColor(theme.TEXT), 1.4))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(rect.adjusted(-2, -2, 2, 2))

        painter.end()


class SettingsRow(QWidget):
    """A title/subtitle row with an optional control at the trailing edge."""

    activated = Signal()

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        control: QWidget | None = None,
        parent: QWidget | None = None,
        *,
        clickable: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(58)
        self._clickable = clickable
        self._hover = False
        self._first = True
        self._last = True
        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(18)

        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("SettingsRowTitle")
        text.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("SettingsRowSubtitle")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setVisible(bool(subtitle))
        text.addWidget(self.subtitle_label)

        layout.addLayout(text, 1)
        if control is not None:
            layout.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if (
            self._clickable
            and event.button() == Qt.MouseButton.LeftButton
            and self.rect().contains(event.position().toPoint())
        ):
            self.activated.emit()
        super().mouseReleaseEvent(event)

    def set_position(self, *, first: bool, last: bool) -> None:
        self._first = first
        self._last = last
        self.update()

    def enterEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if self._clickable and event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
            Qt.Key.Key_Space,
        ):
            self.activated.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if self._clickable and self._hover and self.isEnabled():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 12))
            rect = QRectF(self.rect())
            radius = 0.0
            if self._first and self._last:
                radius = 11.0
            elif self._first:
                rect.adjust(0, 0, 0, 11)
                radius = 11.0
            elif self._last:
                rect.adjust(0, -11, 0, 0)
                radius = 11.0
            painter.drawRoundedRect(rect, radius, radius)
            painter.end()

        super().paintEvent(event)
        if self._clickable and self.hasFocus():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(QPen(QColor(theme.ACCENT), 1.4))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(
                QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5), 9, 9
            )
            painter.end()


class SettingsGroup(QWidget):
    """A libadwaita preference group: a caption above a rounded card."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        caption = QLabel(title)
        caption.setObjectName("SettingsGroupTitle")
        layout.addWidget(caption)

        card = QFrame()
        card.setObjectName("SettingsGroupCard")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.card_layout = QVBoxLayout(card)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(0)
        layout.addWidget(card)

        self._rows: list[SettingsRow] = []

    def add_row(self, row: SettingsRow) -> None:
        if self._rows:
            self._rows[-1].set_position(first=False, last=False)
            divider = QFrame()
            divider.setObjectName("SettingsDivider")
            divider.setFixedHeight(1)
            self.card_layout.addWidget(divider)
        row.set_position(first=not self._rows, last=True)
        self.card_layout.addWidget(row)
        self._rows.append(row)


class SettingsPage(QWidget):
    """Preferences for appearance, updates, and about."""

    backRequested = Signal()
    formatChanged = Signal(str)
    showHexHashChanged = Signal(bool)
    systemAccentChanged = Signal(bool)
    accentColorChanged = Signal(str)
    updateCheckChanged = Signal(bool)
    checkNowRequested = Signal()
    shortcutsRequested = Signal()
    sourceRequested = Signal()

    def __init__(self, version: str = "0.0.0", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsPage")
        self._version = version
        self._accent_color = DEFAULT_ACCENT

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QWidget()
        content.setObjectName("SettingsContent")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(48, 28, 48, 48)
        content_layout.setSpacing(0)

        self.column = QWidget()
        self.column.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        column = QVBoxLayout(self.column)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(24)

        column.addWidget(self._build_appearance_group())
        column.addWidget(self._build_keyboard_group())
        column.addWidget(self._build_updates_group())
        column.addWidget(self._build_about_group())
        column.addStretch(1)

        content_layout.addStretch(1)
        content_layout.addWidget(self.column)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self._update_column_width()

    def _build_header(self) -> QWidget:
        header, self.back_button = build_page_header(
            "Settings", "Back to projects"
        )
        self.back_button.clicked.connect(self.backRequested.emit)
        return header

    def _build_appearance_group(self) -> SettingsGroup:
        group = SettingsGroup("Appearance")

        self.system_accent_switch = Switch()
        self.system_accent_switch.setAccessibleName("Follow the system accent color")
        self.system_accent_switch.toggled.connect(self.systemAccentChanged.emit)
        group.add_row(
            SettingsRow(
                "Follow system accent color",
                "Match the accent color used by your operating system.",
                self.system_accent_switch,
            )
        )

        self.accent_button = AccentColorButton(self._accent_color)
        self.accent_button.clicked.connect(self._choose_accent_color)
        group.add_row(
            SettingsRow(
                "Accent color",
                "Used for highlights, links, and controls across vColor.",
                self.accent_button,
            )
        )

        self.format_combo = FormatComboBox()
        self.format_combo.addItems(["HEX", "RGB", "HSL", "OKLCH"])
        self.format_combo.setAccessibleName("Color format")
        self.format_combo.currentTextChanged.connect(self.formatChanged.emit)
        group.add_row(
            SettingsRow(
                "Color format",
                "Used in the color list and when copying values.",
                self.format_combo,
            )
        )

        self.hex_hash_switch = Switch()
        self.hex_hash_switch.setAccessibleName("Show a number sign in HEX values")
        self.hex_hash_switch.toggled.connect(self.showHexHashChanged.emit)
        group.add_row(
            SettingsRow(
                "Show # in HEX values",
                "Include the leading # when displaying and copying HEX colors.",
                self.hex_hash_switch,
            )
        )
        return group

    def _build_keyboard_group(self) -> SettingsGroup:
        group = SettingsGroup("Keyboard")

        row = SettingsRow(
            "Keyboard shortcuts",
            "View and change the shortcuts used in vColor.",
            Chevron(),
            clickable=True,
        )
        row.setToolTip("View and change keyboard shortcuts")
        row.setAccessibleName("Keyboard shortcuts")
        row.activated.connect(self.shortcutsRequested.emit)
        group.add_row(row)
        return group

    def _build_updates_group(self) -> SettingsGroup:
        group = SettingsGroup("Updates")

        self.update_switch = Switch()
        self.update_switch.setAccessibleName("Check for updates automatically")
        self.update_switch.toggled.connect(self.updateCheckChanged.emit)
        group.add_row(
            SettingsRow(
                "Check for updates automatically",
                "vColor looks for a new GitHub release once every 24 hours.",
                self.update_switch,
            )
        )

        self.check_button = QPushButton("Check now")
        self.check_button.setObjectName("SecondaryButton")
        self.check_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_button.setAccessibleName("Check for updates now")
        self.check_button.clicked.connect(self.checkNowRequested.emit)
        group.add_row(
            SettingsRow(
                "Check now",
                "Look for a new release without waiting.",
                self.check_button,
            )
        )
        return group

    def _build_about_group(self) -> SettingsGroup:
        group = SettingsGroup("About")
        self.version_label = QLabel(f"Version {self._version}")
        self.version_label.setObjectName("SettingsValue")
        group.add_row(
            SettingsRow(
                "vColor",
                "A fast, focused desktop color project manager.",
                self.version_label,
            )
        )

        self.source_button = QPushButton("Open GitHub")
        self.source_button.setObjectName("SecondaryButton")
        self.source_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.source_button.setAccessibleName("Open the vColor source code on GitHub")
        self.source_button.clicked.connect(self.sourceRequested.emit)
        group.add_row(
            SettingsRow(
                "Source code",
                "Browse the vColor source code on GitHub.",
                self.source_button,
            )
        )
        return group

    def _choose_accent_color(self) -> None:
        from .dialogs import run_dialog

        picker = QColorDialog(QColor(self._accent_color), self)
        picker.setWindowTitle("Choose accent color")
        if run_dialog(picker) != QDialog.DialogCode.Accepted:
            return
        color = picker.selectedColor()
        if not color.isValid():
            return
        value = color.name()
        self.set_use_system_accent(False)
        self.set_accent_color(value)
        self.accentColorChanged.emit(value)

    def set_use_system_accent(self, enabled: bool) -> None:
        with QSignalBlocker(self.system_accent_switch):
            self.system_accent_switch.setChecked(enabled)

    def set_accent_color(self, value: str) -> None:
        self._accent_color = value
        self.accent_button.set_color(value)

    def set_accent(self, use_system: bool, value: str) -> None:
        self.set_use_system_accent(use_system)
        self.set_accent_color(value)

    def set_format(self, value: str) -> None:
        with QSignalBlocker(self.format_combo):
            self.format_combo.setCurrentText(value)

    def set_show_hex_hash(self, enabled: bool) -> None:
        with QSignalBlocker(self.hex_hash_switch):
            self.hex_hash_switch.setChecked(enabled)

    def set_update_check(self, enabled: bool) -> None:
        with QSignalBlocker(self.update_switch):
            self.update_switch.setChecked(enabled)

    def set_checking(self, checking: bool) -> None:
        self.check_button.setEnabled(not checking)
        self.check_button.setText("Checking…" if checking else "Check now")

    def set_version(self, version: str) -> None:
        self._version = version
        self.version_label.setText(f"Version {version}")

    def load(
        self,
        *,
        display_format: str,
        show_hex_hash: bool,
        use_system_accent: bool,
        accent_color: str,
        update_check: bool,
        version: str | None = None,
    ) -> None:
        self.set_format(display_format)
        self.set_show_hex_hash(show_hex_hash)
        self.set_accent(use_system_accent, accent_color)
        self.set_update_check(update_check)
        if version is not None:
            self.set_version(version)

    def _update_column_width(self) -> None:
        available = max(0, self.width() - 96)
        self.column.setFixedWidth(min(660, available))

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self._update_column_width()
