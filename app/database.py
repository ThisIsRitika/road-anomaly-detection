import sqlite3, json
from datetime import datetime
from .config import DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS analyses (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            uid           TEXT    NOT NULL UNIQUE,
            created_at    TEXT    NOT NULL,
            file_type     TEXT    NOT NULL,
            original_name TEXT,
            severity      TEXT    NOT NULL,
            total_objects INTEGER NOT NULL DEFAULT 0,
            hazards       INTEGER NOT NULL DEFAULT 0,
            vehicles      INTEGER NOT NULL DEFAULT 0,
            alert_count   INTEGER NOT NULL DEFAULT 0,
            result_url    TEXT,
            original_url  TEXT,
            thumb_url     TEXT,
            pdf_id        TEXT,
            counts_json   TEXT,
            conf_json     TEXT,
            alerts_json   TEXT
        );
        CREATE TABLE IF NOT EXISTS batch_files (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_uid    TEXT NOT NULL,
            filename     TEXT NOT NULL,
            result_url   TEXT,
            original_url TEXT,
            counts_json  TEXT,
            conf_json    TEXT,
            alerts_json  TEXT,
            FOREIGN KEY (batch_uid) REFERENCES analyses(uid)
        );
    """)
    conn.commit()
    conn.close()


def save_analysis(uid, file_type, original_name, counts, alerts,
                  conf_summary, result_url, original_url,
                  thumb_url=None, pdf_id=None):
    hazards  = counts.get("RoadDamages", 0) + counts.get("UnsurfacedRoad", 0)
    vehicles = counts.get("HMV", 0) + counts.get("LMV", 0)
    total    = sum(counts.values())
    severity = "critical" if hazards >= 3 else ("moderate" if hazards > 0 else "low")
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO analyses
          (uid,created_at,file_type,original_name,severity,
           total_objects,hazards,vehicles,alert_count,
           result_url,original_url,thumb_url,pdf_id,
           counts_json,conf_json,alerts_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (uid, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file_type,
          original_name, severity, total, hazards, vehicles, len(alerts),
          result_url, original_url, thumb_url, pdf_id,
          json.dumps(counts), json.dumps(conf_summary), json.dumps(alerts)))
    conn.commit()
    conn.close()


def save_batch_files(batch_uid, results_list):
    conn = get_db()
    for r in results_list:
        conn.execute("""
            INSERT INTO batch_files
              (batch_uid,filename,result_url,original_url,
               counts_json,conf_json,alerts_json)
            VALUES (?,?,?,?,?,?,?)
        """, (batch_uid, r["filename"], r["result_url"], r["original_url"],
              json.dumps(r["counts"]), json.dumps(r["conf_summary"]),
              json.dumps(r["alerts"])))
    conn.commit()
    conn.close()


def get_history(limit=12, offset=0, severity=None, file_type=None, search=None):
    conn  = get_db()
    where, args = [], []
    if severity:  where.append("severity=?");           args.append(severity)
    if file_type: where.append("file_type=?");          args.append(file_type)
    if search:    where.append("original_name LIKE ?"); args.append(f"%{search}%")
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    rows  = conn.execute(
        f"SELECT * FROM analyses {clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        args + [limit, offset]).fetchall()
    total = conn.execute(
        f"SELECT COUNT(*) FROM analyses {clause}", args).fetchone()[0]
    conn.close()
    return [dict(r) for r in rows], total


def get_analysis_detail(uid):
    conn = get_db()
    row  = conn.execute("SELECT * FROM analyses WHERE uid=?", (uid,)).fetchone()
    if not row:
        conn.close()
        return None
    d = dict(row)
    d["counts"]       = json.loads(d["counts_json"]  or "{}")
    d["conf_summary"] = json.loads(d["conf_json"]    or "{}")
    d["alerts"]       = json.loads(d["alerts_json"]  or "[]")
    if d["file_type"] == "batch":
        children = conn.execute(
            "SELECT * FROM batch_files WHERE batch_uid=?", (uid,)).fetchall()
        d["batch_files"] = []
        for c in children:
            cd = dict(c)
            cd["counts"]       = json.loads(cd["counts_json"] or "{}")
            cd["conf_summary"] = json.loads(cd["conf_json"]   or "{}")
            cd["alerts"]       = json.loads(cd["alerts_json"] or "[]")
            d["batch_files"].append(cd)
    conn.close()
    return d


def get_stats():
    conn = get_db()
    row  = conn.execute("""
        SELECT
          COUNT(*)                          AS total_analyses,
          COALESCE(SUM(total_objects),0)    AS total_objects,
          COALESCE(SUM(hazards),0)          AS total_hazards,
          COALESCE(SUM(vehicles),0)         AS total_vehicles,
          COALESCE(SUM(alert_count),0)      AS total_alerts,
          COUNT(CASE WHEN severity='critical' THEN 1 END) AS critical_count,
          COUNT(CASE WHEN file_type='image'   THEN 1 END) AS image_count,
          COUNT(CASE WHEN file_type='video'   THEN 1 END) AS video_count,
          COUNT(CASE WHEN file_type='batch'   THEN 1 END) AS batch_count
        FROM analyses
    """).fetchone()
    trend = conn.execute("""
        SELECT DATE(created_at) AS day,
               COUNT(*)         AS runs,
               COALESCE(SUM(hazards),0) AS hazards
        FROM analyses
        WHERE created_at >= DATE('now','-6 days')
        GROUP BY day ORDER BY day
    """).fetchall()
    conn.close()
    return dict(row), [dict(t) for t in trend]


def delete_analysis(uid):
    conn = get_db()
    conn.execute("DELETE FROM batch_files WHERE batch_uid=?", (uid,))
    conn.execute("DELETE FROM analyses    WHERE uid=?",       (uid,))
    conn.commit()
    conn.close()