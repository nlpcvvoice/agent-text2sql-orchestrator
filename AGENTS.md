# Sqlantra System V2 - Complete Developer Guide

## Overview

Sqlantra System V2 is an enterprise AI orchestration platform that demonstrates:
- Real SQLite database with orders/products/order_items tables
- **Text-to-SQL** using LLM (OpenRouter or Ollama, rule-based fallback)
- HITL (Human-In-The-Loop) approval workflow with approve/reject buttons
- Context Memory System for state persistence and intelligent recall
- Data Pipeline (Bronze/Silver/Gold layers)
- Real-time visualization of all system components

**No external Python dependencies** - Uses standard library only.

---

## Quick Start

```bash
python3 web_demo.py
# open http://localhost:8766
```

---

## Project Structure

```
web_demo.py                # Main entry point - HTTP server + HTML UI (single file)
sqlantra_database_v2.py    # SQLite database initialization and CRUD operations
text_to_sql.py             # Natural language to SQL conversion (LLM + rule-based fallback)
context_memory.py          # SqlantraContextMemory class - operation tracking and state persistence
hitl_workflow.py           # HITLWorkflow class - approval request handling
eval_golden_set.py         # Golden-set evaluation (rule vs LLM)
metrics_bench.py           # Load benchmark (QPS / p50 / p95 / error rate)
```

---

## Core Architecture

### Database Layers
- **Core tables**: orders, products, order_items
- **Pipeline layers**: bronze_/silver_/gold_* for each entity type
- **HITL table**: hitl_approvals for tracking approval requests
- **Memory table**: context_memory_log for operation tracking

### 4-Panel Web Interface
- **Top-Left**: User Input + HITL Approval buttons
- **Top-Right**: Sqlantra System Workflow (real-time step-by-step execution)
- **Bottom-Left**: Database Layer (real-time table viewer)
- **Bottom-Right**: Context Memory System (detailed operation tracking)

---

## Key Modules

### 1. web_demo.py
Main server - contains:
- HTTP server on port 8766
- Complete HTML/CSS/JS interface embedded
- API endpoints: `/`, `/api/tables`, `/api/table/{name}`, `/api/memory`, `/api/hitl/pending`, `/api/query`, `/api/reset`
- Step-by-step execution mode (press Enter/Space to advance)
- Auto-select table in database panel at step 5
- Auto-refresh context memory at step 4

### 2. sqlantra_database_v2.py (~500 lines)
Database operations:
- `init_database()` - Initialize all tables with sample data
- `query_sql(sql)` - Execute SQL query
- `get_table_data(table_name)` - Get table schema and data
- `get_all_tables()` - List all tables
- `insert_bronze_record()`, `insert_silver_record()` - Pipeline operations

### 3. text_to_sql.py (~250 lines)
Text-to-SQL conversion:
- `text_to_sql(query)` - Main entry point
- `rule_based_sql(query)` - Deterministic fallback when LLM unavailable
- `call_ollama(prompt)` - Unified LLM call (OpenRouter first, Ollama fallback)
- Schema-aware prompt engineering

### 4. context_memory.py (~600 lines)
Context memory system:
- `SqlantraContextMemory` class
- `store(key, value, operation, metadata)` - Store entry
- `get_recent_entries(limit)` - Get recent entries
- SkillsRegistry and AgentsRegistry for skill/agent matching

### 5. hitl_workflow.py (~250 lines)
HITL workflow:
- `HITLWorkflow` class
- `request_approval(action_type, data, requester)` - Create approval request
- `approve(approval_id, comment)` - Approve request
- `reject(approval_id, comment)` - Reject request

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main HTML interface |
| `/api/tables` | GET | List all database tables |
| `/api/table/{name}` | GET | Get data from specific table |
| `/api/memory` | GET | Get context memory entries |
| `/api/hitl/pending` | GET | Get pending approval requests |
| `/api/hitl/respond` | POST | Respond to approval request |
| `/api/query` | POST | Execute natural language query |
| `/api/reset` | POST | Reset system to initial state |

---

## Step-by-Step Execution Mode

When user clicks "Send Request", the system enters step-by-step mode:

| Step | Title | Action |
|------|-------|--------|
| 0 | Sqlantra Start Processing | System receives user request |
| 1 | Skill Matching | Match query to available skills |
| 2 | Agent Routing | Select appropriate agent |
| 3 | Text-to-SQL Generation | Convert natural language to SQL |
| 4 | Context Memory Update | Store query context (refresh memory panel) |
| 5 | Database Execution | Execute SQL (auto-select table in DB panel) |
| 6 | Pipeline Processing | Bronze→Silver→Gold transformation |
| 7 | HITL Approval Check | Check if approval needed |

**Controls**: Press ENTER or SPACE to advance to next step.

---

## Configuration

### Configuration

Default model and endpoints are declared in `web_demo.py` (`MODEL`, `PORT`) and `text_to_sql.py` (`MODEL`, `OLLAMA_URL`).

---

