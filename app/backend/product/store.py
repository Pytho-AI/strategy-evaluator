"""The versioned product workspace: SQLite under ``app/workspace/<workspace_id>/``.

Separate from the frozen dataset in every way: a different directory, a different id space
(``rpt_`` / ``pclm_`` / ``preq_`` / ``psrc_``), and its own version counter. ``graph_version``
increments on every accepted change to the claim set, and the overlay cache is keyed on it.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORKSPACE = "demo"
WORKSPACE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reports (
    report_id TEXT PRIMARY KEY, sha256 TEXT NOT NULL UNIQUE, filename TEXT NOT NULL,
    format TEXT NOT NULL, text TEXT NOT NULL, uploaded_at TEXT NOT NULL, actor TEXT NOT NULL,
    report_date TEXT, source_id TEXT NOT NULL, extractor TEXT NOT NULL, seq INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY, report_id TEXT NOT NULL, seq INTEGER NOT NULL,
    status TEXT NOT NULL, data TEXT NOT NULL, flags TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '[]', accepted_graph_version INTEGER, contradicts TEXT NOT NULL DEFAULT '[]',
    contradicts_reason TEXT);
CREATE TABLE IF NOT EXISTS decisions (
    decision_id TEXT PRIMARY KEY, target_type TEXT NOT NULL, target_id TEXT NOT NULL,
    decision TEXT NOT NULL, actor TEXT NOT NULL, decided_at TEXT NOT NULL, reason TEXT,
    revision TEXT NOT NULL DEFAULT '{}', seq INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS requirements (req_id TEXT PRIMARY KEY, seq INTEGER NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS planning (object_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, actor TEXT NOT NULL,
    action TEXT NOT NULL, target_type TEXT NOT NULL, target_id TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '{}');
"""


