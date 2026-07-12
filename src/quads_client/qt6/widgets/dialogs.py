"""Reusable dialog widgets"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


def show_error_dialog(parent, title, message, details=None):
    """Show a scrollable error dialog with copyable text."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setMinimumSize(520, 360 if details else 220)
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)

    layout = QVBoxLayout(dialog)
    layout.setSpacing(8)

    heading = QLabel(f"❌  {title}")
    f = heading.font()
    f.setBold(True)
    f.setPointSize(f.pointSize() + 1)
    heading.setFont(f)
    heading.setStyleSheet("color: #f48771;")
    layout.addWidget(heading)

    body = QTextEdit()
    body.setReadOnly(True)
    mono = QFont("Monospace")
    mono.setStyleHint(QFont.StyleHint.TypeWriter)
    body.setFont(mono)
    body.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

    content = message
    if details:
        content += f"\n\nDetails:\n{details}"
    body.setPlainText(content)
    layout.addWidget(body)

    hint = QLabel("💡 You can select and copy the text above")
    hint.setStyleSheet("color: gray; font-size: 10px;")
    layout.addWidget(hint)

    btn_row = QHBoxLayout()
    copy_btn = QPushButton("Copy to Clipboard")
    copy_btn.clicked.connect(lambda: _copy_to_clipboard(body.toPlainText()))
    btn_row.addWidget(copy_btn)
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    btn_row.addWidget(close_btn)
    btn_row.addStretch()
    layout.addLayout(btn_row)

    dialog.exec()


def _copy_to_clipboard(text):
    from PySide6.QtWidgets import QApplication
    QApplication.clipboard().setText(text)


def show_info_dialog(parent, title, message):
    """Show a simple info dialog."""
    QMessageBox.information(parent, title, message)
