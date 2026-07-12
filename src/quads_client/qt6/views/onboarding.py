"""Onboarding wizard shown on first launch or when no servers are configured"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QTabWidget, QFrame, QWidget, QStackedWidget,
    QScrollArea, QMessageBox, QGroupBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class OnboardingWizard(QDialog):
    """Multi-step first-launch wizard.

    Step 0: Welcome / intro
    Step 1: Add server (URL, name, optional SSL)
    Step 2: Login or Register
    Step 3: Done
    """

    NUM_STEPS = 4

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.shell = shell
        self.setWindowTitle("Welcome to QUADS Client")
        self.resize(620, 520)
        self.setMinimumSize(560, 460)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        self._current_step = 0
        self._server_name = None
        self._create_ui()
        self._go_to_step(0)

    def _create_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Progress bar (step dots)
        progress_bar = QWidget()
        progress_bar.setFixedHeight(50)
        pbl = QHBoxLayout(progress_bar)
        pbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pbl.setSpacing(16)
        self._step_labels = []
        step_names = ["Welcome", "Add Server", "Login", "Done"]
        for i, name in enumerate(step_names):
            step_col = QWidget()
            scl = QVBoxLayout(step_col)
            scl.setSpacing(2)
            scl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot = QLabel("●")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            df = dot.font()
            df.setPointSize(df.pointSize() + 2)
            dot.setFont(df)
            scl.addWidget(dot)
            name_lbl = QLabel(name)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nf = name_lbl.font()
            nf.setPointSize(nf.pointSize() - 1)
            name_lbl.setFont(nf)
            scl.addWidget(name_lbl)
            self._step_labels.append((dot, name_lbl))
            pbl.addWidget(step_col)
        root.addWidget(progress_bar)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        # Step content (stacked widget)
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self._build_step0()
        self._build_step1()
        self._build_step2()
        self._build_step3()

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep2)

        # Navigation buttons
        nav_row = QWidget()
        nrl = QHBoxLayout(nav_row)
        nrl.setContentsMargins(20, 10, 20, 14)
        self.skip_btn = QPushButton("Skip Setup")
        self.skip_btn.clicked.connect(self._skip_all)
        nrl.addWidget(self.skip_btn)
        nrl.addStretch()
        self.back_btn = QPushButton("‹ Back")
        self.back_btn.clicked.connect(self._prev_step)
        self.back_btn.setEnabled(False)
        nrl.addWidget(self.back_btn)
        self.next_btn = QPushButton("Next ›")
        self.next_btn.clicked.connect(self._next_step)
        self.next_btn.setDefault(True)
        nrl.addWidget(self.next_btn)
        root.addWidget(nav_row)

    def _build_step0(self):
        """Welcome step."""
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(50, 40, 50, 20)
        pl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pl.setSpacing(16)

        icon_lbl = QLabel("🖥")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = icon_lbl.font()
        icon_font.setPointSize(icon_font.pointSize() + 16)
        icon_lbl.setFont(icon_font)
        pl.addWidget(icon_lbl)

        title_lbl = QLabel("Welcome to QUADS Client")
        tf = title_lbl.font()
        tf.setPointSize(tf.pointSize() + 4)
        tf.setBold(True)
        title_lbl.setFont(tf)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pl.addWidget(title_lbl)

        desc_lbl = QLabel(
            "QUADS (Quick and Dirty Scheduler) Client lets you manage bare-metal\n"
            "host assignments and schedules on your QUADS server.\n\n"
            "This wizard will help you connect to your QUADS server and get started."
        )
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)
        pl.addWidget(desc_lbl)
        pl.addStretch()
        self.stack.addWidget(page)

    def _build_step1(self):
        """Add server step."""
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(40, 30, 40, 20)
        pl.setSpacing(12)

        title_lbl = QLabel("Add Your QUADS Server")
        tf = title_lbl.font()
        tf.setBold(True)
        tf.setPointSize(tf.pointSize() + 2)
        title_lbl.setFont(tf)
        pl.addWidget(title_lbl)

        pl.addWidget(QLabel("Enter the details for your QUADS server:"))

        form_group = QGroupBox()
        form_group.setFlat(True)
        form_gl = QGridLayout(form_group)
        form_gl.setSpacing(10)

        form_gl.addWidget(QLabel("Server Name:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.ob_server_name_entry = QLineEdit("default")
        self.ob_server_name_entry.setPlaceholderText("Friendly name (e.g. production)")
        form_gl.addWidget(self.ob_server_name_entry, 0, 1)

        form_gl.addWidget(QLabel("Server URL:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.ob_url_entry = QLineEdit("https://")
        self.ob_url_entry.setPlaceholderText("https://quads.example.com")
        form_gl.addWidget(self.ob_url_entry, 1, 1)

        self.ob_verify_ssl = QCheckBox("Verify SSL certificate")
        self.ob_verify_ssl.setChecked(True)
        form_gl.addWidget(self.ob_verify_ssl, 2, 1)

        pl.addWidget(form_group)

        self.ob_server_status_lbl = QLabel("")
        self.ob_server_status_lbl.setWordWrap(True)
        pl.addWidget(self.ob_server_status_lbl)

        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_connection)
        pl.addWidget(test_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        skip_server_btn = QPushButton("I'll add a server later →")
        skip_server_btn.setFlat(True)
        skip_server_btn.clicked.connect(lambda: self._go_to_step(2))
        pl.addWidget(skip_server_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        pl.addStretch()
        self.stack.addWidget(page)

    def _build_step2(self):
        """Login / Register step."""
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(40, 20, 40, 20)
        pl.setSpacing(10)

        title_lbl = QLabel("Login or Register")
        tf = title_lbl.font()
        tf.setBold(True)
        tf.setPointSize(tf.pointSize() + 2)
        title_lbl.setFont(tf)
        pl.addWidget(title_lbl)

        self.ob_server_for_auth_lbl = QLabel("Enter your credentials for the QUADS server:")
        pl.addWidget(self.ob_server_for_auth_lbl)

        tabs = QTabWidget()
        pl.addWidget(tabs)

        # Login tab
        login_w = QWidget()
        login_gl = QGridLayout(login_w)
        login_gl.setContentsMargins(15, 15, 15, 10)
        login_gl.setSpacing(10)
        login_gl.addWidget(QLabel("Email:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.ob_login_email = QLineEdit()
        login_gl.addWidget(self.ob_login_email, 0, 1)
        login_gl.addWidget(QLabel("Password:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.ob_login_pass = QLineEdit()
        self.ob_login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        login_gl.addWidget(self.ob_login_pass, 1, 1)
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self._do_login)
        login_gl.addWidget(login_btn, 2, 1, Qt.AlignmentFlag.AlignLeft)
        self.ob_login_status = QLabel("")
        self.ob_login_status.setWordWrap(True)
        login_gl.addWidget(self.ob_login_status, 3, 0, 1, 2)
        tabs.addTab(login_w, "Login")

        # Register tab
        reg_w = QWidget()
        reg_gl = QGridLayout(reg_w)
        reg_gl.setContentsMargins(15, 15, 15, 10)
        reg_gl.setSpacing(10)
        reg_gl.addWidget(QLabel("Email:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.ob_reg_email = QLineEdit()
        reg_gl.addWidget(self.ob_reg_email, 0, 1)
        reg_gl.addWidget(QLabel("Password:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.ob_reg_pass = QLineEdit()
        self.ob_reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        reg_gl.addWidget(self.ob_reg_pass, 1, 1)
        reg_gl.addWidget(QLabel("Confirm:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.ob_reg_confirm = QLineEdit()
        self.ob_reg_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        reg_gl.addWidget(self.ob_reg_confirm, 2, 1)
        reg_btn = QPushButton("Register")
        reg_btn.clicked.connect(self._do_register)
        reg_gl.addWidget(reg_btn, 3, 1, Qt.AlignmentFlag.AlignLeft)
        self.ob_reg_status = QLabel("")
        self.ob_reg_status.setWordWrap(True)
        reg_gl.addWidget(self.ob_reg_status, 4, 0, 1, 2)
        tabs.addTab(reg_w, "Register")

        skip_auth_btn = QPushButton("Skip login, continue without account →")
        skip_auth_btn.setFlat(True)
        skip_auth_btn.clicked.connect(lambda: self._go_to_step(3))
        pl.addWidget(skip_auth_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        pl.addStretch()
        self.stack.addWidget(page)

    def _build_step3(self):
        """Done step."""
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(50, 40, 50, 20)
        pl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pl.setSpacing(16)

        icon_lbl = QLabel("✓")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = icon_lbl.font()
        icon_font.setPointSize(icon_font.pointSize() + 18)
        icon_font.setBold(True)
        icon_lbl.setFont(icon_font)
        icon_lbl.setStyleSheet("color: #4ec9b0;")
        pl.addWidget(icon_lbl)

        title_lbl = QLabel("You're all set!")
        tf = title_lbl.font()
        tf.setPointSize(tf.pointSize() + 4)
        tf.setBold(True)
        title_lbl.setFont(tf)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pl.addWidget(title_lbl)

        self.ob_done_desc = QLabel(
            "QUADS Client is configured and ready to use.\n\n"
            "Use the sidebar on the left to navigate between views."
        )
        self.ob_done_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ob_done_desc.setWordWrap(True)
        pl.addWidget(self.ob_done_desc)

        pl.addStretch()
        self.stack.addWidget(page)

    def _update_step_indicators(self):
        for i, (dot, name_lbl) in enumerate(self._step_labels):
            if i < self._current_step:
                dot.setStyleSheet("color: #4ec9b0;")
                dot.setText("✓")
            elif i == self._current_step:
                dot.setStyleSheet("color: #007acc;")
                dot.setText("●")
            else:
                dot.setStyleSheet("color: gray;")
                dot.setText("●")

    def _go_to_step(self, step):
        self._current_step = max(0, min(step, self.NUM_STEPS - 1))
        self.stack.setCurrentIndex(self._current_step)
        self._update_step_indicators()

        self.back_btn.setEnabled(self._current_step > 0)

        if self._current_step == self.NUM_STEPS - 1:
            self.next_btn.setText("Finish")
            self.skip_btn.setVisible(False)
        else:
            self.next_btn.setText("Next ›")
            self.skip_btn.setVisible(True)

    def _next_step(self):
        if self._current_step == 1:
            # Must handle server addition before moving
            if not self._add_server_from_form():
                return
        if self._current_step == self.NUM_STEPS - 1:
            self.accept()
            return
        self._go_to_step(self._current_step + 1)

    def _prev_step(self):
        self._go_to_step(self._current_step - 1)

    def _skip_all(self):
        self.accept()

    def _test_connection(self):
        url = self.ob_url_entry.text().strip()
        if not url or url == "https://":
            self.ob_server_status_lbl.setText("❌ Please enter a server URL")
            self.ob_server_status_lbl.setStyleSheet("color: #f48771;")
            return
        self.ob_server_status_lbl.setText("Testing connection…")
        self.ob_server_status_lbl.setStyleSheet("")
        try:
            import requests
            verify = self.ob_verify_ssl.isChecked()
            response = requests.get(f"{url}/api/v3/version", verify=verify, timeout=5)
            if response.ok:
                try:
                    vdata = response.json()
                    version = vdata.get("version", "unknown") if isinstance(vdata, dict) else "unknown"
                except Exception:
                    version = "unknown"
                self.ob_server_status_lbl.setText(f"✓ Connected! QUADS version: {version}")
                self.ob_server_status_lbl.setStyleSheet("color: #4ec9b0;")
            else:
                self.ob_server_status_lbl.setText(f"⚠ Server responded with status {response.status_code}")
                self.ob_server_status_lbl.setStyleSheet("color: #ce9178;")
        except Exception as e:
            self.ob_server_status_lbl.setText(f"❌ Connection failed: {e}")
            self.ob_server_status_lbl.setStyleSheet("color: #f48771;")

    def _add_server_from_form(self):
        """Try to add the server. Returns True if step can proceed, False to stay."""
        name = self.ob_server_name_entry.text().strip()
        url = self.ob_url_entry.text().strip()

        if not name:
            self.ob_server_status_lbl.setText("❌ Please enter a server name")
            self.ob_server_status_lbl.setStyleSheet("color: #f48771;")
            return False

        if not url or url == "https://":
            result = QMessageBox.question(
                self, "No Server URL",
                "You haven't entered a server URL. Skip server setup and continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if result == QMessageBox.StandardButton.Yes:
                self._go_to_step(self.NUM_STEPS - 1)
            return False

        try:
            success, message, version_info = self.shell.server_commands.add_server_programmatic(
                name=name, url=url,
                username="", password="",
                verify=self.ob_verify_ssl.isChecked(),
                test_connection=True,
            )
        except Exception as e:
            success = False
            message = str(e)
            version_info = None

        if not success:
            result = QMessageBox.question(
                self, "Connection Warning",
                f"Could not verify connection to server:\n{message}\n\nAdd server anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if result == QMessageBox.StandardButton.Yes:
                try:
                    success, message, version_info = self.shell.server_commands.add_server_programmatic(
                        name=name, url=url,
                        username="", password="",
                        verify=self.ob_verify_ssl.isChecked(),
                        test_connection=False,
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
                    return False
                if not success:
                    QMessageBox.critical(self, "Error", message)
                    return False
            else:
                return False

        self._server_name = name
        if hasattr(self, "ob_server_for_auth_lbl"):
            self.ob_server_for_auth_lbl.setText(f"Authenticate to server '{name}':")

        try:
            conn_success, err = self.shell.connect_to_server(name)
        except Exception:
            conn_success = False

        return True

    def _do_login(self):
        email = self.ob_login_email.text().strip()
        password = self.ob_login_pass.text().strip()
        if not email or not password:
            self.ob_login_status.setText("❌ Email and password are required")
            self.ob_login_status.setStyleSheet("color: #f48771;")
            return

        self.ob_login_status.setText("Logging in…")
        self.ob_login_status.setStyleSheet("")

        try:
            success, message, role = self.shell.user_commands.login_programmatic(email, password)
        except Exception as e:
            success = False
            message = str(e)
            role = None

        if success:
            if self._server_name:
                try:
                    self.shell.config.update_server_credentials(self._server_name, email, password)
                except Exception:
                    pass
            self.ob_login_status.setText(f"✓ Logged in as {email}")
            self.ob_login_status.setStyleSheet("color: #4ec9b0;")
            if hasattr(self.shell, "gui_app"):
                self.shell.gui_app.update_role_visibility()
            QTimer.singleShot(1200, lambda: self._go_to_step(3))
        else:
            self.ob_login_status.setText(f"❌ {message}")
            self.ob_login_status.setStyleSheet("color: #f48771;")

    def _do_register(self):
        email = self.ob_reg_email.text().strip()
        password = self.ob_reg_pass.text().strip()
        confirm = self.ob_reg_confirm.text().strip()

        if not email or not password:
            self.ob_reg_status.setText("❌ Email and password are required")
            self.ob_reg_status.setStyleSheet("color: #f48771;")
            return
        if "@" not in email or "." not in email:
            self.ob_reg_status.setText("❌ Please enter a valid email address")
            self.ob_reg_status.setStyleSheet("color: #f48771;")
            return
        if len(password) < 6:
            self.ob_reg_status.setText("❌ Password must be at least 6 characters")
            self.ob_reg_status.setStyleSheet("color: #f48771;")
            return
        if password != confirm:
            self.ob_reg_status.setText("❌ Passwords do not match")
            self.ob_reg_status.setStyleSheet("color: #f48771;")
            return

        self.ob_reg_status.setText("Registering…")
        self.ob_reg_status.setStyleSheet("")

        try:
            success, message, role = self.shell.user_commands.register_programmatic(email, password)
        except Exception as e:
            success = False
            message = str(e)
            role = None

        if success:
            if self._server_name:
                try:
                    self.shell.config.update_server_credentials(self._server_name, email, password)
                except Exception:
                    pass
            self.ob_reg_status.setText(f"✓ Registered as {email}")
            self.ob_reg_status.setStyleSheet("color: #4ec9b0;")
            if hasattr(self.shell, "gui_app"):
                self.shell.gui_app.update_role_visibility()
            QTimer.singleShot(1200, lambda: self._go_to_step(3))
        else:
            self.ob_reg_status.setText(f"❌ {message}")
            self.ob_reg_status.setStyleSheet("color: #f48771;")
