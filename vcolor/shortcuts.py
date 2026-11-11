"""Keyboard shortcut definitions and persistence helpers."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from PySide6.QtGui import QKeySequence

PORTABLE = QKeySequence.SequenceFormat.PortableText


@dataclass(frozen=True, slots=True)
class ShortcutAction:
    id: str
    title: str
    group: str
    default: str


SHORTCUT_ACTIONS: tuple[ShortcutAction, ...] = (
    ShortcutAction("add_color", "Add color", "Colors", "Ctrl+N"),
    ShortcutAction("new_project", "New project", "Projects", "Ctrl+Shift+N"),
    ShortcutAction("import_project", "Import project", "Projects", "Ctrl+O"),
    ShortcutAction("export_project", "Export project", "Projects", "Ctrl+E"),
    ShortcutAction("import_colors", "Import colors", "Projects", "Ctrl+I"),
    ShortcutAction("open_settings", "Open settings", "Application", "Ctrl+,"),
)


def normalize_shortcut(value: str) -> str:
    """Return the portable form of a single-chord shortcut, or ``""``."""
    text = value.strip()
    if not text:
        return ""
    sequence = QKeySequence.fromString(text, PORTABLE)
    if sequence.isEmpty() or sequence.count() != 1:
        return ""
    return sequence.toString(PORTABLE)


def shortcut_text(value: str) -> str:
    """Return a shortcut in the platform's native notation."""
    text = normalize_shortcut(value)
    if not text:
        return ""
    return QKeySequence.fromString(text, PORTABLE).toString(
        QKeySequence.SequenceFormat.NativeText
    )


def shortcut_keycaps(value: str) -> list[str]:
    """Split a shortcut into per-key labels for keycap widgets."""
    text = normalize_shortcut(value)
    if not text:
        return []
    labels = text.split("+")
    if sys.platform == "darwin":
        modifiers = {
            "Ctrl": "⌘",
            "Alt": "⌥",
            "Shift": "⇧",
            "Meta": "⌃",
        }
    else:
        modifiers = {"Meta": "Super"}
    return [modifiers.get(label, label) for label in labels]


def is_allowed_shortcut(value: str) -> bool:
    """Reject bare keys that would interfere with typing."""
    text = normalize_shortcut(value)
    if not text:
        return False
    if any(modifier in text for modifier in ("Ctrl+", "Alt+", "Meta+")):
        return True
    key = text.split("+")[-1]
    return key.startswith("F") and key[1:].isdigit()


def default_shortcuts() -> dict[str, str]:
    return {action.id: action.default for action in SHORTCUT_ACTIONS}


def sanitize_overrides(raw: object) -> dict[str, str]:
    """Keep only valid, non-default, conflict-free shortcut overrides."""
    if not isinstance(raw, dict):
        return {}

    candidates: dict[str, str] = {}
    for action in SHORTCUT_ACTIONS:
        value = raw.get(action.id)
        if not isinstance(value, str):
            continue
        if value == "":
            candidates[action.id] = ""
            continue
        normalized = normalize_shortcut(value)
        if normalized and is_allowed_shortcut(normalized):
            candidates[action.id] = normalized

    resolved: dict[str, str] = {}
    used: set[str] = set()
    fixed_defaults = {
        action.default
        for action in SHORTCUT_ACTIONS
        if action.id not in candidates and action.default
    }
    for action in SHORTCUT_ACTIONS:
        if action.id not in candidates:
            continue
        value = candidates[action.id]
        if value and (value in fixed_defaults or value in used):
            continue
        resolved[action.id] = value
        if value:
            used.add(value)

    for action in SHORTCUT_ACTIONS:
        if action.id in resolved:
            continue
        if action.default and action.default in used:
            resolved[action.id] = ""
            continue
        resolved[action.id] = action.default
        if action.default:
            used.add(action.default)

    return {
        action.id: resolved[action.id]
        for action in SHORTCUT_ACTIONS
        if action.id in candidates and resolved[action.id] != action.default
    }


def resolve_shortcuts(overrides: dict[str, str]) -> dict[str, str]:
    """Combine stored overrides with the built-in defaults."""
    resolved = default_shortcuts()
    resolved.update(sanitize_overrides(overrides))
    return resolved
