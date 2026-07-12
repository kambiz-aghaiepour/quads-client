"""Connection and server management view"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QScrollArea,
    QGroupBox,
    QFrame,
    QDialog,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from quads_client.qt6.widgets.dialogs import show_error_dialog
from quads_client.qt6.widgets.base import _WorkerThread


class ConnectionView(QWidget):
    """View for managing servers and connections"""

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.shell = shell
        self.selected_server = None
        self._version_fetcher = None
        self._create_ui()
        self._refresh_server_list()

    def _create_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Title bar
        title_bar = QWidget()
        tbl = QHBoxLayout(title_bar)
        tbl.setContentsMargins(20, 10, 20, 10)
        title = QLabel("Servers & Connections")
        tf = title.font()
        tf.setPointSize(tf.pointSize() + 2)
        tf.setBold(True)
        title.setFont(tf)
        tbl.addWidget(title)
        tbl.addStretch()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_server_list)
        tbl.addWidget(refresh_btn)
        add_btn = QPushButton("+ Add Server")
        add_btn.clicked.connect(self._add_server)
        tbl.addWidget(add_btn)
        root.addWidget(title_bar)

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

        # Configured Servers
        cl.addWidget(QLabel("Configured Servers:"))

        self.server_tree = QTreeWidget()
        self.server_tree.setColumnCount(4)
        self.server_tree.setHeaderLabels(["Name", "URL", "QUADS Version", "Status"])
        self.server_tree.setColumnWidth(0, 150)
        self.server_tree.setColumnWidth(1, 250)
        self.server_tree.setColumnWidth(2, 120)
        self.server_tree.setColumnWidth(3, 100)
        self.server_tree.setRootIsDecorated(False)
        self.server_tree.setAlternatingRowColors(True)
        self.server_tree.setFixedHeight(150)
        self.server_tree.currentItemChanged.connect(self._on_server_selected)
        cl.addWidget(self.server_tree)

        # Server Details
        details_box = QGroupBox("Server Details")
        details_layout = QVBoxLayout(details_box)
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.StyleHint.TypeWriter)
        self.details_text.setFont(mono)
        self.details_text.setFixedHeight(100)
        details_layout.addWidget(self.details_text)

        btn_row = QWidget()
        br_l = QHBoxLayout(btn_row)
        br_l.setContentsMargins(0, 0, 0, 0)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._connect_server)
        self.connect_button.setEnabled(False)
        br_l.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self._disconnect_server)
        self.disconnect_button.setEnabled(False)
        br_l.addWidget(self.disconnect_button)

        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self._edit_server)
        self.edit_button.setEnabled(False)
        br_l.addWidget(self.edit_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_server)
        self.remove_button.setEnabled(False)
        br_l.addWidget(self.remove_button)
        br_l.addStretch()
        details_layout.addWidget(btn_row)
        cl.addWidget(details_box)

        # Active Sessions
        sessions_box = QGroupBox("Active Sessions")
        sessions_layout = QVBoxLayout(sessions_box)

        self.sessions_tree = QTreeWidget()
        self.sessions_tree.setColumnCount(5)
        self.sessions_tree.setHeaderLabels(["ID", "Server", "Label", "Status", "Last Active"])
        self.sessions_tree.setColumnWidth(0, 50)
        self.sessions_tree.setColumnWidth(1, 150)
        self.sessions_tree.setColumnWidth(2, 100)
        self.sessions_tree.setColumnWidth(3, 100)
        self.sessions_tree.setColumnWidth(4, 100)
        self.sessions_tree.setRootIsDecorated(False)
        self.sessions_tree.setAlternatingRowColors(True)
        self.sessions_tree.setFixedHeight(130)
        sessions_layout.addWidget(self.sessions_tree)

        sess_btn_row = QWidget()
        sbrl = QHBoxLayout(sess_btn_row)
        sbrl.setContentsMargins(0, 0, 0, 0)
        switch_btn = QPushButton("Switch")
        switch_btn.clicked.connect(self._switch_session)
        sbrl.addWidget(switch_btn)
        close_sess_btn = QPushButton("Close Session")
        close_sess_btn.clicked.connect(self._close_session)
        sbrl.addWidget(close_sess_btn)
        sbrl.addStretch()
        sessions_layout.addWidget(sess_btn_row)
        cl.addWidget(sessions_box)
        cl.addStretch()

    def _refresh_server_list(self):
        self.server_tree.clear()
        if not self.shell.config:
            return

        active_session = self.shell.session_manager.active_session if self.shell.session_manager else None
        active_server = (
            active_session.connection.current_server if active_session and active_session.connection else None
        )

        servers = self.shell.config.get_all_servers()
        for name, server_config in servers.items():
            url = server_config.get("url", "")
            is_connected = False
            is_active_server = False
            if self.shell.session_manager:
                for session in self.shell.session_manager.sessions.values():
                    if session.connection and session.connection.current_server == name:
                        is_connected = True
                        if name == active_server:
                            is_active_server = True
                        break

            if is_active_server:
                status = "✓ Connected"
            elif is_connected:
                status = "● Idle"
            else:
                status = "○ Disconnected"

            item = QTreeWidgetItem([name, url, "-", status])

            from PySide6.QtGui import QColor, QBrush

            if is_active_server:
                color = QColor(self.shell.gui_app.theme_manager.get_color("success"))
                for col in range(4):
                    item.setForeground(col, QBrush(color))
            elif is_connected:
                color = QColor(self.shell.gui_app.theme_manager.get_color("provisioning"))
                for col in range(4):
                    item.setForeground(col, QBrush(color))

            self.server_tree.addTopLevelItem(item)

        self._refresh_session_list()
        self._fetch_versions_async()

    def _fetch_versions_async(self):
        if not self.shell.config:
            return
        servers = dict(self.shell.config.get_all_servers())

        def fetch():
            versions = {}
            for name, config in servers.items():
                try:
                    import requests

                    url = config.get("url", "")
                    verify = config.get("verify", True)
                    if not url:
                        versions[name] = "-"
                        continue
                    response = requests.get(f"{url}/api/v3/version", verify=verify, timeout=5)
                    if response.status_code == 200:
                        import re

                        version_data = response.json()
                        if isinstance(version_data, dict):
                            version = version_data.get("version", "")
                            if version and version != "unknown":
                                versions[name] = version
                                continue
                        elif isinstance(version_data, str):
                            match = re.search(r"(\d+\.\d+\.\d+)", version_data)
                            if match:
                                versions[name] = match.group(1)
                                continue
                    versions[name] = "-"
                except Exception:
                    versions[name] = "-"
            return versions

        thread = _WorkerThread(fetch)
        thread.result_ready.connect(self._update_versions)
        thread.start()
        self._version_fetcher = thread

    def _update_versions(self, versions):
        try:
            root = self.server_tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                name = item.text(0)
                if name in versions:
                    item.setText(2, versions[name])
        except Exception:
            pass

    def _refresh_session_list(self):
        self.sessions_tree.clear()
        if not self.shell.session_manager:
            return

        from PySide6.QtGui import QColor, QBrush

        active_id = self.shell.session_manager.active_session_id if self.shell.session_manager.active_session else None

        for session_id, session in self.shell.session_manager.sessions.items():
            server_name = session.server_name or (session.connection.current_server if session.connection else "N/A")
            label = session.label or "-"

            if session.connection and session.connection.is_connected:
                status = "✓ Active" if session_id == active_id else "● Idle"
            else:
                status = "✗ Offline"

            now = datetime.now()
            delta = now - session.last_active
            total_sec = delta.total_seconds()
            if total_sec < 60:
                last_active = "now"
            elif total_sec < 3600:
                last_active = f"{int(total_sec / 60)}m ago"
            elif total_sec < 86400:
                last_active = f"{int(total_sec / 3600)}h ago"
            else:
                last_active = f"{int(total_sec / 86400)}d ago"

            session_marker = f"{session_id} (*)" if session_id == active_id else str(session_id)
            item = QTreeWidgetItem([session_marker, server_name, label, status, last_active])

            if session_id == active_id:
                color = QColor(self.shell.gui_app.theme_manager.get_color("success"))
                for col in range(5):
                    item.setForeground(col, QBrush(color))
            elif session.connection and session.connection.is_connected:
                color = QColor(self.shell.gui_app.theme_manager.get_color("provisioning"))
                for col in range(5):
                    item.setForeground(col, QBrush(color))

            self.sessions_tree.addTopLevelItem(item)

    def _on_server_selected(self, current, previous):
        if current is None:
            return
        self.selected_server = current.text(0)
        self._update_server_details()

    def _update_server_details(self):
        if not self.selected_server or not self.shell.config:
            return
        try:
            server_config = self.shell.config.get_server(self.selected_server)
        except Exception:
            server_config = {}

        url = server_config.get("url", "N/A")
        verify = server_config.get("verify", True)
        is_connected = False
        is_active_server = False
        user = "N/A"
        role = "N/A"

        active_session = self.shell.session_manager.active_session if self.shell.session_manager else None
        active_server = (
            active_session.connection.current_server if active_session and active_session.connection else None
        )

        if self.shell.session_manager:
            for session in self.shell.session_manager.sessions.values():
                if session.connection and session.connection.current_server == self.selected_server:
                    is_connected = True
                    is_active_server = self.selected_server == active_server
                    if session.connection.username:
                        user = session.connection.username
                    if session.connection.user_role:
                        role = session.connection.user_role.capitalize()
                    elif session.connection.is_authenticated:
                        role = "User"
                    break

        theme = self.shell.gui_app.theme_manager
        success_color = theme.get_color("success")

        html = f"<b>URL:</b> {url}<br>"
        html += f"<b>SSL Verification:</b> {'Enabled' if verify else 'Disabled'}<br>"
        html += "<b>Status:</b> "
        if is_active_server:
            html += f"<span style='color:{success_color}'>Connected (active)</span><br>"
        elif is_connected:
            html += f"<span style='color:{success_color}'>Idle</span><br>"
        else:
            html += "Disconnected<br>"
        if is_connected:
            html += f"<b>User:</b> {user}<br>"
            html += f"<b>Role:</b> {role}<br>"

        self.details_text.setHtml(html)

        self.connect_button.setEnabled(not is_connected)
        self.disconnect_button.setEnabled(is_connected)
        self.edit_button.setEnabled(True)
        self.remove_button.setEnabled(not is_connected)

    def _add_server(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Server")
        dialog.resize(500, 350)
        dialog.setMinimumSize(500, 350)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)

        layout = QGridLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Server Name:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        name_entry = QLineEdit()
        layout.addWidget(name_entry, 0, 1)

        layout.addWidget(QLabel("Server URL:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        url_entry = QLineEdit("https://")
        layout.addWidget(url_entry, 1, 1)

        layout.addWidget(QLabel("Username:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        username_entry = QLineEdit()
        layout.addWidget(username_entry, 2, 1)

        layout.addWidget(QLabel("Password:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        password_entry = QLineEdit()
        password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(password_entry, 3, 1)

        verify_check = QCheckBox("Verify SSL certificate")
        verify_check.setChecked(True)
        layout.addWidget(verify_check, 4, 1)

        tip = QLabel("💡 Username and password can be left blank.\n" "You'll be prompted to login after connecting.")
        tip.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(tip, 5, 0, 1, 2)

        _result = []

        def save_server():
            name = name_entry.text().strip()
            url = url_entry.text().strip()
            if not name or not url:
                QMessageBox.critical(dialog, "Error", "Name and URL are required")
                return

            username = username_entry.text().strip()
            password = password_entry.text()

            success, message, version_info = self.shell.server_commands.add_server_programmatic(
                name=name,
                url=url,
                username=username,
                password=password,
                verify=verify_check.isChecked(),
                test_connection=True,
            )

            if not success:
                if "Could not connect" in message or "returned status code" in message:
                    result = QMessageBox.question(
                        dialog,
                        "Connection Failed",
                        f"{message}\n\nAdd server anyway?\n\nYou can try connecting later.",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )
                    if result == QMessageBox.StandardButton.Yes:
                        success, message, version_info = self.shell.server_commands.add_server_programmatic(
                            name=name,
                            url=url,
                            username=username,
                            password=password,
                            verify=verify_check.isChecked(),
                            test_connection=False,
                        )
                        if not success:
                            QMessageBox.critical(dialog, "Error", message)
                            return
                    else:
                        return
                else:
                    QMessageBox.critical(dialog, "Error", message)
                    return

            _result.append((name, version_info))
            dialog.accept()

        btn_row_widget = QWidget()
        brwl = QHBoxLayout(btn_row_widget)
        brwl.setContentsMargins(0, 0, 0, 0)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        brwl.addWidget(cancel_btn)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(save_server)
        brwl.addWidget(add_btn)
        brwl.addStretch()
        layout.addWidget(btn_row_widget, 6, 0, 1, 2)

        name_entry.setFocus()

        if dialog.exec() == QDialog.DialogCode.Accepted and _result:
            name, version_info = _result[0]
            self._refresh_server_list()
            if version_info and version_info != "unknown":
                QMessageBox.information(
                    self, "Success", f"Server '{name}' added successfully\n\nQUADS version: {version_info}"
                )
            else:
                QMessageBox.information(
                    self,
                    "Server Added",
                    f"Server '{name}' added to configuration\n\nYou can now connect to this server.",
                )

    def _connect_server(self):
        if not self.selected_server:
            return
        success, error = self.shell.connect_to_server(self.selected_server)
        if not success:
            show_error_dialog(self, "Connection Failed", f"Could not connect to {self.selected_server}", error or "")
        self._refresh_server_list()
        self._update_server_details()
        if hasattr(self.shell, "gui_app"):
            self.shell.gui_app.update_role_visibility()
        if success and self.shell.connection and self.shell.connection.registration_mode:
            self._show_login_register_dialog()

    def _show_login_register_dialog(self):
        server_name = self.shell.connection.current_server
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Authenticate - {server_name}")
        dialog.resize(500, 380)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlayout = QVBoxLayout(dialog)

        header_lbl = QLabel(f"Connected to {server_name}")
        hf = header_lbl.font()
        hf.setBold(True)
        header_lbl.setFont(hf)
        dlayout.addWidget(header_lbl)
        dlayout.addWidget(QLabel("Please login or register to continue"))

        tabs = QTabWidget()
        dlayout.addWidget(tabs)

        # Login tab
        login_widget = QWidget()
        login_grid = QGridLayout(login_widget)
        login_grid.setContentsMargins(15, 15, 15, 15)
        login_grid.setSpacing(8)
        login_grid.addWidget(QLabel("Email:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        login_email = QLineEdit()
        login_grid.addWidget(login_email, 0, 1)
        login_grid.addWidget(QLabel("Password:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        login_pass = QLineEdit()
        login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        login_grid.addWidget(login_pass, 1, 1)

        def do_login():
            email = login_email.text().strip()
            password = login_pass.text().strip()
            if not email or not password:
                QMessageBox.critical(dialog, "Error", "Email and password are required")
                return
            success, message, role = self.shell.user_commands.login_programmatic(email, password)
            if success:
                self.shell.config.update_server_credentials(server_name, email, password)
                dialog.accept()
                self._refresh_server_list()
                self._update_server_details()
                if hasattr(self.shell, "gui_app"):
                    self.shell.gui_app.update_role_visibility()
                QMessageBox.information(self, "Success", f"Logged in as {email}")
            else:
                QMessageBox.critical(dialog, "Login Failed", message)

        login_btn = QPushButton("Login")
        login_btn.clicked.connect(do_login)
        login_grid.addWidget(login_btn, 2, 1, Qt.AlignmentFlag.AlignLeft)
        tabs.addTab(login_widget, "Login")

        # Register tab
        reg_widget = QWidget()
        reg_grid = QGridLayout(reg_widget)
        reg_grid.setContentsMargins(15, 15, 15, 15)
        reg_grid.setSpacing(8)
        reg_grid.addWidget(QLabel("Email:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        reg_email = QLineEdit()
        reg_grid.addWidget(reg_email, 0, 1)
        reg_grid.addWidget(QLabel("Password:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        reg_pass = QLineEdit()
        reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        reg_grid.addWidget(reg_pass, 1, 1)
        reg_grid.addWidget(QLabel("Confirm:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        reg_confirm = QLineEdit()
        reg_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        reg_grid.addWidget(reg_confirm, 2, 1)
        admin_note = QLabel("Admin accounts must be created server-side")
        admin_note.setStyleSheet("color: gray; font-size: 10px;")
        reg_grid.addWidget(admin_note, 3, 0, 1, 2)

        def do_register():
            email = reg_email.text().strip()
            password = reg_pass.text().strip()
            confirm = reg_confirm.text().strip()
            if not email or not password:
                QMessageBox.critical(dialog, "Error", "Email and password are required")
                return
            if "@" not in email or "." not in email:
                QMessageBox.critical(dialog, "Error", "Please enter a valid email address")
                return
            if len(password) < 6:
                QMessageBox.critical(dialog, "Error", "Password must be at least 6 characters")
                return
            if password != confirm:
                QMessageBox.critical(dialog, "Error", "Passwords do not match")
                return
            success, message, role = self.shell.user_commands.register_programmatic(email, password)
            if success:
                self.shell.config.update_server_credentials(server_name, email, password)
                dialog.accept()
                self._refresh_server_list()
                self._update_server_details()
                if hasattr(self.shell, "gui_app"):
                    self.shell.gui_app.update_role_visibility()
                QMessageBox.information(self, "Success", f"Registered and logged in as {email}")
            else:
                QMessageBox.critical(dialog, "Registration Failed", message)

        reg_btn = QPushButton("Register")
        reg_btn.clicked.connect(do_register)
        reg_grid.addWidget(reg_btn, 4, 1, Qt.AlignmentFlag.AlignLeft)
        tabs.addTab(reg_widget, "Register")

        login_email.setFocus()
        dialog.exec()

    def _disconnect_server(self):
        if not self.selected_server or not self.shell.session_manager:
            return
        target_session = None
        for session in self.shell.session_manager.sessions.values():
            if session.connection and session.connection.current_server == self.selected_server:
                target_session = session
                break
        if not target_session:
            QMessageBox.warning(self, "Not Connected", f"No active connection to '{self.selected_server}'")
            return
        try:
            server = target_session.connection.current_server
            target_session.connection.disconnect()
            self.shell.poutput(f"Disconnected from {server}")
            self._refresh_server_list()
            self._update_server_details()
            if hasattr(self.shell, "gui_app"):
                self.shell.gui_app.update_role_visibility()
        except Exception as e:
            import traceback

            show_error_dialog(self, "Disconnect Failed", str(e), traceback.format_exc())

    def _edit_server(self):
        if not self.selected_server or not self.shell.config:
            return
        try:
            server_config = self.shell.config.get_server(self.selected_server)
        except Exception:
            QMessageBox.critical(self, "Error", f"Server '{self.selected_server}' not found in configuration")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Server: {self.selected_server}")
        dialog.resize(500, 320)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)

        layout = QGridLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Server Name:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        name_lbl = QLabel(self.selected_server)
        nf = name_lbl.font()
        nf.setBold(True)
        name_lbl.setFont(nf)
        layout.addWidget(name_lbl, 0, 1)

        layout.addWidget(QLabel("Server URL:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        url_entry = QLineEdit(server_config.get("url", ""))
        layout.addWidget(url_entry, 1, 1)

        layout.addWidget(QLabel("Username:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        username_entry = QLineEdit(server_config.get("username", ""))
        layout.addWidget(username_entry, 2, 1)

        layout.addWidget(QLabel("Password:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        password_entry = QLineEdit(server_config.get("password", ""))
        password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(password_entry, 3, 1)

        verify_check = QCheckBox("Verify SSL certificate")
        verify_check.setChecked(server_config.get("verify", True))
        layout.addWidget(verify_check, 4, 1)

        server_name = self.selected_server
        _result = []

        def on_save():
            new_url = url_entry.text().strip()
            if not new_url:
                QMessageBox.critical(dialog, "Error", "URL is required")
                return
            old_url = server_config.get("url", "")
            success, message = self.shell.server_commands.edit_server_programmatic(
                name=server_name,
                url=new_url,
                username=username_entry.text().strip(),
                password=password_entry.text(),
                verify=verify_check.isChecked(),
            )
            if not success:
                QMessageBox.critical(dialog, "Error", message)
                return
            _result.append((old_url, new_url, message))
            dialog.accept()

        btn_row_w = QWidget()
        brwl = QHBoxLayout(btn_row_w)
        brwl.setContentsMargins(0, 0, 0, 0)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        brwl.addWidget(cancel_btn)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(on_save)
        brwl.addWidget(save_btn)
        brwl.addStretch()
        layout.addWidget(btn_row_w, 5, 0, 1, 2)

        if dialog.exec() == QDialog.DialogCode.Accepted and _result:
            old_url, new_url, message = _result[0]
            is_connected = False
            if self.shell.session_manager:
                for session in self.shell.session_manager.sessions.values():
                    if session.connection and session.connection.current_server == server_name:
                        is_connected = True
                        break

            if old_url != new_url and is_connected:
                result = QMessageBox.question(
                    self,
                    "Reconnect?",
                    f"Server URL changed.\n\nReconnect to '{server_name}' with the new settings?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if result == QMessageBox.StandardButton.Yes:
                    try:
                        for s in self.shell.session_manager.sessions.values():
                            if s.connection and s.connection.current_server == server_name:
                                s.connection.disconnect()
                                break
                        conn_success, error = self.shell.connect_to_server(server_name)
                        if not conn_success:
                            QMessageBox.warning(self, "Reconnect Failed", f"Could not reconnect: {error}")
                    except Exception as e:
                        QMessageBox.warning(self, "Reconnect Failed", f"Could not reconnect: {e}")

            self._refresh_server_list()
            self._update_server_details()
            QMessageBox.information(self, "Success", message)

    def _remove_server(self):
        if not self.selected_server:
            return
        result = QMessageBox.question(
            self,
            "Confirm",
            f"Are you sure you want to remove server '{self.selected_server}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return
        success, message = self.shell.server_commands.rm_server_programmatic(self.selected_server)
        if success:
            self._refresh_server_list()
            self.selected_server = None
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

    def _switch_session(self):
        item = self.sessions_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a session to switch to")
            return
        session_id_str = item.text(0).replace(" (*)", "").strip()
        try:
            self.shell.session_commands.cmd_session_switch(session_id_str)
            self._refresh_session_list()
            self._refresh_server_list()
            if hasattr(self.shell, "gui_app"):
                self.shell.gui_app.update_role_visibility()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to switch session: {e}")

    def _close_session(self):
        item = self.sessions_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a session to close")
            return
        session_id_str = item.text(0).replace(" (*)", "").strip()
        result = QMessageBox.question(
            self,
            "Confirm",
            f"Close session {session_id_str}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return
        try:
            self.shell.session_commands.cmd_session_close(session_id_str)
            self._refresh_session_list()
            self._refresh_server_list()
        except Exception as e:
            import traceback

            show_error_dialog(self, "Close Session Failed", str(e), traceback.format_exc())

    def refresh(self):
        self._refresh_server_list()

    def refresh_theme(self):
        if self.selected_server:
            self._update_server_details()
