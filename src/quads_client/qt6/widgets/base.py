"""Base view class and helper widgets"""

import traceback

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView,
    QMessageBox,
    QDialog,
    QLineEdit,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QKeySequence, QShortcut

from quads_client.qt6.widgets.dialogs import show_error_dialog


class _WorkerThread(QThread):
    result_ready = Signal(object)
    error_occurred = Signal(object)

    def __init__(self, work_func):
        super().__init__()
        self._work_func = work_func

    def run(self):
        try:
            result = self._work_func()
            self.result_ready.emit(result)
        except Exception as exc:
            self.error_occurred.emit(exc)


class ScrolledTreeview(QWidget):
    """QTreeWidget with built-in scrollbars and optional Ctrl+C clipboard copy"""

    def __init__(self, parent, columns, column_configs=None, enable_copy=True, selectmode="browse", **kwargs):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(columns))
        self._columns = list(columns)

        headers = []
        for col_id in columns:
            if column_configs and col_id in column_configs:
                heading, width = column_configs[col_id]
                headers.append(heading)
            else:
                headers.append(col_id)
        self.tree.setHeaderLabels(headers)

        if column_configs:
            for i, col_id in enumerate(columns):
                if col_id in column_configs:
                    _, width = column_configs[col_id]
                    self.tree.setColumnWidth(i, width)

        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setSortingEnabled(False)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setMinimumSectionSize(50)

        if selectmode == "extended":
            self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        else:
            self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        layout.addWidget(self.tree)

        if enable_copy:
            shortcut = QShortcut(QKeySequence.StandardKey.Copy, self.tree)
            shortcut.activated.connect(self.copy_selected)

    def copy_selected(self):
        from PySide6.QtWidgets import QApplication

        items = self.tree.selectedItems()
        if not items:
            return 0
        lines = ["\t".join(item.text(i) for i in range(self.tree.columnCount())) for item in items]
        QApplication.clipboard().setText("\n".join(lines))
        return len(lines)

    def clear(self):
        self.tree.clear()

    def insert(self, parent_ref, index, values=None, tags=None, iid=None):
        item = QTreeWidgetItem()
        if values:
            for i, v in enumerate(values):
                item.setText(i, str(v))
        self.tree.addTopLevelItem(item)
        return item

    def selection(self):
        return self.tree.selectedItems()

    def item(self, item_obj, option=None):
        if option == "values":
            return tuple(item_obj.text(i) for i in range(self.tree.columnCount()))
        return item_obj

    def tag_configure(self, tag, **kwargs):
        # Tags are applied per-item in PySide6; this is a no-op at the tree level.
        pass


