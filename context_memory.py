#!/usr/bin/env python3
"""Sqlantra Context Memory System V2 - Enhanced with detailed tracking."""

import json
from datetime import datetime
from typing import Any, Optional, List, Dict
from collections import OrderedDict
import threading
import traceback

MAX_MEMORY_SIZE = 2000

CONTEXT_WINDOW_SIZE = 5


class ContextMemoryEntry:
    """Single entry in context memory with full details."""

    def __init__(self, key: str, value: Any, operation: str, metadata: dict = None):
        self.key = key
        self.value = value
        self.operation = operation
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
        self.id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        self.caller_file = self.metadata.get("caller_file", "unknown")
        self.caller_line = self.metadata.get("caller_line", 0)
        self.operation_type = self._classify_operation(operation)

    def _classify_operation(self, operation: str) -> str:
        """Classify the type of operation."""
        classifications = {
            "store": "WRITE",
            "recall": "READ",
            "system": "SYSTEM",
            "skill_match": "SKILL_MATCH",
            "agent_routing": "AGENT_ROUTING",
            "sql_generation": "LLM_SQL",
            "db_result": "DATABASE",
            "hitl_request": "HITL_REQUEST",
            "hitl_approved": "HITL_APPROVED",
            "hitl_rejected": "HITL_REJECTED",
            "pipeline": "PIPELINE",
            "workflow": "WORKFLOW",
            "input": "USER_INPUT",
            "ollama_call": "LLM_CALL",
            "config": "CONFIG",
            "mcp_call": "MCP_CALL",
            "insights": "BUSINESS_INSIGHTS",
            "pipeline_metrics": "GOLD_METRICS",
        }
        return classifications.get(operation, operation.upper())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "operation": self.operation,
            "operation_type": self.operation_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "caller_file": self.caller_file,
            "caller_line": self.caller_line,
        }

    def get_formatted_value(self) -> str:
        """Get a nicely formatted value string."""
        if isinstance(self.value, dict):
            return json.dumps(self.value, indent=2, default=str)
        elif isinstance(self.value, list):
            if len(self.value) <= 3:
                return json.dumps(self.value, default=str)
            return (
                f"Array[{len(self.value)}] "
                + json.dumps(self.value[:2], default=str)
                + "..."
            )
        elif isinstance(self.value, str):
            if len(self.value) > 200:
                return self.value[:200] + "..."
            return self.value
        else:
            return str(self.value)

    def get_summary(self) -> str:
        """Get a one-line summary."""
        val_preview = (
            str(self.value)[:40]
            if not isinstance(self.value, (dict, list))
            else "Complex"
        )
        return f"{self.operation_type}: {self.key} = {val_preview}"


