# systems/db_manager.py
import sqlite3, os, datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "db.sqlite3")

# ---------- DB helpers ----------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _col_exists(cur, table, col):
    cur.execute("PRAGMA table_info(%s)" % table)
    cols = [r["name"] for r in cur.fetchall()]
    return col in cols

# ---------- Init & Migration ----------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # base players table (legacy may have high_score only)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            high_score INTEGER DEFAULT 0,
            score_time TEXT
        )
    """)

    # words table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE,
            meaning TEXT,
            audio_path TEXT,
            length INTEGER
        )
    """)

    # Add mode-specific columns if missing
    if not _col_exists(cur, "players", "mode1_high_score"):
        try:
            cur.execute("ALTER TABLE players ADD COLUMN mode1_high_score INTEGER DEFAULT NULL")
            cur.execute("ALTER TABLE players ADD COLUMN mode1_score_time TEXT DEFAULT NULL")
        except Exception:
            pass

    if not _col_exists(cur, "players", "mode2_high_score"):
        try:
            cur.execute("ALTER TABLE players ADD COLUMN mode2_high_score INTEGER DEFAULT NULL")
            cur.execute("ALTER TABLE players ADD COLUMN mode2_score_time TEXT DEFAULT NULL")
        except Exception:
            pass

    # If legacy high_score exists, move it into mode1_high_score when mode1_high_score is null
    try:
        cur.execute("SELECT id, high_score, mode1_high_score FROM players")
        rows = cur.fetchall()
        for r in rows:
            hs = r["high_score"] if r["high_score"] is not None else 0
            if r["mode1_high_score"] is None:
                cur.execute("UPDATE players SET mode1_high_score = ? WHERE id = ?", (hs, r["id"]))
        conn.commit()
    except Exception:
        # ignore migration problems but keep DB usable
        pass

    conn.commit()
    conn.close()

# initialize on import
init_db()


# ---------------- PLAYERS API ----------------
def add_player(name):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO players (name) VALUES (?)", (name,))
        conn.commit()
    except Exception:
        pass
    conn.close()

def delete_player(name):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM players WHERE name=?", (name,))
    conn.commit()
    conn.close()

def get_all_players():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM players ORDER BY name ASC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_high_score(name, score, mode="mode1"):
    """
    Update player's high score for the given mode if score is greater than previous.
    mode must be 'mode1' or 'mode2' (string).
    """
    if mode not in ("mode1", "mode2"):
        raise ValueError("mode must be 'mode1' or 'mode2'")

    score_col = f"{mode}_high_score"
    time_col = f"{mode}_score_time"

    conn = get_connection(); cur = conn.cursor()
    cur.execute(f"SELECT {score_col} FROM players WHERE name=?", (name,))
    row = cur.fetchone()

    if row is None:
        conn.close()
        return

    prev = row[score_col] if row[score_col] is not None else 0
    if score > prev:
        cur.execute(f"""
            UPDATE players
            SET {score_col}=?,
                {time_col}=?
            WHERE name=?
        """, (score, datetime.datetime.now().isoformat(), name))
        conn.commit()
    conn.close()

def get_leaderboard(mode="mode1", limit=10):
    if mode not in ("mode1", "mode2"):
        raise ValueError("mode must be 'mode1' or 'mode2'")
    score_col = f"{mode}_high_score"
    conn = get_connection(); cur = conn.cursor()
    cur.execute(f"SELECT name, {score_col} as high_score, {mode}_score_time as score_time FROM players ORDER BY {score_col} DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------- WORDS API ----------------
def insert_word(word, meaning, audio_path):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT OR IGNORE INTO words (word, meaning, audio_path, length)
            VALUES (?, ?, ?, ?)
        """, (word.upper(), meaning, audio_path, len(word)))
        conn.commit()
    except Exception as e:
        print("Word insert error:", e)
    conn.close()

def get_word_of_length(length):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT * FROM words
        WHERE length=?
        ORDER BY RANDOM()
        LIMIT 1
    """, (length,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def count_words():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM words")
    total = cur.fetchone()["total"]
    conn.close()
    return total

def clear_words():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM words")
    conn.commit()
    conn.close()
