"""Modal dialogs for project and color editing."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .color_utils import (
    ColorError,
    contrast_grade,
    contrast_ratio,
    format_color,
    is_hex,
    normalize_hex,
    srgb_to_display_p3,
)
from .widgets import ColorPreview, ContrastPill


def run_dialog(dialog: QDialog) -> int:
    """Run a dialog, working around GNOME's attached-modal-dialog behavior.

    On Linux, GNOME/Mutter's ``attach-modal-dialogs`` option (enabled by
    default on Ubuntu) glues a modal dialog to its parent window: dragging
    the dialog moves the whole app, and the dialog is positioned over the
    parent instead of the screen. Detaching the transient parent prevents
    Mutter from attaching the dialog. It is still application-modal, and is
    centered on the screen (or on the app's monitor for multi-monitor setups).
    """
    if sys.platform.startswith("linux"):
        window = dialog.parentWidget()
        if window is not None:
            window = window.window()
        dialog.setParent(None)
        # setParent(None) turns the widget into a generic top-level window;
        # restore the dialog type so window managers keep treating it as one.
        dialog.setWindowFlag(Qt.WindowType.Dialog, True)

        # Wayland compositors own window placement, so this move is a no-op
        # there; it still centers the dialog on X11 and other Linux sessions.
        screen = (
            window.screen() if window is not None else QGuiApplication.primaryScreen()
        )
        if screen is not None:
            dialog.adjustSize()
            available = screen.availableGeometry()
            dialog.move(
                available.x() + (available.width() - dialog.width()) // 2,
                available.y() + (available.height() - dialog.height()) // 2,
            )

    return dialog.exec()


class ProjectDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        title: str = "Create project",
        body: str = "Give this palette a name. You can rename it later.",
        action: str = "Create project",
        name: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(430)
        self.setMinimumHeight(230)

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 24, 26, 22)
        root.setSpacing(16)

        heading = QLabel(title)
        heading.setObjectName("DialogTitle")
        root.addWidget(heading)

        description = QLabel(body)
        description.setObjectName("DialogBody")
        description.setWordWrap(True)
        root.addWidget(description)

        field_label = QLabel("Project name")
        field_label.setObjectName("FieldLabel")
        root.addWidget(field_label)

        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("e.g. Website palette")
        self.name_input.setMaxLength(80)
        self.name_input.returnPressed.connect(self._accept_if_valid)
        root.addWidget(self.name_input)

        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setVisible(False)
        root.addWidget(self.error_label)

        root.addStretch(1)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("SecondaryButton")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        self.primary = QPushButton(action)
        self.primary.setObjectName("PrimaryButton")
        self.primary.setCursor(Qt.CursorShape.PointingHandCursor)
        self.primary.setDefault(True)
        self.primary.clicked.connect(self._accept_if_valid)
        buttons.addWidget(self.primary)
        root.addLayout(buttons)

        self.name_input.setFocus()
        self.name_input.selectAll()

    def _accept_if_valid(self) -> None:
        if not self.name_input.text().strip():
            self.error_label.setText("Enter a project name.")
            self.error_label.setVisible(True)
            self.name_input.setProperty("error", True)
            self.name_input.style().unpolish(self.name_input)
            self.name_input.style().polish(self.name_input)
            self.name_input.setFocus()
            return
        self.accept()

    def project_name(self) -> str:
        return self.name_input.text().strip()


class ColorDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        title: str = "Add color",
        body: str = "Name the color and paste a hex value, or open the picker.",
        action: str = "Add color",
        name: str = "",
        hex_value: str = "#3b82f6",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(570)
        self.setMinimumHeight(610)

        self._hex = normalize_hex(hex_value) if is_hex(hex_value) else "#3b82f6"

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 24, 26, 22)
        root.setSpacing(16)

        heading = QLabel(title)
        heading.setObjectName("DialogTitle")
        root.addWidget(heading)

        description = QLabel(body)
        description.setObjectName("DialogBody")
        description.setWordWrap(True)
        root.addWidget(description)

        editor_card = QFrame()
        editor_card.setObjectName("DialogCard")
        editor_layout = QHBoxLayout(editor_card)
        editor_layout.setContentsMargins(18, 18, 18, 18)
        editor_layout.setSpacing(20)

        self.preview = ColorPreview(self._hex)
        self.preview.clicked.connect(self._open_picker)
        editor_layout.addWidget(self.preview, 0, Qt.AlignmentFlag.AlignTop)

        fields = QVBoxLayout()
        fields.setSpacing(7)

        name_label = QLabel("Name")
        name_label.setObjectName("FieldLabel")
        fields.addWidget(name_label)
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("e.g. Ocean blue")
        self.name_input.setMaxLength(80)
        fields.addWidget(self.name_input)

        hex_label = QLabel("Hex value")
        hex_label.setObjectName("FieldLabel")
        fields.addWidget(hex_label)
        self.hex_input = QLineEdit(self._hex)
        self.hex_input.setPlaceholderText("#3b82f6")
        self.hex_input.setMaxLength(7)
        self.hex_input.textChanged.connect(self._on_hex_changed)
        self.hex_input.returnPressed.connect(self._accept_if_valid)
        fields.addWidget(self.hex_input)

        pick_button = QPushButton("Pick color...")
        pick_button.setObjectName("SecondaryButton")
        pick_button.setCursor(Qt.CursorShape.PointingHandCursor)
        pick_button.clicked.connect(self._open_picker)
        fields.addWidget(pick_button)
        fields.addStretch(1)
        editor_layout.addLayout(fields, 1)

        root.addWidget(editor_card)

        conversions_card = QFrame()
        conversions_card.setObjectName("PreviewCard")
        conversions_layout = QVBoxLayout(conversions_card)
        conversions_layout.setContentsMargins(18, 16, 18, 16)
        conversions_layout.setSpacing(10)

        conversions_title = QLabel("Conversions")
        conversions_title.setObjectName("FieldLabel")
        conversions_layout.addWidget(conversions_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(7)
        grid.setColumnStretch(1, 1)
        self._conversion_values: dict[str, QLabel] = {}
        for row, label in enumerate(("RGB", "HSL", "OKLCH", "Display P3")):
            key_label = QLabel(label)
            key_label.setStyleSheet("font-size: 13px; color: #858585;")
            value_label = QLabel()
            value_label.setStyleSheet("font-size: 13px; color: #D2D2D2;")
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(key_label, row, 0)
            grid.addWidget(value_label, row, 1)
            self._conversion_values[label] = value_label
        conversions_layout.addLayout(grid)
        root.addWidget(conversions_card)

        contrast_row = QHBoxLayout()
        contrast_row.setSpacing(10)
        self._white_contrast = ContrastPill()
        self._black_contrast = ContrastPill()
        contrast_row.addWidget(self._white_contrast)
        contrast_row.addWidget(self._black_contrast)
        contrast_row.addStretch(1)
        root.addLayout(contrast_row)

        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setVisible(False)
        root.addWidget(self.error_label)

        root.addStretch(1)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("SecondaryButton")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        self.primary = QPushButton(action)
        self.primary.setObjectName("PrimaryButton")
        self.primary.setCursor(Qt.CursorShape.PointingHandCursor)
        self.primary.setDefault(True)
        self.primary.clicked.connect(self._accept_if_valid)
        buttons.addWidget(self.primary)
        root.addLayout(buttons)

        self._update_preview(self._hex)
        self.name_input.setFocus()

    def _open_picker(self) -> None:
        picker = QColorDialog(QColor(self._hex), self)
        picker.setWindowTitle("Pick a color")
        if run_dialog(picker) == QDialog.DialogCode.Accepted:
            color = picker.selectedColor()
            if color.isValid():
                self.hex_input.setText(color.name())
                self.hex_input.setFocus()
                self.hex_input.selectAll()

    def _on_hex_changed(self, text: str) -> None:
        raw = text.strip()
        if raw and not raw.startswith("#"):
            raw = f"#{raw}"
        if is_hex(raw):
            self._hex = normalize_hex(raw)
            self.error_label.setVisible(False)
            self.hex_input.setProperty("error", False)
            self.hex_input.style().unpolish(self.hex_input)
            self.hex_input.style().polish(self.hex_input)
            self._update_preview(self._hex)
        else:
            self.hex_input.setProperty("error", bool(raw))
            self.hex_input.style().unpolish(self.hex_input)
            self.hex_input.style().polish(self.hex_input)

    def _update_preview(self, value: str) -> None:
        self.preview.set_color(value)
        for label, key in (
            ("RGB", "RGB"),
            ("HSL", "HSL"),
            ("OKLCH", "OKLCH"),
        ):
            self._conversion_values[label].setText(format_color(value, key))

        p3 = srgb_to_display_p3(value)
        gamut_note = "  (outside P3)" if p3.endswith(" *") else ""
        self._conversion_values["Display P3"].setText(p3.removesuffix(" *") + gamut_note)

        white_ratio = contrast_ratio(value, "#ffffff")
        black_ratio = contrast_ratio(value, "#000000")
        self._white_contrast.set_values("On white", white_ratio, contrast_grade(white_ratio))
        self._black_contrast.set_values("On black", black_ratio, contrast_grade(black_ratio))

    def _accept_if_valid(self) -> None:
        raw = self.hex_input.text().strip()
        if not raw.startswith("#"):
            raw = f"#{raw}"
        try:
            self._hex = normalize_hex(raw)
        except ColorError:
            self.error_label.setText("Enter a valid hex color, for example #3b82f6.")
            self.error_label.setVisible(True)
            self.hex_input.setFocus()
            self.hex_input.selectAll()
            return
        self.accept()

    def color_name(self) -> str:
        return self.name_input.text().strip() or "Untitled color"

    def color_hex(self) -> str:
        return self._hex


class ConfirmDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        title: str,
        body: str,
        *,
        confirm_text: str = "Delete",
        danger: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(430)

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 24, 26, 22)
        root.setSpacing(14)

        heading = QLabel(title)
        heading.setObjectName("DialogTitle")
        root.addWidget(heading)

        description = QLabel(body)
        description.setObjectName("DialogBody")
        description.setWordWrap(True)
        root.addWidget(description)
        root.addSpacing(4)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("SecondaryButton")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        confirm = QPushButton(confirm_text)
        confirm.setObjectName("DangerButton" if danger else "PrimaryButton")
        confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm.setDefault(True)
        confirm.clicked.connect(self.accept)
        buttons.addWidget(confirm)
        root.addLayout(buttons)

    @classmethod
    def ask(
        cls,
        parent: QWidget | None,
        title: str,
        body: str,
        *,
        confirm_text: str = "Delete",
        danger: bool = True,
    ) -> bool:
        dialog = cls(
            parent,
            title,
            body,
            confirm_text=confirm_text,
            danger=danger,
        )
        return run_dialog(dialog) == QDialog.DialogCode.Accepted
