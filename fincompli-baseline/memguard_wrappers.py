"""
MemGuard Wrappers for FinCompli Memory Layers

Wraps all 5 memory types with MemGuard interceptor:
1. Episodic (ChromaDB) - Historical SAR cases
2. Semantic (ChromaDB) - Regulations
3. Procedural (SQLite) - SOP rules
4. Working (LangGraph state) - Thread state
5. User Preferences (SQLite) - Officer settings
"""

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MemGuardEpisodicWrapper:
    """Wraps episodic memory (ChromaDB) with MemGuard tracking"""

    def __init__(self, inner, interceptor, agent_id: str = "unknown"):
        self.inner = inner
        self.interceptor = interceptor
        self.agent_id = agent_id

    def query(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """Query similar SAR cases"""
        logger.debug(f"[{self.agent_id}] Querying episodic memory: {query_text[:50]}...")

        # Record QUERY operation
        self.interceptor.record(
            operation="query",
            memory_key="sar_cases",
            memory_type="episodic",
            context={
                "query": query_text,
                "top_k": top_k,
                "agent_id": self.agent_id
            }
        )

        # Execute actual query
        results = self.inner.query(query_text, top_k)

        # Extract similarity scores if available
        similarities = []
        if results:
            for r in results:
                sim = r.get("similarity", r.get("score", 0))
                similarities.append(sim)

        # Record READ operation with results
        self.interceptor.record(
            operation="read",
            memory_key="sar_cases",
            memory_type="episodic",
            after_value={
                "results": [{"id": r.get("id", "unknown"), "similarity": r.get("similarity", 0)} for r in results],
                "count": len(results)
            },
            context={
                "similarities": similarities,
                "agent_id": self.agent_id
            }
        )

        logger.info(f"[{self.agent_id}] Retrieved {len(results)} similar cases, best match: {similarities[0] if similarities else 0:.2f}")

        return results

    def add(self, case_id: str, content: Dict) -> None:
        """Add new SAR case to episodic memory"""
        logger.debug(f"[{self.agent_id}] Adding case to episodic memory: {case_id}")

        self.interceptor.record(
            operation="create",
            memory_key=f"sar_case:{case_id}",
            memory_type="episodic",
            after_value=content,
            context={"agent_id": self.agent_id}
        )

        self.inner.add(case_id, content)

        logger.info(f"[{self.agent_id}] Added case {case_id} to episodic memory")

    def get(self, case_id: str) -> Optional[Dict]:
        """Get specific SAR case"""
        logger.debug(f"[{self.agent_id}] Reading case from episodic memory: {case_id}")

        self.interceptor.record(
            operation="read",
            memory_key=f"sar_case:{case_id}",
            memory_type="episodic",
            context={"agent_id": self.agent_id}
        )

        result = self.inner.get(case_id)

        if result:
            self.interceptor.record(
                operation="read",
                memory_key=f"sar_case:{case_id}",
                memory_type="episodic",
                after_value=result,
                context={"agent_id": self.agent_id}
            )

        return result


class MemGuardSemanticWrapper:
    """Wraps semantic memory (ChromaDB) with MemGuard tracking"""

    def __init__(self, inner, interceptor, agent_id: str = "unknown"):
        self.inner = inner
        self.interceptor = interceptor
        self.agent_id = agent_id

    def query(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """Query regulations"""
        logger.debug(f"[{self.agent_id}] Querying semantic memory: {query_text[:50]}...")

        # Record QUERY operation
        self.interceptor.record(
            operation="query",
            memory_key="regulations",
            memory_type="semantic",
            context={
                "query": query_text,
                "top_k": top_k,
                "agent_id": self.agent_id
            }
        )

        # Execute actual query
        results = self.inner.query(query_text, top_k)

        # Extract similarity scores
        similarities = []
        if results:
            for r in results:
                sim = r.get("similarity", r.get("score", 0))
                similarities.append(sim)

        # Record READ operation with results
        self.interceptor.record(
            operation="read",
            memory_key="regulations",
            memory_type="semantic",
            after_value={
                "results": [{"id": r.get("id", "unknown"), "similarity": r.get("similarity", 0)} for r in results],
                "count": len(results)
            },
            context={
                "similarities": similarities,
                "agent_id": self.agent_id
            }
        )

        logger.info(f"[{self.agent_id}] Retrieved {len(results)} regulations, best match: {similarities[0] if similarities else 0:.2f}")

        return results

    def add(self, reg_id: str, content: Dict) -> None:
        """Add regulation to semantic memory"""
        logger.debug(f"[{self.agent_id}] Adding regulation to semantic memory: {reg_id}")

        self.interceptor.record(
            operation="create",
            memory_key=f"regulation:{reg_id}",
            memory_type="semantic",
            after_value=content,
            context={"agent_id": self.agent_id}
        )

        self.inner.add(reg_id, content)

        logger.info(f"[{self.agent_id}] Added regulation {reg_id} to semantic memory")

    def get(self, reg_id: str) -> Optional[Dict]:
        """Get specific regulation"""
        logger.debug(f"[{self.agent_id}] Reading regulation from semantic memory: {reg_id}")

        self.interceptor.record(
            operation="read",
            memory_key=f"regulation:{reg_id}",
            memory_type="semantic",
            context={"agent_id": self.agent_id}
        )

        result = self.inner.get(reg_id)

        if result:
            self.interceptor.record(
                operation="read",
                memory_key=f"regulation:{reg_id}",
                memory_type="semantic",
                after_value=result,
                context={"agent_id": self.agent_id}
            )

        return result


class MemGuardProceduralWrapper:
    """Wraps procedural memory (SQLite) with MemGuard tracking"""

    def __init__(self, inner, interceptor, agent_id: str = "unknown"):
        self.inner = inner
        self.interceptor = interceptor
        self.agent_id = agent_id

    def get_rule(self, rule_name: str) -> Optional[Dict]:
        """Get SOP rule"""
        logger.debug(f"[{self.agent_id}] Reading SOP rule: {rule_name}")

        self.interceptor.record(
            operation="read",
            memory_key=f"rule:{rule_name}",
            memory_type="procedural",
            context={"agent_id": self.agent_id}
        )

        rule = self.inner.get_rule(rule_name)

        if rule:
            self.interceptor.record(
                operation="read",
                memory_key=f"rule:{rule_name}",
                memory_type="procedural",
                after_value=rule,
                context={"agent_id": self.agent_id}
            )
            logger.info(f"[{self.agent_id}] Retrieved SOP rule: {rule_name}")
        else:
            logger.warning(f"[{self.agent_id}] SOP rule not found: {rule_name}")

        return rule

    def set_rule(self, rule_name: str, rule_data: Dict) -> None:
        """Set SOP rule"""
        logger.debug(f"[{self.agent_id}] Setting SOP rule: {rule_name}")

        self.interceptor.record(
            operation="create",
            memory_key=f"rule:{rule_name}",
            memory_type="procedural",
            after_value=rule_data,
            context={"agent_id": self.agent_id}
        )

        self.inner.set_rule(rule_name, rule_data)

        logger.info(f"[{self.agent_id}] Set SOP rule: {rule_name}")

    def list_rules(self) -> List[str]:
        """List all SOP rules"""
        logger.debug(f"[{self.agent_id}] Listing all SOP rules")

        self.interceptor.record(
            operation="query",
            memory_key="rules:all",
            memory_type="procedural",
            context={"agent_id": self.agent_id}
        )

        rules = self.inner.list_rules()

        self.interceptor.record(
            operation="read",
            memory_key="rules:all",
            memory_type="procedural",
            after_value={"rules": rules, "count": len(rules)},
            context={"agent_id": self.agent_id}
        )

        logger.info(f"[{self.agent_id}] Listed {len(rules)} SOP rules")

        return rules


class MemGuardWorkingWrapper:
    """Wraps working memory (LangGraph state) with MemGuard tracking"""

    def __init__(self, interceptor, agent_id: str = "unknown"):
        self.interceptor = interceptor
        self.agent_id = agent_id
        self.data = {}

    def write(self, key: str, value: Any) -> None:
        """Write to working memory"""
        logger.debug(f"[{self.agent_id}] Writing to working memory: {key}")

        before = self.data.get(key)
        self.data[key] = value

        operation = "update" if before else "create"

        self.interceptor.record(
            operation=operation,
            memory_key=key,
            memory_type="working",
            before_value={"value": before} if before else None,
            after_value={"value": value},
            context={"agent_id": self.agent_id}
        )

        logger.info(f"[{self.agent_id}] {operation.upper()} working memory: {key}")

    def read(self, key: str) -> Any:
        """Read from working memory"""
        logger.debug(f"[{self.agent_id}] Reading from working memory: {key}")

        value = self.data.get(key)

        self.interceptor.record(
            operation="read",
            memory_key=key,
            memory_type="working",
            after_value={"value": value} if value else None,
            context={"agent_id": self.agent_id}
        )

        if value:
            logger.info(f"[{self.agent_id}] Read from working memory: {key}")
        else:
            logger.debug(f"[{self.agent_id}] Key not found in working memory: {key}")

        return value

    def delete(self, key: str) -> None:
        """Delete from working memory"""
        logger.debug(f"[{self.agent_id}] Deleting from working memory: {key}")

        before = self.data.get(key)
        if key in self.data:
            del self.data[key]

        self.interceptor.record(
            operation="delete",
            memory_key=key,
            memory_type="working",
            before_value={"value": before} if before else None,
            context={"agent_id": self.agent_id}
        )

        logger.info(f"[{self.agent_id}] Deleted from working memory: {key}")

    def get_all(self) -> Dict[str, Any]:
        """Get all working memory contents"""
        logger.debug(f"[{self.agent_id}] Reading all working memory")

        self.interceptor.record(
            operation="read",
            memory_key="working:all",
            memory_type="working",
            after_value={"keys": list(self.data.keys()), "count": len(self.data)},
            context={"agent_id": self.agent_id}
        )

        logger.info(f"[{self.agent_id}] Read {len(self.data)} items from working memory")

        return self.data.copy()


class MemGuardUserPreferencesWrapper:
    """Wraps user preferences (SQLite) with MemGuard tracking"""

    def __init__(self, inner, interceptor, agent_id: str = "unknown"):
        self.inner = inner
        self.interceptor = interceptor
        self.agent_id = agent_id

    def get_preference(self, user_id: str, pref_key: str) -> Optional[Any]:
        """Get user preference"""
        logger.debug(f"[{self.agent_id}] Reading user preference: {user_id}:{pref_key}")

        self.interceptor.record(
            operation="read",
            memory_key=f"user_pref:{user_id}:{pref_key}",
            memory_type="user_preferences",
            context={"agent_id": self.agent_id}
        )

        value = self.inner.get_preference(user_id, pref_key)

        if value is not None:
            self.interceptor.record(
                operation="read",
                memory_key=f"user_pref:{user_id}:{pref_key}",
                memory_type="user_preferences",
                after_value={"value": value},
                context={"agent_id": self.agent_id}
            )
            logger.info(f"[{self.agent_id}] Retrieved user preference: {user_id}:{pref_key}")

        return value

    def set_preference(self, user_id: str, pref_key: str, value: Any) -> None:
        """Set user preference"""
        logger.debug(f"[{self.agent_id}] Setting user preference: {user_id}:{pref_key}")

        before = self.inner.get_preference(user_id, pref_key)
        operation = "update" if before is not None else "create"

        self.interceptor.record(
            operation=operation,
            memory_key=f"user_pref:{user_id}:{pref_key}",
            memory_type="user_preferences",
            before_value={"value": before} if before is not None else None,
            after_value={"value": value},
            context={"agent_id": self.agent_id}
        )

        self.inner.set_preference(user_id, pref_key, value)

        logger.info(f"[{self.agent_id}] {operation.upper()} user preference: {user_id}:{pref_key}")
