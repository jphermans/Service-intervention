# Bundled runtime layout

This folder is for an optional **portable, offline Python runtime**.
The app does **not** commit Python binaries to git, but the launchers can use
this layout when you copy a runtime onto a USB stick.

## Expected structure

```text
runtime/
├── README.md
└── python/
    ├── .gitkeep
    └── bin/
        ├── .gitkeep
        ├── python3        # macOS / Linux
        └── python.exe     # Windows
```

## Launcher lookup order

- `serve.sh` checks:
  1. `runtime/python/bin/python3`
  2. `runtime/python/bin/python`
  3. `INTERVENTION_PYTHON`
  4. system Python
- `launch-macos.command` checks:
  1. `runtime/python/bin/python3`
  2. `runtime/python/bin/python`
  3. `INTERVENTION_PYTHON`
  4. system Python
- `launch-windows.ps1` checks:
  1. `runtime\python\python.exe`
  2. `runtime\python\bin\python.exe`
  3. `INTERVENTION_PYTHON`
  4. `python3`, `python`, `py -3`

## Notes

- Keep the runtime local to the stick; do not commit the interpreter files.
- The database lives in `./data/intervention_reports.sqlite3`.
- If you bundle a runtime, test both macOS and Windows launchers once on the target OS.
- See `LAUNCH-NOTES.txt` for a quick user-facing start guide.
- See `USB-STICK-CHECKLIST.md` for the packaging checklist.
