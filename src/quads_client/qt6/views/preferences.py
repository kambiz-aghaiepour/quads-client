"""Preferences dialog"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QScrollArea, QGroupBox, QFrame, QSpinBox, QCheckBox, QComboBox,
    QDialogButtonBox, QWidget,
)
from PySide6.QtCore import Qt


class PreferencesDialog(QDialog):
    """Preferences dialog; call exec() then get_result() to read saved settings."""

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.shell = shell
        self.setWindowTitle("Preferences")
        self.resize(560, 540)
        self.setMinimumSize(500, 460)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._result = None
        self._create_ui()
        self._load_current_prefs()

    def _create_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        title_bar = QWidget()
        tbl = QHBoxLayout(title_bar)
        tbl.setContentsMargins(20, 12, 20, 12)
        lbl = QLabel("Preferences")
        f = lbl.font()
        f.setPointSize(f.pointSize() + 2)
        f.setBold(True)
        lbl.setFont(f)
        tbl.addWidget(lbl)
        root.addWidget(title_bar)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 12, 20, 12)
        cl.setSpacing(14)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # --- Auto-refresh ---
        refresh_group = QGroupBox("Auto-Refresh")
        refresh_layout = QGridLayout(refresh_group)
        refresh_layout.setSpacing(8)

        self.auto_refresh_check = QCheckBox("Enable auto-refresh for My Hosts view")
        refresh_layout.addWidget(self.auto_refresh_check, 0, 0, 1, 2)

        refresh_layout.addWidget(QLabel("Refresh interval (seconds):"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(10, 3600)
        self.refresh_interval_spin.setValue(30)
        self.refresh_interval_spin.setFixedWidth(90)
        refresh_layout.addWidget(self.refresh_interval_spin, 1, 1)
        cl.addWidget(refresh_group)

        # --- Appearance ---
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QGridLayout(appearance_group)
        appearance_layout.setSpacing(8)

        appearance_layout.addWidget(QLabel("Theme:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setFixedWidth(120)
        appearance_layout.addWidget(self.theme_combo, 0, 1)

        self.show_admin_badge_check = QCheckBox("Show admin badge in status bar")
        appearance_layout.addWidget(self.show_admin_badge_check, 1, 0, 1, 2)

        self.compact_sidebar_check = QCheckBox("Use compact sidebar (icons only)")
        appearance_layout.addWidget(self.compact_sidebar_check, 2, 0, 1, 2)
        cl.addWidget(appearance_group)

        # --- Connection ---
        conn_group = QGroupBox("Connection")
        conn_layout = QGridLayout(conn_group)
        conn_layout.setSpacing(8)

        self.auto_reconnect_check = QCheckBox("Auto-reconnect on startup")
        conn_layout.addWidget(self.auto_reconnect_check, 0, 0, 1, 2)

        self.verify_ssl_check = QCheckBox("Verify SSL certificates by default")
        conn_layout.addWidget(self.verify_ssl_check, 1, 0, 1, 2)

        conn_layout.addWidget(QLabel("Request timeout (seconds):"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setFixedWidth(90)
        conn_layout.addWidget(self.timeout_spin, 2, 1)
        cl.addWidget(conn_group)

        # --- Notifications ---
        notif_group = QGroupBox("Notifications")
        notif_layout = QGridLayout(notif_group)
        notif_layout.setSpacing(8)

        self.notify_on_refresh_check = QCheckBox("Show status message on auto-refresh")
        notif_layout.addWidget(self.notify_on_refresh_check, 0, 0, 1, 2)

        self.notify_on_error_check = QCheckBox("Show popup on errors (otherwise show in status bar)")
        notif_layout.addWidget(self.notify_on_error_check, 1, 0, 1, 2)
        cl.addWidget(notif_group)

        cl.addStretch()

        # Button row
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep2)

        btn_row = QWidget()
        brl = QHBoxLayout(btn_row)
        brl.setContentsMargins(20, 10, 20, 10)
        brl.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        brl.addWidget(cancel_btn)
        reset_btn = QPushButton("Reset Defaults")
        reset_btn.clicked.connect(self._reset_defaults)
        brl.addWidget(reset_btn)
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        brl.addWidget(save_btn)
        root.addWidget(btn_row)

    def _load_current_prefs(self):
        config = self.shell.config
        if not config:
            return
        prefs = config.get_preferences() if hasattr(config, "get_preferences") else {}

        self.auto_refresh_check.setChecked(prefs.get("auto_refresh", True))
        self.refresh_interval_spin.setValue(prefs.get("refresh_interval", 30))

        theme = self.shell.gui_app.theme_manager.current_mode if self.shell.gui_app else "dark"
        self.theme_combo.setCurrentText(theme.capitalize())

        self.show_admin_badge_check.setChecked(prefs.get("show_admin_badge", True))
        self.compact_sidebar_check.setChecked(prefs.get("compact_sidebar", False))
        self.auto_reconnect_check.setChecked(prefs.get("auto_reconnect", True))
        self.verify_ssl_check.setChecked(prefs.get("verify_ssl_default", True))
        self.timeout_spin.setValue(prefs.get("request_timeout", 30))
        self.notify_on_refresh_check.setChecked(prefs.get("notify_on_refresh", False))
        self.notify_on_error_check.setChecked(prefs.get("notify_on_error", True))

    def _reset_defaults(self):
        self.auto_refresh_check.setChecked(True)
        self.refresh_interval_spin.setValue(30)
        self.theme_combo.setCurrentText("Dark")
        self.show_admin_badge_check.setChecked(True)
        self.compact_sidebar_check.setChecked(False)
        self.auto_reconnect_check.setChecked(True)
        self.verify_ssl_check.setChecked(True)
        self.timeout_spin.setValue(30)
        self.notify_on_refresh_check.setChecked(False)
        self.notify_on_error_check.setChecked(True)

    def _on_save(self):
        self._result = {
            "auto_refresh": self.auto_refresh_check.isChecked(),
            "refresh_interval": self.refresh_interval_spin.value(),
            "theme": self.theme_combo.currentText().lower(),
            "show_admin_badge": self.show_admin_badge_check.isChecked(),
            "compact_sidebar": self.compact_sidebar_check.isChecked(),
            "auto_reconnect": self.auto_reconnect_check.isChecked(),
            "verify_ssl_default": self.verify_ssl_check.isChecked(),
            "request_timeout": self.timeout_spin.value(),
            "notify_on_refresh": self.notify_on_refresh_check.isChecked(),
            "notify_on_error": self.notify_on_error_check.isChecked(),
        }
        self.accept()

    def get_result(self):
        """Return saved prefs dict or None if cancelled."""
        return self._result
