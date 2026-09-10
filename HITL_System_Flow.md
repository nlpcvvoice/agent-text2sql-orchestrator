# HITL Expense Approval - 完整系统流程图

## 整体技术流程

```mermaid
flowchart TB
    subgraph CLIENT["🌐 浏览器 UI"]
        INPUT[用户输入]
        SEND[点击 Send]
        PANEL1[用户输入面板]
        PANEL2[Sqlantra Workflow]
        PANEL3[审批面板]
        PANEL4[Context Memory]
    end

    subgraph SERVER["⚙️ Sqlantra Server (Python)"]
        HTTP[API Handler]
        
        subgraph PARSE["📝 解析层"]
            P1[Parse Expense]
            P2[Extract fields]
        end
        
        subgraph VALIDATE["✅ 验证层"]
            V1[Validate category]
            V2[Get threshold]
            V3[Compare amount]
        end
        
        subgraph HITL["🔔 HITL Workflow"]
            H1[Create approval]
            H2[Generate notification]
            H3[Store pending]
        end
        
        subgraph OLLAMA["🤖 Ollama LLM"]
            O1[Generate notification]
        end
        
        subgraph MEM["🧠 Context Memory"]
            M1[Store each step]
            M2[Log operations]
        end
        
        subgraph DB["🗄️ SQLite"]
            DB1[Write approval]
            DB2[Log memory]
        end
    end

    INPUT --> HTTP
    SEND --> HTTP
    HTTP --> P1
    P1 --> P2
    P2 --> V1
    V1 --> V2
    V2 --> V3
    V3 -->|需要审批| H1
    V3 -->|自动批准| M1
    H1 --> O1
    O1 --> H2
    H2 --> M1
    M1 --> DB1
    M1 --> DB2
    
    HTTP --> PANEL1
    O1 --> PANEL2
    H2 --> PANEL3
    M1 --> PANEL4
```

---

## Step by Step 详细流程 (含 Context Memory)

### 1. 用户发送请求

```mermaid
sequenceDiagram
    participant U as 用户
    participant UI as Web界面
    participant API as /api/query
    participant Parse as 解析函数
    participant HITL as HITLWorkflow
    participant Ollama as Ollama
    participant Mem as ContextMemory
    participant DB as SQLite

    U->>UI: 输入 Submit expense: John Doe, travel, $1200, Flight to NYC
    UI->>UI: 点击 Send Request
    UI->>API: POST /api/query {query: "..."}
    
    Note over API: ═══════════════════════
    Note over API: Step 0: Sqlantra Start
    API->>API: handle_expense(query)
    
    API->>Parse: parse "Submit expense: John Doe, travel, $1200, Flight to NYC"
    Note over Parse: 提取字段:
    Parse->>Parse: employee = "John Doe"
    Parse->>Parse: category = "travel"
    Parse->>Parse: amount = 1200.0
    Parse->>Parse: description = "Flight to NYC"
    
    Note over API: Step 1: Store to Memory
    Mem->>Mem: store("expense_submission", query, "input")
    Mem->>DB: log_context_memory()
    API-->>UI: Step 0-1 完成
    
    Note over UI: 显示 Step 0-1 在 Sqlantra Workflow 面板
```

### 2. 验证和阈值检查

```mermaid
sequenceDiagram
    participant API as API Handler
    participant Validate as 验证层
    participant Category as ExpenseCategory
    participant Mem as ContextMemory
    participant DB as SQLite

    Note over API: Step 2: Threshold Check
    API->>Validate: check_threshold(travel, 1200)
    Validate->>Category: get_threshold("travel")
    Category-->>Validate: return 1000
    
    Validate->>Validate: 1200 > 1000? = YES
    
    Note over API: Step 2: Store threshold check
    Mem->>Mem: store("threshold_check", {category: travel, amount: 1200, threshold: 1000}, "validation")
    Mem->>DB: log_context_memory()
    
    API-->>UI: Step 2 完成
    Note over UI: 显示: Step 2 - Threshold: $1000
```

