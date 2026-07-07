#!/usr/bin/env python3
"""Local static + SQLite server for the intervention report app."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sqlite3
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from uuid import uuid4


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DEFAULT_DB = DATA_DIR / "intervention_reports.sqlite3"
MAX_BODY_BYTES = 100 * 1024 * 1024


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class ReportStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_sort ON reports(sort_order)")

    def list_reports(self) -> list[dict]:
        with self.lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT data FROM reports ORDER BY sort_order ASC, created_at ASC"
            ).fetchall()
        reports = []
        for row in rows:
            try:
                reports.append(json.loads(row["data"]))
            except json.JSONDecodeError:
                continue
        return reports

    def get_report(self, report_id: str) -> Optional[dict]:
        with self.lock, self._connect() as conn:
            row = conn.execute("SELECT data FROM reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            return None
        return json.loads(row["data"])

    def save_report(self, report: dict) -> dict:
        if not isinstance(report, dict):
            raise ValueError("Report must be an object")
        report = dict(report)
        report_id = str(report.get("id") or uuid4().hex[:6].upper())
        report["id"] = report_id
        data = json.dumps(report, ensure_ascii=False, separators=(",", ":"))
        now = utc_now()
        with self.lock, self._connect() as conn:
            row = conn.execute(
                "SELECT sort_order, created_at FROM reports WHERE id = ?", (report_id,)
            ).fetchone()
            if row:
                sort_order = row["sort_order"]
                created_at = row["created_at"]
            else:
                max_row = conn.execute("SELECT COALESCE(MAX(sort_order), -1) AS max_order FROM reports").fetchone()
                sort_order = int(max_row["max_order"]) + 1
                created_at = now
            conn.execute(
                """
                INSERT INTO reports (id, data, sort_order, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    data = excluded.data,
                    sort_order = excluded.sort_order,
                    updated_at = excluded.updated_at
                """,
                (report_id, data, sort_order, created_at, now),
            )
        return report

    def replace_reports(self, reports: list[dict]) -> list[dict]:
        cleaned = self._clean_reports(reports)
        now = utc_now()
        with self.lock, self._connect() as conn:
            conn.execute("DELETE FROM reports")
            for sort_order, report in enumerate(cleaned):
                conn.execute(
                    """
                    INSERT INTO reports (id, data, sort_order, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        report["id"],
                        json.dumps(report, ensure_ascii=False, separators=(",", ":")),
                        sort_order,
                        now,
                        now,
                    ),
                )
        return cleaned

    def merge_reports(self, reports: list[dict]) -> list[dict]:
        existing = self.list_reports()
        existing_ids = {r.get("id") for r in existing if r.get("id")}
        merged = list(existing)
        for report in self._clean_reports(reports, existing_ids):
            if report["id"] in existing_ids:
                continue
            existing_ids.add(report["id"])
            merged.append(report)
        return self.replace_reports(merged)

    def delete_report(self, report_id: str) -> bool:
        with self.lock, self._connect() as conn:
            cur = conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        return cur.rowcount > 0

    def clear(self) -> None:
        with self.lock, self._connect() as conn:
            conn.execute("DELETE FROM reports")

    def _clean_reports(self, reports: list[dict], existing_ids: Optional[set[str]] = None) -> list[dict]:
        if not isinstance(reports, list):
            raise ValueError("reports must be an array")
        used = set(existing_ids or set())
        cleaned = []
        for item in reports:
            if not isinstance(item, dict):
                continue
            report = dict(item)
            report_id = str(report.get("id") or uuid4().hex[:6].upper())
            while report_id in used:
                report_id = uuid4().hex[:6].upper()
            used.add(report_id)
            report["id"] = report_id
            cleaned.append(report)
        return cleaned


