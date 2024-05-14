import sqlite3

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.init_db()

    def get_conn(self):
        return sqlite3.connect(self.db_file)

    def init_db(self):
        conn = self.get_conn()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                blocks_used INTEGER DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                chars_used INTEGER DEFAULT 0,
                context TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_user(self, user_id):
        conn = self.get_conn()
        with conn:
            conn.execute('''
                INSERT OR IGNORE INTO users (id, blocks_used, tokens_used, chars_used, context) VALUES (?, 0, 0, 0, NULL)
            ''', (user_id,))
            conn.commit()
        conn.close()
