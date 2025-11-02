from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
from PySide6 import QtWidgets


class ConnectionDialog(QtWidgets.QDialog):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None, existing: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Save Connection")
        self._existing = existing or {}
        layout = QtWidgets.QFormLayout(self)

        self.name_edit = QtWidgets.QLineEdit(self._existing.get("saved_name", ""))
        self.db_type = QtWidgets.QComboBox()
        self.db_type.addItems(["sqlite", "postgres", "mysql"])
        self.db_type.setCurrentText(self._existing.get("db_type", "sqlite"))

        self.sqlite_path = QtWidgets.QLineEdit(self._existing.get("name", ":memory:"))
        self.url_override = QtWidgets.QLineEdit(self._existing.get("url_override", ""))
        self.host = QtWidgets.QLineEdit(self._existing.get("host", "localhost"))
        self.port = QtWidgets.QSpinBox()
        self.port.setMaximum(65535)
        self.port.setValue(int(self._existing.get("port", 5432)))
        self.dbname = QtWidgets.QLineEdit(self._existing.get("name", ""))
        self.user = QtWidgets.QLineEdit(self._existing.get("user", ""))
        self.password = QtWidgets.QLineEdit(self._existing.get("password", ""))
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)

        layout.addRow("Save As", self.name_edit)
        layout.addRow("DB Type", self.db_type)
        layout.addRow("SQLite Path", self.sqlite_path)
        layout.addRow("URL Override", self.url_override)
        layout.addRow("Host", self.host)
        layout.addRow("Port", self.port)
        layout.addRow("Database", self.dbname)
        layout.addRow("User", self.user)
        layout.addRow("Password", self.password)

        self.db_type.currentTextChanged.connect(self._toggle_fields)
        self._toggle_fields(self.db_type.currentText())

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _toggle_fields(self, db_type: str) -> None:
        sqlite = db_type == "sqlite"
        self.sqlite_path.setEnabled(sqlite)
        self.host.setEnabled(not sqlite)
        self.port.setEnabled(not sqlite)
        self.dbname.setEnabled(not sqlite)
        self.user.setEnabled(not sqlite)
        self.password.setEnabled(not sqlite)

    def get_config(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        if self.result() != QtWidgets.QDialog.Accepted:
            return None
        name = self.name_edit.text().strip()
        if not name:
            return None
        db_type = self.db_type.currentText()
        cfg: Dict[str, Any] = {
            "db_type": db_type,
            "url_override": self.url_override.text().strip() or None,
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": -1,
        }
        if db_type == "sqlite":
            cfg["name"] = self.sqlite_path.text().strip() or ":memory:"
        else:
            cfg.update({
                "host": self.host.text().strip() or "localhost",
                "port": int(self.port.value()),
                "name": self.dbname.text().strip(),
                "user": self.user.text().strip(),
                "password": self.password.text(),
            })
        return name, cfg


