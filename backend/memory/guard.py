import sqlite3
import datetime
from pathlib import Path
from loguru import logger

DB_PATH = Path(__file__).parent.parent.parent / "jarvis_memory.db"

class RateLimitExceeded(Exception):
    """Exception raised when the daily API request limit is exceeded."""
    pass

class RateLimitGuard:
    def __init__(self, daily_limit: int = 500):
        self.daily_limit = daily_limit
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database with usage_logs table."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS api_usage (
                        date TEXT PRIMARY KEY,
                        requests INTEGER DEFAULT 0,
                        tokens INTEGER DEFAULT 0
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize SQLite memory DB: {e}")

    def _get_today_str(self) -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d")

    def check_limit(self):
        """
        Check if the daily limit is exceeded before making an API call.
        Raises RateLimitExceeded if the limit is reached.
        """
        today = self._get_today_str()
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT requests FROM api_usage WHERE date = ?", (today,))
                row = cursor.fetchone()
                
                if row and row[0] >= self.daily_limit:
                    logger.warning(f"Rate limit exceeded: {row[0]}/{self.daily_limit} calls today.")
                    raise RateLimitExceeded("Daily limit exceeded")
        except sqlite3.Error as e:
            logger.error(f"Database error during check_limit: {e}")

    def log_usage(self, tokens: int = 0):
        """Log a successful API call and its token usage."""
        today = self._get_today_str()
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                # Insert or update today's record
                cursor.execute('''
                    INSERT INTO api_usage (date, requests, tokens) 
                    VALUES (?, 1, ?)
                    ON CONFLICT(date) 
                    DO UPDATE SET 
                        requests = requests + 1, 
                        tokens = tokens + ?
                ''', (today, tokens, tokens))
                conn.commit()
                
                # Fetch current stats to log
                cursor.execute("SELECT requests FROM api_usage WHERE date = ?", (today,))
                row = cursor.fetchone()
                if row:
                    logger.debug(f"API Usage Today: {row[0]}/{self.daily_limit} requests.")
                    
        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")
