---
title: AskDB — Ask your database anything
description: Natural language to SQL desktop app for PostgreSQL, MySQL, and SQLite.
---

# AskDB — Ask your database anything

> Natural language to SQL desktop app for PostgreSQL, MySQL, and SQLite.

[⬇️ Download (Releases)](../releases) · [⭐ Star on GitHub](../) · [Readme](../README.md)


## Demo video

<video src="https://github.com/user-attachments/assets/95feb4a4-5ee5-426b-be1d-fb22645c827f" controls style="max-width:100%;height:auto;"></video>


## Features

- Natural language → SQL using OpenAI via LangChain
- Clean desktop UI (PySide6/Qt): chat, generated SQL, and results in one place
- Streaming responses with captured intermediate SQL steps
- “Queries Executed” list: click to run again; right‑click to copy SQL
- Custom SQL editor with Run button
- Results table with auto column sizing
- Connection management:
  - Paste full database URL or fill fields manually
  - Auto‑detect DB type (postgres/mysql/sqlite) from URL
  - Auto‑populate host/port/database/user/password from URL
  - Test connectivity, Save for reuse, Recent connections, Reconnect
- Settings: set `OPENAI_API_KEY`, choose model (default `gpt-4o-mini`), optional LangSmith tracing
- macOS packaging via PyInstaller (`.app` and optional `.dmg`)


## Screenshots

> Replace these with your own images under `assets/screenshots/` in the repo.

![Connections](../assets/screenshots/connection.png)
![Workspace](../assets/screenshots/workspace.png)
![Settings](../assets/screenshots/setting.png)


## Quick start (desktop)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r desktop_requirements.txt
python desktop_app.py
```

Then in the app:
- Open Settings to set your `OPENAI_API_KEY` and choose a model.
- Create/Test/Save a database connection, then Connect.
- Chat in English; generated SQL appears and results are shown below.


## How it works

1) You ask a question in plain English
2) The AI generates SQL with LangChain + OpenAI
3) SQL is executed via SQLAlchemy against your database
4) Results appear instantly in the UI

Supported databases: PostgreSQL (`psycopg2`), MySQL (`pymysql`), SQLite


## FAQ

- Does my data leave my machine?
  - Queries run locally against your DB. Prompt text goes to your configured LLM provider (OpenAI). Enable LangSmith only if you want tracing.
- Can I use manual SQL?
  - Yes. Use the Custom Query editor and click Run.
- macOS only?
  - Packaged app targets macOS. You can run from source anywhere Python 3.10+ is available.


## Get involved

- Issues and feature requests: open an issue on GitHub
- Contributions welcome: fork and PR

Built with PySide6, SQLAlchemy, LangChain, and OpenAI.

