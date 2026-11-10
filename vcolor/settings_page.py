"""Libadwaita-inspired preferences page."""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
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
from .widgets import FormatComboBox, IconButton


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


class SettingsRow(QWidget):
    """A title/subtitle row with an optional control at the trailing edge."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        control: QWidget | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(58)

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

        self._row_count = 0

    def add_row(self, row: SettingsRow) -> None:
        if self._row_count:
            divider = QFrame()
            divider.setObjectName("SettingsDivider")
            divider.setFixedHeight(1)
            self.card_layout.addWidget(divider)
        self.card_layout.addWidget(row)
        self._row_count += 1


class SettingsPage(QWidget):
    """Preferences for appearance, updates, projects, and about."""

    backRequested = Signal()
    formatChanged = Signal(str)
    updateCheckChanged = Signal(bool)
    checkNowRequested = Signal()
    openInboxRequested = Signal()

    def __init__(self, version: str = "0.0.0", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsPage")
        self._version = version

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
        column.addWidget(self._build_updates_group())
        column.addWidget(self._build_projects_group())
        column.addWidget(self._build_about_group())
        column.addStretch(1)

        content_layout.addStretch(1)
        content_layout.addWidget(self.column)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self._update_column_width()

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("SettingsHeader")
        header.setFixedHeight(56)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(0)

        self.back_button = IconButton(
            "arrow-left",
            size=36,
            icon_size=18,
            color=theme.TEXT_MUTED,
            hover_color=theme.TEXT,
        )
        self.back_button.setToolTip("Back to projects")
        self.back_button.setAccessibleName("Back to projects")
        self.back_button.clicked.connect(self.backRequested.emit)
        layout.addWidget(self.back_button, 0, Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("Settings")
        title.setObjectName("SettingsHeaderTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, 1)

        spacer = QWidget()
        spacer.setFixedWidth(36)
        layout.addWidget(spacer)
        return header

    def _build_appearance_group(self) -> SettingsGroup:
        group = SettingsGroup("Appearance")
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

    def _build_projects_group(self) -> SettingsGroup:
        group = SettingsGroup("Projects")

        self.open_inbox_button = QPushButton("Open")
        self.open_inbox_button.setObjectName("SecondaryButton")
        self.open_inbox_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_inbox_button.setAccessibleName("Open project inbox")
        self.open_inbox_button.clicked.connect(self.openInboxRequested.emit)
        group.add_row(
            SettingsRow(
                "Project inbox",
                "Open the folder where new projects from AI assistants arrive.",
                self.open_inbox_button,
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
        return group

    def set_format(self, value: str) -> None:
        with QSignalBlocker(self.format_combo):
            self.format_combo.setCurrentText(value)

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
        update_check: bool,
        version: str | None = None,
    ) -> None:
        self.set_format(display_format)
        self.set_update_check(update_check)
        if version is not None:
            self.set_version(version)

    def _update_column_width(self) -> None:
        available = max(0, self.width() - 96)
        self.column.setFixedWidth(min(660, available))

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self._update_column_width()