## Development Workflow

### Making Changes
1. Edit `web_demo.py` or other modules
2. Stop running server (Ctrl+C)
3. Restart: `python3 web_demo.py`

### Debugging
- Check browser console (F12) for JavaScript errors
- Check terminal for Python errors
- Database persists at `/tmp/sqlantra_v2_demo.db`

### Testing
```bash
# Quick test
curl -X POST http://localhost:8766/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all completed orders"}'

# List tables
curl -s http://localhost:8766/api/tables

# Reset system
curl -X POST http://localhost:8766/api/reset
```

### Run Test Script
```bash
python3 test_system.py
```

### Performance benchmark
```bash
python3 metrics_bench.py                     # QPS / p50 / p95 / error rate under load
python3 eval_golden_set.py                   # golden-set accuracy (rule vs LLM)
```
Server (`web_demo.py`) uses `ThreadingHTTPServer`; per-request cost is dominated by the bronze→silver→gold pipeline rebuild on read (~205 ms of ~210 ms).

---

## LLM Integration

### How It Works (priority order, in `llm_client.py`)
1. **OpenRouter** (default): when `OPENROUTER_API_KEY` env var is set, uses free models (`nvidia/nemotron-3-super-120b-a12b:free` etc.) via chat-completions, with a fallback model list on 429/errors.
2. **Local Ollama**: without the key, calls Ollama at `http://localhost:11434/api/generate` (offline development).
3. **Rule-based fallback**: if the LLM call fails (`Error calling LLM:`), falls back to `rule_based_sql()`.

Model/URL config lives in `llm_client.py`; `web_demo.py`, `text_to_sql.py`, and `hitl_workflow.py` delegate to `llm_client.call_llm`. Never print or log the API key (log `key_set=True/False` only).

---

## Context Memory System

### What It Tracks
- User queries and inputs
- Skill matching decisions
- Agent routing selections
- LLM calls (with prompts and responses)
- SQL generation and execution
- Database query results
- HITL approval requests and responses
- Data pipeline processing steps

### Storage
- In-memory OrderedDict (temporary)
- Optional JSON file persistence (`/tmp/sqlantra_context_memory.json`)

### Features
- Timestamped entries
- Operation type tracking
- Metadata storage
- JSON value formatting for display

---

## HITL Approval Workflow

### Trigger Conditions
- Any expense amount > category threshold (see ExpenseCategory)

### Flow
1. User queries high-value data
2. System detects threshold
3. Creates approval request
4. User sees approve/reject buttons
5. Decision recorded in context memory

---

## Database Schema

### orders
| Column | Type | Description |
|--------|------|-------------|
| order_id | TEXT | Primary key |
| channel | TEXT | 'Web', 'App', 'POS', 'API' |
| customer_id | TEXT | Customer ID |
| order_date | TEXT | Order date |
| total_amount | REAL | Order total |
| status | TEXT | 'pending', 'completed', 'cancelled' |
| raw_data | TEXT | Original payload JSON |
| created_at | TEXT | Creation timestamp |
| updated_at | TEXT | Update timestamp |

### products
| Column | Type | Description |
|--------|------|-------------|
| product_id | TEXT | Primary key |
| name | TEXT | Product name |
| category | TEXT | 'Electronics', 'Audio', 'Footwear', 'Toys' |
| price | REAL | Unit price |
| stock | INTEGER | Available quantity |
| created_at | TEXT | Creation timestamp |

### order_items
| Column | Type | Description |
|--------|------|-------------|
| item_id | INTEGER | Primary key (autoincrement) |
| order_id | TEXT | FK to orders |
| product_id | TEXT | FK to products |
| quantity | INTEGER | Quantity purchased |
| unit_price | REAL | Price at purchase |

---

## Sample Queries to Test

```bash
# Test 1: Basic query
curl -X POST http://localhost:8766/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all completed orders"}'

# Test 2: List tables
curl -s http://localhost:8766/api/tables

# Test 3: Get specific table
curl -s http://localhost:8766/api/table/orders

# Test 4: Reset
curl -X POST http://localhost:8766/api/reset
```

---

## Known Issues / Notes

1. **Output buffering**: Python may delay output. Use `PYTHONUNBUFFERED=1` if needed:
   ```bash
   PYTHONUNBUFFERED=1 python3 web_demo.py
   ```

2. **Port in use**: If port 8766 is busy, kill existing process:
   ```bash
   pkill -f web_demo.py
   ```

3. **Database lock**: Use reset button or `/api/reset` to clear locks

4. **No SQLite dependencies**: No `sqlite3` pip package needed - uses standard library

---

## Verification Commands

```bash
# Start server
python3 web_demo.py

# In another terminal, test endpoints
curl -s http://localhost:8766/ | grep "<title>"
curl -s http://localhost:8766/api/tables | python3 -m json.tool | head -5
curl -s -X POST http://localhost:8766/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all orders"}' | python3 -m json.tool
```

---

*Last updated: 2026-09-14*