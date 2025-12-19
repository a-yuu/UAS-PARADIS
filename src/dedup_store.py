import sqlite3
import os
import logging
import json

class DeduplicationStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Membuka koneksi database dan inisialisasi tabel."""
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        logging.info(f"DedupStore terhubung ke {self.db_path}")

    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_events (
                    topic TEXT,
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    payload TEXT
                )
            """)

    def try_insert_event(self, topic: str, event_id: str, timestamp: str, payload: dict) -> bool:
        if self.conn is None:
            self.connect()

        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO processed_events (topic, event_id, timestamp, payload) VALUES (?, ?, ?, ?)",
                    (topic, event_id, timestamp, json.dumps(payload))
                )
            return True
        except sqlite3.IntegrityError:
            return False

    async def get_stats(self):
        if self.conn is None:
            self.connect()
        cursor = self.conn.execute("SELECT topic, COUNT(*) FROM processed_events GROUP BY topic")
        rows = cursor.fetchall()
        return {"topics": {r[0]: r[1] for r in rows}}

    def get_events(self, topic=None):
        if self.conn is None:
            self.connect()

        if topic:
            cur = self.conn.execute(
                "SELECT topic, event_id, timestamp, payload FROM processed_events WHERE topic=?",
                (topic,)
            )
        else:
            cur = self.conn.execute(
                "SELECT topic, event_id, timestamp, payload FROM processed_events"
            )

        rows = cur.fetchall()
        return [
            {
                "topic": r[0],
                "event_id": r[1],
                "timestamp": r[2],
                "payload": json.loads(r[3]) if r[3] else {}
            }
            for r in rows
        ]

    async def clear(self):
        if self.conn is None:
            self.connect()
        with self.conn:
            self.conn.execute("DELETE FROM processed_events")

    async def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
