import sqlite3
from datetime import datetime
from typing import Optional, List
from .config import DB_PATH, REGION_NAME, SEASON_ID

def _db():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL;")
    con.row_factory = sqlite3.Row
    return con

def _column_exists(con, table, column):
    cur = con.execute(f"PRAGMA table_info({table})")
    return any(r[1] == column for r in cur.fetchall())

def init_db():
    con = _db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      tg_id      INTEGER PRIMARY KEY,
      full_name  TEXT,
      username   TEXT,
      phone      TEXT,
      region     TEXT,
      score      INTEGER DEFAULT 0,
      created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS votes(
      id            INTEGER PRIMARY KEY AUTOINCREMENT,
      tg_id         INTEGER,
      season_id     TEXT,
      region        TEXT,
      proof_file_id TEXT,
      status        TEXT DEFAULT 'pending',
      created_at    TEXT
    );
    CREATE TABLE IF NOT EXISTS audits(
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      tg_id      INTEGER,
      action     TEXT,
      meta       TEXT,
      created_at TEXT
    );
    """)
    if not _column_exists(con, "votes", "phone"):
        con.execute("ALTER TABLE votes ADD COLUMN phone TEXT")
    con.commit(); con.close()

def audit(tg_id: int, action: str, meta: str = ""):
    con = _db()
    con.execute("INSERT INTO audits(tg_id, action, meta, created_at) VALUES (?,?,?,?)",
                (tg_id, action, meta, datetime.utcnow().isoformat()))
    con.commit(); con.close()

def upsert_user(u, phone: Optional[str]=None, region: Optional[str]=None):
    con = _db()
    cur = con.cursor()
    cur.execute("SELECT 1 FROM users WHERE tg_id=?", (u.id,))
    if cur.fetchone():
        cur.execute("UPDATE users SET full_name=?, username=? WHERE tg_id=?",
                    (u.full_name, u.username or "", u.id))
        if phone is not None:
            cur.execute("UPDATE users SET phone=? WHERE tg_id=?", (phone, u.id))
        if region is not None:
            cur.execute("UPDATE users SET region=? WHERE tg_id=?", (region, u.id))
    else:
        cur.execute("""INSERT INTO users(tg_id, full_name, username, phone, region, created_at)
                       VALUES (?,?,?,?,?,?)""",
                    (u.id, u.full_name, u.username or "", phone or "",
                     region or REGION_NAME, datetime.utcnow().isoformat()))
    con.commit(); con.close()

def add_vote(tg_id: int, file_id: str, phone: str) -> int:
    con = _db()
    con.execute("""INSERT INTO votes(tg_id, season_id, region, proof_file_id, status, created_at, phone)
                   VALUES (?,?,?,?,?,?,?)""",
                (tg_id, SEASON_ID, REGION_NAME, file_id, "pending", datetime.utcnow().isoformat(), phone))
    vote_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.commit(); con.close()
    audit(tg_id, "vote_submitted", f"id={vote_id}, phone={phone}")
    return vote_id

def approve_vote(vote_id: int) -> str:
    con = _db()
    v = con.execute("SELECT tg_id, season_id, status, phone FROM votes WHERE id=?", (vote_id,)).fetchone()
    if not v:
        con.close(); return "not_found"
    if v["status"] != "pending":
        con.close(); return "not_pending"

    if v["phone"]:
        dup = con.execute("""SELECT 1 FROM votes
                             WHERE season_id=? AND phone=? AND status='approved'""",
                          (v["season_id"], v["phone"])).fetchone()
        if dup:
            con.execute("UPDATE votes SET status='rejected' WHERE id=?", (vote_id,))
            con.commit(); con.close()
            audit(v["tg_id"], "vote_rejected_dup_phone", f"id={vote_id}, phone={v['phone']}")
            return "dup_phone"

    con.execute("UPDATE votes SET status='approved' WHERE id=?", (vote_id,))
    con.execute("UPDATE users SET score = COALESCE(score,0) + 1 WHERE tg_id=?", (v["tg_id"],))
    con.commit(); con.close()
    audit(v["tg_id"], "vote_approved", f"id={vote_id}, phone={v['phone']}")
    return "ok"

def reject_vote(vote_id: int) -> str:
    con = _db()
    r = con.execute("UPDATE votes SET status='rejected' WHERE id=? AND status='pending'", (vote_id,))
    con.commit(); con.close()
    return "ok" if r.rowcount else "not_pending"

def top_rows(limit: int = 10) -> List[sqlite3.Row]:
    con = _db()
    rows = con.execute("""SELECT full_name, username, score
                          FROM users WHERE COALESCE(score,0)>0
                          ORDER BY score DESC, full_name ASC LIMIT ?""", (limit,)).fetchall()
    con.close(); return rows

def pending_rows(limit: int = 30) -> List[sqlite3.Row]:
    con = _db()
    rows = con.execute("""SELECT id, tg_id, created_at
                          FROM votes WHERE status='pending'
                          ORDER BY id ASC LIMIT ?""", (limit,)).fetchall()
    con.close(); return rows

def approved_votes_detail(limit: int = 30, offset: int = 0, season_only: bool = True):
    con = _db()
    if season_only:
        sql = """
        SELECT v.id, v.created_at, v.season_id, v.phone,
               u.tg_id, u.full_name, u.username
        FROM votes v
        JOIN users u ON u.tg_id = v.tg_id
        WHERE v.status='approved' AND v.season_id=?
        ORDER BY v.id DESC
        LIMIT ? OFFSET ?
        """
        rows = con.execute(sql, (SEASON_ID, limit, offset)).fetchall()
    else:
        sql = """
        SELECT v.id, v.created_at, v.season_id, v.phone,
               u.tg_id, u.full_name, u.username
        FROM votes v
        JOIN users u ON u.tg_id = v.tg_id
        WHERE v.status='approved'
        ORDER BY v.id DESC
        LIMIT ? OFFSET ?
        """
        rows = con.execute(sql, (limit, offset)).fetchall()
    con.close()
    return rows

def top_users_detail(limit: int = 20, season_only: bool = True):
    con = _db()
    if season_only:
        sql = """
        SELECT u.tg_id, u.full_name, u.username,
               COUNT(*) AS votes,
               GROUP_CONCAT(DISTINCT COALESCE(v.phone,'')) AS phones
        FROM votes v
        JOIN users u ON u.tg_id = v.tg_id
        WHERE v.status='approved' AND v.season_id=?
        GROUP BY u.tg_id, u.full_name, u.username
        ORDER BY votes DESC, u.full_name ASC
        LIMIT ?
        """
        rows = con.execute(sql, (SEASON_ID, limit)).fetchall()
    else:
        sql = """
        SELECT u.tg_id, u.full_name, u.username,
               COUNT(*) AS votes,
               GROUP_CONCAT(DISTINCT COALESCE(v.phone,'')) AS phones
        FROM votes v
        JOIN users u ON u.tg_id = v.tg_id
        WHERE v.status='approved'
        GROUP BY u.tg_id, u.full_name, u.username
        ORDER BY votes DESC, u.full_name ASC
        LIMIT ?
        """
        rows = con.execute(sql, (limit,)).fetchall()
    con.close()
    return rows

def export_votes_csv(season_only: bool = True) -> str:
    import io, csv
    con = _db()
    if season_only:
        sql = """
        SELECT v.id, v.created_at, v.season_id, v.phone,
               u.tg_id, u.full_name, u.username
        FROM votes v
        JOIN users u ON u.tg_id = v.tg_id
        WHERE v.status='approved' AND v.season_id=?
        ORDER BY v.id DESC
        """
        cur = con.execute(sql, (SEASON_ID,))
    else:
        sql = """
        SELECT v.id, v.created_at, v.season_id, v.phone,
               u.tg_id, u.full_name, u.username
        FROM votes v
        JOIN users u ON u.tg_id = v.tg_id
        WHERE v.status='approved'
        ORDER BY v.id DESC
        """
        cur = con.execute(sql)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["vote_id","created_at","season_id","phone","tg_id","full_name","username"])
    for r in cur.fetchall():
        w.writerow([r["id"], r["created_at"], r["season_id"], r["phone"], r["tg_id"], r["full_name"], r["username"]])
    con.close()
    buf.seek(0)
    return buf.getvalue()
