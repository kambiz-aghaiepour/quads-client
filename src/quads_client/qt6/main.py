"""Main application window for QUADS Client GUI"""

import sys
import webbrowser

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QStatusBar,
    QMessageBox,
    QDialog,
    QGridLayout,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QIcon

from quads_client import __version__
from quads_client.qt6.theme import ThemeManager
from quads_client.gui.controllers.gui_shell import GuiShell
from quads_client.qt6.views.onboarding import OnboardingWizard
from quads_client.qt6.views.connection import ConnectionView
from quads_client.qt6.views.schedule import ScheduleView
from quads_client.qt6.views.my_hosts import MyHostsView
from quads_client.qt6.views.assignments import AssignmentsView
from quads_client.qt6.views.clouds import CloudsView
from quads_client.qt6.views.hosts import HostsView
from quads_client.qt6.views.admin_schedule import AdminScheduleView
from quads_client.qt6.views.available import AvailableView
from quads_client.qt6.views.moves import MoveProgressView
from quads_client.qt6.views.settings import SettingsView
from quads_client.qt6.views.preferences import PreferencesDialog


class QuadsClientApp(QMainWindow):
    """Main QUADS Client GUI application"""

    def __init__(self):
        super().__init__()

        self.is_macos = sys.platform == "darwin"
        self.setWindowTitle(f"QUADS Client v{__version__}")
        self.setMinimumSize(1000, 600)

        self._set_window_icon()

        self.theme_manager = ThemeManager(initial_theme="dark")

        self.shell = GuiShell(self)
        self.preferences = self._load_preferences()

        self._apply_window_preferences()

        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()

        self._check_first_launch()

        QTimer.singleShot(500, self._auto_connect_on_startup)

    # ------------------------------------------------------------------ layout

    def _create_menu_bar(self):
        cmd = "Cmd" if self.is_macos else "Ctrl"
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        file_menu.addAction(self._action("New Session", self._new_session, f"{cmd}+N"))
        file_menu.addAction(self._action("Close Session", self._close_session, f"{cmd}+W"))
        file_menu.addSeparator()
        file_menu.addAction(self._action("Exit", self.close, f"{cmd}+Q"))

        edit_menu = mb.addMenu("Edit")
        edit_menu.addAction(self._action("Preferences…", self._show_preferences))
        edit_menu.addAction(self._action("Toggle Theme", self._toggle_theme, f"{cmd}+T"))

        view_menu = mb.addMenu("View")
        view_menu.addAction(self._action("Refresh", self._refresh_view, f"{cmd}+R"))
        view_menu.addAction(self._action("Toggle Sidebar", self._toggle_sidebar))

        help_menu = mb.addMenu("Help")
        help_menu.addAction(self._action("Setup Wizard", self._show_onboarding))
        help_menu.addSeparator()
        help_menu.addAction(self._action("About", self._show_about))
        help_menu.addAction(self._action("Documentation", self._open_documentation))
        help_menu.addAction(self._action("Report Issue", self._report_issue))
        help_menu.addAction(self._action("Keyboard Shortcuts", self._show_shortcuts, "F1"))

    def _action(self, label, slot, shortcut=None):
        act = QAction(label, self)
        act.triggered.connect(slot)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        return act

    def _create_main_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("sidebar")
        self.sidebar_frame.setFixedWidth(210)
        sb_layout = QVBoxLayout(self.sidebar_frame)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        title = QLabel("QUADS Client")
        f = title.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 2)
        title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setContentsMargins(10, 14, 10, 4)
        sb_layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sb_layout.addWidget(sep)
        sb_layout.addSpacing(4)

        nav_items = [
            ("📡 Servers", self._show_servers_view, False, "servers"),
            ("📅 Schedule", self._show_schedule_view, False, "schedule"),
            ("📊 Available", self._show_available_view, False, "available"),
            ("💻 My Hosts", self._show_my_hosts_view, False, "my_hosts"),
            ("📋 Assignments", self._show_assignments_view, False, "assignments"),
            ("~ Move Progress", self._show_moves_view, False, "moves"),
            (None, None, True, None),  # admin separator
            ("👑 Admin Schedule", self._show_admin_schedule_view, True, "admin_schedule"),
            ("☁️  Clouds", self._show_clouds_view, True, "clouds"),
            ("🖥️  Hosts", self._show_hosts_view, True, "hosts"),
            (None, None, False, None),  # settings separator
            ("⚙️  Settings", self._show_settings_view, False, "settings"),
        ]

        self.nav_button_map = {}
        self._sidebar_items = []

        for label, command, is_admin, view_name in nav_items:
            if label is None:
                sep2 = QFrame()
                sep2.setFrameShape(QFrame.Shape.HLine)
                sep2.setContentsMargins(0, 4, 0, 4)
                sb_layout.addWidget(sep2)
                self._sidebar_items.append(("separator", sep2, is_admin))
                continue

            btn = QPushButton(label)
            btn.setObjectName("nav_btn")
            btn.setProperty("active", "false")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(command)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            sb_layout.addWidget(btn)
            self._sidebar_items.append(("button", btn, is_admin))
            if view_name:
                self.nav_button_map[view_name] = btn

        sb_layout.addStretch()
        root.addWidget(self.sidebar_frame)

        # Separator
        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        root.addWidget(vline)

        # Content stack
        self.content_stack = QStackedWidget()
        root.addWidget(self.content_stack, 1)

        self._view_factories = {
            "servers": lambda: ConnectionView(self.content_stack, self.shell),
            "schedule": lambda: ScheduleView(self.content_stack, self.shell),
            "available": lambda: AvailableView(self.content_stack, self.shell),
            "my_hosts": lambda: MyHostsView(self.content_stack, self.shell),
            "assignments": lambda: AssignmentsView(self.content_stack, self.shell),
            "moves": lambda: MoveProgressView(self.content_stack, self.shell),
            "admin_schedule": lambda: AdminScheduleView(self.content_stack, self.shell),
            "clouds": lambda: CloudsView(self.content_stack, self.shell),
            "hosts": lambda: HostsView(self.content_stack, self.shell),
            "settings": lambda: SettingsView(self.content_stack, self.shell),
        }

        self.views = {}
        self.current_view = None
        self.current_view_name = None

        self._show_view("welcome")

    def _create_status_bar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)

        self.connection_indicator = QLabel("●")
        self.connection_indicator.setStyleSheet("color: #888888; font-size: 14px;")
        sb.addPermanentWidget(self.connection_indicator)

        self.connection_status_label = QLabel("Not connected")
        sb.addWidget(self.connection_status_label)

        self.admin_indicator_label = QLabel("")
        self.admin_indicator_label.setStyleSheet("color: #ff9900; font-weight: bold;")
        sb.addPermanentWidget(self.admin_indicator_label)

        self.status_label = QLabel("")
        sb.addPermanentWidget(self.status_label)

    # ------------------------------------------------------------------ views

    def _create_welcome_view(self):
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.addStretch()

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(center, 0, Qt.AlignmentFlag.AlignCenter)
        outer.addStretch()

        welcome = QLabel("Welcome to QUADS Client")
        f = welcome.font()
        f.setPointSize(f.pointSize() + 6)
        welcome.setFont(f)
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(welcome)
        center_layout.addSpacing(20)

        has_servers = False
        if self.shell.config:
            servers = self.shell.config.get_all_servers()
            has_servers = len(servers) > 0

        if has_servers and not self.shell.is_authenticated():
            info = QLabel("You have servers configured.\n\nClick below to connect:")
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            center_layout.addWidget(info)
            center_layout.addSpacing(10)
            login_btn = QPushButton("Connect")
            login_btn.clicked.connect(self._auto_login_from_welcome)
            center_layout.addWidget(login_btn, 0, Qt.AlignmentFlag.AlignCenter)

        elif self.shell.is_authenticated():
            server_name = getattr(self.shell.connection, "current_server", "") if self.shell.connection else ""
            username = getattr(self.shell.connection, "username", "") if self.shell.connection else ""
            info_text = f"Connected to {server_name}\nLogged in as {username}\n\nSelect an item from the sidebar."
            info = QLabel(info_text)
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            center_layout.addWidget(info)

        else:
            info = QLabel(
                "Select an item from the sidebar to get started.\n\nNew to QUADS? Check Help → Documentation"
            )
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            center_layout.addWidget(info)

        return w

    def _ensure_view(self, view_name):
        if view_name not in self.views and view_name in self._view_factories:
            view = self._view_factories[view_name]()
            self.views[view_name] = view
            self.content_stack.addWidget(view)
            return True
        return False

    def _show_view(self, view_name):
        if view_name == "welcome":
            if "welcome" in self.views:
                old = self.views.pop("welcome")
                self.content_stack.removeWidget(old)
                old.deleteLater()
            welcome = self._create_welcome_view()
            self.views["welcome"] = welcome
            self.content_stack.addWidget(welcome)

        just_created = self._ensure_view(view_name)

        if view_name in self.views:
            view = self.views[view_name]
            self.content_stack.setCurrentWidget(view)
            self.current_view = view
            self.current_view_name = view_name

            if not just_created and hasattr(view, "refresh"):
                view.refresh()
        else:
            self.update_status(f"{view_name.title()} view — not yet implemented")

        self._update_nav_highlighting(view_name)

    def _update_nav_highlighting(self, active_view_name):
        for view_name, btn in self.nav_button_map.items():
            is_active = view_name == active_view_name
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ------------------------------------------------------------------ nav

    def _show_servers_view(self):
        self._show_view("servers")

    def _show_schedule_view(self):
        self._show_view("schedule")

    def _show_my_hosts_view(self):
        self._show_view("my_hosts")

    def _show_assignments_view(self):
        self._show_view("assignments")

    def _show_moves_view(self):
        self._show_view("moves")

    def _show_available_view(self):
        self._show_view("available")

    def _show_settings_view(self):
        self._show_view("settings")

    def _show_admin_schedule_view(self):
        if not self.shell.is_admin():
            self.update_status("Admin role required")
            return
        self._show_view("admin_schedule")

    def _show_clouds_view(self):
        if not self.shell.is_admin():
            self.update_status("Admin role required")
            return
        self._show_view("clouds")

    def _show_hosts_view(self):
        if not self.shell.is_admin():
            self.update_status("Admin role required")
            return
        self._show_view("hosts")

    # ------------------------------------------------------------------ actions

    def _toggle_sidebar(self):
        self.sidebar_frame.setVisible(not self.sidebar_frame.isVisible())

    def _toggle_theme(self):
        new_mode = self.theme_manager.toggle_theme()
        for view in self.views.values():
            if hasattr(view, "refresh_theme"):
                view.refresh_theme()
        self.update_status(f"Theme switched to {new_mode} mode")

    def _new_session(self):
        self.update_status("New session — not yet implemented")

    def _close_session(self):
        self.update_status("Close session — not yet implemented")

    def _refresh_view(self):
        if self.current_view and hasattr(self.current_view, "refresh"):
            self.current_view.refresh()

    def _show_preferences(self):
        old_font_size = self.preferences.get("font_size", "large")
        dialog = PreferencesDialog(self, self.shell)
        dialog.exec()
        result = dialog.get_result()
        if result:
            self.preferences = self._load_preferences()
            new_font_size = self.preferences.get("font_size", "large")
            if new_font_size != old_font_size:
                self._apply_font_preferences()
                self.update_status(f"Preferences saved — font size: {new_font_size}")
            else:
                self.update_status("Preferences saved")
            if "my_hosts" in self.views and hasattr(self.views["my_hosts"], "apply_preferences"):
                self.views["my_hosts"].apply_preferences(self.preferences)

    def _auto_login_from_welcome(self):
        from quads_client.qt6.widgets.dialogs import show_error_dialog

        target = self.shell.get_auto_login_server()
        if target:
            success, error = self.shell.connect_to_server(target)
            if success:
                self._show_view("welcome")
                self.update_role_visibility()
            else:
                show_error_dialog(self, "Login Failed", f"Failed to connect to {target}", error or "")
        else:
            self._show_servers_view()

    def _show_about(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("About QUADS Client")
        dlg.setFixedSize(420, 360)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(8)

        title = QLabel(f"QUADS Client v{__version__}")
        f = title.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 4)
        title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(self._centered_label("Graphical User Interface for QUADS"))
        layout.addSpacing(10)

        devs_header = QLabel("Core Developers:")
        f2 = devs_header.font()
        f2.setBold(True)
        devs_header.setFont(f2)
        devs_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(devs_header)

        for name in ("Will Foster", "Gonza Rafuls", "Kambiz Aghaiepour"):
            layout.addWidget(self._centered_label(f"• {name}"))

        layout.addSpacing(10)
        layout.addWidget(self._centered_label("QUADS is Open Source software crafted with love ❤️"))

        btn_row = QHBoxLayout()
        gpl_btn = QPushButton("GPLv3 License")
        gpl_btn.clicked.connect(
            lambda: webbrowser.open("https://github.com/quadsproject/quads-client/blob/main/LICENSE")
        )
        web_btn = QPushButton("QUADS Website")
        web_btn.clicked.connect(lambda: webbrowser.open("https://quads.dev"))
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(gpl_btn)
        btn_row.addWidget(web_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dlg.exec()

    def _show_shortcuts(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Keyboard Shortcuts")
        dlg.setFixedSize(380, 320)
        layout = QVBoxLayout(dlg)

        title = QLabel("Keyboard Shortcuts")
        f = title.font()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 2)
        title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        cmd = "Cmd" if self.is_macos else "Ctrl"
        shortcuts = [
            (f"{cmd}+N", "New Session"),
            (f"{cmd}+W", "Close Session"),
            (f"{cmd}+Q", "Quit Application"),
            (f"{cmd}+T", "Toggle Theme"),
            (f"{cmd}+R", "Refresh View"),
            ("F1", "Show Shortcuts"),
        ]

        grid = QWidget()
        grid_layout = QGridLayout(grid)
        for row, (key, desc) in enumerate(shortcuts):
            key_lbl = QLabel(key)
            f3 = key_lbl.font()
            f3.setBold(True)
            f3.setFamily("Monospace")
            key_lbl.setFont(f3)
            key_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            grid_layout.addWidget(key_lbl, row, 0)
            grid_layout.addWidget(QLabel(desc), row, 1)
        layout.addWidget(grid)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignCenter)

        dlg.exec()

    def _open_documentation(self):
        webbrowser.open("https://quads.dev")
        self.update_status("Opening documentation…")

    def _report_issue(self):
        webbrowser.open("https://github.com/quadsproject/quads-client/issues")
        self.update_status("Opening issue tracker…")

    def _show_onboarding(self):
        OnboardingWizard(self, self.shell).exec()

    @staticmethod
    def _centered_label(text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    # ------------------------------------------------------------------ status

    def update_status(self, message=""):
        if hasattr(self, "status_label"):
            self.status_label.setText(message)
        self.update_connection_indicator()

    def update_connection_indicator(self):
        if not hasattr(self, "connection_indicator"):
            return
        is_connected = self.shell.is_authenticated() if self.shell else False
        if is_connected:
            color = self.theme_manager.get_color("success")
            self.connection_indicator.setStyleSheet(f"color: {color}; font-size: 14px;")
            server = getattr(self.shell.connection, "current_server", "") if self.shell.connection else ""
            username = getattr(self.shell.connection, "username", "") if self.shell.connection else ""
            if server and username:
                self.connection_status_label.setText(f"Connected to {server} as {username}")
            elif server:
                self.connection_status_label.setText(f"Connected to {server}")
            else:
                self.connection_status_label.setText("Connected")
        else:
            self.connection_indicator.setStyleSheet("color: #888888; font-size: 14px;")
            self.connection_status_label.setText("Not connected")

    def update_role_visibility(self):
        is_admin = self.shell.is_admin()
        is_authenticated = self.shell.is_authenticated()

        for item_type, widget, is_admin_only in self._sidebar_items:
            widget.setVisible(not (is_admin_only and not is_admin))

        base_title = f"QUADS Client v{__version__}"
        if is_admin and is_authenticated:
            username = getattr(self.shell.connection, "username", "") if self.shell.connection else ""
            server = getattr(self.shell.connection, "current_server", "") if self.shell.connection else ""
            self.setWindowTitle(f"{base_title} — 👑 ADMIN ({username}@{server})")
        elif is_authenticated:
            username = getattr(self.shell.connection, "username", "") if self.shell.connection else ""
            server = getattr(self.shell.connection, "current_server", "") if self.shell.connection else ""
            self.setWindowTitle(f"{base_title} — {username}@{server}")
        else:
            self.setWindowTitle(base_title)

        if is_admin and is_authenticated:
            self.admin_indicator_label.setText("👑 ADMIN MODE")
        else:
            self.admin_indicator_label.setText("")

        self.update_connection_indicator()

        role_dependent_views = ["available", "assignments"]
        current_invalidated = False
        for vn in role_dependent_views:
            if vn in self.views:
                if self.current_view is self.views[vn]:
                    current_invalidated = True
                view = self.views.pop(vn)
                self.content_stack.removeWidget(view)
                view.deleteLater()

        if current_invalidated and self.current_view_name:
            self._show_view(self.current_view_name)

    def show_message(self, message, level="info"):
        if level == "error":
            self.update_status(f"ERROR: {message}")
        elif level == "warning":
            self.update_status(f"WARNING: {message}")
        elif level == "success":
            self.update_status(f"✓ {message}")
        else:
            self.update_status(message)
        self.update_role_visibility()

    # ------------------------------------------------------------------ prefs / window

    def _load_preferences(self):
        defaults = {
            "auto_refresh_interval": 30,
            "auto_refresh_my_hosts": True,
            "confirm_terminate": True,
            "confirm_release": True,
            "confirm_exit": False,
            "remember_window": True,
            "auto_connect": False,
            "default_server": "",
            "font_size": "large",
            "window_width": 1200,
            "window_height": 800,
        }
        if self.shell.config and hasattr(self.shell.config, "config_data"):
            gui_prefs = self.shell.config.config_data.get("gui_preferences", {})
            return {**defaults, **gui_prefs}
        return defaults

    def _apply_window_preferences(self):
        w = self.preferences.get("window_width", 1200)
        h = self.preferences.get("window_height", 800)
        self.resize(w, h)

    def _apply_font_preferences(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QFont

        size_map = {
            "small": 9,
            "medium": 10,
            "large": 11,
            "extra_large": 13,
        }
        pt = size_map.get(self.preferences.get("font_size", "large"), 11)
        font = QFont()
        font.setPointSize(pt)
        QApplication.setFont(font)

    def _save_window_preferences(self):
        if not self.preferences.get("remember_window", True):
            return
        if self.shell.config and hasattr(self.shell.config, "config_data"):
            prefs = self.shell.config.config_data.setdefault("gui_preferences", {})
            prefs["window_width"] = self.width()
            prefs["window_height"] = self.height()
            try:
                self.shell.config.save_config()
            except Exception:
                pass

    def _set_window_icon(self):
        from pathlib import Path

        candidate_paths = [
            Path(__file__).parent / "assets" / "quads-client.png",
            Path(__file__).parent.parent.parent.parent / "desktop" / "icons" / "quads-client.png",
            Path("/usr/share/icons/hicolor/128x128/apps/quads-client.png"),
        ]
        for p in candidate_paths:
            if p.exists():
                self.setWindowIcon(QIcon(str(p)))
                break

    def _check_first_launch(self):
        if self.shell.config and self.shell.config.needs_initial_setup():
            QTimer.singleShot(500, self._show_onboarding)
        self.update_role_visibility()

    def _auto_connect_on_startup(self):
        if not self.preferences.get("auto_connect", False):
            return
        default_server = self.preferences.get("default_server", "")
        if not default_server:
            return
        if self.shell.config:
            servers = self.shell.config.get_all_servers()
            if default_server in servers:
                success, error = self.shell.connect_to_server(default_server)
                if success:
                    self.update_role_visibility()
                else:
                    self.update_status(f"Auto-connect failed: {error}")

    def closeEvent(self, event):
        if self.preferences.get("confirm_exit", False):
            session_count = 0
            if self.shell.session_manager:
                session_count = len(self.shell.session_manager.sessions)
            if session_count > 0:
                result = QMessageBox.question(
                    self,
                    "Confirm Exit",
                    f"You have {session_count} active session(s). Exit?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if result != QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return
        self._save_window_preferences()
        event.accept()
