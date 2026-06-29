"""
Procedural Memory Module
程序記憶模塊

Procedural memory stores SOP (Standard Operating Procedure) rules.
Uses SQLite for structured rule queries.

程序記憶存儲 SOP（標準操作程序）規則。
使用 SQLite 進行結構化規則查詢。

[Business Purpose] Encodes institutional knowledge of how to handle scenarios
[業務目的] 編碼機構對如何處理場景的知識
"""

import logging
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ProceduralMemory:
    """
    Procedural Memory Manager
    程序記憶管理器

    Stores: SOP rules for different transaction scenarios
    Query: "What are the required actions for structuring cases?"
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize procedural memory with SQLite

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._verify_schema()

    def _verify_schema(self):
        """Verify SOP rules table exists"""
        if not self.db_path or not self.db_path.exists():
            logger.warning(f"Procedural memory database not found: {self.db_path}")
            return

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sop_rules")
            count = cursor.fetchone()[0]
            conn.close()
            logger.info(f"Procedural memory initialized: {count} SOP rules")
        except Exception as e:
            logger.error(f"Failed to verify procedural memory schema: {e}")

    def get_rules_by_scenario(self, scenario_type: str) -> List[Dict[str, Any]]:
        """
        Get SOP rules for a specific scenario type
        獲取特定場景類型的 SOP 規則

        Args:
            scenario_type: Type of scenario (e.g., "structuring", "kyc_expired")

        Returns:
            List of rule dicts ordered by priority
        """
        if not self.db_path or not self.db_path.exists():
            return []

        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT rule_id, rule_name, scenario_type, condition, action,
                       threshold, priority
                FROM sop_rules
                WHERE scenario_type = ?
                ORDER BY priority ASC
            """, (scenario_type,))

            rules = []
            for row in cursor.fetchall():
                rules.append({
                    "rule_id": row["rule_id"],
                    "rule_name": row["rule_name"],
                    "scenario_type": row["scenario_type"],
                    "condition": row["condition"],
                    "action": row["action"],
                    "threshold": row["threshold"],
                    "priority": row["priority"]
                })

            conn.close()
            logger.info(f"Retrieved {len(rules)} SOP rules for scenario: {scenario_type}")
            return rules

        except Exception as e:
            logger.error(f"Failed to retrieve SOP rules: {e}")
            return []

    def get_rule_by_risk_score(self, risk_score: float) -> Optional[Dict[str, Any]]:
        """
        Get applicable SOP rule based on risk score
        根據風險分數獲取適用的 SOP 規則

        Args:
            risk_score: Calculated risk score (0-1)

        Returns:
            Applicable rule dict or None
        """
        if not self.db_path or not self.db_path.exists():
            return None

        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Check high risk threshold first (priority 1)
            cursor.execute("""
                SELECT rule_id, rule_name, scenario_type, condition, action,
                       threshold, priority
                FROM sop_rules
                WHERE threshold IS NOT NULL
                ORDER BY priority ASC
            """)

            for row in cursor.fetchall():
                threshold = row["threshold"]
                condition = row["condition"]

                # Evaluate condition
                if ">" in condition and risk_score > threshold:
                    conn.close()
                    return dict(row)
                elif "<" in condition and risk_score < threshold:
                    conn.close()
                    return dict(row)

            conn.close()
            return None

        except Exception as e:
            logger.error(f"Failed to get rule by risk score: {e}")
            return None

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """
        Get all SOP rules
        獲取所有 SOP 規則

        Returns:
            List of all rule dicts
        """
        if not self.db_path or not self.db_path.exists():
            return []

        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT rule_id, rule_name, scenario_type, condition, action,
                       threshold, priority
                FROM sop_rules
                ORDER BY priority ASC, scenario_type
            """)

            rules = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return rules

        except Exception as e:
            logger.error(f"Failed to retrieve all SOP rules: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get procedural memory statistics
        獲取程序記憶統計信息

        Returns:
            Statistics dict
        """
        if not self.db_path or not self.db_path.exists():
            return {"status": "disabled", "total_rules": 0}

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sop_rules")
            count = cursor.fetchone()[0]
            conn.close()

            return {
                "status": "active",
                "total_rules": count,
                "db_path": str(self.db_path)
            }
        except Exception as e:
            logger.error(f"Failed to get procedural memory stats: {e}")
            return {"status": "error", "error": str(e)}
