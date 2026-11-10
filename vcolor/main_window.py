"""Main application window."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QSignalBlocker, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import (
    QCloseEvent,
    QDesktopServices,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QGuiApplication,
    QKeySequence,
    QResizeEvent,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .color_utils import format_color, slugify
from .models import AppData, ColorEntry, PaletteStore, Project, StoreError, utc_now
from .project_files import project_from_portable, read_project_file
from .settings_page import SettingsPage
from .widgets import (
    ColorItem,
    EmptyState,
    FormatComboBox,
    ProjectItem,
    SidebarAction,
    Toast,
    UpdateBanner,
)

if TYPE_CHECKING:
    from .updater import ReleaseInfo, UpdateChecker


class MainWindow(QMainWindow):
    def __init__(
        self,
        store: PaletteStore,
        version: str = "0.0.0",
        *,
        check_updates: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.store = store
        self.version = version
        self.check_updates = check_updates
        self.data = AppData()
        self.current_format = "HEX"
        self._project_items: dict[str, ProjectItem] = {}
        self._loaded = False
        self.updater: UpdateChecker | None = None
        self._latest_release: ReleaseInfo | None = None
        self._manual_update_check = False

        self.setWindowTitle("vColor")
        self.setMinimumSize(QSize(980, 640))
        self.resize(1440, 900)

        root = QWidget()
        root.setObjectName("Root")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.sidebar = self._build_sidebar()
        root_layout.addWidget(self.sidebar)

        self.main_content = self._build_main_content()
        self.settings_page = SettingsPage(self.version)
        self.page_stack = QStackedWidget(root)
        self.page_stack.setObjectName("PageStack")
        self.page_stack.addWidget(self.main_content)
        self.page_stack.addWidget(self.settings_page)
        root_layout.addWidget(self.page_stack, 1)
        self.setCentralWidget(root)

        self.toast = Toast(self.page_stack)

        self.settings_page.backRequested.connect(self.show_projects_page)
        self.settings_page.formatChanged.connect(self._settings_format_changed)
        self.settings_page.showHexHashChanged.connect(
            self._settings_hex_hash_changed
        )
        self.settings_page.updateCheckChanged.connect(
            self._update_check_changed
        )
        self.settings_page.checkNowRequested.connect(self.check_for_updates)

        self.setAcceptDrops(True)

        self._install_shortcuts()
        self._render_project()
        self._fit_to_screen()

    def _fit_to_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        width = min(1440, max(980, available.width() - 80))
        height = min(900, max(640, available.height() - 80))
        self.resize(width, height)
        self.move(available.center() - self.rect().center())

    # ------------------------------------------------------------------ UI
    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(300)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(22, 22, 22, 24)
        layout.setSpacing(0)

        heading = QLabel("Projects")
        heading.setObjectName("SidebarTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setFixedHeight(38)
        layout.addWidget(heading)
        layout.addSpacing(8)

        create_button = QPushButton("Create project")
        create_button.setObjectName("CreateProjectButton")
        create_button.setCursor(Qt.CursorShape.PointingHandCursor)
        create_button.setToolTip("Create a new project (Ctrl+Shift+N)")
        create_button.clicked.connect(self.new_project)
        layout.addWidget(create_button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(69)

        self.project_scroll = QScrollArea()
        self.project_scroll.setWidgetResizable(True)
        self.project_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.project_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.project_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.project_list = QWidget()
        self.project_list_layout = QVBoxLayout(self.project_list)
        self.project_list_layout.setContentsMargins(0, 0, 0, 0)
        self.project_list_layout.setSpacing(6)
        self.project_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.project_scroll.setWidget(self.project_list)
        layout.addWidget(self.project_scroll, 1)

        layout.addSpacing(12)
        footer = QWidget()
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(2)

        self.import_button = SidebarAction("import", "Import project")
        self.import_button.setToolTip("Import a vColor project file (Ctrl+O)")
        self.import_button.clicked.connect(self.import_project)
        footer_layout.addWidget(self.import_button)

        self.settings_button = SidebarAction("settings", "Settings")
        self.settings_button.setToolTip("Open settings")
        self.settings_button.clicked.connect(self.show_settings_page)
        footer_layout.addWidget(self.settings_button)

        layout.addWidget(footer)
        layout.addSpacing(6)

        self.version_button = QPushButton(f"vColor {self.version}")
        self.version_button.setObjectName("VersionButton")
        self.version_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.version_button.setToolTip("Check for updates")
        self.version_button.setAccessibleName("Check for updates")
        self.version_button.clicked.connect(self.check_for_updates)
        layout.addWidget(self.version_button, 0, Qt.AlignmentFlag.AlignHCenter)
        return sidebar

    def _build_main_content(self) -> QWidget:
        main = QWidget()
        main.setObjectName("MainContent")

        outer = QVBoxLayout(main)
        outer.setContentsMargins(48, 24, 48, 28)
        outer.setSpacing(0)

        self.center_column = QWidget()
        self.center_column.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )
        center = QVBoxLayout(self.center_column)
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(20)

        self.update_banner = UpdateBanner(self.center_column)
        self.update_banner.downloadRequested.connect(self._open_update_page)
        self.update_banner.dismissRequested.connect(self._dismiss_update)
        self.update_banner.hide()
        center.addWidget(self.update_banner)

        header = QWidget()
        header.setFixedHeight(44)
        header_layout = QGridLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setHorizontalSpacing(0)
        header_layout.setVerticalSpacing(0)

        self.format_combo = FormatComboBox()
        self.format_combo.addItems(["HEX", "RGB", "HSL", "OKLCH"])
        self.format_combo.setCurrentIndex(0)
        self.format_combo.currentIndexChanged.connect(self._format_changed)
        self.format_combo.setEnabled(False)
        header_layout.addWidget(
            self.format_combo,
            0,
            0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )

        title = QLabel("Colors")
        title.setObjectName("PageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title, 0, 1, Qt.AlignmentFlag.AlignCenter)

        self.add_button = QPushButton("Add color")
        self.add_button.setObjectName("PrimaryButton")
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.setToolTip("Add color (Ctrl+N)")
        self.add_button.setAccessibleName("Add color")
        self.add_button.setFixedHeight(34)
        self.add_button.clicked.connect(self.add_color)
        self.add_button.hide()

        add_holder = QWidget()
        add_holder.setFixedWidth(192)
        add_layout = QHBoxLayout(add_holder)
        add_layout.setContentsMargins(0, 0, 0, 0)
        add_layout.setSpacing(0)
        add_layout.addStretch(1)
        add_layout.addWidget(self.add_button)
        header_layout.addWidget(
            add_holder,
            0,
            2,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )

        header_layout.setColumnStretch(0, 1)
        header_layout.setColumnStretch(1, 0)
        header_layout.setColumnStretch(2, 1)
        center.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(20)
        self.scroll.setWidget(self.body)
        center.addWidget(self.scroll, 1)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addStretch(1)
        row.addWidget(self.center_column, 0)
        row.addStretch(1)
        outer.addLayout(row, 1)
        return main

    def _install_shortcuts(self) -> None:
        for sequence, slot in (
            (QKeySequence(QKeySequence.StandardKey.New), self.add_color),
            (QKeySequence("Ctrl+Shift+N"), self.new_project),
            (QKeySequence(QKeySequence.StandardKey.Open), self.import_project),
            (QKeySequence("Ctrl+E"), self.export_active_project),
            (QKeySequence("Ctrl+I"), self.import_active_project),
        ):
            shortcut = QShortcut(sequence, self)
            shortcut.activated.connect(slot)

    # --------------------------------------------------------------- data
    def bootstrap(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        self.set_data(self.store.load())
        self._schedule_update_check()

    # ---------------------------------------------------------------- pages
    def show_projects_page(self) -> None:
        self.page_stack.setCurrentWidget(self.main_content)
        self.settings_button.set_selected(False)
        self._position_floating_widgets()

    def show_settings_page(self) -> None:
        self.settings_page.load(
            display_format=self.data.display_format,
            show_hex_hash=self.data.show_hex_hash,
            update_check=self.data.update_check,
            version=self.version,
        )
        self.page_stack.setCurrentWidget(self.settings_page)
        self.settings_button.set_selected(True)
        self._position_floating_widgets()

    # --------------------------------------------------------- project import
    def import_project(self) -> None:
        self.show_projects_page()
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import project",
            "",
            "vColor project (*.json);;All files (*)",
        )
        if paths:
            self.import_project_files([Path(path) for path in paths])

    def _commit_imports(
        self,
        projects: list[Project],
        previous_active_id: str | None,
        *,
        failures: int = 0,
    ) -> None:
        if not projects:
            return
        self.data.active_project_id = projects[-1].id
        self._persist(silent=True)
        self._populate_projects()
        self._render_project()
        self._show_import_toast(projects, previous_active_id, failures=failures)

    def _show_import_toast(
        self,
        projects: list[Project],
        previous_active_id: str | None,
        *,
        failures: int = 0,
    ) -> None:
        if len(projects) == 1:
            message = f'Imported "{projects[0].name}"'
        else:
            message = f"Imported {len(projects)} projects"
        if failures:
            message += f" · {failures} failed"

        project_ids = [project.id for project in projects]
        self.toast.show_message(
            message,
            action_label="Undo",
            action=lambda: self._undo_imports(project_ids, previous_active_id),
            duration=5200,
        )

    def _undo_imports(
        self, project_ids: list[str], previous_active_id: str | None
    ) -> None:
        removed = False
        for project_id in project_ids:
            project = self.data.find_project(project_id)
            if project is not None:
                self.data.projects.remove(project)
                removed = True
        if not removed:
            return

        if previous_active_id and self.data.find_project(previous_active_id):
            self.data.active_project_id = previous_active_id
        else:
            self.data.ensure_active_project()
        self._persist(silent=True)
        self._populate_projects()
        self._render_project()

    def import_project_files(self, paths: list[Path]) -> None:
        previous_active_id = self.data.active_project_id
        projects: list[Project] = []
        failures = 0
        for path in paths:
            try:
                portable = read_project_file(path)
            except (OSError, ValueError):
                failures += 1
                continue
            projects.append(project_from_portable(self.data, portable))

        if projects:
            self._commit_imports(projects, previous_active_id, failures=failures)
        elif failures:
            count = failures
            self.toast.show_message(
                f"Could not import {count} project file{'s' if count != 1 else ''}",
                kind="error",
                duration=5000,
            )

    def _project_paths(self, mime) -> list[Path]:  # type: ignore[no-untyped-def]
        if not mime.hasUrls():
            return []
        paths: list[Path] = []
        for url in mime.urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.suffix.casefold() != ".json":
                continue
            try:
                if path.is_file():
                    paths.append(path)
            except OSError:
                continue
        return paths

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._project_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self._project_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = self._project_paths(event.mimeData())
        if not paths:
            event.ignore()
            return
        event.acceptProposedAction()
        self.import_project_files(paths)

    # --------------------------------------------------------- update checks
    def _schedule_update_check(self) -> None:
        if not self.check_updates or not self.data.update_check:
            return
        from .updater import check_due

        if not check_due(self.data.last_update_check):
            return
        self.data.last_update_check = utc_now()
        self._persist(silent=True)
        QTimer.singleShot(1500, self._start_update_check)

    def _start_update_check(self) -> None:
        self._latest_release = None
        self._ensure_updater().check()

    def _ensure_updater(self) -> UpdateChecker:
        if self.updater is None:
            from .updater import UpdateChecker

            self.updater = UpdateChecker(self.version, self)
            self.updater.updateAvailable.connect(self._on_update_available)
            self.updater.checkFinished.connect(self._on_update_check_finished)
        return self.updater

    def check_for_updates(self) -> None:
        self._manual_update_check = True
        self.settings_page.set_checking(True)
        if not self._ensure_updater().check():
            # A check is already running; let its completion report the result.
            return
        self._latest_release = None
        self.version_button.setEnabled(False)
        self.version_button.setText("Checking for updates…")

    def _on_update_available(self, release: ReleaseInfo) -> None:
        self._latest_release = release
        if not self._manual_update_check and release.version == self.data.skipped_version:
            return
        self.update_banner.set_version(release.version)
        self.update_banner.setToolTip(release.name)
        self.update_banner.show()

    def _on_update_check_finished(self, success: bool) -> None:
        manual = self._manual_update_check
        self._manual_update_check = False
        self.settings_page.set_checking(False)
        self.version_button.setEnabled(True)
        self.version_button.setText(f"vColor {self.version}")
        if not manual:
            return
        if not success:
            self.toast.show_message(
                "Could not check for updates", kind="error", duration=4000
            )
        elif self._latest_release is not None:
            self.toast.show_message(f"vColor {self._latest_release.version} is available")
        else:
            self.toast.show_message(f"You're up to date (vColor {self.version})")

    def _open_update_page(self) -> None:
        if self._latest_release is None:
            return
        QDesktopServices.openUrl(QUrl(self._latest_release.url))

    def _dismiss_update(self) -> None:
        if self._latest_release is not None:
            self.data.skipped_version = self._latest_release.version
            self._persist(silent=True)
        self.update_banner.hide()

    def set_data(self, data: AppData) -> None:
        self.data = data
        self.data.ensure_active_project()
        self._apply_display_format(self.data.display_format)
        self.settings_page.set_show_hex_hash(self.data.show_hex_hash)
        self.settings_page.set_update_check(self.data.update_check)
        self.settings_page.set_version(self.version)
        self._populate_projects()
        self._render_project()
        self._position_floating_widgets()

    def _apply_display_format(self, value: str) -> None:
        index = self.format_combo.findText(value)
        if index < 0:
            index = 0
        with QSignalBlocker(self.format_combo):
            self.format_combo.setCurrentIndex(index)
        self.current_format = self.format_combo.itemText(index)
        self.settings_page.set_format(self.current_format)

    @property
    def active_project(self) -> Project | None:
        return self.data.active_project

    def _populate_projects(self) -> None:
        self._project_items.clear()
        self._clear_layout(self.project_list_layout)
        for project in self.data.projects:
            item = ProjectItem(
                project.id,
                project.name,
                len(project.colors),
                selected=project.id == self.data.active_project_id,
            )
            item.activated.connect(self.select_project)
            item.renameRequested.connect(self.rename_project)
            item.deleteRequested.connect(self.delete_project)
            item.exportRequested.connect(self.export_project)
            item.importRequested.connect(self.import_colors)
            self.project_list_layout.addWidget(item)
            self._project_items[project.id] = item

        if not self.data.projects:
            empty = QLabel("No projects yet")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {theme.TEXT_DIM}; font-size: 13px; padding: 16px;")
            self.project_list_layout.addWidget(empty)

        self.project_list_layout.addStretch(1)

    def select_project(self, project_id: str) -> None:
        project = self.data.find_project(project_id)
        if project is None:
            return
        self.show_projects_page()
        self.data.active_project_id = project.id
        for item_id, item in self._project_items.items():
            item.set_selected(item_id == project.id)
        self._persist(silent=True)
        self._render_project()

    def _render_project(self) -> None:
        project = self.active_project
        has_project = project is not None
        self.format_combo.setEnabled(has_project)
        self.add_button.setVisible(has_project)

        with QSignalBlocker(self.format_combo):
            if has_project:
                if self.format_combo.currentIndex() < 0:
                    self.format_combo.setCurrentIndex(
                        max(0, self.format_combo.findText(self.current_format))
                    )
            else:
                self.format_combo.setCurrentIndex(-1)

        self._clear_layout(self.body_layout)

        if not self.data.projects:
            state = EmptyState(
                "No projects yet",
                "Create your first project, or import a vColor project file.",
                "Create project",
            )
            state.actionTriggered.connect(self.new_project)
            self.body_layout.addStretch(1)
            self.body_layout.addWidget(state)
            self.body_layout.addStretch(1)
        elif project is None:
            state = EmptyState(
                "Select a project",
                "Choose a project from the sidebar to see its colors.",
            )
            self.body_layout.addStretch(1)
            self.body_layout.addWidget(state)
            self.body_layout.addStretch(1)
        elif not project.colors:
            state = EmptyState(
                "No colors yet",
                "Add a color to this project.",
                "Add color",
            )
            state.actionTriggered.connect(self.add_color)
            self.body_layout.addStretch(1)
            self.body_layout.addWidget(state)
            self.body_layout.addStretch(1)
        else:
            for color in project.colors:
                item = ColorItem(
                    color.id,
                    color.name,
                    self._display_color(color.hex),
                    color.hex,
                )
                item.copyRequested.connect(self.copy_color)
                item.editRequested.connect(self.edit_color)
                item.deleteRequested.connect(self.delete_color)
                self.body_layout.addWidget(item)
            self.body_layout.addStretch(1)

    def _format_changed(self, index: int) -> None:
        if index < 0:
            return
        self.current_format = self.format_combo.currentText()
        self.data.display_format = self.current_format
        self.settings_page.set_format(self.current_format)
        self._persist(silent=True)
        if self.active_project is not None:
            self._render_project()

    def _settings_format_changed(self, value: str) -> None:
        index = self.format_combo.findText(value)
        if index < 0:
            return
        with QSignalBlocker(self.format_combo):
            self.format_combo.setCurrentIndex(index)
        self.current_format = value
        self.data.display_format = value
        self._persist(silent=True)
        if self.active_project is not None:
            self._render_project()

    def _settings_hex_hash_changed(self, enabled: bool) -> None:
        if self.data.show_hex_hash == enabled:
            return
        self.data.show_hex_hash = enabled
        self._persist(silent=True)
        if self.active_project is not None:
            self._render_project()

    def _display_color(self, value: str) -> str:
        text = format_color(value, self.current_format)
        if self.current_format == "HEX" and not self.data.show_hex_hash:
            return text.lstrip("#")
        return text

    def _update_check_changed(self, enabled: bool) -> None:
        if self.data.update_check == enabled:
            return
        self.data.update_check = enabled
        self._persist(silent=True)
        if not enabled:
            self.update_banner.hide()
        else:
            self._schedule_update_check()

    # ---------------------------------------------------------- mutations
    def new_project(self) -> None:
        from .dialogs import ProjectDialog, run_dialog

        self.show_projects_page()
        dialog = ProjectDialog(self)
        if run_dialog(dialog) != ProjectDialog.DialogCode.Accepted:
            return
        project = Project(name=dialog.project_name())
        self.data.projects.append(project)
        self.data.active_project_id = project.id
        self._persist(silent=True)
        self._populate_projects()
        self._render_project()
        self.toast.show_message(f'Created "{project.name}"')

    def rename_project(self, project_id: str) -> None:
        from .dialogs import ProjectDialog, run_dialog

        project = self.data.find_project(project_id)
        if project is None:
            return
        dialog = ProjectDialog(
            self,
            title="Rename project",
            body="Choose a new name for this project.",
            action="Save name",
            name=project.name,
        )
        if run_dialog(dialog) != ProjectDialog.DialogCode.Accepted:
            return
        project.name = dialog.project_name()
        project.touch()
        self._persist(silent=True)
        self._populate_projects()
        self._render_project()
        self.toast.show_message("Project renamed")

    def delete_project(self, project_id: str) -> None:
        from .dialogs import ConfirmDialog

        project = self.data.find_project(project_id)
        if project is None:
            return
        if not ConfirmDialog.ask(
            self,
            "Delete project?",
            f'"{project.name}" and its {len(project.colors)} color'
            f'{"s" if len(project.colors) != 1 else ""} will be removed.',
            confirm_text="Delete project",
        ):
            return

        index = self.data.projects.index(project)
        was_active = self.data.active_project_id == project.id
        self.data.projects.remove(project)
        if was_active:
            replacement = self.data.projects[min(index, len(self.data.projects) - 1)] if self.data.projects else None
            self.data.active_project_id = replacement.id if replacement else None
        self._persist(silent=True)
        self._populate_projects()
        self._render_project()

        def undo() -> None:
            self.data.projects.insert(min(index, len(self.data.projects)), project)
            if was_active:
                self.data.active_project_id = project.id
            self._persist(silent=True)
            self._populate_projects()
            self._render_project()

        self.toast.show_message(
            f'Deleted "{project.name}"',
            action_label="Undo",
            action=undo,
            duration=4200,
        )

    def add_color(self) -> None:
        project = self.active_project
        if project is None:
            if not self.data.projects:
                self.new_project()
            else:
                self.toast.show_message("Select a project first")
            return

        self.show_projects_page()

        from .dialogs import ColorDialog, run_dialog

        dialog = ColorDialog(self, show_conversions=False)
        if run_dialog(dialog) != ColorDialog.DialogCode.Accepted:
            return
        color = ColorEntry(name=dialog.color_name(), hex=dialog.color_hex())
        project.colors.append(color)
        project.touch()
        self._persist(silent=True)
        self._populate_projects()
        self._render_project()
        self.toast.show_message(f'Added "{color.name}"')
        QTimer.singleShot(0, self._scroll_to_bottom)

    def edit_color(self, color_id: str) -> None:
        project = self.active_project
        if project is None:
            return
        color = next((item for item in project.colors if item.id == color_id), None)
        if color is None:
            return

        from .dialogs import ColorDialog, run_dialog

        dialog = ColorDialog(
            self,
            title="Edit color",
            body="Update the name or color value. Changes are saved automatically.",
            action="Save changes",
            name=color.name,
            hex_value=color.hex,
        )
        if run_dialog(dialog) != ColorDialog.DialogCode.Accepted:
            return
        color.name = dialog.color_name()
        color.hex = dialog.color_hex()
        project.touch()
        self._persist(silent=True)
        self._populate_projects()
        self._render_project()
        self.toast.show_message("Color updated")

    def delete_color(self, color_id: str) -> None:
        project = self.active_project
        if project is None:
            return
        color = next((item for item in project.colors if item.id == color_id), None)
        if color is None:
            return
        index = project.colors.index(color)
        project.colors.remove(color)
        project.touch()
        self._persist(silent=True)
        self._populate_projects()
        self._render_project()

        def undo() -> None:
            project.colors.insert(min(index, len(project.colors)), color)
            project.touch()
            self._persist(silent=True)
            self._populate_projects()
            self._render_project()

        self.toast.show_message(
            f'Deleted "{color.name}"',
            action_label="Undo",
            action=undo,
            duration=4200,
        )

    def copy_color(self, color_id: str) -> None:
        project = self.active_project
        if project is None:
            return
        color = next((item for item in project.colors if item.id == color_id), None)
        if color is None:
            return
        value = self._display_color(color.hex)
        QApplication.clipboard().setText(value)
        self.toast.show_message(f"Copied {value}")

    def _persist(self, *, silent: bool = True) -> None:
        if not self._loaded:
            return
        try:
            self.store.save(self.data)
        except StoreError as exc:
            self.toast.show_message(f"Could not save: {exc}", kind="error", duration=5000)

    # -------------------------------------------------------- import/export
    def export_active_project(self) -> None:
        self.show_projects_page()
        if self.active_project:
            self.export_project(self.active_project.id)

    def export_project(self, project_id: str) -> None:
        project = self.data.find_project(project_id)
        if project is None:
            return
        suggested = f"{slugify(project.name, 'project')}.json"
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export project",
            suggested,
            "JSON project (*.json);;CSS variables (*.css);;GIMP palette (*.gpl)",
        )
        if not path:
            return
        path_obj = Path(path)
        suffix = path_obj.suffix.lower()
        if not suffix:
            suffix = ".css" if "CSS" in selected_filter else ".gpl" if "GIMP" in selected_filter else ".json"
            path_obj = path_obj.with_suffix(suffix)
        kind = suffix.lstrip(".")
        try:
            from .palette_io import export_palette

            export_palette(project, path_obj, kind)
        except (OSError, ValueError) as exc:
            self.toast.show_message(f"Export failed: {exc}", kind="error", duration=5000)
            return
        self.toast.show_message(f"Exported {path_obj.name}")

    def import_active_project(self) -> None:
        self.show_projects_page()
        if self.active_project:
            self.import_colors(self.active_project.id)

    def import_colors(self, project_id: str) -> None:
        project = self.data.find_project(project_id)
        if project is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import colors",
            "",
            "Project files (*.json *.css *.gpl *.txt);;All files (*)",
        )
        if not path:
            return
        try:
            from .palette_io import import_palette

            colors = import_palette(Path(path))
        except (OSError, ValueError) as exc:
            self.toast.show_message(f"Import failed: {exc}", kind="error", duration=5000)
            return
        project.colors.extend(colors)
        project.touch()
        self._persist(silent=True)
        self.data.active_project_id = project.id
        self._populate_projects()
        self._render_project()
        self.toast.show_message(
            f"Imported {len(colors)} color{'s' if len(colors) != 1 else ''}"
        )

    # ------------------------------------------------------------- layout
    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
            elif child_layout is not None:
                self._clear_layout(child_layout)  # type: ignore[arg-type]

    def _scroll_to_bottom(self) -> None:
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _position_floating_widgets(self) -> None:
        if not hasattr(self, "page_stack"):
            return
        self.toast.reposition()
        self.toast.raise_()

    def _update_responsive_layout(self) -> None:
        sidebar_width = max(280, min(384, round(self.width() * 0.2)))
        if self.sidebar.width() != sidebar_width:
            self.sidebar.setFixedWidth(sidebar_width)
        available = self.page_stack.width() - 96
        self.center_column.setFixedWidth(max(560, min(1148, available)))
        self._position_floating_widgets()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_responsive_layout()

    def showEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().showEvent(event)
        self._update_responsive_layout()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._loaded:
            self._persist(silent=True)
        super().closeEvent(event)
