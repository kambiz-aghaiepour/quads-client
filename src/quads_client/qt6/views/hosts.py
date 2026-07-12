"""Hosts view - admin host management"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QColor, QBrush

from quads_client.qt6.widgets.base import BaseAdminView, ScrolledTreeview


class HostsView(BaseAdminView):
    """View for managing hosts (admin only)"""

    def __init__(self, parent, shell):
        super().__init__(parent, shell, "Host Management", requires_admin=True)
        self.filter_mode = "active"
        self._filter_buttons = []
        self._create_ui()

    def _create_ui(self):
        self.create_header([("🔄 Refresh", self._load_hosts)])

        # Filter button row
        filter_bar = QWidget()
        fbl = QHBoxLayout(filter_bar)
        fbl.setContentsMargins(20, 0, 20, 8)
        fbl.setSpacing(6)
        fbl.addWidget(QLabel("Filter:"))

        for label, mode in [
            ("Active", "active"),
            ("All Hosts", "all"),
            ("Broken", "broken"),
            ("Retired", "retired"),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked=False, m=mode: self._set_filter(m))
            fbl.addWidget(btn)
            self._filter_buttons.append(btn)
        fbl.addStretch()
        self._main_layout.addWidget(filter_bar)

        # Tree
        content = QWidget()
        from PySide6.QtWidgets import QVBoxLayout
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 0, 20, 20)

        columns = ("name", "model", "default_cloud", "type", "broken", "retired")
        column_configs = {
            "name": ("Name", 200),
            "model": ("Model", 100),
            "default_cloud": ("Default Cloud", 120),
            "type": ("Type", 100),
            "broken": ("Broken", 80),
            "retired": ("Retired", 80),
        }
        self.tree = ScrolledTreeview(content, columns, column_configs)
        cl.addWidget(self.tree)
        self._main_layout.addWidget(content, 1)

        self.create_action_bar([
            ("Mark Broken", self._mark_broken),
            ("Mark Repaired", self._mark_repaired),
            ("Retire", self._retire),
            ("Un-retire", self._unretire),
        ])
        self.create_status_label()
        self._load_hosts()

    def _set_filter(self, mode):
        self.filter_mode = mode
        self._load_hosts()

    def _load_hosts(self):
        def load_data():
            if self.filter_mode == "active":
                return self.shell.connection.api.filter_hosts({"broken": False, "retired": False})
            elif self.filter_mode == "all":
                return self.shell.connection.api.get_hosts()
            elif self.filter_mode == "broken":
                return self.shell.connection.api.filter_hosts({"broken": True})
            elif self.filter_mode == "retired":
                return self.shell.connection.api.filter_hosts({"retired": True})
            return []

        self.tree.clear()
        error_color = QColor(self.shell.gui_app.theme_manager.get_color("error"))
        retired_color = QColor("#999999")

        def on_loaded(hosts):
            if not hosts:
                return
            for host in hosts:
                name = host.get("name", "")
                model = host.get("model", "")
                default_cloud = host.get("default_cloud", {})
                if isinstance(default_cloud, dict):
                    default_cloud = default_cloud.get("name", "")
                host_type = host.get("host_type", "")
                broken = "Yes" if host.get("broken", False) else "No"
                retired = "Yes" if host.get("retired", False) else "No"

                item = self.tree.insert("", 0, values=(name, model, default_cloud, host_type, broken, retired))

                if host.get("broken", False):
                    brush = QBrush(error_color)
                    for col in range(6):
                        item.setForeground(col, brush)
                elif host.get("retired", False):
                    brush = QBrush(retired_color)
                    for col in range(6):
                        item.setForeground(col, brush)

            filter_text = f" ({self.filter_mode})" if self.filter_mode != "active" else ""
            self.update_status(f"Showing {len(hosts)} host(s){filter_text} | Last updated: Just now")

        self.safe_load_data_async(
            load_data, on_loaded,
            success_message="Showing {count} host(s)",
            disable_widgets=self._filter_buttons,
        )

    def _mark_broken(self):
        _, values = self.get_selected_item("Please select a host to mark as broken")
        if not values:
            return
        hostname = values[0]
        if not self.confirm_action("Confirm", f"Mark host '{hostname}' as broken?\n\nThis will prevent it from being scheduled."):
            return
        self.safe_execute(
            lambda: self.shell.host_commands.cmd_mark_broken(hostname),
            f"Host '{hostname}' marked as broken",
            "Mark Broken Failed",
            self._load_hosts,
        )

    def _mark_repaired(self):
        _, values = self.get_selected_item("Please select a host to mark as repaired")
        if not values:
            return
        hostname = values[0]
        self.safe_execute(
            lambda: self.shell.host_commands.cmd_mark_repaired(hostname),
            f"Host '{hostname}' marked as repaired",
            "Mark Repaired Failed",
            self._load_hosts,
        )

    def _retire(self):
        _, values = self.get_selected_item("Please select a host to retire")
        if not values:
            return
        hostname = values[0]
        if not self.confirm_action("Confirm", f"Retire host '{hostname}'?\n\nThis will remove it from the active pool."):
            return
        self.safe_execute(
            lambda: self.shell.host_commands.cmd_retire(hostname),
            f"Host '{hostname}' retired",
            "Retire Failed",
            self._load_hosts,
        )

    def _unretire(self):
        _, values = self.get_selected_item("Please select a host to un-retire")
        if not values:
            return
        hostname = values[0]
        self.safe_execute(
            lambda: self.shell.host_commands.cmd_unretire(hostname),
            f"Host '{hostname}' is now active",
            "Un-retire Failed",
            self._load_hosts,
        )

    def refresh(self):
        self._load_hosts()