def workspace_root() -> Path:
    """Where workspaces live. ``STRATEGY_WORKSPACE_DIR`` overrides it (the tests do)."""
    configured = os.environ.get("STRATEGY_WORKSPACE_DIR")
    return Path(configured) if configured else REPO_ROOT / "app" / "workspace"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Workspace:
    """One workspace. Every method is a small SQL statement; JSON columns hold the records."""

    def __init__(self, workspace_id: str = DEFAULT_WORKSPACE) -> None:
        if not WORKSPACE_ID.match(workspace_id):
            raise ValueError(
                f"workspace id {workspace_id!r} must be 1-64 characters of "
                "letters, digits, '-' or '_'."
            )
        self.workspace_id = workspace_id
        self.dir = workspace_root() / workspace_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "workspace.db"
        with self._db() as db:
            db.executescript(SCHEMA)

    def _db(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        return db

    # ------------------------------------------------------------------ versions
    @property
    def graph_version(self) -> int:
        """Bumped on every accepted change to the claim set (SCHEMA-level evidence change)."""
        return self._version("graph_version")

    @property
    def state_version(self) -> int:
        """Bumped by every workspace write. The overlay cache key carries it, so a new draft
        requirement or a review decision shows up without waiting for a claim to be accepted."""
        return self._version("state_version")

    def _version(self, key: str) -> int:
        with self._db() as db:
            row = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return int(row["value"]) if row else 0

    def _bump(self, key: str) -> int:
        version = self._version(key) + 1
        with self._db() as db:
            db.execute(
                "INSERT INTO meta(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(version)),
            )
        return version

    def bump_graph_version(self) -> int:
        self._bump("state_version")
        return self._bump("graph_version")

    def _next(self, table: str) -> int:
        with self._db() as db:
            row = db.execute(f"SELECT COALESCE(MAX(seq), 0) + 1 AS n FROM {table}").fetchone()
        return int(row["n"])

    # ------------------------------------------------------------------ audit
    def log(
        self,
        actor: str,
        action: str,
        target_type: str,
        target_id: str,
        detail: dict | None = None,
    ) -> None:
        with self._db() as db:
            db.execute(
                "INSERT INTO audit(at, actor, action, target_type, target_id, detail) "
                "VALUES(?,?,?,?,?,?)",
                (now(), actor, action, target_type, target_id, json.dumps(detail or {})),
            )

    def audit_log(self) -> list[dict]:
        with self._db() as db:
            rows = db.execute("SELECT * FROM audit ORDER BY seq").fetchall()
        return [
            {
                "seq": r["seq"], "at": r["at"], "actor": r["actor"], "action": r["action"],
                "target_type": r["target_type"], "target_id": r["target_id"],
                "detail": json.loads(r["detail"]),
            }
            for r in rows
        ]

    # ------------------------------------------------------------------ reports
    def report_by_sha(self, sha256: str) -> dict | None:
        with self._db() as db:
            row = db.execute("SELECT * FROM reports WHERE sha256=?", (sha256,)).fetchone()
        return dict(row) if row else None

    def report(self, report_id: str) -> dict | None:
        with self._db() as db:
            row = db.execute("SELECT * FROM reports WHERE report_id=?", (report_id,)).fetchone()
        return dict(row) if row else None

    def reports(self) -> list[dict]:
        with self._db() as db:
            rows = db.execute("SELECT * FROM reports ORDER BY seq").fetchall()
        return [dict(r) for r in rows]

    def add_report(
        self,
        *,
        sha256: str,
        filename: str,
        fmt: str,
        text: str,
        actor: str,
        report_date: str | None,
        extractor: str,
    ) -> dict:
        seq = self._next("reports")
        record = {
            "report_id": f"rpt_{seq:04d}", "sha256": sha256, "filename": filename,
            "format": fmt, "text": text, "uploaded_at": now(), "actor": actor,
            "report_date": report_date, "source_id": f"psrc_{seq:04d}",
            "extractor": extractor, "seq": seq,
        }
        with self._db() as db:
            db.execute(
                "INSERT INTO reports(report_id, sha256, filename, format, text, uploaded_at, "
                "actor, report_date, source_id, extractor, seq) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                tuple(record[k] for k in (
                    "report_id", "sha256", "filename", "format", "text", "uploaded_at",
                    "actor", "report_date", "source_id", "extractor", "seq")),
            )
        self._bump("state_version")
        return record

    # ------------------------------------------------------------------ claims
    def add_claims(self, report_id: str, claims: list[dict]) -> list[dict]:
        seq = self._next("claims")
        out = []
        with self._db() as db:
            for offset, claim in enumerate(claims):
                claim_id = f"pclm_{seq + offset:04d}"
                data = dict(claim["claim"], claim_id=claim_id)
                db.execute(
                    "INSERT INTO claims(claim_id, report_id, seq, status, data, flags, notes) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (claim_id, report_id, seq + offset, "proposed", json.dumps(data),
                     json.dumps(claim["flags"]), json.dumps(claim.get("notes", []))),
                )
                out.append(self._claim_record(
                    claim_id, report_id, "proposed", data, claim["flags"],
                    notes=claim.get("notes", []),
                ))
        self._bump("state_version")
        return out

    @staticmethod
    def _claim_record(
        claim_id: str, report_id: str, status: str, data: dict, flags: list,
        accepted_graph_version: int | None = None, contradicts: list | None = None,
        contradicts_reason: str | None = None, notes: list | None = None,
    ) -> dict:
        return {
            "claim_id": claim_id, "report_id": report_id, "status": status,
            "claim": data, "flags": flags, "notes": notes or [],
            "accepted_graph_version": accepted_graph_version,
            "contradicts": contradicts or [], "contradicts_reason": contradicts_reason,
        }

    def _row_to_claim(self, row: sqlite3.Row) -> dict:
        return self._claim_record(
            row["claim_id"], row["report_id"], row["status"], json.loads(row["data"]),
            json.loads(row["flags"]), row["accepted_graph_version"],
            json.loads(row["contradicts"]), row["contradicts_reason"],
            json.loads(row["notes"]),
        )

    def claim(self, claim_id: str) -> dict | None:
        with self._db() as db:
            row = db.execute("SELECT * FROM claims WHERE claim_id=?", (claim_id,)).fetchone()
        return self._row_to_claim(row) if row else None

    def claims(self, *, report_id: str | None = None, status: str | None = None) -> list[dict]:
        sql = "SELECT * FROM claims"
        where, params = [], []
        if report_id:
            where.append("report_id=?")
            params.append(report_id)
        if status:
            where.append("status=?")
            params.append(status)
        if where:
            sql += " WHERE " + " AND ".join(where)
        with self._db() as db:
            rows = db.execute(sql + " ORDER BY seq", params).fetchall()
        return [self._row_to_claim(r) for r in rows]

    def accepted_claims(self) -> list[dict]:
        return self.claims(status="approved")

    def set_claim(
        self, claim_id: str, *, status: str, data: dict | None = None,
        accepted_graph_version: int | None = None, contradicts: list | None = None,
        contradicts_reason: str | None = None,
    ) -> dict:
        current = self.claim(claim_id)
        if current is None:
            raise KeyError(claim_id)
        data = data if data is not None else current["claim"]
        with self._db() as db:
            db.execute(
                "UPDATE claims SET status=?, data=?, accepted_graph_version=?, "
                "contradicts=?, contradicts_reason=? WHERE claim_id=?",
                (status, json.dumps(data), accepted_graph_version,
                 json.dumps(contradicts or []), contradicts_reason, claim_id),
            )
        self._bump("state_version")
        return self.claim(claim_id)

    # ------------------------------------------------------------------ decisions
    def add_decision(
        self, *, target_type: str, target_id: str, decision: str, actor: str,
        reason: str | None, revision: dict | None = None,
    ) -> dict:
        seq = self._next("decisions")
        record = {
            "decision_id": f"dec_{seq:04d}", "target_type": target_type, "target_id": target_id,
            "decision": decision, "actor": actor, "decided_at": now(), "reason": reason,
            "revision": revision or {}, "seq": seq,
        }
        with self._db() as db:
            db.execute(
                "INSERT INTO decisions(decision_id, target_type, target_id, decision, actor, "
                "decided_at, reason, revision, seq) VALUES(?,?,?,?,?,?,?,?,?)",
                (record["decision_id"], target_type, target_id, decision, actor,
                 record["decided_at"], reason, json.dumps(record["revision"]), seq),
            )
        self._bump("state_version")
        return record

    def decisions(self, target_id: str | None = None) -> list[dict]:
        sql = "SELECT * FROM decisions"
        params: list[Any] = []
        if target_id:
            sql += " WHERE target_id=?"
            params.append(target_id)
        with self._db() as db:
            rows = db.execute(sql + " ORDER BY seq", params).fetchall()
        return [dict(r, revision=json.loads(r["revision"])) for r in rows]

    # ------------------------------------------------------------------ requirements
    def add_requirement(self, record: dict) -> dict:
        seq = self._next("requirements")
        record = dict(record, req_id=f"preq_{seq:04d}")
        with self._db() as db:
            db.execute(
                "INSERT INTO requirements(req_id, seq, data) VALUES(?,?,?)",
                (record["req_id"], seq, json.dumps(record)),
            )
        self._bump("state_version")
        return record

    def requirement(self, req_id: str) -> dict | None:
        with self._db() as db:
            row = db.execute("SELECT data FROM requirements WHERE req_id=?", (req_id,)).fetchone()
        return json.loads(row["data"]) if row else None

    def requirements(self) -> list[dict]:
        with self._db() as db:
            rows = db.execute("SELECT data FROM requirements ORDER BY seq").fetchall()
        return [json.loads(r["data"]) for r in rows]

    def save_requirement(self, record: dict) -> dict:
        with self._db() as db:
            db.execute(
                "UPDATE requirements SET data=? WHERE req_id=?",
                (json.dumps(record), record["req_id"]),
            )
        self._bump("state_version")
        return record

    # ------------------------------------------------------------------ planning
    def planning_object(self, object_id: str) -> dict | None:
        with self._db() as db:
            row = db.execute(
                "SELECT data FROM planning WHERE object_id=?", (object_id,)
            ).fetchone()
        return json.loads(row["data"]) if row else None

    def planning_objects(self) -> dict[str, dict]:
        with self._db() as db:
            rows = db.execute("SELECT object_id, data FROM planning").fetchall()
        return {r["object_id"]: json.loads(r["data"]) for r in rows}

    def save_planning_object(self, object_id: str, record: dict) -> dict:
        with self._db() as db:
            db.execute(
                "INSERT INTO planning(object_id, data) VALUES(?,?) "
                "ON CONFLICT(object_id) DO UPDATE SET data=excluded.data",
                (object_id, json.dumps(record)),
            )
        self._bump("state_version")
        return record

    # ------------------------------------------------------------------ reset
    def reset(self) -> None:
        """Clear this workspace only. Never touches the dataset or another workspace."""
        root = workspace_root().resolve()
        target = self.dir.resolve()
        if target.parent != root:
            raise ValueError(f"refusing to reset {target}: not a workspace directory")
        shutil.rmtree(target, ignore_errors=True)
        self.dir.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript(SCHEMA)

    def summary(self) -> dict:
        return {
            "workspace": self.workspace_id,
            "graph_version": self.graph_version,
            "state_version": self.state_version,
            "reports": len(self.reports()),
            "proposed_claims": len(self.claims(status="proposed")),
            "accepted_claims": len(self.accepted_claims()),
            "rejected_claims": len(self.claims(status="rejected")),
            "requirements": len(self.requirements()),
            "decisions": len(self.decisions()),
            "reviewed_planning_objects": len(self.planning_objects()),
        }
