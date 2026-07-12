"""Settings view - application configuration"""

import sys

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGroupBox, QFrame,
)
from PySide6.QtCore import Qt


class SettingsView(QWidget):
    """View for application settings"""

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.shell = shell
        self.theme_label = None
        self.status_label = None
        self._create_ui()

    def _create_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 10, 20, 10)
        title = QLabel("Settings")
        f = title.font()
        f.setPointSize(f.pointSize() + 2)
        f.setBold(True)
        title.setFont(f)
        hl.addWidget(title)
        hl.addStretch()
        root.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 0, 20, 20)
        cl.setSpacing(12)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # Appearance
        appearance_box = QGroupBox("Appearance")
        al = QVBoxLayout(appearance_box)
        theme_row = QWidget()
        th = QHBoxLayout(theme_row)
        th.setContentsMargins(0, 0, 0, 0)
        th.addWidget(QLabel("Theme:"))
        current_theme = self.shell.gui_app.theme_manager.current_mode
        self.theme_label = QLabel(f"{current_theme.capitalize()} Mode")
        bf = self.theme_label.font()
        bf.setBold(True)
        self.theme_label.setFont(bf)
        th.addWidget(self.theme_label)
        toggle_btn = QPushButton("Toggle Theme")
        toggle_btn.clicked.connect(self._toggle_theme)
        th.addWidget(toggle_btn)
        th.addStretch()
        al.addWidget(theme_row)
        cl.addWidget(appearance_box)

        # Auto-refresh
        refresh_box = QGroupBox("Auto-Refresh")
        rl = QVBoxLayout(refresh_box)
        rl.addWidget(QLabel(
            "Default auto-refresh is disabled.\n"
            "You can enable it per-view in 'My Hosts' view."
        ))
        cl.addWidget(refresh_box)

        # Connection
        conn_box = QGroupBox("Connection")
        connl = QVBoxLayout(conn_box)
        srv_row = QWidget()
        srv_h = QHBoxLayout(srv_row)
        srv_h.setContentsMargins(0, 0, 0, 0)
        srv_h.addWidget(QLabel("Configured Servers:"))
        server_count = 0
        if self.shell.config:
            server_count = len(self.shell.config.get_all_servers())
        cnt_lbl = QLabel(str(server_count))
        cf = cnt_lbl.font()
        cf.setBold(True)
        cnt_lbl.setFont(cf)
        srv_h.addWidget(cnt_lbl)
        manage_btn = QPushButton("Manage Servers")
        manage_btn.clicked.connect(self._manage_servers)
        srv_h.addWidget(manage_btn)
        srv_h.addStretch()
        connl.addWidget(srv_row)

        sess_row = QWidget()
        sess_h = QHBoxLayout(sess_row)
        sess_h.setContentsMargins(0, 0, 0, 0)
        sess_h.addWidget(QLabel("Active Sessions:"))
        session_count = 0
        if self.shell.session_manager:
            session_count = len(self.shell.session_manager.sessions)
        sess_lbl = QLabel(str(session_count))
        sf2 = sess_lbl.font()
        sf2.setBold(True)
        sess_lbl.setFont(sf2)
        sess_h.addWidget(sess_lbl)
        sess_h.addStretch()
        connl.addWidget(sess_row)
        cl.addWidget(conn_box)

        # Keyboard shortcuts
        shortcuts_box = QGroupBox("Keyboard Shortcuts")
        sl = QVBoxLayout(shortcuts_box)
        cmd_key = "Cmd" if sys.platform == "darwin" else "Ctrl"
        shortcuts_text = (
            f"{cmd_key}+N     New Session\n"
            f"{cmd_key}+W     Close Session\n"
            f"{cmd_key}+Q     Quit Application\n"
            f"{cmd_key}+T     Toggle Theme\n"
            f"{cmd_key}+R     Refresh View\n"
            f"{cmd_key}+C     Copy to Clipboard\n"
            "F1         Show Shortcuts Help"
        )
        shortcuts_lbl = QLabel(shortcuts_text)
        mf = shortcuts_lbl.font()
        mf.setFamily("Monospace")
        shortcuts_lbl.setFont(mf)
        sl.addWidget(shortcuts_lbl)
        cl.addWidget(shortcuts_box)

        # About
        about_box = QGroupBox("About")
        abl = QVBoxLayout(about_box)
        from quads_client import __version__
        about_lbl = QLabel(
            f"QUADS Client GUI v{__version__}\n\n"
            "A graphical interface for QUADS\n"
            "(QUADS Automated Deployment System)"
        )
        about_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        abl.addWidget(about_lbl)
        about_btn = QPushButton("View Full About")
        about_btn.clicked.connect(self.shell.gui_app._show_about)
        abl.addWidget(about_btn)
        cl.addWidget(about_box)

        # Config file location
        if self.shell.config:
            config_box = QGroupBox("Configuration")
            cfl = QVBoxLayout(config_box)
            path_lbl = QLabel(f"Config file: {self.shell.config.config_path}")
            path_lbl.setStyleSheet("color: gray; font-size: 10px;")
            cfl.addWidget(path_lbl)
            cl.addWidget(config_box)

        cl.addStretch()

        # Status bar
        self.status_label = QLabel("")
        self.status_label.setContentsMargins(20, 2, 20, 8)
        root.addWidget(self.status_label)

    def _toggle_theme(self):
        new_mode = self.shell.gui_app.theme_manager.toggle_theme()
        for view in self.shell.gui_app.views.values():
            if hasattr(view, "refresh_theme"):
                view.refresh_theme()
        if self.status_label:
            self.status_label.setText(f"Theme switched to {new_mode} mode")
        if self.theme_label:
            self.theme_label.setText(f"{new_mode.capitalize()} Mode")

    def _manage_servers(self):
        self.shell.gui_app._show_view("connection")

    def refresh(self):
        pass
