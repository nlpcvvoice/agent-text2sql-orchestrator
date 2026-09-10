# Sqlantra System V3 - Project Overview (English Version)
> All Mermaid diagrams, no text descriptions. For non-Chinese speakers.

---

## 1. System Architecture

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
graph TB
    subgraph Frontend["Frontend (Browser)"]
        UI["User Input + Approval Buttons"]
        WF["Workflow Display (Step-by-Step)"]
        DBV["Database Viewer (Real-time Tables)"]
        MEM["Context Memory (Operation History)"]
    end

    UI -->|HTTP API :8766| BE
    WF -->|HTTP API :8766| BE
    DBV -->|HTTP API :8766| BE
    MEM -->|HTTP API :8766| BE

    subgraph Backend["Backend Engine (web_demo.py)"]
        BE["HTTP Server"]
        TTS["Text-to-SQL"]
        HITL["HITL Workflow"]
        CM["Context Memory"]
        BE --> TTS
        BE --> HITL
        BE --> CM
    end

    TTS --> TTSMod["text_to_sql.py"]
    HITL --> HITLMod["hitl_workflow.py"]
    CM --> CMMod["context_memory.py"]

    subgraph Database["SQLite (/tmp/sqlantra_v2_demo.db)"]
        ORD["orders"]
        PRD["products"]
        OI["order_items"]
        BSG["bronze / silver / gold tables"]
    end

    TTSMod --> Database
    HITLMod --> Database
    CMMod --> Database
```

---

## 2. Text-to-SQL Query Flow

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
flowchart TD
    A["User Input: Show completed orders"] --> B[Step 0: Sqlantra Start Processing]
    B --> C[Step 1: Skill Matching → text_to_sql]
    C --> D[Step 2: Agent Routing → SQLGenerator]
    D --> E[Step 3: Text-to-SQL Generation]
    E --> F{Ollama Available?}
    F -->|Success| G["Generate SQL"]
    F -->|Fail| H["Rule Engine Fallback"]
    G --> I[Step 4: Context Memory Update]
    H --> I
    I --> J[Step 5: Database Execution]
    J --> K[Step 6: Pipeline Processing Bronze→Silver→Gold]
    K --> L[Step 7: HITL Check]
    L --> M{"Needs Approval?"}
    M -->|No| N["✅ Complete: Display Query Results Table"]
    M -->|Yes| O["Enter Approval Flow"]
```

---

## 3. HITL Expense Approval Flow

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
flowchart TD
    A["Employee Submit: Submit expense: John Doe, travel, $1200"] --> B[Step 0: Sqlantra Start Processing]
    B --> C[Step 1: Skill Matching → expense_reimbursement]
    C --> D[Step 2: Agent Routing → ExpenseAgent]
    D --> E[Step 3: Expense Submission Processing]
    E --> F{Check: travel > $1000?}
    F -->|Yes| G["Status: pending, generate approval_id"]
    F -->|No| H["✅ Auto-Approved"]
    G --> I[Step 4: Context Memory Update]
    I --> J[Step 5: Database Temp Storage]
    J --> K[Step 6: Pipeline Processing Bronze Layer]
    K --> L[Step 7: HITL Approval Check]
    L --> M["Employee View: Waiting for approval..."]
    L --> N["Manager View: Show Approval Card"]
    N --> O{"Manager Action"}
    O -->|✅ Approve| P[confirm_and_notify approved]
    O -->|❌ Reject| Q[confirm_and_notify rejected]
    P --> R["Status: approved"]
    Q --> S["Status: rejected"]
    R --> T["Employee: Expense approved $1200"]
    S --> U["Employee: Expense rejected"]
```

---

## 4. Data Pipeline Flow

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
flowchart LR
    A["Raw Data Input"] --> B["Bronze Layer<br/>Raw Data Staging"]
    B --> C["Silver Layer<br/>Cleaned Data"]
    C --> D["Gold Layer<br/>Service-Ready Data"]
    D --> E["Context Memory<br/>Log Transformation"]
    
    B --> B1["Data Validation"]
    B --> B2["Deduplication"]
    C --> C1["Format Standardization"]
    C --> C2["Outlier Handling"]
    D --> D1["Aggregation"]
    D --> D2["Business Metrics"]
```

---

## 5. UI Layout & Data Flow

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
graph LR
    subgraph Browser["Browser - http://localhost:8766"]
        subgraph Left["Left Panels"]
            UI["Top-Left: User Input + Approval Buttons"]
            Result["Bottom-Left: Query Results / Approval Messages"]
        end
        subgraph Right["Right Panels"]
            WF["Top-Right: Sqlantra Workflow (Step-by-Step)"]
            DB["Bottom-Right: Database Viewer"]
            MEM["Bottom-Right: Context Memory"]
        end
    end
    
    UI -->|"Send Request"| WF
    WF -->|"Step 5: Auto-select Table"| DB
    WF -->|"Step 4: Update"| MEM
    WF -->|"On Complete"| Result
    UI -->|"Reset"| RST["Reset All Panels"]
```

---

## 6. Approval Threshold Decision

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
flowchart TD
    A["Expense Submission"] --> B{Category Check}
    B -->|travel| C{Amount > $1000?}
    B -->|meals| D{Amount > $100?}
    B -->|software| E{Amount > $200?}
    B -->|other| F["✅ Auto-Approved"]
    
    C -->|Yes| G["⏳ Needs Approval"]
    C -->|No| F
    D -->|Yes| G
    D -->|No| F
    E -->|Yes| G
    E -->|No| F
    
    G --> H["Manager Approval Card"]
    H --> I{"Approve / Reject"}
    I -->|Approve| J["✅ approved"]
    I -->|Reject| K["❌ rejected"]
```

---

## 7. System Reset Flow

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
flowchart TD
    A["Click Reset System"] --> B["POST /api/reset"]
    B --> C["Backend: db.reset_database()"]
    B --> D["Backend: memory.clear()"]
    B --> E["Frontend: Clear All Panels"]
    B --> F["Frontend: Reset Input to Default"]
    C --> G["✅ System Back to Initial State"]
    D --> G
    E --> G
    F --> G
```

---

## 8. Tech Stack Overview

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
graph LR
    subgraph Frontend["Frontend"]
        HTML["HTML"]
        CSS["CSS"]
        JS["JavaScript"]
    end
    subgraph Backend["Backend"]
        Py["Python 3.14"]
        Http["http.server"]
        Sql["SQLite"]
    end
    subgraph AI["AI Module"]
        Ollama["Ollama qwen3.5:2b"]
        Rule["Rule Engine"]
    end
    Frontend -->|HTTP API| Backend
    Backend --> Sql
    Backend -->|Optional| Ollama
    Ollama -->|Fail| Rule
```

---

## 9. Context Memory Recall

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
flowchart TD
    A["Operation Storage"] --> B["key-value + operation_type + timestamp"]
    B --> C1["EXPENSE_SUBMITTED"]
    B --> C2["CONFIRMATION"]
    B --> C3["EXPENSE_APPROVED"]
    B --> C4["QUERY_LOGGED"]
    
    D["smart_recall('that expense I just submitted')"] --> E["Match Recent EXPENSE_SUBMITTED"]
    F["semantic_search('travel')"] --> G["Return History with 'travel'"]
    
    E --> H["Bottom-Right Panel: Show Timeline"]
    G --> H
```
