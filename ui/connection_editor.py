from __future__ import annotations

from typing import Any, Dict, Optional
from PySide6 import QtWidgets, QtCore

from .utils import mk_label
class ConnectionEditor(QtWidgets.QWidget):
    test_clicked = QtCore.Signal()
    connect_clicked = QtCore.Signal()
    save_clicked = QtCore.Signal()
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.stack = QtWidgets.QStackedLayout(self)

        # Page 1: full form
        form_page = QtWidgets.QWidget()
        form_container = QtWidgets.QFrame()
        form_container.setObjectName("ConnectionEditorFrame")
        form_container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        form = QtWidgets.QFormLayout(form_container)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        form.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        form.setFormAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(16)

        self.db_type = QtWidgets.QComboBox()
        self.db_type.setFixedHeight(30)
        self.db_type.addItems(["sqlite", "postgres", "mysql"])
        self.db_type.setFixedWidth(150)

        self.conn_name = QtWidgets.QLineEdit("")
        self.conn_name.setPlaceholderText("Optional name for saving this connection")
        self.conn_name.setMinimumWidth(300)
      

        self.sqlite_path = QtWidgets.QLineEdit(":memory:")
        self.sqlite_path.setPlaceholderText("/path/to/database.db or :memory:")
        self.sqlite_path.setMinimumWidth(400)

        self.url_override = QtWidgets.QLineEdit()
        self.url_override.setPlaceholderText("Optional full database URL")
        self.url_override.setMinimumWidth(500)

        self.host = QtWidgets.QLineEdit()
        self.host.setFixedWidth(240)
        self.host.setPlaceholderText("localhost")

        self.port = QtWidgets.QSpinBox()
        self.port.setMaximum(65535)
        self.port.setValue(5432)
        self.port.setFixedWidth(100)
        self.dbname = QtWidgets.QLineEdit("")
        self.dbname.setFixedWidth(260)
        self.user = QtWidgets.QLineEdit("")
        self.user.setFixedWidth(220)
        self.password = QtWidgets.QLineEdit("")
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.setFixedWidth(220)

        # Group: DB Type
        self.dbtype_box = QtWidgets.QGroupBox("Database Type")
        dtform = QtWidgets.QFormLayout(self.dbtype_box)
        dtform.setVerticalSpacing(10)
        dtform.setHorizontalSpacing(14)
        dtform.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        dtform.setFormAlignment(QtCore.Qt.AlignLeft)
        dtform.addRow(mk_label("DB Type", self.db_type), self.db_type)

        # Group: General
        self.general_box = QtWidgets.QGroupBox("General")
        gform = QtWidgets.QFormLayout(self.general_box)
        gform.setVerticalSpacing(10)
        gform.setHorizontalSpacing(14)
        gform.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        gform.setFormAlignment(QtCore.Qt.AlignLeft)
        gform.addRow(mk_label("Connection Name", self.conn_name), self.conn_name)
        gform.addRow(mk_label("URL Override", self.url_override), self.url_override)

        # Group: SQLite
        self.sqlite_box = QtWidgets.QGroupBox("SQLite")
        sform = QtWidgets.QFormLayout(self.sqlite_box)
        sform.setVerticalSpacing(10)
        sform.setHorizontalSpacing(14)
        sform.setFormAlignment(QtCore.Qt.AlignLeft)
        sform.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        sform.addRow(mk_label("SQLite Path", self.sqlite_path), self.sqlite_path)

        # Group: Network
        self.net_box = QtWidgets.QGroupBox("Network")
        nform = QtWidgets.QFormLayout(self.net_box)
        nform.setVerticalSpacing(10)
        nform.setHorizontalSpacing(14)
        nform.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        nform.setFormAlignment(QtCore.Qt.AlignLeft)
        self.host.setMinimumWidth(420)
        self.host.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        nform.addRow(mk_label("Host", self.host), self.host)
        nform.addRow(mk_label("Port", self.port), self.port)
        nform.addRow(mk_label("Database", self.dbname), self.dbname)

        # Group: Auth
        self.auth_box = QtWidgets.QGroupBox("Auth")
        aform = QtWidgets.QFormLayout(self.auth_box)
        aform.setVerticalSpacing(10)
        aform.setHorizontalSpacing(14)
        aform.setFormAlignment(QtCore.Qt.AlignLeft)
        aform.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        aform.addRow(mk_label("User", self.user), self.user)
        aform.addRow(mk_label("Password", self.password), self.password)

        form.addRow(self.dbtype_box)
        form.addRow(self.general_box)
        form.addRow(self.sqlite_box)
        form.addRow(self.net_box)
        form.addRow(self.auth_box)
        # Inline actions inside editor
        actions = QtWidgets.QHBoxLayout()
        actions.addStretch(1)
        self.btn_test = QtWidgets.QPushButton("Test")
        self.btn_connect = QtWidgets.QPushButton("Connect")
        self.btn_save = QtWidgets.QPushButton("Save")
        actions.addWidget(self.btn_save)
        actions.addWidget(self.btn_test)
        actions.addWidget(self.btn_connect)
        form.addRow(actions)

        # Center the editor
        form_page_layout = QtWidgets.QHBoxLayout(form_page)
        form_page_layout.addWidget(form_container)

        # Assemble stack (single page)
        self.stack.addWidget(form_page)  # index 0

        # Wire
        self.db_type.currentTextChanged.connect(self._toggle_fields)
        self._toggle_fields(self.db_type.currentText())
        self.btn_save.clicked.connect(lambda: self.save_clicked.emit())
        self.btn_test.clicked.connect(lambda: self.test_clicked.emit())
        self.btn_connect.clicked.connect(lambda: self.connect_clicked.emit())

    def _toggle_fields(self, db_type: str) -> None:
        sqlite = db_type == "sqlite"
        self.sqlite_box.setVisible(sqlite)
        self.net_box.setVisible(not sqlite)
        self.auth_box.setVisible(not sqlite)

    def set_config(self, cfg: Dict[str, Any]) -> None:
        # Ensure we are on form page when editing/previewing
        self.stack.setCurrentIndex(0)
        self.db_type.setCurrentText(cfg.get("db_type", "sqlite"))
        self.conn_name.setText(cfg.get("saved_name", ""))
        self.sqlite_path.setText(cfg.get("name", ":memory:"))
        self.url_override.setText(cfg.get("url_override", "") or "")
        self.host.setText(cfg.get("host", "localhost") or "localhost")
        self.port.setValue(int(cfg.get("port", 5432) or 5432))
        self.dbname.setText(cfg.get("name", "") or "")
        self.user.setText(cfg.get("user", "") or "")
        self.password.setText(cfg.get("password", "") or "")

    def get_config(self) -> Dict[str, Any]:
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
        return cfg

    def start_new(self) -> None:
        # Reset values
        self.sqlite_path.setText(":memory:")
        self.url_override.clear()
        self.host.setText("localhost")
        self.port.setValue(5432)
        self.dbname.clear()
        self.user.clear()
        self.password.clear()
        self.conn_name.clear()
        # Stay on editor view
        self.stack.setCurrentIndex(0)

    def set_busy(self, busy: bool) -> None:
        self.btn_test.setEnabled(not busy)
        self.btn_connect.setEnabled(not busy)


