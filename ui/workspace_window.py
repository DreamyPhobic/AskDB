from __future__ import annotations

from typing import Optional
from PySide6 import QtWidgets
from sqlalchemy.engine import Engine

from core.config_store import SettingsManager
from ui.query_tab import QueryTab


class WorkspaceWindow(QtWidgets.QMainWindow):
    def __init__(self, engine: Engine, settings: SettingsManager, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AskDB - Workspace")
        self.resize(1200, 800)
        self.engine = engine
        self.settings = settings

        # Single query tab only
        self.query_tab = QueryTab(self.engine, self.settings)
        self.setCentralWidget(self.query_tab)

    # No tab management; kept for compatibility if referenced elsewhere


