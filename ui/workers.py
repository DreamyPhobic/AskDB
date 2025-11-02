from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6 import QtCore
from sqlalchemy import text
from sqlalchemy.engine import Engine

from services.agent_service import create_agent


class _AgentStreamWorker(QtCore.QThread):
    add_query = QtCore.Signal(int, str)  # (ai_index, sql)
    set_output = QtCore.Signal(int, str)  # (ai_index, output_text)
    failed = QtCore.Signal(str)

    def __init__(self, agent, prompt: str, ai_index: int) -> None:
        super().__init__()
        self.agent = agent
        self.prompt = prompt
        self.ai_index = ai_index

    def run(self) -> None:  # type: ignore[override]
        try:
            final_output: Optional[str] = None
            for chunk in self.agent.stream({"input": self.prompt}):
                try:
                    if isinstance(chunk, dict):
                        actions = chunk.get("actions")
                        if actions:
                            try:
                                tools = ", ".join(getattr(a, "tool", "") for a in actions)
                                self.set_output.emit(self.ai_index, f"Running: {tools}…")
                            except Exception:
                                pass
                            for a in actions:
                                self._maybe_emit_query_from_action(a)

                        steps = chunk.get("steps") or chunk.get("next_step")
                        if steps:
                            for s in steps:
                                action = s[0] if isinstance(s, (list, tuple)) and s else s
                                try:
                                    tool_name = getattr(action, "tool", "")
                                    if tool_name:
                                        self.set_output.emit(self.ai_index, f"Running: {tool_name}…")
                                except Exception:
                                    pass
                                self._maybe_emit_query_from_action(action)
                                try:
                                    obs = s[1] if isinstance(s, (list, tuple)) and len(s) > 1 else None
                                    if obs is not None:
                                        snippet = str(obs).replace("\n", " ")
                                        if len(snippet) > 80:
                                            snippet = snippet[:77] + "…"
                                        if snippet:
                                            self.set_output.emit(self.ai_index, f"Analyzing: {snippet}")
                                except Exception:
                                    pass

                        if isinstance(chunk.get("output"), str):
                            final_output = chunk["output"]
                            self.set_output.emit(self.ai_index, final_output)
                except Exception:
                    continue
            if final_output is not None:
                self.set_output.emit(self.ai_index, final_output)
        except Exception as ex:  # noqa: BLE001
            self.failed.emit(str(ex))

    def _maybe_emit_query_from_action(self, action: Any) -> None:
        try:
            tool_name = getattr(action, "tool", "")
            if tool_name != "sql_db_query":
                return
            tool_input = getattr(action, "tool_input", None)
            q = None
            if isinstance(tool_input, dict):
                for k in ("query", "sql", "input"):
                    if k in tool_input and isinstance(tool_input[k], str):
                        q = tool_input[k]
                        break
            elif isinstance(tool_input, str):
                q = tool_input
            if q:
                self.add_query.emit(self.ai_index, str(q))
        except Exception:
            return


class _AgentInitWorker(QtCore.QThread):
    ready = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, engine: Engine, model_name: str, api_key: str, tracing: Dict[str, Any]) -> None:
        super().__init__()
        self.engine = engine
        self.model_name = model_name
        self.api_key = api_key
        self.tracing = tracing

    def run(self) -> None:  # type: ignore[override]
        try:
            agent = create_agent(self.engine, self.model_name, self.api_key, self.tracing)
            self.ready.emit(agent)
        except Exception as ex:  # noqa: BLE001
            self.failed.emit(str(ex))


class _SQLExecWorker(QtCore.QThread):
    result_ready = QtCore.Signal(list, list)  # rows, cols
    failed = QtCore.Signal(str)

    def __init__(self, engine: Engine, sql: str) -> None:
        super().__init__()
        self.engine = engine
        self.sql = sql

    def run(self) -> None:  # type: ignore[override]
        try:
            sql_str = self.sql.strip()
            with self.engine.connect() as conn:
                res = conn.execute(text(sql_str))
                cols = list(res.keys())
                rows = [list(row) for row in res.fetchall()]
            self.result_ready.emit(rows, cols)
        except Exception as ex:  # noqa: BLE001
            self.failed.emit(str(ex))
