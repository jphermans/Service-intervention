# Atlas Copco Intervention Report — Start Here

This folder is the portable, offline launch point for the app.

## 1) Start the app

### macOS
Double-click:

```text
launch-macos.command
```

### Windows
Double-click:

```text
launch-windows.bat
```

### Shell
From the project root:

```bash
./serve.sh
```

The app will start a local server on `127.0.0.1:8000` by default and store data in:

```text
./data/intervention_reports.sqlite3
```

## 2) Bundled runtime layout

If you want this to work on a machine with no Python installed, place a portable interpreter here:

```text
runtime/python/bin/python3   # macOS / Linux
runtime/python/python.exe    # Windows
```

The launchers check those locations first, then fall back to `INTERVENTION_PYTHON`, then system Python.

## 3) How to retrieve records from the database

Each saved report is stored as one row in the `reports` table.
The report itself is saved as JSON in the `data` column.

### Show all saved report IDs

```bash
sqlite3 ./data/intervention_reports.sqlite3 \
  "SELECT id, created_at, updated_at FROM reports ORDER BY sort_order, created_at;"
```

### Get one report by ID

Replace `ABC123` with the report ID:

```bash
sqlite3 ./data/intervention_reports.sqlite3 \
  "SELECT data FROM reports WHERE id='ABC123';"
```

### Pretty-print the JSON for one report

```bash
sqlite3 ./data/intervention_reports.sqlite3 \
  "SELECT data FROM reports WHERE id='ABC123';" | python3 -m json.tool
```

### Export all reports as JSON

If the server is running, you can also use the API:

```bash
curl -s http://127.0.0.1:8000/api/reports | python3 -m json.tool
```

### Retrieve one report through the API

```bash
curl -s http://127.0.0.1:8000/api/reports/ABC123 | python3 -m json.tool
```

## 4) Open, edit, and print a saved report

In the app, use the **Saved Reports** section:

1. Click **Open** on a saved card.
2. The form loads that exact report.
3. The save button changes to **Update Report**.
4. Print if needed, then save again to update the **same Report ID**.

Use **Clone** only when you want a new report based on an old one.

## 5) What to back up

For a full portable backup, copy these folders/files together:

- `data/` — the SQLite database with all saved reports
- `runtime/` — optional bundled Python runtime
- the app files (`index.html`, `server.py`, `serve.sh`, launchers, icons, etc.)

## 5) Quick rule of thumb

- **Need to work offline on the stick?** Use the launchers.
- **Need the records?** Open `./data/intervention_reports.sqlite3` with `sqlite3` or use the API while the app is running.
- **Need a machine with no Python?** Bundle a runtime under `runtime/python/`.
