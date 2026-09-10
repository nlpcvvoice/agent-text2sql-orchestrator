# Sqlantra System V3 - 项目全景图
> 全 Mermaid 图表版本，无文字描述。

---

## 1. 系统总览

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
graph TB
    subgraph Frontend["前端界面 (浏览器)"]
        UI["用户输入 + 审批按钮"]
        WF["工作流展示 (单步执行)"]
        DBV["数据库查看器 (实时表)"]
        MEM["上下文记忆 (操作历史)"]
    end

    UI -->|HTTP API :8766| BE
    WF -->|HTTP API :8766| BE
    DBV -->|HTTP API :8766| BE
    MEM -->|HTTP API :8766| BE

    subgraph Backend["后端引擎 (web_demo.py)"]
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

    subgraph Database["SQLite 数据库 (/tmp/sqlantra_v2_demo.db)"]
        ORD["orders"]
        PRD["products"]
        OI["order_items"]
        BSG["bronze / silver / gold 表"]
    end

    TTSMod --> Database
    HITLMod --> Database
    CMMod --> Database
```

---

## 2. Text-to-SQL 查询流程

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
flowchart TD
    A["用户输入: Show completed orders"] --> B[Step 0: Sqlantra 开始处理]
    B --> C[Step 1: 技能匹配 → text_to_sql]
    C --> D[Step 2: 智能体路由 → SQLGenerator]
    D --> E[Step 3: Text-to-SQL 生成]
    E --> F{尝试 Ollama}
    F -->|成功| G["生成 SQL"]
    F -->|失败| H["规则引擎 fallback"]
    G --> I[Step 4: 上下文记忆更新]
    H --> I
    I --> J[Step 5: 数据库执行]
    J --> K[Step 6: 管道处理 Bronze→Silver→Gold]
    K --> L[Step 7: HITL 检查]
    L --> M{"需要审批?"}
    M -->|否| N["✅ 完成: 显示查询结果表格"]
    M -->|是| O["进入审批流程"]
```

---

## 3. HITL 费用审批流程

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
flowchart TD
    A["员工提交: Submit expense: John Doe, travel, $1200"] --> B[Step 0: Sqlantra 开始处理]
    B --> C[Step 1: 技能匹配 → expense_reimbursement]
    C --> D[Step 2: 智能体路由 → ExpenseAgent]
    D --> E[Step 3: 费用提交处理]
    E --> F{检查: travel > $1000?}
    F -->|是| G["状态: pending, 生成 approval_id"]
    F -->|否| H["✅ 自动批准"]
    G --> I[Step 4: 上下文记忆更新]
    I --> J[Step 5: 数据库暂存]
    J --> K[Step 6: 管道处理 Bronze层]
    K --> L[Step 7: HITL 审批检查]
    L --> M["员工界面: 等待审批..."]
    L --> N["经理界面: 显示审批卡片"]
    N --> O{"经理操作"}
    O -->|✅ 批准| P[confirm_and_notify approved]
    O -->|❌ 拒绝| Q[confirm_and_notify rejected]
    P --> R["状态: approved"]
    Q --> S["状态: rejected"]
    R --> T["员工看到: 费用已批准 $1200"]
    S --> U["员工看到: 费用已拒绝"]
```

---

## 4. 数据管道流程

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
flowchart LR
    A["原始数据"] --> B["Bronze 层<br/>原始数据暂存"]
    B --> C["Silver 层<br/>清洗后数据"]
    C --> D["Gold 层<br/>可服务数据"]
    D --> E["上下文记忆<br/>记录转换操作"]
    
    B --> B1["数据校验"]
    B --> B2["去重检查"]
    C --> C1["格式标准化"]
    C --> C2["异常值处理"]
    D --> D1["聚合计算"]
    D --> D2["业务指标"]
```

---

