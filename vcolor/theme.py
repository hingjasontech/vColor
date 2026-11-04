"""Dark theme tokens and Qt stylesheet."""

from __future__ import annotations

APP_BG = "#202020"
SIDEBAR_BG = "#2B2B2B"
SURFACE = "#353535"
SURFACE_HOVER = "#3C3C3C"
SURFACE_ACTIVE = "#414141"
SURFACE_INPUT = "#2E2E2E"
BORDER = "#3E3E3E"
BORDER_STRONG = "#4A4A4A"
TEXT = "#F3F3F3"
TEXT_MUTED = "#A6A6A6"
TEXT_DIM = "#7C7C7C"
ACCENT = "#3B82F6"
ACCENT_HOVER = "#4C8FFB"
ACCENT_PRESSED = "#2F6FD0"
DANGER = "#F05252"
DANGER_BG = "#22F05252"
SUCCESS = "#3DD68C"
WARNING = "#F5A524"


def build_stylesheet(font_family: str = "Inter Variable") -> str:
    return f"""
    * {{
        font-family: "{font_family}";
        color: {TEXT};
    }}

    QMainWindow, QWidget#Root, QWidget#MainContent {{
        background: {APP_BG};
    }}

    QWidget#Sidebar {{
        background: {SIDEBAR_BG};
    }}

    QLabel {{
        background: transparent;
    }}

    QLabel#SidebarTitle {{
        font-size: 24px;
        font-weight: 600;
        color: {TEXT};
    }}

    QLabel#PageTitle {{
        font-size: 24px;
        font-weight: 600;
        color: {TEXT};
    }}

    QPushButton#CreateProjectButton {{
        background: #3A3A3A;
        border: none;
        border-radius: 22px;
        color: {TEXT};
        font-size: 15px;
        font-weight: 500;
        min-height: 44px;
        padding: 0 18px;
        text-align: center;
    }}
    QPushButton#CreateProjectButton:hover {{
        background: #444444;
    }}
    QPushButton#CreateProjectButton:pressed {{
        background: #333333;
    }}

    QPushButton#CopyButton {{
        background: #3A3A3A;
        border: 1px solid #5A5A5A;
        border-radius: 18px;
        color: {TEXT};
        font-size: 14px;
        font-weight: 500;
        min-width: 72px;
        max-width: 72px;
        min-height: 36px;
        max-height: 36px;
        padding: 0;
    }}
    QPushButton#CopyButton:hover {{
        background: #454545;
        border-color: #6A6A6A;
    }}
    QPushButton#CopyButton:pressed {{
        background: #323232;
        border-color: #505050;
    }}

    QComboBox#FormatSelect {{
        background: {SURFACE_INPUT};
        border: 1px solid #383838;
        border-radius: 10px;
        color: #D8D8D8;
        font-size: 15px;
        min-height: 42px;
        padding-left: 14px;
        padding-right: 36px;
    }}
    QComboBox#FormatSelect:hover {{
        background: #333333;
        border-color: {BORDER_STRONG};
    }}
    QComboBox#FormatSelect:focus {{
        border-color: {ACCENT};
    }}
    QComboBox#FormatSelect:disabled {{
        color: #6F6F6F;
        background: #2A2A2A;
        border-color: #333333;
    }}
    QComboBox#FormatSelect::drop-down {{
        border: none;
        width: 34px;
    }}
    QComboBox#FormatSelect::down-arrow {{
        image: none;
        width: 0;
        height: 0;
    }}
    QComboBox QAbstractItemView {{
        background: #2D2D2D;
        border: 1px solid {BORDER_STRONG};
        border-radius: 9px;
        color: {TEXT};
        outline: 0;
        padding: 6px;
        selection-background-color: {ACCENT};
        selection-color: white;
    }}
    QComboBox QAbstractItemView::item {{
        border-radius: 6px;
        min-height: 32px;
        padding-left: 8px;
        padding-right: 18px;
    }}
    QComboBox QAbstractItemView::item:hover {{
        background: #3A3A3A;
    }}

    QFrame#ColorRow {{
        background: {SURFACE};
        border: none;
        border-radius: 16px;
    }}
    QFrame#ColorRow:hover {{
        background: {SURFACE_HOVER};
    }}
    QFrame#ColorRow[selected="true"] {{
        background: {SURFACE_ACTIVE};
    }}

    QLabel#ColorName {{
        color: {TEXT};
        font-size: 16px;
        font-weight: 500;
    }}
    QLabel#ColorValue {{
        color: {TEXT_MUTED};
        font-size: 15px;
    }}

    QLabel#ProjectName {{
        background: transparent;
        color: #D7D7D7;
        font-size: 16px;
        font-weight: 400;
    }}
    QFrame#ProjectItem[selected="true"] QLabel#ProjectName {{
        color: {TEXT};
        font-weight: 500;
    }}
    QFrame#ProjectItem {{
        background: transparent;
        border-radius: 10px;
    }}
    QFrame#ProjectItem:hover {{
        background: #343434;
    }}
    QFrame#ProjectItem[selected="true"] {{
        background: #3A3A3A;
    }}
    QLabel#ProjectCount {{
        color: {TEXT_DIM};
        font-size: 12px;
    }}

    QScrollArea, QScrollArea > QWidget > QWidget {{
        background: transparent;
        border: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: #4A4A4A;
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #5A5A5A;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
        border: none;
        height: 0;
    }}
    QScrollBar:horizontal {{
        height: 0;
        width: 0;
    }}

    QLabel#EmptyTitle {{
        color: {TEXT};
        font-size: 20px;
        font-weight: 600;
    }}
    QLabel#EmptyBody {{
        color: {TEXT_MUTED};
        font-size: 15px;
    }}

    QDialog {{
        background: #252525;
    }}
    QLabel#DialogTitle {{
        color: {TEXT};
        font-size: 23px;
        font-weight: 600;
    }}
    QLabel#DialogBody {{
        color: {TEXT_MUTED};
        font-size: 14px;
    }}
    QLabel#FieldLabel {{
        color: #B8B8B8;
        font-size: 13px;
        font-weight: 500;
    }}
    QLabel#ErrorLabel {{
        color: {DANGER};
        font-size: 13px;
    }}
    QLabel#HintLabel {{
        color: {TEXT_DIM};
        font-size: 12px;
    }}

    QLineEdit {{
        background: {SURFACE_INPUT};
        border: 1px solid {BORDER};
        border-radius: 9px;
        color: {TEXT};
        font-size: 15px;
        min-height: 42px;
        padding: 0 12px;
        selection-background-color: {ACCENT};
    }}
    QLineEdit:hover {{
        border-color: #4C4C4C;
    }}
    QLineEdit:focus {{
        border-color: {ACCENT};
    }}
    QLineEdit[error="true"] {{
        border-color: {DANGER};
    }}

    QPushButton#PrimaryButton {{
        background: {ACCENT};
        border: none;
        border-radius: 10px;
        color: white;
        font-size: 15px;
        font-weight: 600;
        min-height: 42px;
        padding: 0 22px;
    }}
    QPushButton#PrimaryButton:hover {{
        background: {ACCENT_HOVER};
    }}
    QPushButton#PrimaryButton:pressed {{
        background: {ACCENT_PRESSED};
    }}
    QPushButton#PrimaryButton:disabled {{
        background: #2E3A4C;
        color: #7F8A99;
    }}
    QPushButton#SecondaryButton {{
        background: #343434;
        border: none;
        border-radius: 10px;
        color: {TEXT};
        font-size: 15px;
        font-weight: 500;
        min-height: 42px;
        padding: 0 22px;
    }}
    QPushButton#SecondaryButton:hover {{
        background: #3E3E3E;
    }}
    QPushButton#SecondaryButton:pressed {{
        background: #2C2C2C;
    }}
    QPushButton#DangerButton {{
        background: {DANGER};
        border: none;
        border-radius: 10px;
        color: white;
        font-size: 15px;
        font-weight: 600;
        min-height: 42px;
        padding: 0 22px;
    }}
    QPushButton#DangerButton:hover {{
        background: #FF6262;
    }}

    QFrame#DialogCard {{
        background: #303030;
        border: 1px solid #3B3B3B;
        border-radius: 14px;
    }}
    QFrame#PreviewCard {{
        background: #2D2D2D;
        border: 1px solid #3B3B3B;
        border-radius: 14px;
    }}
    QFrame#Divider {{
        background: #383838;
        max-height: 1px;
        border: none;
    }}
    QFrame#ContrastPill {{
        background: #2D2D2D;
        border: 1px solid #3B3B3B;
        border-radius: 10px;
    }}
    QFrame#Toast {{
        background: #3A3A3A;
        border: 1px solid #4A4A4A;
        border-radius: 12px;
    }}
    QPushButton#ToastAction {{
        background: transparent;
        border: none;
        border-radius: 6px;
        color: #8AB4FF;
        font-size: 13px;
        font-weight: 600;
        min-height: 30px;
        padding: 0 10px;
    }}
    QPushButton#ToastAction:hover {{
        background: #2A3B82F6;
        color: #B4D0FF;
    }}

    QMenu {{
        background: #2C2C2C;
        border: 1px solid #444444;
        border-radius: 8px;
        padding: 6px;
    }}
    QMenu::item {{
        border-radius: 6px;
        color: {TEXT};
        min-width: 180px;
        padding: 8px 24px 8px 12px;
    }}
    QMenu::item:selected {{
        background: {ACCENT};
        color: white;
    }}
    QMenu::separator {{
        background: #414141;
        height: 1px;
        margin: 5px 8px;
    }}

    QToolTip {{
        background: #111111;
        border: 1px solid #3A3A3A;
        border-radius: 5px;
        color: #F0F0F0;
        padding: 5px 8px;
        font-size: 12px;
    }}

    QMessageBox {{
        background: #252525;
    }}
    QMessageBox QLabel {{
        color: {TEXT};
        font-size: 14px;
    }}
    """
