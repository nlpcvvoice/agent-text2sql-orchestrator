# Agent Text2SQL Orchestrator

[![CI](https://github.com/nlpcvvoice/agent-text2sql-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/nlpcvvoice/agent-text2sql-orchestrator/actions)

A stateful agent pipeline that converts natural-language e-commerce questions into SQL, enforces a human-in-the-loop approval gate on high-value actions, and refreshes a layered analytics store on every query. Zero third-party runtime dependencies.

> **One-second summary:** type a business question → an 8-stage agent orchestrates skill matching, SQL generation (LLM with deterministic fallback), execution, approval checks, and insight output → you get an auditable, human-gated result.

## Live demo

Demo endpoint is being set up (see [Deployment roadmap](#deployment-roadmap)). Until then, the fastest way to evaluate the system:

```bash
python3 web_demo.py        # no setup, no packages
# open http://localhost:8766
```

## Why this exists

This project demonstrates how an agent workflow can wrap a text-to-SQL capability rather than treating SQL generation as a single-shot LLM call. The query path is decomposed into explicit stages — skill matching, agent routing, SQL generation (LLM with deterministic fallback), context logging, execution, pipeline refresh, and insight generation — so every step is observable and testable. A human-in-the-loop approval gate interrupts high-value actions before they are committed.

## Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| SQL generation | LLM with rule-based fallback | A deterministic fallback keeps the pipeline usable when the model is unreachable; the two paths make quality differences measurable (see [Evaluation](#evaluation)) |
| Human-in-the-loop | Tool-permissioning gate with category thresholds | Instead of blanket approvals, each action type maps to a threshold (e.g., travel > $1000), mirroring how production agents gate side-effecting tool calls |
| Runtime | Python standard library only | No `requirements.txt`, no dependency drift; the heavy lifting is the orchestration logic, not libraries |
| Storage | SQLite | Zero-ops persistence with real SQL semantics suitable for a self-contained demo; schema is portable to Postgres |
| Pipeline | Bronze → Silver → Gold on every execution | Query results refresh a medallion store, so text-to-SQL is wired into data engineering, not an island feature |
| Web surface | Single-file server + embedded UI | One `python3 web_demo.py` to inspect every stage, memory log, and approval — reviewers see the full loop without setup |

## Highlights

| Capability | What it does | Where |
|---|---|---|
| Text-to-SQL | Converts natural language to SQL via LLM, with a rule-based deterministic fallback when the model is unavailable | `text_to_sql.py` |
| Agent orchestration | 8-stage pipeline: skill matching → agent routing → SQL → memory → execution → pipeline → HITL check → insights | `web_demo.py` |
| Human-in-the-loop | Tool-permissioning gate: high-value actions create approval requests with category thresholds; decisions are recorded and enforced | `hitl_workflow.py` |
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

LLM is optional. Without a model backend, the system runs entirely on the rule-based SQL fallback:

```bash
# optional: enable LLM-backed SQL generation
# 1) OpenRouter (default when OPENROUTER_API_KEY is set, no local install)
# 2) local Ollama, e.g.:
ollama pull qwen3.5:2b-q4_K_M
```

Model selection is priority-ordered in `llm_client.py`: OpenRouter free models first, then local Ollama, then the deterministic rule path.

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

## Evaluation

The SQL generation path is measured against a golden set of 30 hand-labeled e-commerce queries (12 exact-rule hits, 6 near-rule, 12 LLM-only). Every query maps to an expected SQL statement; the system compares the generated SQL (LLM vs rule-based fallback) for exact-match, validity (executes without error), and normalized equivalence (equal result rows).

| Path | Exact-match | Valid | Equivalent | Median latency |
|---|---|---|---|---|
| `rule_based_sql` (deterministic) | 18/30 (60%) | 30/30 (100%) | 18/30 (60%) | 0 ms |
| LLM (OpenRouter free, 2-run avg) | 12/30 (40%) | 30/30 (100%) | 23/30 (76.7%) | ~2.2 s |

Class split on the rule-based path: 12/12 exact on covered patterns, 0/12 on LLM-only intents — the fallback is a safety net, not a generalizer. LLM wins on equivalent correctness (+16.7 pp) at a latency cost — the core tradeoff the dual-path design is built around. Free-model availability is variable (see [Testing](#testing) for offline verification). Run locally:

```bash
python3 eval_golden_set.py   # prints the comparison table above with real numbers
```

The harness lives near the top of the repo (see [Project Layout](#project-layout)) and doubles as a regression test: any change that lowers pass rate below the baseline fails the [CI](#testing) gate.

## Performance under load

Measured with `metrics_bench.py` (mixed 10-query set, N concurrent clients, 30 requests/wave, rule path):

| Concurrency | QPS | p50 (ms) | p95 (ms) | Error rate | Cost/query |
|---|---|---|---|---|---|
| 1 | 4.5 | 157 | 427 | 0.0% | $0.000 (local) |
| 5 | 3.5 | 1154 | 2447 | 0.0% | $0.000 |
| 10 | 3.8 | 2425 | 3905 | 0.0% | $0.000 |
| 20 | 3.6 | 4359 | 5655 | 0.0% | $0.000 |

A single request costs ~210 ms, of which ~205 ms is the **pipeline write path** (bronze → silver → gold is recomputed on every read); SQL parsing and querying are ~3 ms. Under concurrency, SQLite write-lock contention shows up as p50/p95 growth rather than throughput loss; error rate stays 0%.

`run: python3 metrics_bench.py`

## Known failure modes

Deliberately documented so the guarantees are explicit (and the trade-offs are visible to reviewers).

| Failure mode | Trigger | Observable behavior | Mitigation |
|---|---|---|---|
| LLM hallucinates SQL (fabricated columns/joins) | coverage gap in rule set | wrong-but-syntactically-valid query | rule-based fallback still executes; `SELECT`-only discipline; post-processing fixups |
| LLM emits prose/fenced response | model returns text instead of SQL | non-SELECT output | stripping (` ```sql ` fences), `SELECT` prefix guard, else fallback |
| Rule set misses intent | out-of-vocabulary phrasing | falls back to generic `completed orders` query | routed to LLM path instead; golden set tracks coverage (`LLM_ONLY` class) |
| Free model unavailable / rate-limited | OpenRouter 429 or Ollama down | latency spikes, eventual fallback | model list rotation with retries, then deterministic rule path |
| SQLite write contention | high concurrency on read+rebuild | p50/p95 growth (see table) | single-writer design for the demo; WAL or Postgres for production |
| Threshold boundary | expense exactly at category limit | gate decision depends on `>` vs `>=` | thresholds centralized in `hitl_workflow.py`, used by both reporter and gate |

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

## Deployment roadmap

The system is designed to ship as a single container. Planned path:

| Step | Target |
|---|---|
| Package | `Dockerfile` + `start.sh` wrapping `web_demo.py` on port 8766 |
| Host | Hugging Face Space — basic CPU tier (preferred; stdlib + SQLite need no GPU) |
| Alt. host | HF Spaces **ZeroGPU** (GPU-backed, for a future local-LLM inference variant) or Railway free tier |
| Outcome | Persistent public URL for the web UI and `/api/*` endpoints |

Until the endpoint is live, local verification via `python3 web_demo.py` is the canonical path.

## License

MIT