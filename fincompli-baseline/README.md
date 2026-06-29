# FinCompli Baseline

**Enterprise Multi-Agent Financial Compliance System**  
**企業級多 Agent 金融合規系統**

Version 0.1 - MVP Baseline

---

## Overview / 概述

FinCompli Baseline is a **runnable sandbox system** that simulates the compliance automation workflow of a mid-sized Hong Kong/Singapore bank. This baseline demonstrates how enterprise AI agents work together in real business scenarios — from suspicious transaction detection to multi-agent collaborative analysis to manual review to final compliance report submission.

FinCompli Baseline 是一個**可運行的沙盒系統**，模擬一家中型香港/新加坡銀行的合規自動化流程。這個 Baseline 展示了企業 AI Agent 如何在真實業務場景中協作——從可疑交易檢測到多 Agent 協同分析到人工審核到最終合規報告提交。

**Core Value / 核心價值**: This system allows anyone to clearly understand "how enterprise agents work in real business scenarios" at first glance.

---

## System Architecture / 系統架構

```
User/System Input Suspicious Transaction
用戶/系統輸入可疑交易
        ↓
  [Supervisor Agent]  ← Coordinates all analysis work / 協調所有分析工作
  ↙           ↘
[Fraud Detection]  [Case History]  ← Execute in parallel / 並行執行
詐欺偵測            案例歷史
  ↘           ↙
  [Supervisor Aggregate] ← Consolidate results / 彙整結果
        ↓ (Medium/High Risk)
  [Compliance Research Agent]  ← Query applicable regulations / 查詢適用法規
        ↓
  [Report Generation Agent]    ← Generate SAR draft / 生成 SAR 草稿
        ↓ (High Risk)
  [Human Review Node]          ← Compliance officer confirms / 合規官確認
        ↓
  [Final Submission/Archive] ← Submit/archive / 提交/存檔
```

---

## Memory Layer Design / 記憶層設計

| Memory Type<br/>記憶類型 | Storage<br/>存儲 | Use Case<br/>使用場景 | Visualization<br/>可視化 |
|------------|-------------|----------------------------|-----------|
| Short-term Memory<br/>短期記憶 | Thread State | Current conversation context<br/>當前對話上下文 | ✓ |
| Episodic Memory<br/>情節記憶 | ChromaDB | Historical SAR case retrieval<br/>歷史 SAR 案件檢索 | ✓ **重點** |
| Semantic Memory<br/>語義記憶 | ChromaDB | Regulatory text query<br/>法規條文查詢 | ✓ |
| Procedural Memory<br/>程序記憶 | SQLite | SOP rules<br/>SOP 規則 | ✓ |
| User Preferences<br/>用戶偏好 | SQLite | Compliance officer personalization<br/>合規官個性化設定 | ✓ |

---

## Technology Stack / 技術棧

```
Language: Python 3.9+
Agent Framework: LangGraph >= 0.2.0
LLM: Local Qwen 3.6 (via llama.cpp)
Short-term Memory: LangGraph Thread State (built-in checkpointer)
Episodic Memory: ChromaDB (past SAR case vector database)
Semantic Memory: ChromaDB (regulatory text vector database)
Procedural Memory: SQLite (SOP workflow rules)
User Memory: SQLite (compliance officer preferences)
Embedding: sentence-transformers (all-MiniLM-L6-v2)
Audit Log: SQLite (structured, with reserved fields for future product integration)
API Service: FastAPI + uvicorn
Mock Data Generation: Faker (all English)
Test Interface: CLI interactive script
Language: English
```

---

## Quick Start / 快速開始

### 1. Environment Setup / 環境搭建

```bash
# Clone or navigate to project directory
cd fincompli-baseline

# Run one-click setup script
python setup.py

# Install dependencies (recommended: use virtual environment)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Verify installation
python -c "import langgraph; import chromadb; print('✓ OK')"
```

### 2. Configure LLM / 配置 LLM

Edit `.env` file and configure your local Qwen endpoint:

```env
LLM_BASE_URL=http://localhost:8080
LLM_MODEL=Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf
```

### 3. Generate Mock Data / 生成模擬數據

```bash
python mock_data/seed_database.py
```

This will generate:
- 100 virtual customers (60 low-risk, 30 medium-risk, 10 high-risk)
- 30 historical SAR cases
- 40 regulatory text segments
- 25 test transaction scenarios

### 4. Run Test Scenario / 運行測試場景

