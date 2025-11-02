from __future__ import annotations

from typing import Optional
from PySide6 import QtWidgets, QtCore

from core.config_store import ConnectionManager, SettingsManager, RecentsManager
from services.db_service import build_engine
from db_util import quick_test_connection
from ui.settings_dialog import SettingsDialog
from ui.connection_editor import ConnectionEditor
from ui.query_tab import QueryTab
from ui.about_dialog import AboutDialog
from ui.widgets import ConnectionListItemWidget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AskDB")
        self.resize(1200, 800)

        self.settings = SettingsManager()
        self.conn_mgr = ConnectionManager()
        self.recents = RecentsManager()
        self.current_config: Optional[dict] = None
        self.current_engine = None

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self._build_connections_page()
        self._build_workspace_page()
        self.stack.setCurrentIndex(0)

        # Toolbar
        # Window menu with navigation/actions
        window_menu = self.menuBar().addMenu("Window")
        self.act_back = window_menu.addAction("Back to Connections")
        self.act_settings = window_menu.addAction("Settings")
        self.act_back.setEnabled(False)
        self.act_settings.triggered.connect(self._on_settings)
        self.act_back.triggered.connect(lambda: self._show_connections())

        help_menu = self.menuBar().addMenu("Help")
        self.act_about = help_menu.addAction("About AskDB…")
        self.act_about.triggered.connect(self._on_about)

    def _build_connections_page(self) -> None:
        page = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(page)

        # Side panel: saved + recent lists
        side = QtWidgets.QWidget()
        side_layout = QtWidgets.QVBoxLayout(side)
        # Settings button above New Connection
        self.btn_settings_conn = QtWidgets.QPushButton("AI Agent Settings")
        self.btn_settings_conn.clicked.connect(self._on_settings)
        side_layout.addWidget(self.btn_settings_conn)
        self.btn_new = QtWidgets.QPushButton("New Connection")
        side_layout.addWidget(self.btn_new)
        lbl_saved = QtWidgets.QLabel("Saved Connections")
        lbl_saved.setObjectName("SideListHeader")
        side_layout.addWidget(lbl_saved)
        self.saved_list = QtWidgets.QListWidget()
        self.saved_list.setObjectName("SideList")
        self.saved_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        side_layout.addWidget(self.saved_list)
        lbl_recent = QtWidgets.QLabel("Recent Connections")
        lbl_recent.setObjectName("SideListHeader")
        side_layout.addWidget(lbl_recent)
        self.recent_list = QtWidgets.QListWidget()
        self.recent_list.setObjectName("SideList")
        self.recent_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        side_layout.addWidget(self.recent_list)

        # Middle panel: connection editor + actions
        mid = QtWidgets.QWidget()
        mid_layout = QtWidgets.QVBoxLayout(mid)
        mid_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        title = QtWidgets.QLabel("Connection Details")
        title.setObjectName("SideListHeader")
        mid_layout.addWidget(title)
        self.editor = ConnectionEditor()
        mid_layout.addWidget(self.editor)
        # (Save now lives inside editor)

        # Layout
        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Horizontal)
        splitter.addWidget(side)
        splitter.addWidget(mid)
        splitter.setSizes([350, 850])
        h.addWidget(splitter)

        self.connections_page = page
        self.stack.addWidget(page)

        # Wire
        self.saved_list.itemSelectionChanged.connect(self._on_saved_selected)
        self.recent_list.itemSelectionChanged.connect(self._on_recent_selected)
        self.btn_new.clicked.connect(self._on_new)
        self.editor.save_clicked.connect(self._on_save)
        self.editor.test_clicked.connect(self._on_test)
        self.editor.connect_clicked.connect(self._on_connect_from_editor)

        self._reload_lists()

    def _clear_workspace(self) -> None:
        while self.workspace_container_layout.count():
            item = self.workspace_container_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                try:
                    if hasattr(w, "shutdown"):
                        w.shutdown()
                except Exception:
                    pass
                w.setParent(None)
                w.deleteLater()

    def _update_header(self, engine: Optional[object], cfg: dict) -> None:
        try:
            conn_name = self.editor.conn_name.text().strip()
        except Exception:
            conn_name = "Connection"
        self.header_title.setText(conn_name or "Connection")
        # Subtitle: prefer engine URL sans password, else fallback to cfg parts
        url_text = ""
        try:
            if engine is not None:
                url_text = engine.url.render_as_string(hide_password=True)
        except Exception:
            url_text = cfg.get("url_override") or ""
        if not url_text:
            parts = []
            if cfg.get("db_type"):
                parts.append(str(cfg.get("db_type")))
            if cfg.get("host"):
                host_port = cfg.get("host")
                if cfg.get("port"):
                    host_port += f":{cfg.get('port')}"
                parts.append(host_port)
            name = cfg.get("name")
            if name:
                parts.append(f"/{name}")
            url_text = " ".join(parts)
        self.header_meta.setText(url_text)
        self.header_meta.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

    def _open_workspace(self, engine, cfg: dict) -> None:
        self._clear_workspace()
        first = QueryTab(engine, self.settings)
        self.workspace_container_layout.addWidget(first)
        self._update_header(engine, cfg)

    def _build_workspace_page(self) -> None:
        page = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(page)
        # Allow vertical stretching; keep left alignment only
        v.setAlignment(QtCore.Qt.AlignLeft)

        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(6)
        # Workspace header: connection info
        self.workspace_header = QtWidgets.QWidget()
        self.workspace_header.setObjectName("WorkspaceHeader")
        hdr = QtWidgets.QVBoxLayout(self.workspace_header)
        hdr.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        hdr.setContentsMargins(8, 8, 8, 8)
        hdr.setSpacing(4)
        top_row = QtWidgets.QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)
        self.header_title = QtWidgets.QLabel("Connection")
        self.header_title.setObjectName("WorkspaceHeaderTitle")
        top_row.addWidget(self.header_title, 0, QtCore.Qt.AlignLeft)
        top_row.addStretch(1)
        self.btn_reconnect = QtWidgets.QPushButton("Reconnect")
        self.btn_reconnect.clicked.connect(self._on_reconnect)
        top_row.addWidget(self.btn_reconnect, 0, QtCore.Qt.AlignRight)
        hdr.addLayout(top_row)

        self.header_meta = QtWidgets.QLabel("")
        self.header_meta.setObjectName("WorkspaceHeaderMeta")
        # Ensure no extra per-label margins
        try:
            self.header_title.setContentsMargins(0, 0, 0, 0)
            self.header_meta.setContentsMargins(0, 0, 0, 0)
        except Exception:
            pass
        hdr.addWidget(self.header_meta)
        v.addWidget(self.workspace_header)

        # Container to host a single QueryTab instance
        self.workspace_container = QtWidgets.QWidget()
        self.workspace_container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.workspace_container_layout = QtWidgets.QVBoxLayout(self.workspace_container)
        self.workspace_container_layout.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.workspace_container, 1)
        self.workspace_page = page
        self.stack.addWidget(page)

    def _show_workspace(self) -> None:
        self.stack.setCurrentIndex(1)
        self.act_back.setEnabled(True)

    def _show_connections(self) -> None:
        self.stack.setCurrentIndex(0)
        self.act_back.setEnabled(False)

    def _on_about(self) -> None:
        dlg = AboutDialog(self)
        dlg.exec()

    def _reload_lists(self) -> None:
        self.saved_list.clear()
        for c in self.conn_mgr.connections:
            name = c.get("saved_name", "(unnamed)")
            widget = ConnectionListItemWidget(
                name,
                c.get("url_override") or f"{c.get('db_type')}://{c.get('host','')}:{c.get('port','')}/{c.get('name','')}",
                c.get("db_type", ""),
            )
            item = QtWidgets.QListWidgetItem()
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            item.setSizeHint(widget.sizeHint())
            self.saved_list.addItem(item)
            self.saved_list.setItemWidget(item, widget)
        self.recent_list.clear()
        for c in self.recents.recents:
            # Display a short description
            title = c.get("db_type", "?")
            desc = c.get("url_override") or f"{c.get('db_type')}://{c.get('host', '')}:{c.get('port', '')}/{c.get('name', '')}"
            widget = ConnectionListItemWidget(title, desc, c.get("db_type", ""))
            item = QtWidgets.QListWidgetItem()
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            item.setSizeHint(widget.sizeHint())
            self.recent_list.addItem(item)
            self.recent_list.setItemWidget(item, widget)

    def _selected_saved_config(self) -> Optional[dict]:
        row = self.saved_list.currentRow()
        if row < 0 or row >= len(self.conn_mgr.connections):
            return None
        return self.conn_mgr.connections[row]

    def _selected_recent_config(self) -> Optional[dict]:
        idx = self.recent_list.currentRow()
        if idx < 0 or idx >= len(self.recents.recents):
            return None
        return dict(self.recents.recents[idx])

    def _on_settings(self) -> None:
        dlg = SettingsDialog(self.settings, self)
        dlg.exec()

    def _on_saved_selected(self) -> None:
        # ensure only one list has a selection
        if self.saved_list.selectedItems():
            self.recent_list.clearSelection()
        cfg = self._selected_saved_config()
        if cfg:
            self.editor.set_config(cfg)

    def _on_recent_selected(self) -> None:
        # ensure only one list has a selection
        if self.recent_list.selectedItems():
            self.saved_list.clearSelection()
        cfg = self._selected_recent_config()
        if cfg:
            self.editor.set_config(cfg)

    def _on_delete(self) -> None:
        cfg = self._selected_saved_config()
        if not cfg:
            return
        name = cfg.get("saved_name", "")
        if not name:
            return
        self.conn_mgr.delete(name)
        self._reload_lists()

    def _on_save(self) -> None:
        # Use name from editor if provided; else prompt
        cfg = self.editor.get_config()
        name = self.editor.conn_name.text().strip()
        if not name:
            name, ok = QtWidgets.QInputDialog.getText(self, "Save Connection", "Save As:")
            if not ok or not name.strip():
                return
        self.conn_mgr.add_or_update(name.strip(), cfg)
        self._reload_lists()

    def _on_new(self) -> None:
        self.editor.start_new()
        # Clear selections in both lists
        self.saved_list.clearSelection()
        self.recent_list.clearSelection()
    def _set_busy(self, busy: bool, text: str = "") -> None:
        if busy:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.statusBar().showMessage(text or "Working…")
            self.btn_new.setEnabled(False)
            # no external save button; keep editor controls
            self.editor.set_busy(True)
        else:
            QtWidgets.QApplication.restoreOverrideCursor()
            self.statusBar().clearMessage()
            self.btn_new.setEnabled(True)
            # no external save button
            self.editor.set_busy(False)

    def _on_test(self) -> None:
        cfg = self.editor.get_config()
        try:
            self._set_busy(True, "Testing connection…")
            engine = build_engine(cfg)
            ok, err = quick_test_connection(engine)
        except Exception as ex:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Connection Error", str(ex))
            self._set_busy(False)
            return
        finally:
            self._set_busy(False)
        if ok:
            QtWidgets.QMessageBox.information(self, "Test Connection", "Connection successful.")
        else:
            QtWidgets.QMessageBox.warning(self, "Test Connection", f"Connection failed: {err}")

    def _on_connect_from_editor(self) -> None:
        cfg = self.editor.get_config()
        try:
            self._set_busy(True, "Connecting…")
            engine = build_engine(cfg)
            # ok, err = quick_test_connection(engine)
            # if not ok:
            #     raise RuntimeError(err or "Unknown connection error")
        except Exception as ex:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Connection Error", str(ex))
            self._set_busy(False)
            return
        # Save to recents
        self.recents.add_recent(cfg)
        # Remember current connection
        self.current_config = dict(cfg)
        self.current_engine = engine
        # Enter workspace immediately with a single query tab
        self._open_workspace(engine, cfg)
        # Update workspace header info
        try:
            conn_name = self.editor.conn_name.text().strip()
        except Exception:
            conn_name = "Connection"
        try:
            db_name = cfg.get("name") or getattr(engine.url, "database", "") or ""
        except Exception:
            db_name = cfg.get("name", "")
        self.header_title.setText(conn_name or "Connection")
        # Subtitle: full URL (without password if possible)
        url_text = ""
        try:
            url_text = engine.url.render_as_string(hide_password=True)
        except Exception:
            url_text = cfg.get("url_override") or ""
        # Fallback to a simple composed hint if URL not available
        if not url_text:
            parts = []
            if cfg.get("db_type"):
                parts.append(str(cfg.get("db_type")))
            if cfg.get("host"):
                host_port = cfg.get("host")
                if cfg.get("port"):
                    host_port += f":{cfg.get('port')}"
                parts.append(host_port)
            if db_name:
                parts.append(f"/{db_name}")
            url_text = " ".join(parts)
        self.header_meta.setText(url_text)
        self.header_meta.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self._show_workspace()
        self._set_busy(False)

    def _on_reconnect(self) -> None:
        cfg = self.current_config or {}
        if not cfg:
            QtWidgets.QMessageBox.information(self, "Reconnect", "No active connection to reconnect.")
            return
        try:
            self._set_busy(True, "Reconnecting…")
            engine = build_engine(cfg)
            ok, err = quick_test_connection(engine)
            if not ok:
                raise RuntimeError(err or "Unknown connection error")
        except Exception as ex:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Reconnect Failed", str(ex))
            self._set_busy(False)
            return
        # Replace the workspace QueryTab with a fresh one bound to the new engine
        self.current_engine = engine
        self._open_workspace(engine, self.current_config or {})
        self._set_busy(False)
        QtWidgets.QMessageBox.information(self, "Reconnect", "Reconnected successfully.")


