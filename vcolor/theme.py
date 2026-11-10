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
ACCENT = "#3584E4"
ACCENT_HOVER = "#4990E7"
ACCENT_PRESSED = "#2A6AB8"
DANGER = "#FF7B84"
DANGER_BG = "#22FF7B84"
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

    QPushButton {{
        background-color: rgba(255, 255, 255, 10%);
        border: 1px solid transparent;
        border-radius: 9px;
        color: {TEXT};
        font-size: 15px;
        font-weight: 700;
        min-height: 34px;
        padding: 0 17px;
    }}
    QPushButton:hover {{
        background-color: rgba(255, 255, 255, 15%);
    }}
    QPushButton:pressed {{
        background-color: rgba(255, 255, 255, 30%);
    }}
    QPushButton:disabled {{
        background-color: rgba(255, 255, 255, 5%);
        color: {TEXT_DIM};
    }}

    QPushButton#CreateProjectButton {{
        background-color: rgba(255, 255, 255, 10%);
        border: 1px solid transparent;
        border-radius: 17px;
        color: {TEXT};
        font-size: 15px;
        font-weight: 700;
        min-height: 34px;
        padding: 0 24px;
        text-align: center;
    }}
    QPushButton#CreateProjectButton:hover {{
        background-color: rgba(255, 255, 255, 15%);
    }}
    QPushButton#CreateProjectButton:pressed {{
        background-color: rgba(255, 255, 255, 30%);
    }}

    QPushButton#PillButton {{
        background-color: {ACCENT};
        border: 1px solid transparent;
        border-radius: 22px;
        color: white;
        font-size: 15px;
        font-weight: 700;
        min-height: 44px;
        padding: 0 32px;
    }}
    QPushButton#PillButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton#PillButton:pressed {{
        background-color: {ACCENT_PRESSED};
    }}

    QPushButton#CopyButton {{
        background-color: rgba(255, 255, 255, 10%);
        border: 1px solid transparent;
        border-radius: 9px;
        color: {TEXT};
        font-size: 14px;
        font-weight: 700;
        min-width: 72px;
        max-width: 72px;
        min-height: 34px;
        max-height: 34px;
        padding: 0;
    }}
    QPushButton#CopyButton:hover {{
        background-color: rgba(255, 255, 255, 15%);
    }}
    QPushButton#CopyButton:pressed {{
        background-color: rgba(255, 255, 255, 30%);
    }}

    QComboBox#FormatSelect {{
        background-color: rgba(255, 255, 255, 10%);
        border: 1px solid transparent;
        border-radius: 9px;
        color: {TEXT};
        font-size: 15px;
        min-height: 34px;
        padding-left: 12px;
        padding-right: 36px;
    }}
    QComboBox#FormatSelect:hover {{
        background-color: rgba(255, 255, 255, 15%);
        border-color: {ACCENT};
    }}
    QComboBox#FormatSelect:focus {{
        border-color: {ACCENT};
    }}
    QComboBox#FormatSelect:disabled {{
        color: {TEXT_DIM};
        background-color: rgba(255, 255, 255, 5%);
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
        border-radius: 10px;
        color: {TEXT};
        outline: 0;
        padding: 0;
        selection-background-color: transparent;
        selection-color: {TEXT};
    }}
    QComboBox QAbstractItemView::item {{
        border: none;
        min-height: 34px;
        padding-left: 12px;
        padding-right: 12px;
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
        background-color: rgba(255, 255, 255, 10%);
        border: 1px solid transparent;
        border-radius: 9px;
        color: {TEXT};
        font-size: 15px;
        min-height: 34px;
        padding: 0 10px;
        selection-background-color: {ACCENT};
    }}
    QLineEdit:focus {{
        border-color: {ACCENT};
    }}
    QLineEdit[error="true"] {{
        border-color: {DANGER};
    }}

    QPushButton#PrimaryButton {{
        background-color: {ACCENT};
        border: 1px solid transparent;
        border-radius: 9px;
        color: white;
        font-size: 15px;
        font-weight: 700;
        min-height: 34px;
        padding: 0 17px;
    }}
    QPushButton#PrimaryButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton#PrimaryButton:pressed {{
        background-color: {ACCENT_PRESSED};
    }}
    QPushButton#PrimaryButton:disabled {{
        background-color: rgba(53, 132, 228, 50%);
        color: rgba(255, 255, 255, 50%);
    }}
    QPushButton#SecondaryButton {{
        background-color: rgba(255, 255, 255, 10%);
        border: 1px solid transparent;
        border-radius: 9px;
        color: {TEXT};
        font-size: 15px;
        font-weight: 700;
        min-height: 34px;
        padding: 0 17px;
    }}
    QPushButton#SecondaryButton:hover {{
        background-color: rgba(255, 255, 255, 15%);
    }}
    QPushButton#SecondaryButton:pressed {{
        background-color: rgba(255, 255, 255, 30%);
    }}
    QPushButton#DangerButton {{
        background-color: rgba(255, 123, 132, 15%);
        border: 1px solid transparent;
        border-radius: 9px;
        color: #FF7B84;
        font-size: 15px;
        font-weight: 700;
        min-height: 34px;
        padding: 0 17px;
    }}
    QPushButton#DangerButton:hover {{
        background-color: rgba(255, 123, 132, 20%);
    }}
    QPushButton#DangerButton:pressed {{
        background-color: rgba(255, 123, 132, 35%);
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

    QFrame#UpdateBanner {{
        background: #26364B;
        border: 1px solid #37506E;
        border-radius: 12px;
    }}
    QLabel#UpdateBannerLabel {{
        color: #D7E5F8;
        font-size: 13px;
        font-weight: 500;
    }}
    QPushButton#UpdateBannerAction {{
        background-color: {ACCENT};
        border: 1px solid transparent;
        border-radius: 8px;
        color: white;
        font-size: 13px;
        font-weight: 700;
        min-height: 28px;
        max-height: 28px;
        padding: 0 14px;
    }}
    QPushButton#UpdateBannerAction:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton#UpdateBannerAction:pressed {{
        background-color: {ACCENT_PRESSED};
    }}

    QWidget#SettingsPage, QWidget#SettingsContent {{
        background: {APP_BG};
    }}
    QWidget#SettingsHeader {{
        background: {SIDEBAR_BG};
        border-bottom: 1px solid #3A3A3A;
    }}
    QLabel#SettingsHeaderTitle {{
        color: {TEXT};
        font-size: 16px;
        font-weight: 700;
    }}
    QLabel#SettingsGroupTitle {{
        color: {TEXT};
        font-size: 15px;
        font-weight: 700;
        padding-left: 4px;
    }}
    QFrame#SettingsGroupCard {{
        background: #303030;
        border: 1px solid #393939;
        border-radius: 12px;
    }}
    QWidget#SettingsRow {{
        background: transparent;
    }}
    QLabel#SettingsRowTitle {{
        color: {TEXT};
        font-size: 14px;
        font-weight: 500;
    }}
    QLabel#SettingsRowSubtitle {{
        color: {TEXT_MUTED};
        font-size: 12px;
    }}
    QLabel#SettingsValue {{
        color: {TEXT_MUTED};
        font-size: 13px;
    }}
    QFrame#SettingsDivider {{
        background: #3C3C3C;
        border: none;
        margin-left: 16px;
        margin-right: 16px;
    }}

    QPushButton#VersionButton {{
        background: transparent;
        border: none;
        color: {TEXT_DIM};
        font-size: 12px;
        font-weight: 500;
        min-height: 24px;
        padding: 0;
    }}
    QPushButton#VersionButton:hover {{
        color: {TEXT_MUTED};
    }}
    QPushButton#VersionButton:disabled {{
        color: {TEXT_DIM};
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
