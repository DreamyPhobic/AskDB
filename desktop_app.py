from __future__ import annotations

import sys
from pathlib import Path
from PySide6 import QtWidgets, QtGui, QtCore

from ui.main_window import MainWindow
from ui.theme import app_stylesheet


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    # App identity for dev runs
    QtCore.QCoreApplication.setApplicationName("AskDB")
    # QtCore.QCoreApplication.setApplicationDisplayName("AskDB")
    QtCore.QCoreApplication.setOrganizationName("AskDB")
    # App icon for dev runs
    root = Path(__file__).resolve().parent
    logo = root / "assets" / "logo.png"
    if logo.exists():
        icon = QtGui.QIcon(str(logo))
        app.setWindowIcon(icon)
    app.setStyleSheet(app_stylesheet())
    w = MainWindow()
    try:
        if logo.exists():
            w.setWindowIcon(QtGui.QIcon(str(logo)))
    except Exception:
        pass
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


