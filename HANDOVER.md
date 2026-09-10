# Sqlantra System V3 - Agent 交接文档
> 本文档供后续接手开发的 Agent 阅读，包含项目全量细节、模块说明、配置、测试方法等。

---

## 1. 项目基础信息
| 项目 | 详情 |
|------|------|
| 项目路径 | `./Sqlantra-local-ollama_mysql_v3` |
| 项目目标 | 企业级 AI 编排平台 Demo，演示 Text-to-SQL、HITL 审批、Context Memory、数据管道等核心能力 |
| 运行环境 | Python 3.14.4（当前）、无强制外部依赖（可选 Ollama） |
| 访问地址 | `http://localhost:8766`（端口可配置） |
| 数据存储 | SQLite：`/tmp/sqlantra_v2_demo.db`；上下文记忆：`/tmp/sqlantra_context_memory.json`（可选持久化） |

---

## 2. 目录结构与文件说明
```
Sqlantra-local-ollama_mysql_v3/
├── web_demo.py           # 主入口：HTTP 服务器 + 嵌入式前端（HTML/JS/CSS 全集成）
├── sqlantra_database_v2.py   # SQLite 数据库初始化、CRUD、表结构定义
├── text_to_sql.py       # 自然语言转 SQL（Ollama 优先，规则 fallback）
├── context_memory.py    # 上下文记忆系统（存储、召回、语义搜索）
├── hitl_workflow.py     # HITL 审批工作流（提交、审批、通知）
├── AGENTS.md            # 旧版 V2 开发指南（部分内容已过时，以本文档为准）
├── HANDOVER.md          # 本文档（Agent 交接用）
└── PROJECT_OVERVIEW.md  # 用户版图表总结（全流程图，无代码细节）
```

---

## 3. 核心模块详解
### 3.1 web_demo.py（876行 + 嵌入式前端）
#### 后端部分
- **服务器**：Python 内置 `HTTPServer`，端口 8766
- **API 端点**：
  | 端点 | 方法 | 功能 |
  |------|------|------|
  | `/` | GET | 返回主界面 HTML |
  | `/api/tables` | GET | 列出所有数据库表 |
  | `/api/table/{name}` | GET | 获取指定表的数据和 schema |
  | `/api/memory` | GET | 获取上下文记忆条目 |
  | `/api/hitl/pending` | GET | 获取待审批请求 |
  | `/api/hitl/respond` | POST | 审批/拒绝请求（参数：`approval_id`、`approved`、`comment`） |
  | `/api/query` | POST | 执行查询/提交费用（参数：`query`） |
  | `/api/reset` | POST | 重置系统（清数据库+记忆） |

#### 前端部分（嵌入式 JS）
- **核心函数**：
  - `sendQuery()`：发送用户请求，防重复提交（`isWaitingForApi` 标志）
  - `renderCurrentStep()`：单步执行模式渲染（按 Enter/Space 前进）
  - `showFinalResult()`：最终结果展示（✅ 已修复 `resultDiv` 未定义问题，查询结果可正常显示）
  - `approveRequest(approvalId)` / `rejectRequest(approvalId)`：审批操作
  - `resetSystem()`：重置所有界面状态
- **4 面板布局**：
  1. 左上：用户输入 + HITL 审批按钮
  2. 右上：Sqlantra 工作流单步执行过程
  3. 左下：数据库表实时查看器
  4. 右下：上下文记忆跟踪面板

---

### 3.2 sqlantra_database_v2.py（~500行）
- **核心函数**：
  - `init_database()`：初始化 11 张表（orders、products、order_items、bronze/silver/gold 层表等）
  - `query_sql(sql)`：执行 SQL，返回 `{"columns": [], "data": [], "error": null}`
  - `get_table_data(table_name)`：获取表结构和前 100 条数据
  - `reset_database()`：删除所有表并重新初始化
- **关键表结构**：
  - `orders`：order_id, channel, customer_id, order_date, total_amount, status 等
  - `hitl_approvals`：审批请求记录（approval_id, action_type, details, requester, status 等）
  - `context_memory_log`：上下文记忆持久化存储

---

### 3.3 text_to_sql.py（~250行）
- **核心函数**：
  - `text_to_sql(query)`：入口函数，优先调用 Ollama，失败则走规则引擎
  - `rule_based_sql(query)`：基于关键词的规则转换（支持查询、过滤、排序等常见场景）
  - `call_ollama(prompt)`：调用 Ollama API（`http://localhost:11434/api/generate`）
- **配置**：默认模型 `qwen3.5:2b-q4_K_M`，可在 `web_demo.py` 第 21 行修改