### 3. 创建审批请求 (需要 Ollama)

```mermaid
sequenceDiagram
    participant API as API Handler
    participant HITL as HITLWorkflow
    participant Ollama as Ollama
    participant DB as SQLite
    participant Mem as ContextMemory

    Note over API: Step 3: HITL Approval Required
    API->>HITL: submit_expense("John Doe", "travel", 1200, "Flight to NYC")
    
    HITL->>DB: create_approval()
    Note over DB: action_type = "expense_reimbursement"
    Note over DB: details = {employee, category, amount...}
    Note over DB: status = "pending"
    DB-->>HITL: approval_id = "APR-20260426xxxxx"
    
    Note over HITL: 生成通知 (调用 Ollama)
    HITL->>Ollama: call_ollama(prompt)
    Note over Ollama: prompt = "Generate a Slack-style notification..."
    
    Note over Ollama: 🤖 调用本地 Ollama
    Ollama-->>HITL: notification = "🤖 *Sqlantra - Expense Reimbursement*..."
    
    Note over API: Step 3: Store approval request
    Mem->>Mem: store("hitl_request_APR-xxx", {...}, "hitl_request")
    Mem->>DB: log_context_memory()
    
    API-->>UI: Step 3 完成 + pending=true
    Note over UI: Sqlantra Workflow 显示 Step 3
    Note over UI: 审批面板显示 "⏳ Awaiting your approval"
```

### 4. 用户点击 Approve

```mermaid
sequenceDiagram
    participant U as 用户
    participant UI as Web界面
    participant API as /api/hitl/respond
    participant HITL as HITLWorkflow
    participant DB as SQLite
    participant Mem as ContextMemory

    U->>UI: 点击 ✅ Approve 按钮
    
    UI->>API: POST /api/hitl/respond {approval_id: APR-xxx, approved: true}
    
    Note over API: 处理批准
    API->>HITL: approve(approval_id, "Approved by user")
    
    HITL->>DB: respond_approval(approved=true)
    DB-->>HITL: status = "approved"
    
    Note over API: Store to Context Memory
    Mem->>Mem: store("expense_approved_EXP-xxx", {...}, "expense_approved")
    Mem->>DB: log_context_memory()
    
    HITL-->>API: return {status: "approved", message: "..."}
    
    API-->>UI: 返回结果
    Note over UI: 显示 ✅ "Expense EXP-xxx has been approved"
```

---

## Context Memory 完整日志

当用户提交 `Submit expense: John Doe, travel, $1200, Flight to NYC` 时，Context Memory 记录：

```mermaid
flowchart TB
    subgraph MEM["🧠 Context Memory Log"]
        M1["mem_20260426xxxx01<br/>key: expense_submission<br/>op: input<br/>value: Submit expense..."]
        M2["mem_20260426xxxx02<br/>key: expense_parsing<br/>op: parse<br/>value: {employee, category, amount}"]
        M3["mem_20260426xxxx03<br/>key: threshold_check<br/>op: validation<br/>value: {threshold: 1000, result: exceeded}"]
        M4["mem_20260426xxxx04<br/>key: hitl_request_APR-xxx<br/>op: hitl_request<br/>value: {approval_id, pending}"]
        M5["mem_20260426xxxx05<br/>key: ollama_call_xxx<br/>op: ollama_call<br/>value: notification text"]
        M6["mem_20260426xxxx06<br/>key: workflow_step_3<br/>op: workflow<br/>value: HITL pending}"]
    end

    M1 --> M2
    M2 --> M3
    M3 --> M4
    M4 --> M5
    M5 --> M6
```

