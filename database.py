import sqlite3

class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.init_db()

    def init_db(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                blocks_used INTEGER DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                chars_used INTEGER DEFAULT 0,
                context TEXT
            )
        ''')

        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def add_user(self, user_id):
        if not self.get_user(user_id):
            self.conn.execute('INSERT INTO users (user_id, blocks_used, tokens_used, chars_used) VALUES (?, 0, 0, 0)', (user_id,))
            self.conn.commit()

    def get_user(self, user_id):
        cursor = self.conn.execute('SELECT user_id, blocks_used, tokens_used, chars_used FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

    def is_user_authorized(self, user_id):
        return self.get_user(user_id) is not None

    def get_authorized_users(self):
        cursor = self.conn.execute('SELECT user_id FROM users')
        return [row[0] for row in cursor.fetchall()]

    def get_message_count(self, user_id):
        cursor = self.conn.execute('SELECT COUNT(*) FROM messages WHERE user_id = ?', (user_id,))
        return cursor.fetchone()[0]

    def save_message(self, user_id, message, msg_type):
        self.conn.execute('INSERT INTO messages (user_id, message, type) VALUES (?, ?, ?)', (user_id, message, msg_type))
        self.conn.commit()

    def get_user_history(self, user_id):
        cursor = self.conn.execute('SELECT message FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20', (user_id,))
        return [row[0] for row in cursor.fetchall()]

    def get_blocks_used(self, user_id):
        cursor = self.conn.execute('SELECT blocks_used FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

    def update_blocks_used(self, user_id, blocks_used):
        self.conn.execute('UPDATE users SET blocks_used = blocks_used + ? WHERE user_id = ?', (blocks_used, user_id))
        self.conn.commit()

    def get_tokens_used(self, user_id):
        cursor = self.conn.execute('SELECT tokens_used FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

    def update_tokens_used(self, user_id, tokens_used):
        self.conn.execute('UPDATE users SET tokens_used = tokens_used + ? WHERE user_id = ?', (tokens_used, user_id))
        self.conn.commit()

    def get_chars_used(self, user_id):
        cursor = self.conn.execute('SELECT chars_used FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

    def update_chars_used(self, user_id, chars_used):
        self.conn.execute('UPDATE users SET chars_used = chars_used + ? WHERE user_id = ?', (chars_used, user_id))
        self.conn.commit()

    def close(self):
        self.conn.close()
