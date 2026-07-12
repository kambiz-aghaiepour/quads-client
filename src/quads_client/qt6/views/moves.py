"""Move Progress view - shows active move/rebuild progress"""

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QCheckBox,
)
from PySide6.QtCore import QTimer

from quads_client.qt6.widgets.base import BaseAdminView, ScrolledTreeview
from quads_client.qt6.widgets.dialogs import show_error_dialog
from quads_client.progress import format_progress_str


class MoveProgressView(BaseAdminView):
    """View for displaying active move/rebuild progress"""

    def __init__(self, parent, shell):
        super().__init__(parent, shell, "Move Progress", requires_admin=False)
        self._loading = False
        self._auto_refresh = False
        self._refresh_timer = None
        self._create_ui()

    def _create_ui(self):
        self.create_header([("↻ Refresh", self._load_progress)])

        # Auto-refresh checkbox row
        ctrl_widget = QWidget()
        ctrl_layout = QHBoxLayout(ctrl_widget)
        ctrl_layout.setContentsMargins(20, 0, 20, 4)
        self._auto_cb = QCheckBox("Auto-refresh (10s)")
        self._auto_cb.setChecked(False)
        self._auto_cb.toggled.connect(self._toggle_auto_refresh)
        ctrl_layout.addWidget(self._auto_cb)
        ctrl_layout.addStretch()
        self._main_layout.addWidget(ctrl_widget)

        content = QWidget()
        from PySide6.QtWidgets import QVBoxLayout

        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 0, 20, 20)

        columns = ("host", "from_cloud", "to_cloud", "progress", "status", "message")
        column_configs = {
            "host": ("Host", 200),
            "from_cloud": ("From", 100),
            "to_cloud": ("To", 100),
            "progress": ("Progress", 100),
            "status": ("Status", 120),
            "message": ("Message", 250),
        }
        self.tree = ScrolledTreeview(content, columns, column_configs)
        cl.addWidget(self.tree)
        self._main_layout.addWidget(content, 1)

        self.create_status_label()
        self._load_progress()

    def _load_progress(self):
        if self._loading:
            return
        if not self.check_auth():
            return

        self._loading = True
        self.update_status("Loading…")

        def _fetch():
            api = self.shell.connection.api
            active = api.get_all_move_status()
            if active:
                return ("active", active)
            try:
                pending = api.get_moves()
            except Exception:
                pending = []
            return ("pending", pending) if pending else ("active", [])

        def _on_loaded(result):
            self._loading = False
            self.tree.clear()
            source, moves = result
            if not moves:
                self.update_status("No active moves")
                return

            if source == "pending":
                for move in moves:
                    item = self.tree.insert(
                        "",
                        0,
                        values=(
                            move.get("host", "?"),
                            move.get("current", ""),
                            move.get("new", ""),
                            "",
                            "Scheduled",
                            "Awaiting next move cycle",
                        ),
                    )
                    self._color_item(item, "scheduled")
                self.update_status(f"{len(moves)} scheduled move(s) (awaiting next move cycle)")
                return

            for move in moves:
                status = move.get("status", "pending")
                item = self.tree.insert(
                    "",
                    0,
                    values=(
                        move.get("host", "?"),
                        move.get("source_cloud", ""),
                        move.get("target_cloud", ""),
                        format_progress_str(status),
                        status,
                        move.get("message", "") or "",
                    ),
                )
                self._color_item(item, status)

            self.update_status(f"{len(moves)} active move(s)")

        def _on_error(exc):
            self._loading = False
            err = str(exc)
            if "404" in err or "not found" in err.lower():
                self.update_status("Move tracking is not available on this server")
                self._auto_cb.setChecked(False)
            else:
                self.update_status(f"Error: {exc}")
                show_error_dialog(self, "Load Failed", err)

        self._run_in_thread(_fetch, _on_loaded, _on_error)

    @staticmethod
    def _color_item(item, status):
        from PySide6.QtGui import QColor, QBrush

        color_map = {
            "failed": "#f48771",
            "completed": "#4ec9b0",
            "scheduled": "#dcdcaa",
        }
        color = color_map.get(status)
        if color and item is not None:
            brush = QBrush(QColor(color))
            col_count = item.treeWidget().columnCount() if item.treeWidget() else 6
            for col in range(col_count):
                item.setForeground(col, brush)

    def _toggle_auto_refresh(self, checked):
        self._auto_refresh = checked
        if checked:
            self._refresh_timer = QTimer(self)
            self._refresh_timer.setInterval(10000)
            self._refresh_timer.timeout.connect(self._load_progress)
            self._refresh_timer.start()
        else:
            if self._refresh_timer:
                self._refresh_timer.stop()
                self._refresh_timer = None

    def refresh(self):
        self._load_progress()