## 5. 界面布局与数据流向

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
graph LR
    subgraph Browser["浏览器 - http://localhost:8766"]
        subgraph Left["左侧"]
            UI["左上: 用户输入 + 审批按钮"]
            Result["左下: 查询结果 / 审批消息"]
        end
        subgraph Right["右侧"]
            WF["右上: Sqlantra 工作流 (单步)"]
            DB["右下: 数据库查看器"]
            MEM["右下: 上下文记忆"]
        end
    end

    UI -->|"发送请求"| WF
    WF -->|"Step 5: 选中表"| DB
    WF -->|"Step 4: 更新"| MEM
    WF -->|"完成后"| Result
    UI -->|"Reset"| RST["重置所有面板"]
```

---

## 6. 审批阈值决策

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
flowchart TD
    A["费用提交"] --> B{类别判断}
    B -->|travel| C{> $1000?}
    B -->|meals| D{> $100?}
    B -->|software| E{> $200?}
    B -->|其他| F["✅ 自动批准"]
    
    C -->|是| G["⏳ 需审批"]
    C -->|否| F
    D -->|是| G
    D -->|否| F
    E -->|是| G
    E -->|否| F
    
    G --> H["经理审批卡片"]
    H --> I{"批准/拒绝"}
    I -->|批准| J["✅ approved"]
    I -->|拒绝| K["❌ rejected"]
```

---

## 7. 系统重置流程

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
flowchart TD
    A["点击 Reset System"] --> B["POST /api/reset"]
    B --> C["后端: db.reset_database()"]
    B --> D["后端: memory.clear()"]
    B --> E["前端: 清空所有面板"]
    B --> F["前端: 重置输入框"]
    C --> G["✅ 系统回到初始状态"]
    D --> G
    E --> G
    F --> G
```

---

## 8. 技术栈总览

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
graph LR
    subgraph Frontend["前端"]
        HTML["HTML"]
        CSS["CSS"]
        JS["JavaScript"]
    end
    subgraph Backend["后端"]
        Py["Python 3.14"]
        Http["http.server"]
        Sql["SQLite"]
    end
    subgraph AI["AI 模块"]
        Ollama["Ollama qwen3.5:2b"]
        Rule["规则引擎"]
    end
    Frontend -->|HTTP API| Backend
    Backend --> Sql
    Backend -->|可选| Ollama
    Ollama -->|失败| Rule
```

---

## 9. 上下文记忆智能召回

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor':'#1f2937', 'primaryTextColor':'#f9fafb', 'primaryBorderColor':'#374151', 'lineColor':'#6b7280', 'secondaryColor':'#111827', 'background':'#0f172a', 'mainBkg':'#1e293b', 'nodeBorder':'#475569', 'clusterBkg':'#1e293b', 'titleColor':'#e2e8f0', 'edgeLabelBackground':'#1e293b', 'actorBkg':'#1e293b', 'actorBorder':'#475569', 'actorTextColor':'#f1f5f9', 'actorLineColor':'#475569', 'signalColor':'#cbd5e1', 'signalTextColor':'#f1f5f9', 'labelBoxBkgColor':'#1e293b', 'labelTextColor':'#f1f5f9', 'loopTextColor':'#f1f5f9', 'noteBorderColor':'#475569', 'noteBkgColor':'#334155', 'noteTextColor':'#f1f5f9', 'activationBorderColor':'#475569', 'activationBkgColor':'#1e293b'}}}%%
flowchart TD
    A["操作存储"] --> B["key-value + 操作类型 + 时间戳"]
    B --> C1["EXPENSE_SUBMITTED"]
    B --> C2["CONFIRMATION"]
    B --> C3["EXPENSE_APPROVED"]
    B --> C4["QUERY_LOGGED"]
    
    D["smart_recall('刚才的费用')"] --> E["关联最近 EXPENSE_SUBMITTED"]
    F["semantic_search('旅行')"] --> G["返回含 'travel' 的历史"]
    
    E --> H["右下方面板展示"]
    G --> H
```
