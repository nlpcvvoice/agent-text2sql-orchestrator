# Sqlantra System V2 - Comprehensive Technical Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Design](#architecture-design)
3. [Database Schema](#database-schema)
4. [Module Specifications](#module-specifications)
5. [Ollama Integration](#ollama-integration)
6. [Context Memory System](#context-memory-system)
7. [HITL Workflow](#hitl-workflow)
8. [Web Interface](#web-interface)
9. [API Endpoints](#api-endpoints)
10. [Design Decisions](#design-decisions)
11. [Future Extensions](#future-extensions)
12. [Troubleshooting](#troubleshooting)

---

## 1. Project Overview

### Purpose
Sqlantra System V2 is an enterprise AI orchestration platform that demonstrates:
- Real SQLite database operations
- Text-to-SQL conversion using Ollama
- Human-in-the-loop (HITL) approval workflows
- Context memory system for state persistence
- Real-time web-based visualization

### Location
```
/path/to/Sqlantra-local-ollama_mysql_v2_1/
```

### Core Files
| File | Purpose |
|------|---------|
| `sqlantra_database_v2.py` | SQLite database with pipeline layers |
| `text_to_sql.py` | Natural language to SQL conversion |
| `context_memory.py` | Memory system, skills, agents |
| `hitl_workflow.py` | Approval workflow management |
| `web_demo.py` | 4-panel web interface |

---

## 2. Architecture Design

### System Components
```
┌─────────────────────────────────────────────────────────────────┐
│                     Web Interface (Port 8766)                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────┐ │
│  │ User Input   │ │ Sqlantra Workflow │ │   Database   │ │Memory │ │
│  │ + HITL       │ │   Display    │ │   Tables     │ │Panel  │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └───────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Sqlantra Demo Handler                              │
│  - Skill Matching    - Agent Routing                            │
│  - Text-to-SQL       - Query Execution                          │
│  - Pipeline Processing - HITL Workflow                          │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │   Ollama    │    │  SQLite    │    │   Context  │
    │  (LLM)      │    │  Database  │    │   Memory   │
    └─────────────┘    └─────────────┘    └─────────────┘
```

### Data Flow
1. User enters query in web interface
2. Query matched to skills (keyword-based scoring)
3. Query routed to appropriate agent
4. Ollama generates SQL from natural language
5. SQL executed against SQLite database
6. Results processed through pipeline (Bronze→Silver→Gold)
7. High-value transactions trigger HITL approval
8. All operations logged to context memory

---

## 3. Database Schema

### Database Location
```
/tmp/sqlantra_v2_demo.db
```

### Core Business Tables

#### orders
```sql
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    channel TEXT NOT NULL,             -- 'Web', 'App', 'POS', 'API'
    customer_id TEXT,
    order_date TEXT,                   -- ISO date string
    total_amount REAL NOT NULL,        -- Numeric amount
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'completed', 'cancelled'
    raw_data TEXT,                     -- JSON of original payload
    created_at TEXT,                   -- ISO timestamp
    updated_at TEXT                    -- ISO timestamp
);
```
**Sample Data:** 8 orders (Web/App/POS/API channels) with amounts from $89.99 to $4,797.00

#### products
```sql
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,                     -- 'Electronics', 'Audio', 'Footwear', 'Toys'
    price REAL NOT NULL,
    stock INTEGER DEFAULT 0,
    created_at TEXT
);
```
**Sample Data:** 5 products (MacBook Pro, iPhone 15 Pro, etc.)

#### order_items
```sql
CREATE TABLE order_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    product_id TEXT,
    quantity INTEGER,
    unit_price REAL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```
**Sample Data:** 8 line items linking orders to products

### Pipeline Layer Tables

The pipeline implements the Bronze→Silver→Gold architecture for orders:

#### Bronze Layer (Raw Data)
```sql
CREATE TABLE bronze_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    raw_data TEXT,           -- JSON of original data
    _source TEXT,           -- 'channel_input', 'api', etc.
    _ingested_at TEXT       -- ISO timestamp
);
```

#### Silver Layer (Curated/Normalized)
```sql
CREATE TABLE silver_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    channel TEXT,
    customer_id TEXT,
    total_amount REAL,
    status TEXT,
    order_date TEXT,
    _curated_at TEXT,       -- ISO timestamp
    _domain TEXT            -- 'orders'
);
```

#### Gold Layer (Enriched/Business-Ready)
```sql
CREATE TABLE gold_daily_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    channel TEXT,
    total_orders INTEGER,
    total_revenue REAL,
    avg_order_value REAL,
    _processed_at TEXT
);

CREATE TABLE gold_product_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT,
    product_name TEXT,
    category TEXT,
    total_sold INTEGER,
    total_revenue REAL,
    stock_alert TEXT,
    _processed_at TEXT
);

CREATE TABLE gold_customer_360 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT,
    total_orders INTEGER,
    total_spent REAL,
    avg_order_value REAL,
    customer_segment TEXT,   -- 'VIP', 'PREMIUM', 'STANDARD'
    clv_prediction REAL,
    _processed_at TEXT
);
```

### System Tables

#### hitl_approvals
```sql
CREATE TABLE hitl_approvals (
    approval_id TEXT PRIMARY KEY,
    action_type TEXT NOT NULL,     -- 'high_value_transaction', etc.
    details TEXT NOT NULL,         -- JSON with details
    requester TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'approved', 'rejected'
    comment TEXT,
    notification TEXT,              -- Slack-style notification message
    created_at TEXT,
    responded_at TEXT
);
```

#### context_memory_log
```sql
CREATE TABLE context_memory_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_key TEXT,
    memory_value TEXT,
    operation TEXT,               -- 'store', 'recall', etc.
    metadata TEXT,                -- JSON with additional info
    created_at TEXT
);
```

---

## 4. Module Specifications

### sqlantra_database_v2.py

**Purpose:** SQLite database management with pipeline layer support

**Key Functions:**

#### `init_database()`
- Creates all tables if not exist
- Inserts sample data (8 orders, 5 products, 8 order_items)
- Called automatically on module import

#### `get_all_tables()`
- Returns list of all table names in database
- Used for populating table selector in UI

#### `get_table_data(table_name, limit=100)`
- Returns columns and rows for specified table
- Used by `/api/table/{name}` endpoint

#### `query_sql(sql, params=())`
- Executes raw SQL against database
- Returns: `{"columns": [...], "data": [...], "error": str or None}`
- Handles both SELECT and non-SELECT statements

#### `insert_bronze_record(order_id, raw_data)`
- Inserts raw JSON data into bronze layer
- Domain mapping: orders → `bronze_orders`

#### `insert_silver_record(order_data)`
- Inserts curated/normalized data into silver layer
- Handles type conversions

#### `process_gold_metrics()`
- Processes silver data into gold layer metrics (daily sales, product performance, customer 360)
- Adds business logic (customer segmentation, CLV prediction, stock alerts)

#### `create_approval(action_type, details, requester, notification)`
- Creates HITL approval request
- Returns: `{"approval_id": str, "status": "pending", "created_at": str}`

#### `respond_approval(approval_id, approved, comment)`
- Updates approval status
- Returns: `{"approval_id": str, "status": "approved"|"rejected"}`

#### `get_pending_approvals()`
- Returns all approvals with status='pending'

#### `log_context_memory(memory_key, memory_value, operation, metadata)`
- Persists memory operations to database

---

### text_to_sql.py

**Purpose:** Convert natural language queries to SQL using Ollama OR rule-based fallback

**Configuration:**
```python
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3.5:2b-q4_K_M"  # Default to smaller model
```

**Key Functions:**

#### `call_ollama(prompt, timeout=60)`
- Makes HTTP POST to Ollama API
- Returns response text or error message
- Temperature: 0.1 (low for consistent SQL generation)
- Max tokens: 512
- **Note:** Returns "Error calling Ollama: ..." on failure

#### `get_table_schemas()`
- Returns detailed schema information for all tables
- Includes column descriptions and value constraints
- **Critical:** Documents that `hitl_approvals` has NO `amount` column

#### `text_to_sql(natural_language_query)`
1. Builds prompt with system instructions + table schemas
2. Sends to Ollama
3. Post-processes response:
   - Strips markdown code blocks
   - **Fixes common SQL errors:**
     - Removes erroneous `amount` conditions from hitl_queries
     - Cleans up malformed WHERE clauses
4. If Ollama fails (error in response OR no SELECT), falls back to rule-based SQL
5. Returns generated SQL

#### `rule_based_sql(query)` - **NEW: Automatic Fallback**
When Ollama is unavailable (out of memory, not running, etc.), the system uses pattern matching:

```python
RULES = [
    (r"completed.*order|order.*completed", 
     "SELECT * FROM orders WHERE status = 'completed'"),
    (r"pending.*order|order.*pending", 
     "SELECT * FROM orders WHERE status = 'pending'"),
    (r"daily.*sales|sales.*report", 
     "SELECT * FROM gold_daily_sales ORDER BY date DESC"),
    (r"product.*performance|top.*product", 
     "SELECT * FROM gold_product_performance ORDER BY total_revenue DESC"),
    (r"customer.*360|customer.*segment", 
     "SELECT * FROM gold_customer_360 ORDER BY total_spent DESC"),
    (r"order.*over.*?(\d+)", 
     "SELECT * FROM orders WHERE total_amount > {0}"),
]
```

Supported queries:
- "Show all completed orders" → `SELECT * FROM orders WHERE status = 'completed'`
- "List pending orders" → `SELECT * FROM orders WHERE status = 'pending'`
- "Show daily sales report" → `SELECT * FROM gold_daily_sales ORDER BY date DESC`
- "Top products" → `SELECT * FROM gold_product_performance ORDER BY total_revenue DESC`
- "Show orders over $1,000" → `SELECT * FROM orders WHERE total_amount > 1000`

#### `execute_text_query(db_module, natural_language_query)`
- Combines text_to_sql + query_sql execution
- Returns complete result with query, SQL, data, row_count, error

#### `generate_sql_explanation(sql, result_data, natural_query)`
- Uses Ollama to explain query results in plain English
- Called after query execution

**Design Decision - Post-Processing:**
The post-processing regex logic handles a known issue where Ollama sometimes generates invalid SQL for the `hitl_approvals` table (querying for a non-existent `amount` column). The fix:
```python
# Remove amount conditions from hitl_approvals queries
sql = re.sub(r"\s+AND\s+amount\s*[=<>!]+\s*[\d\.]+", "", sql, flags=re.IGNORECASE)
```

**Design Decision - Rule-Based Fallback:**
The system automatically falls back to rule-based SQL when Ollama fails:
1. If response starts with "Error calling Ollama"
2. If response is empty
3. If no SELECT keyword in response
4. Pattern matching on query text for known query types

This ensures the demo works even without Ollama running.

---

### context_memory.py

**Purpose:** In-memory state tracking with database persistence

**Key Classes:**

#### ContextMemoryEntry
Represents a single memory entry with:
- `key`: Unique identifier
- `value`: Stored data (any type)
- `operation`: Type of operation ('store', 'recall', etc.)
- `timestamp`: ISO format datetime
- `id`: Unique memory ID
- `operation_type`: Classification (WRITE, READ, LLM_SQL, etc.)
- `caller_file`, `caller_line`, `caller_function`: Stack trace info

#### SqlantraContextMemory
In-memory memory system with:
- **Thread-safe** using `threading.Lock`
- **OrderedDict** for maintaining insertion order
- **LRU eviction** when exceeding MAX_MEMORY_SIZE (2000)
- **Database persistence** optional (via set_db_module)

**Key Methods:**

#### `store(key, value, operation, metadata)`
- Stores value in memory
- Auto-captures caller info via traceback
- Logs to database if db_module set
- Returns ContextMemoryEntry

#### `recall(key)`
- Retrieves value by key
- **Also logs the recall** as a new memory entry (audit trail)

#### `log_ollama_call(prompt, response, model, duration_ms)`
- Specialized logging for LLM calls
- Stores prompt preview, response preview, timing

#### `log_mcp_call(tool_name, params, result, success)`
- Specialized logging for MCP tool calls

#### `get_detailed_entries(limit=20)`
- Returns formatted entries for UI display
- Includes formatted value (JSON pretty-print, truncation)

#### `search(query)`
- Searches keys and string values

#### SkillsRegistry
Registry for Sqlantra skills with keyword-based matching.

**Default Skills:**
| Skill ID | Name | Description | Category |
|----------|------|-------------|----------|
| query_database | Query Database | Execute SQL queries | database |
| approval_workflow | HITL Approval Workflow | Request human approval | workflow |
| data_pipeline | Data Pipeline | Process Bronze→Silver→Gold | pipeline |
| context_recall | Context Recall | Recall from memory | memory |
| semantic_transform | Semantic Transform | Transform queries | nlp |

**Skill Matching Algorithm (match_skill):**
1. Check for exact substring match in skill name (score: 20)
2. Check for exact substring match in description (score: 15)
3. If no exact match:
   - Count matching words between query and skill name (3 pts each)
   - Count matching words between query and description (2 pts each)
   - **Category-specific keyword bonuses:**
     - `approval_workflow`: approval, request, approve, reject, high-value, transaction
     - `query_database`: show, list, find, get, select, query, order, product, sales, amount, total, sum, count, over, under, greater, less
     - `data_pipeline`: process, pipeline, bronze, silver, gold, ingest, curate, enrich, transform
     - `context_recall`: memory, recall, remember, context, history, past, store, retrieve

#### AgentsRegistry
Registry for Sqlantra agents with keyword-based routing.

**Default Agents:**
| Agent ID | Name | Skills | Capabilities |
|----------|------|--------|--------------|
| query_agent | Query Agent | query_database, semantic_transform | text_to_sql, db_query, data_analysis |
| approval_agent | Approval Agent | approval_workflow | request_approval, notify, workflow_control |
| pipeline_agent | Pipeline Agent | data_pipeline | bronze_ingest, silver_curate, gold_enrich |
| memory_agent | Memory Agent | context_recall | store, recall, search, persist |

**Agent Matching (match_agent):**
- Simple keyword matching (any keyword triggers agent)
- Falls back to query_agent if no match

---

### hitl_workflow.py

**Purpose:** Human-in-the-loop approval workflow management

**Configuration:**
```python
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3.5:2b-q4_K_M"
# Note: Uses higher temperature (0.3) for more creative notifications
```

**Key Class: HITLWorkflow**

#### `request_approval(action_type, details, requester)`
1. Generate Slack-style notification using Ollama
2. Create approval record in database
3. Store in pending_requests dict
4. Log to context memory
5. Return: `{"approval_id": str, "notification": str, "pending": bool}`

#### `approve(approval_id, comment, approver)`
1. Update database with approved status
2. Execute registered workflow handler if exists
3. Log to context memory
4. Generate confirmation message via Ollama
5. Return: `{"status": "approved", "approval_id": str, "message": str}`

#### `reject(approval_id, comment, approver)`
1. Update database with rejected status
2. Log to context memory
3. Generate rejection message via Ollama
4. Return: `{"status": "rejected", "approval_id": str, "message": str}`

#### `get_pending_for_ui()`
- Returns pending requests formatted for UI display

**Notification Generation:**
Uses Ollama with specific prompt:
```
Generate a Slack-style notification message for a human approval request.
- Concise (under 200 characters)
- Include action type and key details
- Mention who requested it
- Professional but friendly
- Start with "🤖 *Sqlantra Notification*"
```

**Response Message Generation:**
```
Generate a brief confirmation message (under 100 characters).
- Confirm action and status
- Acknowledge any comment
- Start with emoji: ✅ if approved, ❌ if rejected
```

---

### web_demo.py

**Purpose:** HTTP server with 4-panel web interface

**Configuration:**
```python
PORT = 8766
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3.5:2b-q4_K_M"
```

**HTTP Server:**
- Uses Python's built-in `http.server.HTTPServer`
- Custom request handler for GET/POST

**HTML Interface:**

#### 4-Panel Layout:
```
┌─────────────────────────────────────────────────────────┐
│  User Input + HITL    │    Sqlantra Workflow Display       │
│  (textarea, buttons)   │    (step-by-step logs)      │
├─────────────────────────────────────────────────────────┤
│  Database Tables       │    Context Memory             │
│  (table selector)     │    (detailed entries)         │
└─────────────────────────────────────────────────────────┘
```

**UI Features:**
- Dark theme with color-coded panels
- Scenario dropdown selector
- Real-time updates (polling)
- Highlight animations for new content
- HITL approval buttons (approve/reject)
- Table data viewer with pagination

**Scenario Selector Options:**
- `user_query`: Default SQL query demo
- `pipeline`: Data pipeline demonstration
- `hitl_workflow`: HITL approval demo
- `context_memory`: Memory exploration
- `full_demo`: Combined demo

---

## 5. Ollama Integration

### Model Used
```
qwen3.5:2b-q4_K_M
```

### API Endpoint
```
POST http://localhost:11434/api/generate
```

### Request Format
```json
{
    "model": "qwen3.5:2b-q4_K_M",
    "prompt": "...",
    "stream": false,
    "options": {
        "temperature": 0.1,
        "num_predict": 512
    }
}
```

### Usage in System

#### 1. Text-to-SQL (text_to_sql.py)
- **Temperature:** 0.1 (low for deterministic SQL)
- **Max tokens:** 512
- **Prompt:** System instructions + table schemas + user query

#### 2. HITL Notifications (hitl_workflow.py)
- **Temperature:** 0.3 (slightly creative)
- **Max tokens:** 256
- **Purpose:** Generate human-readable Slack-style messages

#### 3. SQL Explanation (text_to_sql.py)
- **Temperature:** 0.1
- **Max tokens:** 256
- **Purpose:** Explain query results in plain English

### Error Handling
All Ollama calls include try/except with fallback:
```python
except Exception as e:
    return f"Error calling Ollama: {e}"
```

---

## 6. Context Memory System

### Architecture

```
┌─────────────────────────────────────────────┐
│           SqlantraContextMemory                  │
│  ┌─────────────────────────────────────┐  │
│  │  OrderedDict (key → Entry)          │  │
│  │  - Thread-safe with Lock            │  │
│  │  - Max 2000 entries (LRU evict)    │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Operation History List              │  │
│  │  - Timestamps                        │  │
│  │  - Operation types                    │  │
│  │  - Keys                              │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Ollama Calls Log                   │  │
│  │  - Prompt/response previews          │  │
│  │  - Timing                             │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  MCP Calls Log                       │  │
│  │  - Tool name, params, results        │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
          │                    │
          ▼                    ▼
   ┌──────────────┐    ┌──────────────┐
   │ In-Memory    │    │   Database   │
   │ (OrderedDict)│    │ (persistent) │
   └──────────────┘    └──────────────┘
```

### Operation Types (Classification)
| Type | Description |
|------|-------------|
| WRITE | New value stored |
| READ | Value recalled |
| SYSTEM | System event |
| SKILL_MATCH | Skill matched to query |
| AGENT_ROUTING | Agent selected |
| LLM_SQL | SQL generated |
| DATABASE | Query executed |
| HITL_REQUEST | Approval requested |
| HITL_APPROVED | Approval granted |
| HITL_REJECTED | Approval denied |
| PIPELINE | Data processed |
| WORKFLOW | Workflow executed |
| USER_INPUT | User query received |
| LLM_CALL | Ollama called |
| MCP_CALL | MCP tool called |

### Caller Information Capture
Uses Python's `traceback.extract_stack()` to capture:
- Source file (last 3 frames)
- Line number
- Function name

This enables detailed debugging and audit trails.

---

## 7. HITL Workflow

### Workflow Diagram
```
User Query
    │
    ▼
Text-to-SQL + Execute
    │
    ▼
Check: High-value transaction? (>$50,000)
    │
    ├── No ──────────────────► Process Pipeline
    │                               │
    │                               ▼
    │                        Return Results
    │
    └── Yes ──► Request Approval
                      │
                      ▼
              ┌───────────────┐
              │ HITL Approval │
              │ (Pending)     │
              └───────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
   [Approve]                  [Reject]
        │                           │
        ▼                           ▼
  Execute Handler          Log Rejection
  (if registered)          Return Results
        │
        ▼
  Log Approval
  Return Results
```

### Approval Types
- `high_value_transaction`: For transactions > $50,000
- Custom types can be registered via `register_workflow_handler()`

### Handler Registration
```python
def my_handler(details, approved, comment):
    # Custom logic after approval
    return {"result": "processed"}

hitl.register_workflow_handler("high_value_transaction", my_handler)
```

---

## 8. Web Interface

### Panel Details

#### Top-Left: User Input + HITL
- Textarea for query input
- "Send Request" button
- HITL approval section (appears when pending approvals exist)
- Approve/Reject buttons with comments

#### Top-Right: Sqlantra Workflow Display
- Step-by-step workflow visualization
- Shows: Skill matching, Agent routing, SQL generation, Context memory update, DB execution, Pipeline processing, HITL check
- Each step shows: Number, Title, Detail, Code (if applicable)
- Color-coded by status (info, success, error)

#### Bottom-Left: Database Tables
- Dropdown to select table
- Status bar: DB connection, Ollama model, row count
- Scrollable data table
- All 15 tables accessible

#### Bottom-Right: Context Memory
- Real-time memory entry display
- Shows: Key, Operation type, Value (truncated), Timestamp
- Color-coded by operation type

### Real-Time Updates
- Memory: Every 3 seconds
- HITL pending: Every 5 seconds
- Database tables: On selection change

### Highlight Animations
- New log entries get golden highlight
- Auto-fades after 3 seconds
- Applied to: User queries, Approvals, Rejections, Errors

---

## 9. API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main HTML interface |
| `/api/tables` | GET | List all database tables |
| `/api/table/{name}` | GET | Get data from table |
| `/api/memory` | GET | Get context memory entries |
| `/api/hitl/pending` | GET | Get pending approvals |
| `/api/hitl/respond` | POST | Approve/Reject (JSON body) |
| `/api/query` | POST | Execute query (JSON body) |
| `/api/reset` | POST | Reset system |

### Query API Request Format
```json
{
    "query": "Show all completed orders"
}
```

### Query API Response Format
```json
{
    "query": "Show all completed orders",
    "sql": "SELECT * FROM orders WHERE status = 'completed'",
    "data": [
        {"order_id": "ORD-001", "channel": "Web", "total_amount": 2478.0, ...}
    ],
    "workflow": [
        {"step": 1, "title": "Skill Matching", "detail": "...", "code": "..."},
        ...
    ],
    "error": null
}
```

### HITL Response Request Format
```json
{
    "approval_id": "APR-20260423120000",
    "approved": true,
    "comment": "Approved by manager"
}
```

---

## 10. Design Decisions

### Why SQLite?
- Simple, file-based, no external dependencies
- Suitable for demo purposes
- Easy to reset and reinitialize

### Why qwen3.5:2b-q4_K_M?
- Good balance of capability and speed
- Supports instruction following for SQL generation
- Works well with local Ollama deployment

### Why In-Memory + Database Persistence?
- In-memory: Fast access, thread-safe, real-time
- Database: Persistent audit trail across sessions

### Skill/Agent Matching Algorithm
- Weighted keyword matching rather than exact match
- Allows flexibility in user queries
- Category-specific keywords for accuracy

### Pipeline Architecture
- Bronze: Raw data with metadata (source, timestamp)
- Silver: Curated, type-converted, domain-tagged
- Gold: Business rules applied, enriched

---

## 11. Future Extensions

### Database
- [ ] Add more business tables (employees, departments, budgets)
- [ ] Implement actual foreign key relationships
- [ ] Add indexes for performance
- [ ] Support for PostgreSQL/MySQL (currently SQLite only)

### Text-to-SQL
- [ ] Support for JOIN queries
- [ ] Aggregation functions (SUM, AVG, COUNT)
- [ ] Better error handling for invalid SQL
- [ ] Query history and favorites

### Context Memory
- [ ] Vector similarity search
- [ ] Automatic memory summarization
- [ ] Session persistence
- [ ] Memory expiration policies

### HITL Workflow
- [ ] Multiple approvers with escalation
- [ ] Email notification integration
- [ ] Approval deadline/timeout
- [ ] Audit trail with signatures

### Web Interface
- [ ] WebSocket for real-time updates
- [ ] User authentication
- [ ] Query history sidebar
- [ ] Export to CSV/Excel

### Pipeline
- [ ] Actual data transformation functions
- [ ] Validation rules
- [ ] Data quality scoring
- [ ] Incremental processing

---

## 12. Troubleshooting

### Server Won't Start
```bash
# Check if port is already in use
lsof -i :8766
# Kill existing process
kill <PID>
# Or use a different port in web_demo.py
PORT = 8767
```

### Ollama Connection Error
```bash
# Check if Ollama is running
ollama list
# Start Ollama
ollama serve
# Pull model if needed
ollama pull qwen3.5:2b-q4_K_M
```

### Database Errors
```bash
# Reset database to clean state
# Call /api/reset endpoint or:
rm /tmp/sqlantra_v2_demo.db
# Restart server - will auto-recreate
```

### High Memory Usage
- Context memory auto-evicts at 2000 entries
- Can reduce MAX_MEMORY_SIZE in context_memory.py

### Query Errors
- Check API response for SQL error messages
- Verify table/column names match schema
- Use `/api/tables` to list available tables

---

## Appendix: File Structure

```
Sqlantra-local-ollama_mysql_v2_1/
├── sqlantra_database_v2.py    # 698 lines - Database management
├── text_to_sql.py         # 182 lines - NL to SQL conversion
├── context_memory.py      # 610 lines - Memory + Skills + Agents
├── hitl_workflow.py       # 262 lines - Approval workflow
├── web_demo.py            # 876 lines - HTTP server + HTML UI
└── README.md              # This documentation
```

---

## Appendix: Quick Reference

### Starting the System
```bash
cd /path/to/Sqlantra-local-ollama_mysql_v2_1
source /path/to/sqlantra_env/bin/activate
python3 web_demo.py
# Open http://localhost:8766
```

### Key Configuration
```python
# Database
DB_PATH = "/tmp/sqlantra_v2_demo.db"

# Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3.5:2b-q4_K_M"

# Server
PORT = 8766
```

### Environment Requirements
- Python 3.8+
- Ollama running with qwen3.5:2b-q4_K_M model
- SQLite3 (built into Python)
- No additional pip packages required

---

*This documentation was generated for Sqlantra System V2. For questions or clarifications, refer to the source code comments or contact the development team.*
