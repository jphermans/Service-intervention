# USB-stick packaging checklist

Use this checklist when you want to hand the app to someone on a stick.

## Files to include
- `index.html`
- `index.js`
- `server.py`
- `serve.sh`
- `launch-macos.command`
- `launch-windows.bat`
- `launch-windows.ps1`
- `manifest.json`
- `sw.js`
- `icons/`
- `runtime/` *(optional bundled Python runtime)*
- `data/` *(created automatically at first run)*

## If you want fully offline/no-install
Bundle a Python runtime in one of these places:
- macOS/Linux: `runtime/python/bin/python3`
- Windows: `runtime/python/python.exe`

The launchers will look there first.

## Before copying to the stick
- Keep the folder structure intact.
- Do not rename `server.py` or the launchers.
- Ensure the macOS launcher is executable: `chmod +x launch-macos.command`.
- Test once on each target OS.

## On first run
- The app creates `data/intervention_reports.sqlite3` automatically.
- Saved reports live in that local SQLite file.
- If Python is missing, the launcher shows a clear message instead of failing silently.