class SqlantraContextMemory:
    """Context Memory System for Sqlantra - tracks all system state and operations."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "/tmp/sqlantra_context_memory.json"
        self._memory: OrderedDict[str, ContextMemoryEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._operation_history: List[Dict] = []
        self._db_module = None
        self._ollama_calls: List[Dict] = []
        self._mcp_calls: List[Dict] = []

    def set_db_module(self, db_module):
        """Set database module for persistence."""
        self._db_module = db_module

    def store(
        self, key: str, value: Any, operation: str = "store", metadata: dict = None
    ) -> ContextMemoryEntry:
        """Store a value in context memory with enhanced tracking."""
        with self._lock:
            caller_info = self._get_caller_info()
            if metadata:
                metadata.update(caller_info)
            else:
                metadata = caller_info

            entry = ContextMemoryEntry(key, value, operation, metadata)
            self._memory[key] = entry
            self._operation_history.append(
                {
                    "timestamp": entry.timestamp,
                    "operation": operation,
                    "operation_type": entry.operation_type,
                    "key": key,
                    "action": f"{operation}: {key}",
                    "id": entry.id,
                }
            )

            if len(self._memory) > MAX_MEMORY_SIZE:
                self._memory.popitem(last=False)

            if self._db_module:
                self._db_module.log_context_memory(
                    key, json.dumps(value, default=str), operation, metadata
                )

            return entry

    def _get_caller_info(self) -> dict:
        """Get information about the caller."""
        try:
            tb = traceback.extract_stack()
            if len(tb) > 2:
                frame = tb[-3]
                return {
                    "caller_file": frame.filename.split("/")[-1]
                    if "/" in frame.filename
                    else frame.filename,
                    "caller_line": frame.lineno,
                    "caller_function": frame.name,
                }
        except Exception:
            pass
        return {}

    def recall(self, key: str) -> Optional[Any]:
        """Recall a value from context memory."""
        entry = self._memory.get(key)
        if entry:
            self.store(
                f"_recall_{key}",
                entry.value,
                "recall",
                {"recalled_key": key, "source": "memory_recall"},
            )
        return entry.value if entry else None

    def recall_all(self) -> Dict[str, Any]:
        """Recall all stored values."""
        return {k: v.value for k, v in self._memory.items()}

    def recall_history(self, limit: int = 50) -> List[Dict]:
        """Get operation history."""
        return self._operation_history[-limit:]

    def log_ollama_call(
        self, prompt: str, response: str, model: str, duration_ms: int = 0
    ):
        """Log an Ollama LLM call."""
        call_record = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "response_preview": response[:100] + "..."
            if len(response) > 100
            else response,
            "duration_ms": duration_ms,
            "id": f"ollama_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        }
        self._ollama_calls.append(call_record)
        self.store(
            f"_ollama_{call_record['id']}",
            call_record,
            "ollama_call",
            {"model": model, "duration_ms": duration_ms},
        )
        return call_record

    def log_mcp_call(
        self, tool_name: str, params: dict, result: Any, success: bool = True
    ):
        """Log an MCP tool call."""
        call_record = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "params": params,
            "success": success,
            "result_preview": str(result)[:100] if result else None,
            "id": f"mcp_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        }
        self._mcp_calls.append(call_record)
        self.store(
            f"_mcp_{call_record['id']}",
            call_record,
            "mcp_call",
            {"tool": tool_name, "success": success},
        )
        return call_record

    def delete(self, key: str) -> bool:
        """Delete a key from context memory."""
        with self._lock:
            if key in self._memory:
                del self._memory[key]
                self._operation_history.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "operation": "delete",
                        "key": key,
                        "action": f"delete: {key}",
                    }
                )
                return True
            return False

    def clear(self) -> None:
        """Clear all context memory."""
        with self._lock:
            self._memory.clear()
            self._operation_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "operation": "clear",
                    "key": "*",
                    "action": "clear: all memory",
                }
            )

    def get_state(self) -> dict:
        """Get current state of context memory."""
        return {
            "keys": list(self._memory.keys()),
            "total_entries": len(self._memory),
            "history_count": len(self._operation_history),
            "ollama_calls_count": len(self._ollama_calls),
            "mcp_calls_count": len(self._mcp_calls),
            "recent_history": self._operation_history[-10:]
            if self._operation_history
            else [],
        }

    def get_recent_entries(self, limit: int = 30) -> List[dict]:
        """Get recent memory entries with full details."""
        entries = list(self._memory.values())[-limit:]
        return [e.to_dict() for e in reversed(entries)]

    def get_detailed_entries(self, limit: int = 20) -> List[dict]:
        """Get detailed memory entries for UI display."""
        entries = list(self._memory.values())[-limit:]
        result = []
        for e in reversed(entries):
            result.append(
                {
                    "id": e.id,
                    "key": e.key,
                    "value": e.get_formatted_value(),
                    "operation": e.operation,
                    "operation_type": e.operation_type,
                    "timestamp": e.timestamp,
                    "caller_file": e.caller_file,
                    "caller_line": e.caller_line,
                    "caller_function": e.metadata.get("caller_function", ""),
                    "metadata": e.metadata,
                    "summary": e.get_summary(),
                }
            )
        return result

    def get_ollama_calls(self, limit: int = 10) -> List[dict]:
        """Get recent Ollama calls."""
        return self._ollama_calls[-limit:]

    def get_mcp_calls(self, limit: int = 10) -> List[dict]:
        """Get recent MCP calls."""
        return self._mcp_calls[-limit:]

    def search(self, query: str) -> List[dict]:
        """Search memory entries by key or value content."""
        results = []
        query_lower = query.lower()
        for entry in self._memory.values():
            if query_lower in entry.key.lower():
                results.append(entry.to_dict())
            elif isinstance(entry.value, str) and query_lower in entry.value.lower():
                results.append(entry.to_dict())
        return results

    def get_context_window(self) -> Dict[str, Any]:
        """Get the context window for smart recall - last N interactions."""
        recent_entries = list(self._memory.values())[-CONTEXT_WINDOW_SIZE:]
        context = {}
        for entry in recent_entries:
            context[entry.key] = entry.value
        return context

    def smart_recall(self, query: str) -> Dict[str, Any]:
        """Smart recall - understand context-aware queries (follow-up questions).

        Detects if query is a follow-up and attempts to resolve based on previous context.
        Examples:
        - "Show me the recent orders" -> "What was the last query about orders?"
        - "What about over $1000?" -> "Previous query + amount filter"
        """
        query_lower = query.lower()

        follow_up_indicators = [
            "what about", "that", "those", "show me", "also",
            "and", "but", "however", "the same", "similar",
            "also", "plus", "add", "with", "including",
        ]

        is_follow_up = any(indicator in query_lower for indicator in follow_up_indicators)

        if not is_follow_up:
            direct = self._memory.get(query_lower)
            if direct:
                return {
                    "type": "direct",
                    "query": query,
                    "result": direct.value,
                    "matched_key": direct.key,
                }

        context = self.get_context_window()

        matched_entry = None
        for key, entry in reversed(list(self._memory.items())):
            if entry.operation in ["user_input", "input"]:
                matched_entry = entry
                break

        resolved_query = query
        resolution_method = "direct"

        if is_follow_up and matched_entry:
            original_query = matched_entry.value if isinstance(matched_entry.value, str) else str(matched_entry.value)

            resolution_notes = []

            for word in ["order", "orders"]:
                if word in query_lower and word in original_query.lower():
                    resolution_notes.append(f"Reused filter: {word} from context")

            amount_indicators = ["over", "under", "more than", "less than", "above", "below"]
            for indicator in amount_indicators:
                if indicator in query_lower:
                    resolution_notes.append(f"Using amount filter from query")

            category_indicators = ["unpaid", "pending", "paid", "approved", "rejected"]
            for indicator in category_indicators:
                if indicator in query_lower:
                    resolution_notes.append(f"Using status filter: {indicator}")

            resolved_query = original_query
            resolution_method = "context_aware"

            return {
                "type": "follow_up",
                "original_query": original_query,
                "resolved_query": resolved_query,
                "query": query,
                "context_window": context,
                "resolution_method": resolution_method,
                "resolution_notes": resolution_notes,
                "requires_context_merge": True,
            }

        return {
            "type": "new",
            "query": query,
            "context_window": context,
            "resolution_method": resolution_method,
        }

    def semantic_search(self, query: str, top_k: int = 5) -> List[dict]:
        """Semantic search - search by meaning, not just keywords."""
        query_words = set(query.lower().split())

        scored_results = []

        for key, entry in self._memory.items():
            score = 0

            if query.lower() in entry.key.lower():
                score = 100
            elif any(w in entry.key.lower() for w in query_words if len(w) > 2):
                matching = len([w for w in query_words if w in entry.key.lower() and len(w) > 2])
                score = matching * 20

            if isinstance(entry.value, str):
                if query.lower() in entry.value.lower():
                    score += 50
                matching = len([w for w in query_words if w in entry.value.lower() and len(w) > 2])
                score += matching * 5

            if entry.operation in ["user_input", "input"]:
                score += 30

            if score > 0:
                scored_results.append((score, entry))

        scored_results.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                "key": entry.key,
                "value": entry.value,
                "operation": entry.operation,
                "operation_type": entry.operation_type,
                "timestamp": entry.timestamp,
                "score": score,
            }
            for score, entry in scored_results[:top_k]
        ]

    def get_display_text(self) -> str:
        """Get formatted text for UI display."""
        if not self._operation_history:
            return "Context Memory (empty)"

        lines = ["=== CONTEXT MEMORY ==="]
        for op in self._operation_history[-20:]:
            lines.append(
                f"[{op['timestamp'][11:19]}] [{op.get('operation_type', 'OP')}] {op['action']}"
            )

        if len(self._memory) > 0:
            lines.append("\n--- Recent Values ---")
            for key, entry in list(self._memory.items())[-5:]:
                lines.append(f"  [{entry.operation_type}] {key}: {entry.get_summary()}")

        return "\n".join(lines)


class SkillsRegistry:
    """Registry for Sqlantra skills."""

    def __init__(self):
        self._skills: Dict[str, Dict] = {}
        self._initialize_default_skills()

    def _initialize_default_skills(self):
        """Initialize default skills."""
        self._skills = {
            "query_database": {
                "name": "Query Database",
                "description": "Execute SQL queries on the database",
                "file": "text_to_sql.py",
                "function": "execute_text_query",
                "category": "database",
            },
            "approval_workflow": {
                "name": "HITL Approval Workflow",
                "description": "Request human approval for sensitive operations",
                "file": "hitl_workflow.py",
                "function": "request_approval",
                "category": "workflow",
            },
            "data_pipeline": {
                "name": "Data Pipeline",
                "description": "Process data through Bronze/Silver/Gold layers",
                "file": "data_pipeline.py",
                "function": "process",
                "category": "pipeline",
            },
            "context_recall": {
                "name": "Context Recall",
                "description": "Recall information from context memory",
                "file": "context_memory.py",
                "function": "recall",
                "category": "memory",
            },
            "semantic_transform": {
                "name": "Semantic Transform",
                "description": "Transform user queries using semantic understanding",
                "file": "semantic_layer.py",
                "function": "transform",
                "category": "nlp",
            },
        }

    def register(self, skill_id: str, skill_def: Dict):
        """Register a new skill."""
        self._skills[skill_id] = skill_def

    def get_skill(self, skill_id: str) -> Optional[Dict]:
        """Get skill definition."""
        return self._skills.get(skill_id)

    def list_skills(self) -> List[Dict]:
        """List all skills."""
        return list(self._skills.values())

    def match_skill(self, query: str) -> Optional[Dict]:
        """Match a query to best skill."""
        query_lower = query.lower()
        best_match = None
        best_score = 0

        for skill_id, skill in self._skills.items():
            score = 0

            # Check for exact substring matches (higher priority)
            if query_lower in skill["name"].lower():
                score = 20
            elif query_lower in skill["description"].lower():
                score = 15
            else:
                # Check for keyword matches
                name_words = set(skill["name"].lower().split())
                desc_words = set(skill["description"].lower().split())
                query_words = set(query_lower.split())

                # Count matching words
                name_matches = len(name_words & query_words)
                desc_matches = len(desc_words & query_words)

                # Score based on matches
                if name_matches > 0:
                    score = name_matches * 3  # 3 points per name word match
                if desc_matches > 0 and score < desc_matches * 2:
                    score = desc_matches * 2  # 2 points per description word match

                # Bonus for important keywords - weighted by category
                if skill_id == "approval_workflow":
                    important_keywords = {
                        "approval",
                        "request",
                        "approve",
                        "reject",
                        "high-value",
                        "high value",
                        "transaction",
                    }
                elif skill_id == "query_database":
                    important_keywords = {
                        "show",
                        "list",
                        "find",
                        "get",
                        "select",
                        "query",
                        "order",
                        "product",
                        "sales",
                        "amount",
                        "total",
                        "sum",
                        "count",
                        "over",
                        "under",
                        "greater",
                        "less",
                    }
                elif skill_id == "data_pipeline":
                    important_keywords = {
                        "process",
                        "pipeline",
                        "bronze",
                        "silver",
                        "gold",
                        "ingest",
                        "curate",
                        "enrich",
                        "transform",
                        "process",
                    }
                elif skill_id == "context_recall":
                    important_keywords = {
                        "memory",
                        "recall",
                        "remember",
                        "context",
                        "history",
                        "past",
                        "store",
                        "retrieve",
                    }
                elif skill_id == "semantic_transform":
                    important_keywords = {
                        "transform",
                        "convert",
                        "change",
                        "alter",
                        "modify",
                        "semantic",
                        "meaning",
                    }
                else:
                    important_keywords = set()

                keyword_matches = len(
                    [w for w in query_words if w in important_keywords]
                )
                if keyword_matches > 0:
                    score = max(score, keyword_matches * 2)

            if score > best_score:
                best_score = score
                best_match = skill

        return best_match


class AgentsRegistry:
    """Registry for Sqlantra agents."""

    def __init__(self):
        self._agents: Dict[str, Dict] = {}
        self._initialize_default_agents()

    def _initialize_default_agents(self):
        """Initialize default agents."""
        self._agents = {
            "query_agent": {
                "name": "Query Agent",
                "description": "Handles database queries and SQL generation",
                "skills": ["query_database", "semantic_transform"],
                "file": "orchestrator.py",
                "class": "QueryAgent",
                "capabilities": ["text_to_sql", "db_query", "data_analysis"],
            },
            "approval_agent": {
                "name": "Approval Agent",
                "description": "Manages HITL approval workflows",
                "skills": ["approval_workflow"],
                "file": "hitl_mcp.py",
                "class": "HITLAgent",
                "capabilities": ["request_approval", "notify", "workflow_control"],
            },
            "pipeline_agent": {
                "name": "Pipeline Agent",
                "description": "Orchestrates data pipeline processing",
                "skills": ["data_pipeline"],
                "file": "data_pipeline.py",
                "class": "PipelineAgent",
                "capabilities": ["bronze_ingest", "silver_curate", "gold_enrich"],
            },
            "memory_agent": {
                "name": "Memory Agent",
                "description": "Manages context memory operations",
                "skills": ["context_recall"],
                "file": "context_memory.py",
                "class": "MemoryAgent",
                "capabilities": ["store", "recall", "search", "persist"],
            },
        }

    def register(self, agent_id: str, agent_def: Dict):
        """Register a new agent."""
        self._agents[agent_id] = agent_def

    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent definition."""
        return self._agents.get(agent_id)

    def list_agents(self) -> List[Dict]:
        """List all agents."""
        return list(self._agents.values())

    def match_agent(self, query: str) -> Optional[Dict]:
        """Match query to best agent."""
        query_lower = query.lower()
        keywords = {
            "query_agent": [
                "query",
                "show",
                "list",
                "find",
                "order",
                "product",
                "sales",
                "sql",
                "total",
            ],
            "approval_agent": [
                "approve",
                "reject",
                "approval",
                "confirm",
                "high-value",
            ],
            "pipeline_agent": [
                "process",
                "pipeline",
                "bronze",
                "silver",
                "gold",
                "enrich",
            ],
            "memory_agent": [
                "remember",
                "context",
                "memory",
                "recall",
                "past",
                "history",
            ],
        }

        for agent_id, words in keywords.items():
            if any(w in query_lower for w in words):
                return self._agents.get(agent_id)

        return self._agents.get("query_agent")


if __name__ == "__main__":
    memory = SqlantraContextMemory()
    memory.store("test", "Hello World", "store", {"source": "test"})
    memory.store(
        "sql_query", "SELECT * FROM orders", "sql_generation", {"model": "qwen3.5:2b-q4_K_M"}
    )
    memory.log_ollama_call("Generate SQL", "SELECT * FROM orders", "qwen3.5:2b-q4_K_M", 1500)
    print(memory.get_display_text())
