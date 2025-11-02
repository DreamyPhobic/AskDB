# AskDB

Ask your database anything. Natural language to SQL desktop app for PostgreSQL, MySQL, and SQLite.

Built with PySide6 (Qt) for UI, SQLAlchemy for database access, and LangChain + OpenAI for NL→SQL.

## Quick start (desktop)

1) Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r desktop_requirements.txt
```

2) Run the desktop app

```bash
python /Users/Harsh/Desktop/SideProjects/AiSql/desktop_app.py
```

3) In the app

- Open Settings to set your `OPENAI_API_KEY` and preferred model (default: `gpt-4o-mini`).
- Create/Test/Save a database connection, then Connect.
- Chat with the AI; generated SQL appears on the right and results below.

## Configuration

- `OPENAI_API_KEY`: required for NL→SQL. Can be entered in Settings or sourced from the environment.
- Optional LangSmith tracing is supported via Settings; the app sets the corresponding env vars (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`) when enabled.
- Database configuration is managed in-app and persisted to `~/.aisql`.

## Supported databases

- PostgreSQL (`psycopg2`), MySQL (`pymysql`), SQLite

## Project structure

- `desktop_app.py`: PySide6 bootstrapper (creates the Qt app and main window)
- `ui/`: Qt UI components (`main_window.py`, `query_tab.py`, dialogs, theme, widgets)
- `services/`: agent and DB services (`agent_service.py`, `db_service.py`)
- `core/`: simple JSON-backed stores for settings, saved connections, recents
- `db_util.py`: engine adapters/factory (postgres/mysql/sqlite), multiton engine cache, connection test
- `app.py`: examples for creating engines and testing connectivity
- `requirements.txt`, `desktop_requirements.txt`: Python dependencies
- `assets/`: icons and images used by the UI

## Build a macOS desktop app (.app)

Use PyInstaller to package the PySide6 desktop app:

```bash
pyinstaller --noconfirm --windowed \
  --name "AskDB" \
  /Users/Harsh/Desktop/SideProjects/AiSql/desktop_app.py
```

Then launch:

```bash
open dist/AskDB.app
```

Notes:
- First run on macOS may show a Gatekeeper warning. Use right‑click → Open, or codesign/notarize for distribution.
- Build on the target architecture (Apple Silicon vs Intel) for best compatibility.
- The app inherits shell environment variables (e.g., `OPENAI_API_KEY`). You can also set values in the Settings dialog.

## Pack and ship (macOS)

The steps below produce a signed, notarized app you can distribute to users.

1) Build the app

```bash
pyinstaller --noconfirm --windowed \
  --name "AskDB" \
  /Users/Harsh/Desktop/SideProjects/AiSql/desktop_app.py

# Alternatively, use the provided spec file
pyinstaller AskDB.spec
```

Output: `dist/AskDB.app`

2) (Optional) Set a custom app icon

```bash
# Use an .icns file; you can pass it during build or edit the spec
pyinstaller --noconfirm --windowed \
  --icon /path/to/icon.icns \
  --name "AskDB" \
  /Users/Harsh/Desktop/SideProjects/AiSql/desktop_app.py
```

3) Codesign the app (Developer ID required)

```bash
APP="dist/AskDB.app"
IDENTITY="Developer ID Application: Your Name (TEAMID)"

codesign --deep --force --verify --options runtime \
  --sign "$IDENTITY" "$APP"

codesign --verify --deep --strict --verbose=2 "$APP"
spctl -a -vv "$APP"
```

4) Notarize with Apple

```bash
# Use an app-specific password or keychain profile
xcrun notarytool submit "$APP" \
  --apple-id YOUR_APPLE_ID \
  --team-id TEAMID \
  --password YOUR_APP_SPECIFIC_PW \
  --wait

# Staple the ticket
xcrun stapler staple "$APP"
```

5) Create an archive for distribution

```bash
# Zip
(cd dist && zip -r AskDB-macOS.zip "AskDB.app")

# Or DMG
hdiutil create -volname "AskDB" -srcfolder dist/AskDB.app -ov -format UDZO dist/AskDB.dmg
```

6) Ship it

- Upload `AskDB-macOS.zip` or `AskDB.dmg` to a GitHub Release (or your website).
- In release notes, include minimum macOS version and architecture (arm64/x86_64) if relevant.

Tips:
- To change the bundle metadata (name, icon) permanently, update the spec file (`AskDB.spec`).
- Test on a clean macOS user and network environment to verify Gatekeeper behavior post‑notarization.

## Distribute without signing (no Developer ID)

You can share the app unsigned, but macOS Gatekeeper will warn/block until users approve it.

Build and package (unsigned):

```bash
pyinstaller AskDB.spec

(cd dist && zip -r AskDB-unsigned.zip "AskDB.app")
# or create a DMG
hdiutil create -volname "AskDB" -srcfolder dist/AskDB.app -ov -format UDZO dist/AskDB-unsigned.dmg
```

What users must do on first run:

- Right‑click the app → Open → Open, or
- System Settings → Privacy & Security → click "Open Anyway" for AskDB, or
- Terminal (advanced):
  ```bash
  xattr -dr com.apple.quarantine /Applications/AskDB.app
  ```

Notes:
- Managed Macs may block unidentified developers entirely.
- Each fresh download is quarantined, so users may need to repeat approval after re‑downloading.
- Self‑signed certificates do not satisfy Gatekeeper; only Developer ID + notarization removes prompts.

## Legacy Streamlit/Docker

This repository previously included a Streamlit UI and Docker instructions. The current version focuses on the native PySide6 desktop app. The provided `Dockerfile` still references a Streamlit entrypoint (`streamlit_app.py`) which is not part of this version and is kept only for historical context.

