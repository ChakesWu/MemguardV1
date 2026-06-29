"""
User Preferences Memory Module
用戶偏好記憶模塊

Stores and retrieves user-specific preferences and settings.
Uses SQLite for structured user data.
"""

import logging
import sqlite3
import json
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class UserPreferencesMemory:
    """User Preferences Memory Manager"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        self._verify_schema()

    def _verify_schema(self):
        if not self.db_path or not self.db_path.exists():
            logger.warning(f"User preferences database not found: {self.db_path}")
            return
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_preferences")
            count = cursor.fetchone()[0]
            conn.close()
            logger.info(f"User preferences memory initialized: {count} users")
        except Exception as e:
            logger.error(f"Failed to verify user preferences schema: {e}")

    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.db_path or not self.db_path.exists():
            return None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, preferred_language, report_format,
                       notification_enabled, risk_tolerance, preferences_json
                FROM user_preferences WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                prefs = dict(row)
                if prefs.get("preferences_json"):
                    try:
                        prefs["additional_preferences"] = json.loads(prefs["preferences_json"])
                    except:
                        pass
                return prefs
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve user preferences: {e}")
            return None

    def get_report_format(self, user_id: str) -> str:
        prefs = self.get_user_preferences(user_id)
        if prefs:
            return prefs.get("report_format", "detailed")
        return "detailed"

    def get_risk_tolerance(self, user_id: str) -> str:
        prefs = self.get_user_preferences(user_id)
        if prefs:
            return prefs.get("risk_tolerance", "medium")
        return "medium"

    def get_statistics(self) -> Dict[str, Any]:
        if not self.db_path or not self.db_path.exists():
            return {"status": "disabled", "total_users": 0}
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_preferences")
            count = cursor.fetchone()[0]
            conn.close()
            return {"status": "active", "total_users": count, "db_path": str(self.db_path)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
