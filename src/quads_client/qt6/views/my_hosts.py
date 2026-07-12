"""My Hosts view - shows user's active assignments and hosts"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QScrollArea, QGroupBox, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QColor, QBrush

from quads_client.qt6.widgets.dialogs import show_error_dialog


class _AssignmentFetcher(QThread):
    result_ready = Signal(object)
    error_occurred = Signal(object)

    def __init__(self, shell):
        super().__init__()
        self._shell = shell

    def run(self):
        try:
            data = self._fetch()
            self.result_ready.emit(data)
        except Exception as exc:
            self.error_occurred.emit(exc)

    def _fetch(self):
        from quads_client.utils import get_username_short
        assignments_data = []
        try:
            username = get_username_short(self._shell.connection.username)
            user_assignments = self._shell.connection.api.filter_assignments({"owner": username, "active": True})
            if not user_assignments:
                return []
            for assignment in user_assignments:
                if isinstance(assignment, dict):
                    assignment_id = assignment.get("_id") or assignment.get("id")
                    cloud = assignment.get("cloud", {})
                    cloud_name = cloud.get("name") if isinstance(cloud, dict) else str(cloud)
                    description = assignment.get("description", "No description")
                    try:
                        schedules = self._shell.connection.api.get_schedules({"assignment_id": int(assignment_id)})
                    except (TypeError, ValueError):
                        schedules = []
                    is_validated = assignment.get("validated", False)
                    hosts = []
                    for schedule in schedules if schedules else []:
                        if isinstance(schedule, dict):
                            hostname = schedule.get("host", {})
                            if isinstance(hostname, dict):
                                hostname = hostname.get("name", "")
                            status = "active" if is_validated else "provisioning"
                            hosts.append({"name": str(hostname), "status": status, "progress": "N/A"})
                    assignments_data.append({
                        "id": assignment_id,
                        "cloud": cloud_name,
                        "description": description,
                        "created": "N/A",
                        "expires": "N/A",
                        "hosts": hosts,
                        "days_remaining": "N/A",
                    })
        except Exception as e:
            self._shell.perror(f"Failed to fetch assignments: {e}")
        return assignments_data


class MyHostsView(QWidget):
    """View for displaying user's active hosts and assignments"""

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.shell = shell
        self._loading = False
        self._fetcher = None
        self._refresh_timer = None

        prefs = self._get_preferences()
        self.auto_refresh_enabled = prefs.get("auto_refresh_my_hosts", True)
        self.refresh_interval = prefs.get("auto_refresh_interval", 30) * 1000

        self._create_ui()

    def _get_preferences(self):
        if self.shell.config and hasattr(self.shell.config, "config_data"):
            return self.shell.config.config_data.get("gui_preferences", {})
        return {}

    def _auto_login(self):
        target_server = self.shell.get_auto_login_server()
        if target_server:
            success, error = self.shell.connect_to_server(target_server)
            if success:
                self._load_assignments()
            else:
                show_error_dialog(self, "Login Failed", f"Failed to connect to {target_server}", error or "")
        else:
            self.shell.gui_app._show_view("connection")

    def _create_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 10, 20, 10)
        title = QLabel("My Hosts")
        tf = title.font()
        tf.setPointSize(tf.pointSize() + 2)
        tf.setBold(True)
        title.setFont(tf)
        hl.addWidget(title)
        hl.addStretch()

        interval_sec = self.refresh_interval // 1000
        self.auto_refresh_check = QCheckBox(f"Auto-refresh ({interval_sec}s)")
        self.auto_refresh_check.setChecked(self.auto_refresh_enabled)
        self.auto_refresh_check.stateChanged.connect(self._toggle_auto_refresh)
        hl.addWidget(self.auto_refresh_check)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._manual_refresh)
        hl.addWidget(refresh_btn)
        root.addWidget(header)

        # Scroll area for dynamic content
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(20, 0, 20, 20)
        self._content_layout.setSpacing(12)
        self._scroll.setWidget(self._content_widget)
        root.addWidget(self._scroll, 1)

        # Status label
        self.status_label = QLabel("Loading...")
        self.status_label.setContentsMargins(20, 2, 20, 8)
        root.addWidget(self.status_label)

        # Auto-refresh timer
        if self.auto_refresh_enabled:
            self._refresh_timer = QTimer(self)
            self._refresh_timer.timeout.connect(self._schedule_auto_refresh)
            self._refresh_timer.start(self.refresh_interval)

        self._load_assignments()

    def _clear_content(self):
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _load_assignments(self):
        if self._loading:
            return
        self._loading = True
        self._clear_content()

        if not self.shell.is_authenticated():
            self._loading = False
            center = QWidget()
            cl = QVBoxLayout(center)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(QLabel("Please login to view your hosts"))
            login_btn = QPushButton("Login")
            login_btn.clicked.connect(self._auto_login)
            cl.addWidget(login_btn)
            self._content_layout.addWidget(center)
            self._content_layout.addStretch()
            self.status_label.setText("Not authenticated")
            return

        self.status_label.setText("Loading assignments...")

        self._fetcher = _AssignmentFetcher(self.shell)
        self._fetcher.result_ready.connect(self._on_assignments_loaded)
        self._fetcher.error_occurred.connect(self._on_load_error)
        self._fetcher.start()

    def _on_assignments_loaded(self, assignments_data):
        self._loading = False
        self._clear_content()

        if not assignments_data:
            lbl = QLabel("No active assignments\n\nGo to Schedule view to reserve hosts")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._content_layout.addWidget(lbl)
            self._content_layout.addStretch()
            self.status_label.setText("No assignments found")
            return

        for assignment in assignments_data:
            self._create_assignment_panel(assignment)

        self._content_layout.addStretch()
        self.status_label.setText(f"Showing {len(assignments_data)} assignment(s) | Last updated: Just now")

    def _on_load_error(self, exc):
        self._loading = False
        self._clear_content()
        err_lbl = QLabel(f"Error loading assignments:\n{str(exc)}")
        err_lbl.setStyleSheet("color: red;")
        self._content_layout.addWidget(err_lbl)
        self._content_layout.addStretch()
        self.status_label.setText("Error loading data")

    def _create_assignment_panel(self, assignment):
        panel = QGroupBox(f"Assignment #{assignment['id']}: {assignment['description']}")
        pl = QVBoxLayout(panel)

        info_text = (
            f"Cloud: {assignment['cloud']} | Created: {assignment['created']} | "
            f"Expires: {assignment['expires']} ({assignment['days_remaining']} days remaining)"
        )
        pl.addWidget(QLabel(info_text))

        tree = QTreeWidget()
        tree.setColumnCount(3)
        tree.setHeaderLabels(["Host", "Status", "Progress"])
        tree.setColumnWidth(0, 250)
        tree.setColumnWidth(1, 120)
        tree.setColumnWidth(2, 150)
        tree.setRootIsDecorated(False)
        tree.setAlternatingRowColors(True)

        theme = self.shell.gui_app.theme_manager
        success_color = QColor(theme.get_color("success"))
        prov_color = QColor(theme.get_color("provisioning"))
        error_color = QColor(theme.get_color("error"))

        for host in assignment["hosts"]:
            status_icon = self._get_status_icon(host["status"])
            progress_bar = self._get_progress_bar(host["progress"])

            item = QTreeWidgetItem([
                host["name"],
                f"{status_icon} {host['status'].capitalize()}",
                progress_bar,
            ])

            if host["status"] == "active":
                brush = QBrush(success_color)
            elif host["status"] == "provisioning":
                brush = QBrush(prov_color)
            elif host["status"] == "failed":
                brush = QBrush(error_color)
            else:
                brush = None

            if brush:
                for col in range(3):
                    item.setForeground(col, brush)

            tree.addTopLevelItem(item)

        tree.setFixedHeight(max(80, len(assignment["hosts"]) * 24 + 28))
        pl.addWidget(tree)

        terminate_btn = QPushButton("Terminate Assignment")
        terminate_btn.clicked.connect(lambda checked=False, aid=assignment["id"]: self._terminate_assignment(aid))
        pl.addWidget(terminate_btn)

        self._content_layout.addWidget(panel)

    def _get_status_icon(self, status):
        return {"active": "✓", "provisioning": "⏳", "queued": "○", "failed": "✗"}.get(status, "○")

    def _get_progress_bar(self, progress):
        if progress == "N/A":
            return "░" * 10 + " N/A"
        filled = int(progress / 10)
        return "█" * filled + "░" * (10 - filled) + f" {progress}%"

    def _terminate_assignment(self, assignment_id):
        prefs = self._get_preferences()
        if prefs.get("confirm_terminate", True):
            result = QMessageBox.question(
                self,
                "Confirm Termination",
                f"Are you sure you want to terminate assignment #{assignment_id}?\n\n"
                "This will release all hosts in this assignment.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if result != QMessageBox.StandardButton.Yes:
                return

        try:
            old_gui_mode = getattr(self.shell, "gui_mode", False)
            self.shell.gui_mode = True
            try:
                self.shell.user_commands.cmd_terminate(str(assignment_id))
                QMessageBox.information(
                    self,
                    "Success",
                    f"Assignment #{assignment_id} terminated\n\n"
                    "Note: It may take a few moments for the termination to complete.",
                )
                self._load_assignments()
            finally:
                self.shell.gui_mode = old_gui_mode
        except Exception as e:
            import traceback
            show_error_dialog(self, "Termination Failed", str(e), traceback.format_exc())

    def _manual_refresh(self):
        self._load_assignments()

    def _toggle_auto_refresh(self, state):
        self.auto_refresh_enabled = bool(state)
        if self._refresh_timer:
            if self.auto_refresh_enabled:
                self._refresh_timer.start(self.refresh_interval)
            else:
                self._refresh_timer.stop()
        elif self.auto_refresh_enabled:
            self._refresh_timer = QTimer(self)
            self._refresh_timer.timeout.connect(self._schedule_auto_refresh)
            self._refresh_timer.start(self.refresh_interval)

    def _schedule_auto_refresh(self):
        self._load_assignments()

    def refresh(self):
        self._load_assignments()

    def apply_preferences(self, preferences):
        new_interval = preferences.get("auto_refresh_interval", 30) * 1000
        if new_interval != self.refresh_interval:
            self.refresh_interval = new_interval
            interval_sec = self.refresh_interval // 1000
            self.auto_refresh_check.setText(f"Auto-refresh ({interval_sec}s)")
            if self._refresh_timer and self.auto_refresh_enabled:
                self._refresh_timer.start(self.refresh_interval)

        new_enabled = preferences.get("auto_refresh_my_hosts", True)
        if new_enabled != self.auto_refresh_enabled:
            self.auto_refresh_enabled = new_enabled
            self.auto_refresh_check.setChecked(new_enabled)
            if self._refresh_timer:
                if new_enabled:
                    self._refresh_timer.start(self.refresh_interval)
                else:
                    self._refresh_timer.stop()
