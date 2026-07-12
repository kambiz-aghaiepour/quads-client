"""QUADS Client GUI entry point"""

import sys


def main():
    """Main entry point for quads-client-gui"""
    try:
        from PySide6.QtWidgets import QApplication as _QApplication  # noqa: F401
    except ImportError:
        print("ERROR: GUI dependencies not available.")
        print("\npython3-pyside6 is required for the GUI but is not installed.")
        print("\nOn Linux (Fedora/RHEL):")
        print("  sudo dnf install python3-pyside6")
        print("\nOn macOS (in a venv):")
        print("  pip install PySide6")
        print("\nAlternatively, use the CLI instead: quads-client")
        return 1

    from PySide6.QtWidgets import QApplication
    from quads_client.qt6.main import QuadsClientApp

    app = QApplication(sys.argv)
    app.setApplicationName("QUADS Client")
    app.setOrganizationName("QUADS Project")

    try:
        window = QuadsClientApp()
        window.show()
        return app.exec()
    except Exception as e:
        print(f"ERROR: Failed to start GUI: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
