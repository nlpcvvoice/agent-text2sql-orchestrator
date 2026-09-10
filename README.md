# Agent Text2SQL Orchestrator

An LLM-orchestrated text-to-SQL demo system with agent routing, human-in-the-loop approval, layered data pipelines, and persistent context memory. Runs on Python standard library only; SQLite-backed.

## Why this exists

This project demonstrates how an agent workflow can wrap a text-to-SQL capability rather than treating SQL generation as a single-shot LLM call. The query path is decomposed into explicit stages — skill matching, agent routing, SQL generation (LLM with deterministic fallback), context logging, execution, pipeline refresh, and insight generation — so every step is observable and testable. A human-in-the-loop gate interrupts high-value transactions before they are committed.

## Highlights

| Capability | What it does | Where |
|---|---|---|
| Text-to-SQL | Converts natural language to SQL via LLM, with a rule-based deterministic fallback when the model is unavailable | `text_to_sql.py` |
| Agent orchestration | 8-stage pipeline: skill matching → agent routing → SQL → memory → execution → pipeline → HITL check → insights | `web_demo.py` |
| Human-in-the-loop | High-value operations create approval requests; approve/reject decisions are recorded and enforced | `hitl_workflow.py` |
| Context memory | Every stage, LLM call, SQL statement and decision is logged with timestamps and metadata; searchable | `context_memory.py` |
| Data pipeline | Bronze → Silver → Gold layers with daily sales, product performance, and customer 360 aggregations | `sqlantra_database_v2.py` |
| Web UI | Embedded 4-panel interface: input/approval, live workflow, database viewer, memory browser | `web_demo.py` |

## Architecture

```
User query
   │
   ▼
web_demo.py  (HTTP server, port 8766, embedded UI)
   │
   ├─ Skill Matching ───────────► SkillsRegistry (context_memory.py)
   ├─ Agent Routing ────────────► AgentsRegistry  (context_memory.py)
   ├─ Text-to-SQL ──────────────► text_to_sql.py   (LLM  → rule-based fallback)
   ├─ Context Memory ───────────► SqlantraContextMemory
   ├─ DB Execution ─────────────► sqlantra_database_v2.py  (SQLite)
   ├─ Pipeline Refresh ─────────► bronze_* → silver_* → gold_*
   ├─ HITL Approval Check ──────► hitl_workflow.py  (hitl_approvals table)
   └─ Insight Generation
```

**Database schema** (`sqlantra_database_v2.py`)

| Layer | Tables |
|---|---|
| Operational | `orders`, `products`, `order_items` |
| Bronze | `bronze_orders` |
| Silver | `silver_orders` |
| Gold | `gold_daily_sales`, `gold_product_performance`, `gold_customer_360` |
| Support | `hitl_approvals`, `context_memory_log` |

## Quick Start

Requires Python 3.8+. No third-party packages.

```bash
python3 web_demo.py
# open http://localhost:8766
```

LLM is optional. Without Ollama, the system runs entirely on the rule-based SQL fallback:

```bash
# optional: enable LLM-backed SQL generation
ollama pull qwen3.5:2b-q4_K_M
```

Default model/endpoint are declared in `web_demo.py` and `text_to_sql.py` (`MODEL`, `OLLAMA_URL`, `PORT`).

## API

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Web UI |
| `/api/tables` | GET | List all tables |
| `/api/table/{name}` | GET | Table data |
| `/api/memory` | GET | Context memory entries |
| `/api/hitl/pending` | GET | Pending approvals |
| `/api/query` | POST | Execute natural-language query (`{"query": "..."}`) |
| `/api/reset` | POST | Reset database and state |
| `/api/hitl/respond` | POST | Approve/reject a request |

## Testing

```bash
python3 test_system.py      # main workflow smoke test
python3 test_workflow.py    # agent pipeline test
python3 test_workflow2.py   # extended workflow coverage
python3 test_rapid.py       # quick endpoint checks
```

Manual verification while the server runs:

```bash
curl -s http://localhost:8766/api/tables
curl -s -X POST http://localhost:8766/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all completed orders"}'
```

## Project Layout

| File | Lines | Role |
|---|---|---|
| `web_demo.py` | 1359 | HTTP server, orchestration, embedded UI |
| `context_memory.py` | 742 | Memory store + skill/agent registries |
| `sqlantra_database_v2.py` | 502 | SQLite schema, CRUD, pipeline |
| `hitl_workflow.py` | 291 | Approval request lifecycle |
| `text_to_sql.py` | 274 | LLM + rule-based SQL generation |

## Skills Used

- Text-to-SQL prompt design (schema-aware prompting, LLM + deterministic fallback)
- Agent orchestration design (stateful multi-stage workflow, explicit routing)
- Human-in-the-loop system design (approval gates, audit trail)
- Context/memory systems (structured operation logging, persistence, retrieval)
- SQL and pipeline architecture (bronze/silver/gold, aggregations)
- Web API design (REST endpoints, embedded single-file UI)
- Python standard-library engineering (zero third-party runtime dependencies)

## License

MIT