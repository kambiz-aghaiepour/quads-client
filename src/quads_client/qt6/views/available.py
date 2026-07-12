"""Available hosts view - shows available hosts for scheduling"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QApplication,
)
from PySide6.QtCore import Qt

from quads_client.qt6.widgets.base import BaseAdminView, ScrolledTreeview
from quads_client.qt6.widgets.host_filters import HostFilterFrame


class AvailableView(BaseAdminView):
    """View for displaying available hosts"""

    def __init__(self, parent, shell):
        super().__init__(parent, shell, "Available Hosts", requires_admin=False)
        self._create_ui()

    def _create_ui(self):
        self.create_header([("🔄 Refresh", self.refresh)])

        if not self.shell.is_authenticated():
            center = QWidget()
            cl = QVBoxLayout(center)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg = QLabel("Not connected to any QUADS server")
            mf = msg.font()
            mf.setPointSize(mf.pointSize() + 2)
            msg.setFont(mf)
            msg.setStyleSheet("color: gray;")
            cl.addWidget(msg)
            hint = QLabel("Please connect to a server from the Servers view")
            hint.setStyleSheet("color: gray;")
            cl.addWidget(hint)
            go_btn = QPushButton("Go to Servers")
            go_btn.clicked.connect(lambda: self.shell.gui_app._show_view("connection"))
            cl.addWidget(go_btn)
            self._main_layout.addWidget(center, 1)
            self.create_status_label()
            return

        # Filter frame
        filter_wrapper = QWidget()
        fw_layout = QVBoxLayout(filter_wrapper)
        fw_layout.setContentsMargins(20, 0, 20, 0)
        self.filter_frame = HostFilterFrame(filter_wrapper, self.shell, show_dates=True)
        fw_layout.addWidget(self.filter_frame)
        self._main_layout.addWidget(filter_wrapper)

        # Button row
        btn_wrapper = QWidget()
        bwl = QHBoxLayout(btn_wrapper)
        bwl.setContentsMargins(20, 4, 20, 4)
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._load_available)
        bwl.addWidget(apply_btn)
        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self._clear_and_reload)
        bwl.addWidget(clear_btn)
        bwl.addStretch()
        self._main_layout.addWidget(btn_wrapper)

        # Tree
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 0, 20, 20)
        columns = ("host", "model", "type", "self_schedule")
        column_configs = {
            "host": ("Host", 300),
            "model": ("Model", 120),
            "type": ("Type", 100),
            "self_schedule": ("Self-Schedule", 120),
        }
        self.tree = ScrolledTreeview(content, columns, column_configs, selectmode="extended")
        self.tree.tree.itemSelectionChanged.connect(self._on_selection_changed)
        cl.addWidget(self.tree)
        self._main_layout.addWidget(content, 1)

        # Action bar
        action_wrapper = QWidget()
        awl = QHBoxLayout(action_wrapper)
        awl.setContentsMargins(20, 4, 20, 8)
        awl.setSpacing(8)

        self.copy_selected_btn = QPushButton("Copy Selected")
        self.copy_selected_btn.clicked.connect(self._copy_selected)
        self.copy_selected_btn.setEnabled(False)
        awl.addWidget(self.copy_selected_btn)

        copy_all_btn = QPushButton("Copy All")
        copy_all_btn.clicked.connect(self._copy_all)
        awl.addWidget(copy_all_btn)

        btn_text = "Admin Schedule" if self.shell.is_admin() else "Schedule Now"
        self.schedule_btn = QPushButton(btn_text)
        self.schedule_btn.clicked.connect(self._schedule_selected)
        self.schedule_btn.setEnabled(False)
        awl.addWidget(self.schedule_btn)

        self.unselect_btn = QPushButton("Unselect All")
        self.unselect_btn.clicked.connect(self._unselect_all)
        self.unselect_btn.setEnabled(False)
        awl.addWidget(self.unselect_btn)
        awl.addStretch()
        self._main_layout.addWidget(action_wrapper)

        self.create_status_label()
        self._load_available()

    def _on_selection_changed(self):
        has_selection = bool(self.tree.selection())
        self.copy_selected_btn.setEnabled(has_selection)
        self.schedule_btn.setEnabled(has_selection)
        self.unselect_btn.setEnabled(has_selection)

    def _unselect_all(self):
        self.tree.tree.clearSelection()
        self.update_status("Selection cleared")

    def _clear_and_reload(self):
        self.filter_frame.clear_filters()
        self._load_available()

    def _load_available(self):
        if not self.shell.is_authenticated():
            self.update_status("Not connected to server")
            return
        if self.tree is None:
            return
        self.tree.clear()
        filters = self.filter_frame.get_filters()

        def load_data():
            return self.shell.get_available_hosts_data(**filters)

        def on_loaded(hosts):
            if not hosts:
                self.update_status("No available hosts found")
                return
            for host in hosts:
                self.tree.insert(
                    "",
                    0,
                    values=(
                        host["name"],
                        host["model"],
                        host["host_type"],
                        "Yes" if host["can_self_schedule"] else "No",
                    ),
                )
            self.update_status(f"Loaded {len(hosts)} available host(s)")

        self.safe_load_data_async(load_data, on_loaded)

    def _copy_selected(self):
        items = self.tree.selection()
        if not items:
            self.update_status("No items selected to copy")
            return
        hostnames = [self.tree.item(item, "values")[0] for item in items]
        QApplication.clipboard().setText("\n".join(hostnames))
        self.update_status(f"Copied {len(hostnames)} hostname(s) to clipboard")

    def _copy_all(self):
        all_items = self.tree.tree.invisibleRootItem()
        count = all_items.childCount()
        if count == 0:
            self.update_status("No data to copy")
            return
        cols = self.tree.tree.columnCount()
        headers = [self.tree.tree.headerItem().text(i) for i in range(cols)]
        lines = ["\t".join(headers)]
        for i in range(count):
            item = all_items.child(i)
            lines.append("\t".join(item.text(c) for c in range(cols)))
        QApplication.clipboard().setText("\n".join(lines))
        self.update_status(f"Copied {count} row(s) with headers to clipboard")

    def _schedule_selected(self):
        items = self.tree.selection()
        if not items:
            self.update_status("No hosts selected - please select one or more hosts")
            return
        hostnames = [self.tree.item(item, "values")[0] for item in items]
        if not hostnames:
            return

        if self.shell.is_admin():
            self.shell.gui_app._ensure_view("admin_schedule")
            if "admin_schedule" in self.shell.gui_app.views:
                self.shell.gui_app.views["admin_schedule"]._create_schedule(prefill_hosts=",".join(hostnames))
                self.update_status(f"Opened admin schedule dialog with {len(hostnames)} host(s) pre-filled")
        else:
            self.shell.gui_app._show_view("schedule")
            if "schedule" in self.shell.gui_app.views:
                self.shell.gui_app.views["schedule"].prefill_hosts(hostnames)
            self.update_status(f"Navigated to Schedule with {len(hostnames)} host(s) pre-filled")

    def refresh(self):
        if self.tree is not None and self.shell.is_authenticated():
            self._load_available()
        else:
            # Auth state changed - rebuild UI
            while self._main_layout.count():
                item = self._main_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.tree = None
            self.status_label = None
            self._create_ui()