---

### 3.4 context_memory.py（~600行）
- **核心类**：`SqlantraContextMemory`
  - `store(key, value, operation_type, metadata)`：存储操作记录
  - `get_recent_entries(limit)`：获取最近 N 条记录
  - `smart_recall(query)`：智能召回（识别后续提问，关联历史操作）
  - `semantic_search(keyword)`：关键词语义搜索
- **跟踪的操作类型**：
  - `EXPENSE_SUBMITTED`：费用提交
  - `CONFIRMATION`：审批确认
  - `EXPENSE_APPROVED` / `EXPENSE_REJECTED`：审批结果
  - `QUERY_LOGGED`：查询记录

---

### 3.5 hitl_workflow.py（~300行）
- **核心类**：
  - `HITLWorkflow`：审批工作流管理
    - `submit_expense(employee, category, amount, description)`：提交费用，返回是否需审批、approval_id
    - `confirm_and_notify(approval_id, approved, comment)`：审批/拒绝，返回双方通知消息
    - `get_pending_for_ui()`：获取待审批列表（给前端渲染）
  - `ExpenseReimbursement`：费用记录类（expense_id, employee, amount, status 等）
- **审批阈值**：
  | 类别 | 阈值 | 超阈值需审批 |
  |------|------|----------------|
  | travel | $1000 | ✅ |
  | meals | $100 | ✅ |
  | software | $200 | ✅ |
  | 其他 | 无 | 自动通过 |
- **ID 生成**：expense_id/approval_id 使用微秒精度，避免重复

---

## 4. 环境配置与依赖
| 配置项 | 值 | 修改位置 |
|--------|-----|------------|
| Ollama 地址 | `http://localhost:11434/api/generate` | `web_demo.py` 第 20 行 |
| 模型 | `qwen3.5:2b-q4_K_M` | `web_demo.py` 第 21 行 |
| 端口 | 8766 | `web_demo.py` 第 23 行 |
| 数据库路径 | `/tmp/sqlantra_v2_demo.db` | `sqlantra_database_v2.py` |
| 记忆存储路径 | `/tmp/sqlantra_context_memory.json` | `context_memory.py` |

- **可选依赖**：Ollama（安装后拉取模型 `ollama pull qwen3.5:2b-q4_K_M`，不安装则自动 fallback 到规则模式）

---

## 5. 测试与运行方法
### 5.1 启动系统
```bash
cd ./Sqlantra-local-ollama_mysql_v3
rm -f /tmp/sqlantra_v2_demo.db  # 可选：清旧数据
python3 web_demo.py
```
> 前台运行可查看日志，后台运行用 `nohup python3 web_demo.py > server.log 2>&1 &`

### 5.2 功能测试
| 测试场景 | 操作步骤 | 预期结果 |
|----------|------------|------------|
| Text-to-SQL 查询 | 1. 选择 `User Query` 场景<br>2. 输入 `Show all completed orders`<br>3. 按 Enter 单步执行 | 最后在员工界面显示 8 条查询结果表格 |
| HITL 审批 | 1. 选择 `HITL Workflow` 场景<br>2. 输入 `Submit expense: John Doe, travel, $1200, Flight to NYC`<br>3. 审批通过/拒绝 | 员工和经理界面都显示确认消息 |
| 系统重置 | 点击 `Reset System` 按钮 | 所有面板清空，数据库重建 |

### 5.3 命令行测试
```bash
# 测试查询 API
curl -s -X POST http://localhost:8766/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all completed orders"}' | python3 -m json.tool

# 测试重置
curl -s -X POST http://localhost:8766/api/reset
```

---

## 6. 已知问题与待办
1. **服务器后台启动偶发无响应**：建议前台运行调试，后台运行请检查 `server.log`
2. **查询结果默认截断**：仅显示前 10 条，可自行修改 `web_demo.py` 第 435 行的 `slice(0, 10)`
3. **Ollama 超时处理**：当前无超时配置，若 Ollama 响应慢会阻塞请求
4. **前端无错误提示**：若 API 返回空，界面无明确报错，可优化

---

## 7. 关键修复记录（最新）
- ✅ `showFinalResult()` 中 `resultDiv` 未定义问题 → 已添加 `const resultDiv = document.getElementById('query-result');`
- ✅ 查询结果重复渲染问题 → 已清理重复代码
- ✅ 费用提交重复 ID 问题 → 已添加微秒精度
- ✅ 前端重复提交问题 → 已添加 `isWaitingForApi` 标志

---

> 后续开发可直接基于本文档定位模块，所有核心逻辑均在对应文件的标注行附近。