```bash
# Interactive CLI mode
python cli/interactive.py --scenario 02

# Scenario 02: Structuring (most complete demo scenario)
# 場景 02：結構化分拆（最完整的演示場景）
```

### 5. Start API Server / 啟動 API 服務

```bash
uvicorn api.server:app --reload

# API will be available at: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

---

## Test Scenarios / 測試場景

| Scenario | Type | Risk Level | Description |
|----------|------|------------|-------------|
| 01 | Normal Transfer | Low | Standard cross-border remittance with clear business purpose |
| 02 | **Structuring** | **Critical** | Customer splits HKD 1.47M into 3×490K to avoid reporting threshold |
| 03 | High-Risk KYC | High | Large transaction with expired KYC documentation |
| 04 | Cross-Border | Medium | Unusual destination country pattern |
| 05 | False Positive | Low | Appears suspicious but has valid business explanation |

**Scenario 02 (Structuring)** is the **primary demonstration scenario** with the most complete workflow including human review.

---

## Directory Structure / 目錄結構

```
fincompli-baseline/
├── README.md                    # This file / 本文件
├── requirements.txt             # Python dependencies / Python 依賴
├── .env.example                 # Environment template / 環境變量模板
├── .env                         # Environment config (created by setup.py)
├── setup.py                     # One-click initialization / 一鍵初始化
│
├── config/                      # Global configuration / 全局配置
├── agents/                      # All agent definitions / 所有 Agent 定義
├── graph/                       # LangGraph state and builder / LangGraph 狀態和構建
├── memory/                      # Memory layer (tiered design) / 記憶層（分層設計）
├── tools/                       # Enterprise tools mock / 企業工具 Mock
├── mock_data/                   # Simulated enterprise data / 模擬企業數據
│   ├── generators/              # Data generators / 數據生成器
│   └── seeds/                   # Generated data files / 已生成數據文件
├── api/                         # FastAPI service / FastAPI 服務
├── cli/                         # Interactive CLI / 交互式 CLI
├── scenarios/                   # Complete test scenarios / 完整測試場景
├── audit_logs/                  # Audit log output / 審計日誌輸出
└── data/                        # Runtime data / 運行時數據
    ├── chroma/                  # ChromaDB persistence / ChromaDB 持久化
    └── sqlite/                  # SQLite databases / SQLite 數據庫
```

---

## API Endpoints / API 端點

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Submit transaction for analysis |
| `/api/status/{thread_id}` | GET | Get analysis status |
| `/api/human-decision/{thread_id}` | POST | Submit human review decision |
| `/api/report/{thread_id}` | GET | Get SAR report and execution trace |
| `/api/memory-traces/{thread_id}` | GET | **Get memory traces (for visualization products)** |
| `/api/audit-log` | GET | Get audit log |
| `/api/health` | GET | System health check |

**Key Integration Point for Downstream Products:**  
`GET /api/memory-traces/{thread_id}` - This endpoint provides complete memory trace data including similarity scores, which is the primary data source for memory visualization products.

---

## Future Product Integration Points / 後續產品接入點

The following hook points are **reserved but not implemented** in this baseline:

1. **Memory Call Hooks** (`memory/*.py` modules)
   - Current: Only writes to audit log
   - Future: Replace with WebSocket push for real-time visualization

2. **State `memory_traces` List** (`graph/state.py`)
   - Downstream products read this for visualization
   - Contains: memory_type, agent_id, query, similarity_scores

3. **`GET /api/memory-traces/{thread_id}` Endpoint**
   - Primary data source for visualization products
   - Returns structured memory trace data

4. **`GET /api/audit-log` Endpoint**
   - Data source for security audit products
   - Structured SQLite format with reserved security_flag field

---

## Development Status / 開發狀態

- [x] TASK 1: Project initialization and environment setup
- [ ] TASK 2: Mock enterprise data generation
- [ ] TASK 3: Memory layer implementation
- [ ] TASK 4: Graph state schema definition
- [ ] TASK 5: Four sub-agent implementation
- [ ] TASK 6: Supervisor and graph assembly
- [ ] TASK 7: CLI test interface and scenario scripts
- [ ] TASK 8: FastAPI service + final integration testing

---

## License / 許可證

This is a baseline demonstration system for internal development and testing purposes.

---

## Contact / 聯繫

For questions or issues, please refer to the project documentation.

---

**Last Updated:** 2026-06-26  
**Version:** 0.1.0-baseline
