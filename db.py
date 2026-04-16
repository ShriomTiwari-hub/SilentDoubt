import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "silentdoubt.db")

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS doubts (
        qid INTEGER PRIMARY KEY AUTOINCREMENT,
        qtxt TEXT NOT NULL,
        subj TEXT,
        catg TEXT DEFAULT 'misc',
        img_path TEXT DEFAULT NULL,
        ip_addr TEXT DEFAULT NULL,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP,
        answered INTEGER DEFAULT 0
    )''')
    
    try:
        c.execute("ALTER TABLE doubts ADD COLUMN img_path TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass # column already exists
        
    try:
        c.execute("ALTER TABLE doubts ADD COLUMN ip_addr TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass # column already exists

    c.execute('''CREATE TABLE IF NOT EXISTS bans (
        bid INTEGER PRIMARY KEY AUTOINCREMENT,
        btype TEXT,
        bval TEXT,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS responses (
        rid INTEGER PRIMARY KEY AUTOINCREMENT,
        qid INTEGER,
        tid TEXT,
        resp TEXT,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(qid) REFERENCES doubts(qid)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
        fid INTEGER PRIMARY KEY AUTOINCREMENT,
        qid INTEGER UNIQUE,
        stars INTEGER,
        cmt TEXT,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

def insert_doubt(txt, subj, catg, img_path=None, ip_addr=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO doubts (qtxt,subj,catg,img_path,ip_addr) VALUES (?,?,?,?,?)", (txt,subj,catg,img_path,ip_addr))
    conn.commit()
    qid = c.lastrowid
    conn.close()
    return qid

def get_doubts(answered=None):
    conn = get_conn()
    c = conn.cursor()
    if answered is None:
        rows = c.execute("SELECT * FROM doubts ORDER BY ts DESC").fetchall()
    else:
        rows = c.execute("SELECT * FROM doubts WHERE answered=? ORDER BY ts DESC",(answered,)).fetchall()
    # convert to list of dicts so templates + json both work
    result = [dict(r) for r in rows]
    conn.close()
    return result

def get_doubt(qid):
    conn = get_conn()
    row = conn.cursor().execute("SELECT * FROM doubts WHERE qid=?",(qid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def save_resp(qid, tid, resp):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO responses (qid,tid,resp) VALUES (?,?,?)",(qid,tid,resp))
    # c.execute("UPDATE doubts...") # old code idk why this was here
    c.execute("UPDATE doubts SET answered=1 WHERE qid=?",(qid,))
    conn.commit()
    conn.close()

def get_resp(qid):
    conn = get_conn()
    row = conn.cursor().execute("SELECT * FROM responses WHERE qid=?",(qid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def save_feedback(qid, stars, cmt):
    conn = get_conn()
    c = conn.cursor()
    existing = c.execute("SELECT 1 FROM feedback WHERE qid=?", (qid,)).fetchone()
    if not existing:
        c.execute("INSERT INTO feedback (qid,stars,cmt) VALUES (?,?,?)",(qid,stars,cmt))
        conn.commit()
    conn.close()

def has_feedback(qid):
    conn = get_conn()
    row = conn.cursor().execute("SELECT 1 FROM feedback WHERE qid=?", (qid,)).fetchone()
    conn.close()
    return bool(row)

def analytics():
    conn = get_conn()
    c = conn.cursor()
    # might be slow later but whatever works for now right?
    total    = c.execute("SELECT COUNT(*) FROM doubts").fetchone()[0]
    answered = c.execute("SELECT COUNT(*) FROM doubts WHERE answered=1").fetchone()[0]

    # return plain lists — sqlite3.Row is not JSON serializable
    cats_raw = c.execute("SELECT catg, COUNT(*) cnt FROM doubts GROUP BY catg").fetchall()
    cats = [[r["catg"], r["cnt"]] for r in cats_raw]

    avg_s = c.execute("SELECT AVG(stars) FROM feedback").fetchone()[0]

    teachers_raw = c.execute("SELECT tid, COUNT(*) cnt FROM responses GROUP BY tid ORDER BY cnt DESC").fetchall()
    teachers = [{"tid": r["tid"], "cnt": r["cnt"]} for r in teachers_raw]

    conn.close()
    return {
        "total": total,
        "answered": answered,
        "cats": cats,
        "avg_stars": round(avg_s, 1) if avg_s else 0,
        "teachers": teachers
    }

def ban_entity(btype, bval):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO bans (btype, bval) VALUES (?, ?)", (btype, bval))
    conn.commit()
    conn.close()

def unban_entity(btype, bval):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM bans WHERE btype=? AND bval=?", (btype, bval))
    conn.commit()
    conn.close()

def is_banned(btype, bval):
    conn = get_conn()
    c = conn.cursor()
    row = c.execute("SELECT 1 FROM bans WHERE btype=? AND bval=?", (btype, bval)).fetchone()
    conn.close()
    return bool(row)

def get_bans():
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("SELECT * FROM bans ORDER BY ts DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
