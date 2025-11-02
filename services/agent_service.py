from __future__ import annotations

import os
from sqlalchemy.engine import Engine
from typing import Optional, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent


def _apply_tracing_env(tracing: Optional[Dict[str, Any]]) -> None:
    if not tracing:
        return
    enabled = bool(tracing.get("enable", False))
    if enabled:
        # LangChain v2 tracing (LangSmith)
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        api_key = tracing.get("api_key", "")
        project = tracing.get("project", "")
        if api_key:
            # New env name used by LangChain for LangSmith
            os.environ["LANGCHAIN_API_KEY"] = str(api_key)
        if project:
            os.environ["LANGCHAIN_PROJECT"] = str(project)
        # Endpoint defaults to api.smith.langchain.com
    else:
        # Disable tracing explicitly
        os.environ.pop("LANGCHAIN_TRACING_V2", None)


def create_agent(engine: Engine, model: str, api_key: str, tracing: Optional[Dict[str, Any]] = None):
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    _apply_tracing_env(tracing)
    db = SQLDatabase(engine=engine)
    llm = ChatOpenAI(model=model, temperature=0)
    agent = create_sql_agent(
        llm,
        db=db,
        agent_type="tool-calling",
        verbose=False,
        top_k=10,
        agent_executor_kwargs={"return_intermediate_steps": True},
    )
    return agent


