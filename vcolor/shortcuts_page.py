"""Keyboard shortcuts page and shortcut editing dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
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

from .shortcuts import (
    SHORTCUT_ACTIONS,
    ShortcutAction,
    is_allowed_shortcut,
    normalize_shortcut,
    resolve_shortcuts,
    shortcut_keycaps,
)
from .settings_page import SettingsGroup, SettingsRow, build_page_header


class KeycapLabel(QWidget):
    """A row of keycaps, one per key in a shortcut."""

    def __init__(
        self,
        sequence: str = "",
        *,
        large: bool = False,
        placeholder: str = "Disabled",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._large = large
        self._placeholder = placeholder
        self._sequence = ""
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self.set_sequence(sequence)

    def sequence(self) -> str:
        return self._sequence

    def set_sequence(self, value: str) -> None:
        self._sequence = value
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()

        labels = shortcut_keycaps(value)
        if not labels:
            placeholder = QLabel(self._placeholder)
            placeholder.setObjectName(
                "ShortcutPlaceholderLarge" if self._large else "ShortcutPlaceholder"
            )
            self._layout.addWidget(placeholder)
        else:
            for index, label in enumerate(labels):
                if index:
                    plus = QLabel("+")
                    plus.setObjectName("KeycapPlus")
                    self._layout.addWidget(plus)
                keycap = QLabel(label)
                keycap.setObjectName("KeycapLarge" if self._large else "Keycap")
                keycap.setAlignment(Qt.AlignmentFlag.AlignCenter)
                keycap.setFixedHeight(34 if self._large else 24)
                self._layout.addWidget(keycap)
        self.updateGeometry()
        self.update()


class ShortcutDialog(QDialog):
    """Libadwaita-style dialog that captures a new shortcut."""

    def __init__(
        self,
        parent: QWidget | None,
        *,
        action: ShortcutAction,
        sequence: str,
        is_custom: bool,
        taken: dict[str, str],
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Set Shortcut")
        self.setModal(True)
        self.setFixedWidth(430)
        self.setMinimumHeight(320)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._sequence = normalize_shortcut(sequence)
        self._default = action.default
        self._taken = dict(taken)

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 24, 26, 22)
        root.setSpacing(14)

        heading = QLabel("Set Shortcut")
        heading.setObjectName("DialogTitle")
        root.addWidget(heading)

        description = QLabel(
            f"Press a key combination to use for “{action.title}”."
        )
        description.setObjectName("DialogBody")
        description.setWordWrap(True)
        root.addWidget(description)

        capture = QFrame()
        capture.setObjectName("ShortcutCapture")
        capture.setFixedHeight(84)
        capture_layout = QVBoxLayout(capture)
        capture_layout.setContentsMargins(18, 12, 18, 12)
        capture_layout.setSpacing(0)
        self.keycaps = KeycapLabel(
            self._sequence,
            large=True,
            placeholder="Press a key combination",
        )
        capture_layout.addWidget(self.keycaps, 0, Qt.AlignmentFlag.AlignCenter)
        root.addWidget(capture)

        hint = QLabel("Press Backspace to clear, or Esc to cancel.")
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        root.addWidget(self.error_label)

        root.addStretch(1)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.reset_button = QPushButton("Reset to Default")
        self.reset_button.setObjectName("LinkButton")
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.reset_button.setVisible(is_custom)
        self.reset_button.clicked.connect(self._reset)
        buttons.addWidget(self.reset_button)
        buttons.addStretch(1)

        cancel = QPushButton("Cancel")
        cancel.setObjectName("SecondaryButton")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)

        self.set_button = QPushButton("Set")
        self.set_button.setObjectName("PrimaryButton")
        self.set_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.set_button.setDefault(True)
        self.set_button.clicked.connect(self._accept_if_valid)
        buttons.addWidget(self.set_button)
        root.addLayout(buttons)

        self.setFocus()

    def sequence(self) -> str:
        return self._sequence

    def showEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().showEvent(event)
        self.setFocus()

    def _set_sequence(self, value: str) -> None:
        self._sequence = normalize_shortcut(value)
        self.keycaps.set_sequence(self._sequence)
        self.error_label.setVisible(False)

    def _reset(self) -> None:
        self._set_sequence(self._default)
        self.setFocus()

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        self.setFocus()

    def _accept_if_valid(self) -> None:
        if self._sequence and self._sequence in self._taken:
            self._show_error(
                f"That shortcut is already used for “{self._taken[self._sequence]}”."
            )
            return
        self.accept()

    @staticmethod
    def _allowed(sequence: str) -> bool:
        return is_allowed_shortcut(sequence)

    def keyPressEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key.Key_Escape:
            self.reject()
            return
        if key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete) and (
            modifiers == Qt.KeyboardModifier.NoModifier
        ):
            self._set_sequence("")
            return
        if key in (
            Qt.Key.Key_Shift,
            Qt.Key.Key_Control,
            Qt.Key.Key_Alt,
            Qt.Key.Key_Meta,
            Qt.Key.Key_CapsLock,
            Qt.Key.Key_NumLock,
            Qt.Key.Key_ScrollLock,
        ):
            return
        if key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab) and (
            modifiers == Qt.KeyboardModifier.NoModifier
        ):
            self.focusNextPrevChild(key == Qt.Key.Key_Tab)
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (
            modifiers == Qt.KeyboardModifier.NoModifier
        ):
            self._accept_if_valid()
            return

        sequence = QKeySequence(modifiers.value | int(key)).toString(
            QKeySequence.SequenceFormat.PortableText
        )
        normalized = normalize_shortcut(sequence)
        if not normalized:
            return
        if not self._allowed(normalized):
            self._show_error(
                "Include Ctrl, Alt, or use a function key in the shortcut."
            )
            return
        self._set_sequence(normalized)


class ShortcutsPage(QWidget):
    """A settings subpage listing editable keyboard shortcuts."""

    backRequested = Signal()
    shortcutsChanged = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ShortcutsPage")
        self._overrides: dict[str, str] = {}
        self._rows: dict[str, SettingsRow] = {}
        self._keycaps: dict[str, KeycapLabel] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header, self.back_button = build_page_header(
            "Keyboard Shortcuts", "Back to settings"
        )
        self.back_button.clicked.connect(self.backRequested.emit)
        root.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QWidget()
        content.setObjectName("ShortcutsContent")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(48, 28, 48, 48)
        content_layout.setSpacing(0)

        self.column = QWidget()
        self.column.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        column = QVBoxLayout(self.column)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(24)

        intro = QLabel(
            "Select a shortcut to change it. Changes are saved automatically."
        )
        intro.setObjectName("ShortcutsHint")
        intro.setWordWrap(True)
        column.addWidget(intro)

        groups: dict[str, SettingsGroup] = {}
        for action in SHORTCUT_ACTIONS:
            group = groups.get(action.group)
            if group is None:
                group = SettingsGroup(action.group)
                groups[action.group] = group
                column.addWidget(group)

            keycaps = KeycapLabel(placeholder="Disabled")
            keycaps.setAccessibleName(f"{action.title} shortcut")
            row = SettingsRow(action.title, control=keycaps, clickable=True)
            row.setToolTip(f"Change the shortcut for {action.title.lower()}")
            row.setAccessibleName(f"{action.title} shortcut")
            row.activated.connect(
                lambda action=action: self._edit_shortcut(action)
            )
            group.add_row(row)
            self._rows[action.id] = row
            self._keycaps[action.id] = keycaps

        column.addStretch(1)
        content_layout.addStretch(1)
        content_layout.addWidget(self.column)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self._update_column_width()

    def load(self, overrides: dict[str, str]) -> None:
        self._overrides = dict(overrides)
        self._refresh()

    def _refresh(self) -> None:
        resolved = resolve_shortcuts(self._overrides)
        for action_id, keycaps in self._keycaps.items():
            keycaps.set_sequence(resolved[action_id])

    def _edit_shortcut(self, action: ShortcutAction) -> None:
        from .dialogs import run_dialog

        resolved = resolve_shortcuts(self._overrides)
        taken = {
            resolved[other.id]: other.title
            for other in SHORTCUT_ACTIONS
            if other.id != action.id and resolved[other.id]
        }
        dialog = ShortcutDialog(
            self,
            action=action,
            sequence=resolved[action.id],
            is_custom=action.id in self._overrides,
            taken=taken,
        )
        if run_dialog(dialog) != QDialog.DialogCode.Accepted:
            return

        value = dialog.sequence()
        if value == action.default:
            self._overrides.pop(action.id, None)
        else:
            self._overrides[action.id] = value
        self._refresh()
        self.shortcutsChanged.emit(dict(self._overrides))

    def _update_column_width(self) -> None:
        available = max(0, self.width() - 96)
        self.column.setFixedWidth(min(660, available))

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self._update_column_width()