class BaseAdminView(QWidget):
    """Base class for admin views with common patterns"""

    def __init__(self, parent, shell, title, requires_admin=True):
        super().__init__(parent)
        self.shell = shell
        self.title_text = title
        self.requires_admin = requires_admin
        self.tree = None
        self.status_label = None
        self._threads = []

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

    def create_header(self, buttons=None):
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel(self.title_text)
        font = title.font()
        font.setPointSize(font.pointSize() + 2)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        layout.addStretch()

        if buttons:
            for text, command in buttons:
                btn = QPushButton(text)
                btn.clicked.connect(command)
                layout.addWidget(btn)

        self._main_layout.addWidget(header)
        return header

    def create_action_bar(self, buttons):
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 4, 20, 8)
        layout.setSpacing(8)

        for text, command in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(command)
            layout.addWidget(btn)
        layout.addStretch()

        self._main_layout.addWidget(bar)
        return bar

    def create_status_label(self):
        self.status_label = QLabel("")
        self.status_label.setContentsMargins(20, 2, 20, 8)
        f = self.status_label.font()
        f.setPointSize(max(8, f.pointSize() - 1))
        self.status_label.setFont(f)
        self._main_layout.addWidget(self.status_label)
        return self.status_label

    def update_status(self, message):
        if self.status_label:
            self.status_label.setText(message)

    def check_auth(self):
        if not self.shell.is_authenticated():
            self.update_status("Not authenticated — please connect to a server")
            return False
        if self.requires_admin and not self.shell.is_admin():
            self.update_status("Admin role required for this view")
            return False
        return True

    def _run_in_thread(self, work_func, on_success, on_error=None):
        thread = _WorkerThread(work_func)
        self._threads.append(thread)
        thread.result_ready.connect(on_success)
        if on_error:
            thread.error_occurred.connect(on_error)
        thread.finished.connect(lambda t=thread: self._threads.remove(t) if t in self._threads else None)
        thread.start()

    def safe_load_data_async(self, load_func, on_loaded, success_message=None, disable_widgets=None):
        if not self.check_auth():
            return

        self.update_status("Loading…")

        if disable_widgets:
            for w in disable_widgets:
                w.setEnabled(False)

        def _restore():
            if disable_widgets:
                for w in disable_widgets:
                    try:
                        w.setEnabled(True)
                    except Exception:
                        pass

        def _on_success(data):
            _restore()
            if success_message and data:
                count = len(data) if isinstance(data, (list, tuple)) else 0
                self.update_status(success_message.format(count=count) + " | Last updated: Just now")
            elif data:
                self.update_status("Loaded successfully")
            else:
                self.update_status("No items found")
            on_loaded(data)

        def _on_error(exc):
            _restore()
            self.update_status("Error loading data")
            show_error_dialog(self, "Load Failed", str(exc), traceback.format_exc())

        self._run_in_thread(load_func, _on_success, _on_error)

    def get_selected_item(self, warning_message="Please select an item"):
        if not self.tree:
            return None, None
        items = self.tree.selection()
        if not items:
            QMessageBox.warning(self, "No Selection", warning_message)
            return None, None
        item = items[0]
        values = self.tree.item(item, "values")
        return item, values

    def confirm_action(self, title, message):
        result = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    def create_simple_dialog(self, title, geometry="400x200"):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        try:
            w, h = (int(v) for v in geometry.split("x"))
            dialog.resize(w, h)
            dialog.setMinimumSize(w, h)
        except (ValueError, AttributeError):
            pass
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        QVBoxLayout(dialog)
        return dialog

    def safe_execute(self, command_func, success_message, error_title, refresh_func=None):
        try:
            if hasattr(self.shell, "_capture_output"):
                self.shell._capture_output = True
                self.shell._captured_messages = []

            command_func()

            if hasattr(self.shell, "_captured_messages"):
                errors = [msg for level, msg in self.shell._captured_messages if level == "error"]
                if errors:
                    QMessageBox.critical(self, error_title, "\n".join(errors))
                    return

            QMessageBox.information(self, "Success", success_message)
            if refresh_func:
                refresh_func()
        except Exception as e:
            show_error_dialog(self, error_title, str(e), traceback.format_exc())
        finally:
            if hasattr(self.shell, "_capture_output"):
                self.shell._capture_output = False


class FormDialog:
    """Static helpers for form field creation inside QGridLayout parents"""

    @staticmethod
    def create_labeled_entry(parent_widget, label_text, row, entry_width=30, **kwargs):
        """
        Add a label+entry row to parent_widget's QGridLayout.
        parent_widget must have a QGridLayout set on it.
        Returns the QLineEdit.
        """
        layout = parent_widget.layout()
        lbl = QLabel(label_text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl, row, 0)
        entry = QLineEdit()
        layout.addWidget(entry, row, 1, Qt.AlignmentFlag.AlignLeft)
        return entry

    @staticmethod
    def create_button_row(parent_layout, buttons):
        """
        Append a row of buttons to parent_layout (QVBoxLayout or similar).
        Returns the container widget.
        """
        container = QWidget()
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 8, 0, 0)
        for text, command in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(command)
            h.addWidget(btn)
        h.addStretch()
        parent_layout.addWidget(container)
        return container