| Step | Key | Operation | Value | 说明 |
|-----:|-----|-----------|-------|------|
| 0 | `expense_submission` | input | Submitted expense query | 用户输入 |
| 1 | `expense_parsing` | parse | {employee: John Doe, category: travel, amount: 1200} | 解析结果 |
| 2 | `threshold_check` | validation | {threshold: $1000, amount: $1200, exceeded: true} | 阈值检查 |
| 3 | `hitl_request_APR-xxx` | hitl_request | {approval_id, status: pending} | 审批请求创建 |
| 3 | `ollama_call_xxx` | ollama_call | Notification text from Ollama | LLM 生成通知 |
| 3 | `workflow_complete` | workflow | {steps: 4} | 工作流完成 | |

---

## Sqlantra Workflow 面板显示内容

每个 Step 在 Sqlantra Workflow 面板的显示：

```
┌────────────────────────────────────────────────────────────────┐
│  ⚙️ Sqlantra System Workflow                              │
├────────────────────────────────────────────────────────────────┤
│  Step 0: ⚡ Sqlantra Start Processing                    │
│    Detail: Processing expense submission         │
│    Code:  Employee: John Doe, Category: travel,    │
│           Amount: $1200.00                       │
├────────────────────────────────────────────────────────────────┤
│  Step 1: 📝 Expense Validation                    │
│    Detail: Validating expense details...             │
│    Code:  Category: travel, Amount: $1200.00     │
├────────────────────────────────────────────────────────────────┤
│  Step 2: ⚖️ Threshold Check                     │
│    Detail: Checking approval threshold...      │
│    Code:  Threshold: $1000 (travel)          │
├────────────────────────────────────────────────────────────────┤
│  Step 3: 🔔 HITL Approval Required ⭐           │
│    Detail: Amount $1200 exceeds $1000           │
│           threshold - approval needed          │
│    Code:  Pending Approval: APR-20260426xxxxx   │
│           <span class='warning'>⏳ PENDING</span> │
└────────────────────────────────────────────────────────────────┘
                          ↓
              ┌────────────────────────────────┐
              │   🔔 Pending Approvals         │
              │   🤖 Sqlantra - Expense Reimbursement│
              │   John Doe                    │
              │   travel | $1200.00           │
              │   ⏳ Awaiting Approval        │
              │   [✅ Approve] [❌ Reject]     │
              └────────────────────────────────┘
```

---

## Ollama 调用详情

当 Step 3 执行时，HITL Workflow 调用本地 Ollama 生成通知：

```
URL: http://localhost:11434/api/generate
Model: qwen3.5:2b-q4_K_M

Prompt:
"""
Generate a Slack-style notification for expense reimbursement approval.

Employee: John Doe
Category: travel
Amount: $1200.00
Description: Flight to NYC

The notification should:
- Start with "🤖 *Sqlantra - Expense Reimbursement*"
- Include employee, amount, category
- Be concise (under 200 chars)
- Mention awaiting approval
"""

Response:
"🤖 *Sqlantra - Expense Reimbursement*

*John Doe* submitted a *$1200.00* expense for *travel*

Description: Flight to NYC

💰 Amount: $1200.00 (threshold: $1000)

⚠️ Awaiting your approval"
```

---

## 完整 API 调用链

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Parse
    participant Validate
    participant HITL
    participant Ollama
    participant Mem
    participant DB

    Client->>API: POST /api/query
    API->>Parse: handle_expense(query)
    Parse->>Mem: store("expense_submission", ...)
    Mem->>DB: log_context_memory()
    
    Parse->>Validate: threshold = get_threshold()
    Mem->>Mem: store("threshold_check", ...)
    Mem->>DB: log_context_memory()
    
    Validate->>HITL: submit_expense()
    HITL->>DB: create_approval()
    DB-->>HITL: approval_id
    
    HITL->>Ollama: generate notification
    Ollama-->>HITL: notification text
    
    HITL->>Mem: store("hitl_request_xxx", ...)
    Mem->>DB: log_context_memory()
    
    API-->>Client: {pending: true, approval_id: xxx, notification: ...}
```

*文档更新时间: 2026-04-26*