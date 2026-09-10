# Snowflake Data Pipeline Demo Scenarios
> 为什么需要 Bronze/Silver/Gold？在 Snowflake 作为 Data Warehouse 的场景下，分层架构的意义在于：
> - **Bronze**: 保留原始数据完整性（合规、审计、可追溯）
> - **Silver**: 数据清洗与标准化（去重、格式统一、质量保障）
> - **Gold**: 业务就绪的数据服务（聚合、指标、可消费）

---

## 场景1：电商全渠道订单分析

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    subgraph Sources["数据源"]
        WEB["🌐 Web订单<br/>JSON"]
        APP["📱 App订单<br/>JSON"]
        POS["🏪 POS系统<br/>CSV"]
        API["🔌 第三方API<br/>XML"]
    end

    Sources --> Bronze

    subgraph Bronze["Bronze层 - 原始数据"]
        B_ORDERS["raw_orders<br/>──────────<br/>• 原始JSON/XML<br/>• 无修改保留<br/>• Time Travel启用"]
    end

    Bronze -->|Snowpipe自动摄入| Silver

    subgraph Silver["Silver层 - 清洗后"]
        S_ORDERS["clean_orders<br/>──────────<br/>• 去重（订单ID）<br/>• 标准化货币<br/>• 填充缺失值<br/>• 类型转换"]
    end

    Silver -->|dbt增量更新| Gold

    subgraph Gold["Gold层 - 业务指标"]
        G_DAILY["daily_sales_metrics<br/>──────────<br/>• 日销售额<br/>• 渠道分布<br/>• 转化率"]
        G_PRODUCT["product_performance<br/>──────────<br/>• 热销商品TOP10<br/>• 库存预警<br/>• 利润率"]
        G_CUSTOMER["customer_360<br/>──────────<br/>• CLV计算<br/>• 客户分群<br/>• 复购预测"]
    end

    Gold --> VIZ["📊 Tableau/PowerBI<br/>实时仪表盘"]
```

**关键价值**：
- Bronze保留原始订单（争议时可追溯）
- Silver确保数据质量（一处清洗，全局复用）
- Gold直接服务业务（零ETL延迟）

---

## 场景2：IoT设备预测性维护

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    subgraph IoT["IoT设备"]
        TEMP["🌡️ 温度传感器<br/>10万+/秒"]
        VIB["🔧 振动传感器<br/>高频采样"]
        PRESS["⏲️ 压力传感器<br/>连续流"]
    end

    IoT -->|Snowflake Kafka Connect| Bronze

    subgraph Bronze["Bronze层 - 原始遥测"]
        B_TELEMETRY["raw_sensor_data<br/>──────────<br/>• 原始二进制<br/>• 毫秒级时间戳<br/>• 设备元数据"]
    end

    Bronze -->|Streams + Tasks| Silver

    subgraph Silver["Silver层 - 特征工程"]
        S_FEATURES["sensor_features<br/>──────────<br/>• 滑动窗口统计<br/>• 异常值标记<br/>• 设备健康基线<br/>• 采样频率归一"]
    end

    Silver -->|ML模型推理| Gold

    subgraph Gold["Gold层 - 预测洞察"]
        G_ALERTS["maintenance_alerts<br/>──────────<br/>• 故障预测<br/>• 优先级排序<br/>• 影响评估"]
        G_SCHEDULE["maintenance_schedule<br/>──────────<br/>• 最优维护窗口<br/>• 备件需求预测<br/>• 成本优化"]
    end

    Gold --> ACTION["🔔 PagerDuty<br/>自动工单"]

    style G_ALERTS fill:#ff4444,stroke:#ff6666
    style G_SCHEDULE fill:#44ff44,stroke:#66ff66
```

**关键价值**：
- Bronze处理高吞吐原始流（Snowflake弹性算力）
- Silver做实时特征工程（窗口函数+UDF）
- Gold输出可行动洞察（集成ML模型）

---

## 场景3：金融实时反欺诈

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart LR
    subgraph Transactions["交易流"]
        CARD["💳 信用卡交易<br/>10K TPS"]
        WIRE["🏦 电汇转账<br/>高金额"]
        CRYPTO["₿ 加密货币<br/>区块链"]
    end

    Transactions -->|Snowflake Data Sharing| Bronze

    subgraph Bronze["Bronze层 - 原始交易"]
        B_TX["raw_transactions<br/>──────────<br/>• 完整交易报文<br/>• 原始IP/设备指纹<br/>• 未脱敏（加密存储）"]
    end

    Bronze -->|Dynamic Table物化视图| Silver

    subgraph Silver["Silver层 - 风险特征"]
        S_RISK["risk_features<br/>──────────<br/>• 速度检查（1h内N笔）<br/>• 地理异常（跨国跳）<br/>• 行为基线偏离<br/>• 黑名单匹配"]
    end

    Silver -->|Snowpark Python UDF| Gold

    subgraph Gold["Gold层 - 实时决策"]
        G_SCORE["fraud_scores<br/>──────────<br/>• 实时风险评分<br/>• 置信区间<br/>• 规则触发明细"]
        G_ACTION["auto_actions<br/>──────────<br/>• 自动冻结<br/>• 人工审核队列<br/>• 合规报告"]
    end

    Gold -->|Zero-Copy Cloning| AUDIT["📋 监管审计<br/>不可变快照"]

    style G_SCORE fill:#ffaa00,stroke:#ffcc44
    style G_ACTION fill:#ff4444,stroke:#ff6666
    style AUDIT fill:#4444ff,stroke:#6666ff
```

**关键价值**：
- Bronze满足合规（数据保留政策+加密）
- Silver实时特征计算（Dynamic Table自动刷新）
- Gold秒级决策（Snowpark原生Python执行）
- Audit零拷贝克隆（瞬间生成审计环境）

---

## 对比：为什么Snowflake让分层更有意义？

| 传统数仓 | Snowflake + 分层 |
|-----------|------------------|
| 每层需独立存储 | Zero-copy克隆，存储成本接近0 |
| ETL延迟小时级 | Snowpipe秒级摄入 |
| 难以追溯原始 | Time Travel可回溯90天 |
| 特征工程困难 | Snowpark原生支持Python/Java |
| 合规审计复杂 | Data Sharing + 克隆秒级交付 |

> **核心思想**：分层不是技术负担，而是**数据治理的边界**——Bronze保护原始、Silver保证质量、Gold服务业务。
