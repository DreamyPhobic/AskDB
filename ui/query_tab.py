from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from PySide6 import QtCore, QtWidgets
from sqlalchemy.engine import Engine

from core.config_store import SettingsManager
from ui.utils import markdown_to_html
from ui.widgets import ChatMessageRowWidget, QueryListItemWidget
from services.sql_utils import normalize_sql, format_sql
from ui.workers import _AgentStreamWorker, _AgentInitWorker, _SQLExecWorker
  


class QueryTab(QtWidgets.QWidget):
    def __init__(self, engine: Engine, settings: SettingsManager, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self.settings = settings
        tracing = {
            "enable": settings.enable_tracing,
            "api_key": settings.langsmith_api_key,
            "project": settings.langsmith_project,
        }
        self.agent: Optional[Any] = None  # created asynchronously
        self._pending_prompts: List[Tuple[int, str]] = []
        self._ai_messages: List[Dict[str, Any]] = []  # {text, queries: [str], steps}
        self.all_queries: List[Dict[str, Any]] = []  # {sql: str, ai_index: Optional[int]}
        self._ai_items: List[QtWidgets.QListWidgetItem] = []
        self._ai_widgets: List[Any] = []  # ChatMessageRowWidget aligned by ai index

        root = QtWidgets.QVBoxLayout(self)

        # LEFT: Chat (upper 50%) + SQL Output (lower 50%)
        chat_wrap = QtWidgets.QWidget()
        chat_layout = QtWidgets.QVBoxLayout(chat_wrap)
        self.chat_list = QtWidgets.QListWidget()
        self.chat_list.setObjectName("ChatList")
        self.chat_list.setUniformItemSizes(False)
        self.chat_list.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.chat_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.chat_list.installEventFilter(self)
        self.chat_list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.chat_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self._on_chat_context_menu)
        self.chat_input = QtWidgets.QLineEdit()
        self.chat_send = QtWidgets.QPushButton("Send")
        send_row = QtWidgets.QHBoxLayout()
        send_row.addWidget(self.chat_input)
        send_row.addWidget(self.chat_send)
        chat_title = QtWidgets.QLabel("Chat")
        chat_title.setObjectName("SectionTitle")
        chat_layout.addWidget(chat_title)
        self._chat_placeholder = QtWidgets.QLabel("Start a conversation. Type a question and press Send. The AI will reply and generate SQL you can run.")
        self._chat_placeholder.setObjectName("SectionSubtitle")
        self._chat_placeholder.setWordWrap(True)
        chat_layout.addWidget(self._chat_placeholder)
       
        chat_layout.addWidget(self.chat_list)
        chat_layout.addLayout(send_row)

        output_wrap = QtWidgets.QWidget()
        output_layout = QtWidgets.QVBoxLayout(output_wrap)
        output_title = QtWidgets.QLabel("SQL Output")
        output_title.setObjectName("SectionTitle")
        output_layout.addWidget(output_title)
        self._output_placeholder = QtWidgets.QLabel("Query results will appear here after you run a query.")
        self._output_placeholder.setObjectName("SectionSubtitle")
        self._output_placeholder.setWordWrap(True)
        output_layout.addWidget(self._output_placeholder)

        output_layout.setObjectName("SQLOutputLayout")
        self.output_table = QtWidgets.QTableWidget()
        output_layout.addWidget(self.output_table)

        left_splitter = QtWidgets.QSplitter()
        left_splitter.setOrientation(QtCore.Qt.Vertical)
        left_splitter.addWidget(chat_wrap)
        left_splitter.addWidget(output_wrap)
        left_splitter.setStretchFactor(0, 1)
        left_splitter.setStretchFactor(1, 1)
        left_splitter.setSizes([600, 600])

        # RIGHT: Queries (upper 70%) + Custom Query (lower 30%)
        queries_panel = QtWidgets.QWidget()
        queries_panel_layout = QtWidgets.QVBoxLayout(queries_panel)
        queries_title = QtWidgets.QLabel("Queries Executed")
        queries_title.setObjectName("SectionTitle")
        queries_panel_layout.addWidget(queries_title)
        self._queries_placeholder = QtWidgets.QLabel("AI-generated and custom queries will be listed here. Right-click a query to copy it or click to run.")
        self._queries_placeholder.setObjectName("SectionSubtitle")
        self._queries_placeholder.setWordWrap(True)
        queries_panel_layout.addWidget(self._queries_placeholder)

        self.query_list = QtWidgets.QListWidget()
        self.query_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.query_list.customContextMenuRequested.connect(self._on_query_context_menu)
        queries_panel_layout.addWidget(self.query_list)

        custom_panel = QtWidgets.QWidget()
        custom_panel_layout = QtWidgets.QVBoxLayout(custom_panel)
        custom_title = QtWidgets.QLabel("Custom Query")
        custom_title.setObjectName("SectionTitle")
        custom_panel_layout.addWidget(custom_title)
        self._custom_placeholder = QtWidgets.QLabel("Write your own SQL here and click Run Query to execute it.")
        self._custom_placeholder.setObjectName("SectionSubtitle")
        self._custom_placeholder.setWordWrap(True)
        custom_panel_layout.addWidget(self._custom_placeholder)
    
        self.custom_query_edit = QtWidgets.QPlainTextEdit()
        self.custom_query_edit.setPlaceholderText("Write a custom SQL query...")
        self.custom_query_run = QtWidgets.QPushButton("Run Query")
        custom_row = QtWidgets.QHBoxLayout()
        custom_row.addWidget(self.custom_query_run)
        custom_panel_layout.addWidget(self.custom_query_edit)
        custom_panel_layout.addLayout(custom_row)

        right_splitter = QtWidgets.QSplitter()
        right_splitter.setOrientation(QtCore.Qt.Vertical)
        right_splitter.addWidget(queries_panel)
        right_splitter.addWidget(custom_panel)
        right_splitter.setStretchFactor(0, 7)
        right_splitter.setStretchFactor(1, 3)
        right_splitter.setSizes([700, 300])

        # MAIN: Left 70% / Right 30%
        main_splitter = QtWidgets.QSplitter()
        main_splitter.setOrientation(QtCore.Qt.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 7)
        main_splitter.setStretchFactor(1, 3)
        main_splitter.setSizes([700, 300])

        root.addWidget(main_splitter)

        # Wire signals
        self.chat_send.clicked.connect(self._on_send)
        self.query_list.itemSelectionChanged.connect(self._on_query_selected)
        self.custom_query_run.clicked.connect(self._on_run_custom_query)
        self._sql_worker: Optional[_SQLExecWorker] = None

        # Kick off agent initialization in the background
        self._agent_init_worker: Optional[_AgentInitWorker] = None
        self._start_agent_init()
        # Track current stream worker explicitly for cleanup
        self._worker: Optional[_AgentStreamWorker] = None


    def eventFilter(self, obj: QtCore.QObject, ev: QtCore.QEvent) -> bool:  # type: ignore[override]
        try:
            if obj is self.chat_list and ev.type() == QtCore.QEvent.Resize:
                self._fit_chat_bubbles()
        except Exception:
            pass
        return super().eventFilter(obj, ev)

    def _fit_chat_bubbles(self) -> None:
        try:
            avail = max(120, self.chat_list.viewport().width() - 40)
            for i in range(self.chat_list.count()):
                it = self.chat_list.item(i)
                w = self.chat_list.itemWidget(it)
                if hasattr(w, "bubble"):
                    try:
                        w.bubble.setMaximumWidth(avail)
                        w.bubble.adjustSize()
                        w.adjustSize()
                        it.setSizeHint(w.sizeHint())
                    except Exception:
                        continue
            self.chat_list.updateGeometries()
        except Exception:
            pass

    def _normalize_sql(self, q: str) -> str:
        return normalize_sql(q)

    def _format_sql(self, q: str) -> str:
        """Return SQL string with common keywords uppercased for readability.

        This is a lightweight formatter (no full SQL parsing). It avoids changing
        text inside simple single quotes by temporarily masking them.
        """
        return format_sql(q)

    def _append_chat(self, role: str, text: str, ai_index: Optional[int] = None) -> None:
        row_widget = ChatMessageRowWidget(text, role=role.lower())
        item = QtWidgets.QListWidgetItem()
        item.setData(QtCore.Qt.UserRole, {"role": role.lower(), "ai_index": ai_index})
        # Chat messages are not selectable
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item.setSizeHint(row_widget.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, row_widget)
        # Recompute size hint to avoid truncation
        row_widget.adjustSize()
        item.setSizeHint(row_widget.sizeHint())
        self.chat_list.updateGeometries()
        self.chat_list.scrollToBottom()
        try:
            self._fit_chat_bubbles()
        except Exception:
            pass

    def _extract_queries(self, steps: List[Any]) -> List[str]:
        queries: List[str] = []
        for tup in steps:
            try:
                action, observation = tup
            except Exception:
                continue
            tool_name = getattr(action, "tool", "")
            if tool_name != "sql_db_query":
                continue
            tool_input = getattr(action, "tool_input", None)
            if isinstance(tool_input, dict):
                q = tool_input.get("query") if tool_input else None
                if isinstance(q, str):
                    queries.append(self._format_sql(q))
            elif isinstance(tool_input, str):
                queries.append(self._format_sql(tool_input))
        return queries

    def _on_send(self) -> None:
        text = self.chat_input.text().strip()
        if not text:
            return
        self.chat_input.clear()
        self._append_chat("You", text)

        # Create placeholder AI message and stream updates
        self._ai_messages.append({"text": "", "queries": [], "steps": []})
        ai_idx = len(self._ai_messages) - 1
        # Append placeholder row to chat
        row_widget = ChatMessageRowWidget("…", role="ai")
        item = QtWidgets.QListWidgetItem()
        item.setData(QtCore.Qt.UserRole, {"role": "ai", "ai_index": ai_idx})
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        item.setSizeHint(row_widget.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, row_widget)
        row_widget.adjustSize()
        item.setSizeHint(row_widget.sizeHint())
        self.chat_list.updateGeometries()
        self.chat_list.scrollToBottom()
        self._ai_items.append(item)
        self._ai_widgets.append(row_widget)
        try:
            self._fit_chat_bubbles()
        except Exception:
            pass

        # If agent ready, start stream; otherwise queue until init completes
        if self.agent is not None:
            self._start_stream_for(ai_idx, text)
        else:
            # show a brief initializing hint
            try:
                w = self._ai_widgets[ai_idx]
                w.bubble.label.setText("Initializing model…")
            except Exception:
                pass
            self._pending_prompts.append((ai_idx, text))
            self._start_agent_init()

    def _start_stream_for(self, ai_index: int, prompt: str) -> None:
        worker = _AgentStreamWorker(self.agent, prompt, ai_index)
        worker.add_query.connect(self._on_stream_query)
        worker.set_output.connect(self._on_stream_output)
        worker.failed.connect(self._on_agent_failed)
        worker.finished.connect(lambda ai=ai_index: self._on_stream_finished(ai))
        try:
            worker.finished.connect(lambda: setattr(self, "_worker", None))
        except Exception:
            pass
        worker.start()
        self._worker = worker

    def _start_agent_init(self) -> None:
        if self.agent is not None:
            return
        if getattr(self, "_agent_init_worker", None) is not None and self._agent_init_worker.isRunning():
            return
        tracing = {
            "enable": self.settings.enable_tracing,
            "api_key": self.settings.langsmith_api_key,
            "project": self.settings.langsmith_project,
        }
        w = _AgentInitWorker(self.engine, self.settings.model_name, self.settings.api_key, tracing)
        w.ready.connect(self._on_agent_init_ready)
        w.failed.connect(self._on_agent_init_failed)
        self._agent_init_worker = w
        w.start()

    def _on_agent_init_ready(self, agent: Any) -> None:
        self.agent = agent
        # Drain pending prompts
        try:
            pending = list(self._pending_prompts)
            self._pending_prompts.clear()
            for ai_index, prompt in pending:
                self._start_stream_for(ai_index, prompt)
        except Exception:
            pass

    def _on_agent_init_failed(self, err: str) -> None:
        self._append_chat("Error", err)

    def _on_chat_context_menu(self, pos: QtCore.QPoint) -> None:
        try:
            item = self.chat_list.itemAt(pos)
            if not item:
                return
            widget = self.chat_list.itemWidget(item)
            text = ""
            try:
                if hasattr(widget, "bubble") and hasattr(widget.bubble, "label"):
                    text = widget.bubble.label.text()
            except Exception:
                text = ""
            if not text:
                return
            menu = QtWidgets.QMenu(self)
            act_copy = menu.addAction("Copy Message")
            chosen = menu.exec_(self.chat_list.viewport().mapToGlobal(pos))
            if chosen == act_copy:
                QtWidgets.QApplication.clipboard().setText(text)
        except Exception:
            pass

    def _on_agent_failed(self, err: str) -> None:
        self._append_chat("Error", err)

    def _on_agent_result(self, result: Dict[str, Any]) -> None:
        # Fallback path (non-stream)
        output = result.get("output", "")
        steps = result.get("intermediate_steps", [])
        queries = self._extract_queries(steps)
        self._ai_messages.append({"text": output, "queries": queries, "steps": steps})
        ai_idx = len(self._ai_messages) - 1
        self._append_chat("AI", output, ai_index=ai_idx)
        for q in queries:
            self.all_queries.append({"sql": q, "ai_index": ai_idx})
        self._refresh_query_list()
        # Auto-run last query if available
        try:
            if queries:
                self._run_sql_and_show(queries[-1])
        except Exception:
            pass

    def _on_stream_query(self, ai_index: int, query: str) -> None:
        norm = self._format_sql(query)
        if 0 <= ai_index < len(self._ai_messages):
            self._ai_messages[ai_index]["queries"].append(norm)
        self.all_queries.append({"sql": norm, "ai_index": ai_index})
        self._refresh_query_list()

    def _on_stream_output(self, ai_index: int, text: str) -> None:
        if 0 <= ai_index < len(self._ai_messages):
            # Append status lines, replace for final content
            prev = self._ai_messages[ai_index].get("text", "")
            if text.startswith("Thinking") or text.startswith("Analyzing") or text.startswith("Planning"):
                new_text = (prev + ("\n" if prev else "") + text).strip()
            else:
                new_text = text
            self._ai_messages[ai_index]["text"] = new_text
            # Update bubble widget text and resize
            w = self._ai_widgets[ai_index]
            item = self._ai_items[ai_index]
            try:
                w.bubble.label.setText(markdown_to_html(new_text))
                w.bubble.adjustSize()
                w.adjustSize()
                item.setSizeHint(w.sizeHint())
                self.chat_list.updateGeometries()
                self.chat_list.scrollToBottom()
            except Exception:
                pass


    def _refresh_query_list(self) -> None:
        self.query_list.clear()
        for idx, entry in enumerate(self.all_queries, start=1):
            ai_idx = entry.get("ai_index")
            source_text = f"Source: AI #{ai_idx + 1}" if ai_idx is not None else "Source: Custom"
            widget = QueryListItemWidget(idx, entry["sql"], source_text)
            item = QtWidgets.QListWidgetItem()
            item.setData(QtCore.Qt.UserRole, entry)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            item.setSizeHint(widget.sizeHint())
            self.query_list.addItem(item)
            self.query_list.setItemWidget(item, widget)
        # Sync selection style on refresh
        self._sync_query_item_selection()

    def _on_query_selected(self) -> None:
        items = self.query_list.selectedItems()
        if not items:
            self._sync_query_item_selection()
            return
        self._sync_query_item_selection()
        data = items[0].data(QtCore.Qt.UserRole) or {}
        sql = data.get("sql") if isinstance(data, dict) else items[0].text()
        self._start_sql_in_thread(sql)

    def _on_query_context_menu(self, pos: QtCore.QPoint) -> None:
        try:
            item = self.query_list.itemAt(pos)
            if not item:
                return
            data = item.data(QtCore.Qt.UserRole) or {}
            sql = data.get("sql") if isinstance(data, dict) else ""
            if not sql:
                widget = self.query_list.itemWidget(item)
                try:
                    if hasattr(widget, "code"):
                        sql = widget.code.text()
                except Exception:
                    sql = ""
            if not sql:
                return
            menu = QtWidgets.QMenu(self)
            act_copy = menu.addAction("Copy SQL")
            chosen = menu.exec_(self.query_list.viewport().mapToGlobal(pos))
            if chosen == act_copy:
                QtWidgets.QApplication.clipboard().setText(sql)
        except Exception:
            pass

    def _on_stream_finished(self, ai_index: int) -> None:
        try:
            if 0 <= ai_index < len(self._ai_messages):
                queries = self._ai_messages[ai_index].get("queries", [])
                if queries:
                    self._run_sql_and_show(queries[-1])
        except Exception:
            pass

    def _sync_query_item_selection(self) -> None:
        for i in range(self.query_list.count()):
            it = self.query_list.item(i)
            w = self.query_list.itemWidget(it)
            if hasattr(w, "set_selected"):
                w.set_selected(it.isSelected())


    def _on_run_custom_query(self) -> None:
        sql = self.custom_query_edit.toPlainText().strip()
        if not sql:
            return
        self.all_queries.append({"sql": sql, "ai_index": None})
        self._refresh_query_list()
        self._run_sql_and_show(sql)

    def _run_sql_and_show(self, sql: str) -> None:
        try:
            self._start_sql_in_thread(sql)
        except Exception as ex:
            self._on_sql_error(str(ex))

    def _start_sql_in_thread(self, sql: str) -> None:
        # Show loading state
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.output_table.clear()
        self.output_table.setRowCount(0)
        self.output_table.setColumnCount(1)
        self.output_table.setHorizontalHeaderLabels(["Running…"])
        # Stop previous worker if any
        if getattr(self, "_sql_worker", None) is not None and self._sql_worker.isRunning():
            try:
                self._sql_worker.terminate()
            except Exception:
                pass
        worker = _SQLExecWorker(self.engine, sql)
        worker.result_ready.connect(self._on_sql_result)
        worker.failed.connect(self._on_sql_error)
        try:
            worker.finished.connect(lambda: setattr(self, "_sql_worker", None))
        except Exception:
            pass
        self._sql_worker = worker
        worker.start()

    def shutdown(self) -> None:
        """Stop any running background threads to avoid QThread destruction errors."""
        try:
            workers: List[Any] = []
            try:
                if getattr(self, "_sql_worker", None) is not None:
                    workers.append(self._sql_worker)
            except Exception:
                pass
            try:
                if getattr(self, "_worker", None) is not None:
                    workers.append(self._worker)
            except Exception:
                pass
            try:
                if getattr(self, "_agent_init_worker", None) is not None:
                    workers.append(self._agent_init_worker)
            except Exception:
                pass
            for w in workers:
                try:
                    if w is not None and hasattr(w, "isRunning") and w.isRunning():
                        # Hard stop since our threads override run() without an event loop
                        w.terminate()
                        # Wait briefly to ensure thread exit before widget deletion
                        if hasattr(w, "wait"):
                            w.wait(2000)
                except Exception:
                    continue
        except Exception:
            pass

    def _on_sql_result(self, rows: List[List[Any]], cols: List[str]) -> None:
        try:
            self.output_table.setRowCount(len(rows))
            self.output_table.setColumnCount(len(cols))
            self.output_table.setHorizontalHeaderLabels([str(c) for c in cols])
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.output_table.setItem(r, c, QtWidgets.QTableWidgetItem(str(val)))
            self.output_table.resizeColumnsToContents()
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def _on_sql_error(self, msg: str) -> None:
        try:
            self.output_table.setRowCount(0)
            self.output_table.setColumnCount(1)
            self.output_table.setHorizontalHeaderLabels(["Error"])
            self.output_table.setRowCount(1)
            self.output_table.setItem(0, 0, QtWidgets.QTableWidgetItem(msg))
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()


 