class Handler(SimpleHTTPRequestHandler):
    server_version = "InterventionServer/1.0"

    def __init__(self, *args, directory: Optional[str] = None, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    @property
    def store(self) -> ReportStore:
        return self.server.store  # type: ignore[attr-defined]

    def end_headers(self) -> None:
        if self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path = self._path()
        if path == "/api/health":
            return self._json({"ok": True, "database": str(self.store.db_path), "reports": len(self.store.list_reports())})
        if path == "/api/reports":
            return self._json({"reports": self.store.list_reports()})
        if path == "/api/export":
            reports = self.store.list_reports()
            return self._json(
                {
                    "exportType": "tightening-intervention-backup",
                    "exportVersion": 1,
                    "exportedAt": utc_now(),
                    "count": len(reports),
                    "reports": reports,
                }
            )
        if path.startswith("/api/reports/"):
            report = self.store.get_report(urllib.parse.unquote(path.rsplit("/", 1)[-1]))
            if not report:
                return self._error(404, "Report not found")
            return self._json({"report": report})
        return super().do_GET()

    def do_POST(self) -> None:
        path = self._path()
        try:
            if path == "/api/reports":
                data = self._read_json()
                report = data.get("report", data) if isinstance(data, dict) else data
                return self._json({"report": self.store.save_report(report)}, status=201)
            if path == "/api/import":
                data = self._read_json()
                reports = data if isinstance(data, list) else data.get("reports", [])
                mode = "merge" if isinstance(data, list) else data.get("mode", "merge")
                saved = self.store.replace_reports(reports) if mode == "replace" else self.store.merge_reports(reports)
                return self._json({"reports": saved, "count": len(saved)})
        except ValueError as exc:
            return self._error(400, str(exc))
        return self._error(404, "API endpoint not found")

    def do_PUT(self) -> None:
        path = self._path()
        try:
            if path.startswith("/api/reports/"):
                report_id = urllib.parse.unquote(path.rsplit("/", 1)[-1])
                data = self._read_json()
                report = data.get("report", data) if isinstance(data, dict) else data
                if not isinstance(report, dict):
                    return self._error(400, "Report must be an object")
                report["id"] = report_id
                return self._json({"report": self.store.save_report(report)})
        except ValueError as exc:
            return self._error(400, str(exc))
        return self._error(404, "API endpoint not found")

    def do_DELETE(self) -> None:
        path = self._path()
        if path == "/api/reports":
            self.store.clear()
            return self._json({"ok": True, "reports": []})
        if path.startswith("/api/reports/"):
            deleted = self.store.delete_report(urllib.parse.unquote(path.rsplit("/", 1)[-1]))
            return self._json({"ok": deleted})
        return self._error(404, "API endpoint not found")

    def translate_path(self, path: str) -> str:
        translated = super().translate_path(path)
        root = str(ROOT.resolve())
        resolved = str(Path(translated).resolve())
        if not resolved.startswith(root):
            return root
        return translated

    def guess_type(self, path: str) -> str:
        if path.endswith(".webmanifest"):
            return "application/manifest+json"
        return mimetypes.guess_type(path)[0] or super().guess_type(path)

    def _path(self) -> str:
        return urllib.parse.urlparse(self.path).path

    def _read_json(self) -> dict | list:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > MAX_BODY_BYTES:
            raise ValueError("Request body is too large")
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc.msg}") from exc

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str) -> None:
        self._json({"error": message}, status=status)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), fmt % args))


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the intervention app with a local SQLite JSON API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", type=Path, default=Path(os.environ.get("INTERVENTION_DB", DEFAULT_DB)))
    parser.add_argument("--open-browser", action="store_true")
    args = parser.parse_args()

    store = ReportStore(args.db.resolve())
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    httpd.store = store  # type: ignore[attr-defined]
    url = f"http://{args.host}:{args.port}/"

    print("Atlas Copco Intervention Report - Local Server")
    print(f"Serving:  {ROOT}")
    print(f"Database: {store.db_path}")
    print(f"URL:      {url}")
    print("Stop:     Ctrl+C")

    if args.open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
