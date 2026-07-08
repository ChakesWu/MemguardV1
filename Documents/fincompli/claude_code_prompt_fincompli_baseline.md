
## 專案概覽

你將為我建構一個名為 **FinCompli Baseline** 的企業級金融合規多 Agent 系統。

這是一個**可運行的沙盒系統**，模擬一家中型香港/新加坡銀行的合規自動化流程。目標是建立一個架構真實、流程完整的 Baseline，後續我會在此基礎上插入獨立的記憶層可視化與安全層產品進行測試，**但本次不包含任何可視化或監控功能**。

**本系統的核心價值**：讓任何人第一次看到這個系統，就能清楚理解「企業 Agent 在真實業務場景中是如何工作的」——從可疑交易觸發，到多 Agent 協作分析，到人工審核，到最終合規報告提交。

---

## 嚴格執行規則

1. **分任務執行**：我會列出 8 個任務，每完成一個任務後，輸出摘要並暫停，等我輸入 `繼續` 後再執行下一個任務。
2. **每個任務完成後**，列出：已建立的文件、可執行的驗證命令、以及下一個任務的預告。
3. **遇到依賴衝突或環境問題**，直接告訴我並提供兩個解決方案，不要自行假設繼續。
4. **所有 Mock 數據必須真實可信**：客戶名稱、金額、地區、案件描述都要符合金融業真實樣貌，不要使用 `foo`、`test`、`example` 等佔位符。
5. **代碼必須有中英文雙語注釋**：這個系統後續要展示給非技術人員，注釋要說明「這段代碼在做什麼業務操作」而不只是技術描述。

---

## 技術棧

```
語言：Python 3.11+
Agent 框架：langgraph >= 0.2.0
LLM：使用本地部署qwen3.6
短期記憶：LangGraph Thread State（內建 checkpointer）
情節記憶：ChromaDB（過去 SAR 案件向量庫）
語義記憶：ChromaDB（法規條文向量庫）
程序記憶：SQLite（SOP 工作流規則）
長期用戶記憶：SQLite（合規官偏好設定）
Embedding：sentence-transformers（all-MiniLM-L6-v2）
審計日誌：SQLite（結構化，為後續產品接入預留欄位）
API 服務：FastAPI + uvicorn
Mock 數據生成：Faker（全英文）
測試入口：CLI 交互式腳本
語言：英文
```

**所有依賴版本固定在 requirements.txt 中，確保可重現。**

---

## 完整目錄結構

建立以下完整目錄結構（先建結構，再填內容）：

```
fincompli-baseline/
│
├── README.md                         # 系統說明（中英文）
├── requirements.txt                  # 固定版本依賴
├── .env.example                      # 環境變量模板
├── .gitignore
├── setup.py                          # 一鍵初始化腳本
│
├── config/
│   ├── __init__.py
│   └── settings.py                   # 全局配置（從 .env 讀取）
│
├── agents/                           # 所有 Agent 定義
│   ├── __init__.py
│   ├── supervisor.py                 # 主 Supervisor Agent（LangGraph 入口）
│   ├── fraud_detection.py            # Sub-Agent 1：交易詐欺偵測
│   ├── compliance_research.py        # Sub-Agent 2：法規條文研究
│   ├── case_history.py               # Sub-Agent 3：歷史案件檢索
│   └── report_generator.py           # Sub-Agent 4：SAR 報告生成
│
├── graph/
│   ├── __init__.py
│   ├── state.py                      # LangGraph State Schema 定義
│   ├── builder.py                    # Graph 構建與編譯
│   └── nodes.py                      # 所有 Graph Node 函數
│
├── memory/                           # 記憶層（分層設計）
│   ├── __init__.py
│   ├── short_term.py                 # 短期：Thread State 封裝
│   ├── episodic.py                   # 情節：SAR 案件向量庫
│   ├── semantic.py                   # 語義：法規知識向量庫
│   ├── procedural.py                 # 程序：SOP 規則 SQLite
│   └── user_prefs.py                 # 用戶：合規官偏好 SQLite
│
├── tools/                            # 企業工具 Mock 實現
│   ├── __init__.py
│   ├── transaction_monitor.py        # 交易串流監控工具
│   ├── customer_database.py          # 客戶資料庫查詢工具
│   ├── risk_scorer.py                # 風險評分計算工具
│   ├── regulatory_lookup.py          # 法規條文查詢工具
│   ├── sar_submission.py             # SAR 提交模擬工具
│   └── audit_logger.py              # 審計日誌記錄（預留接口）
│
├── mock_data/                        # 模擬企業數據
│   ├── __init__.py
│   ├── generators/
│   │   ├── customers.py              # 生成 100 個虛擬客戶
│   │   ├── transactions.py           # 生成交易場景（正常/異常/邊界）
│   │   ├── sar_cases.py             # 生成 30 條歷史 SAR 案件
│   │   └── regulations.py            # 生成法規條文片段
│   ├── seeds/
│   │   ├── customers.json            # 已生成的客戶數據
│   │   ├── sar_cases.json           # 已生成的歷史案件
│   │   ├── regulations.json          # 法規條文
│   │   └── transaction_scenarios.json # 測試場景
│   └── seed_database.py              # 將 seeds 導入所有記憶層
│
├── api/
│   ├── __init__.py
│   ├── server.py                     # FastAPI 主服務
│   ├── routes/
│   │   ├── transactions.py           # /api/transactions 端點
│   │   ├── analysis.py               # /api/analyze 端點
│   │   └── reports.py                # /api/reports 端點
│   └── schemas.py                    # Pydantic 請求/響應模型
│
├── cli/
│   ├── __init__.py
│   ├── interactive.py                # 交互式測試 CLI
│   └── batch_test.py                 # 批量場景測試
│
├── scenarios/                        # 完整測試場景腳本
│   ├── scenario_01_normal_transfer.py
│   ├── scenario_02_structuring.py    # 結構化分拆（主要演示場景）
│   ├── scenario_03_high_risk_kyc.py
│   ├── scenario_04_cross_border.py
│   └── scenario_05_false_positive.py
│
├── audit_logs/                       # 審計日誌輸出目錄（git ignore）
│   └── .gitkeep
│
└── data/                             # 運行時數據（git ignore）
    ├── chroma/                       # ChromaDB 持久化目錄
    └── sqlite/                       # SQLite 數據庫目錄
```

---

## 任務清單（按順序執行）

---

### TASK 1：項目初始化與環境搭建

**目標**：建立完整目錄結構，配置所有依賴，確保環境可運行。

**執行步驟**：

1. 建立完整目錄結構（所有目錄和空的 `__init__.py`）

2. 建立 `requirements.txt`，內容如下（版本固定）如有需要可以新增：
```
langgraph==0.2.35
langchain==0.3.7
langchain-community==0.3.7
langchain-chroma==0.1.4
chromadb==0.5.15
sentence-transformers==3.2.1
fastapi==0.115.5
uvicorn==0.32.1
sqlalchemy==2.0.36
pydantic==2.10.1
pydantic-settings==2.6.1
faker==33.1.0
python-dotenv==1.0.1
rich==13.9.4
typer==0.13.1
httpx==0.28.0
pytest==8.3.3
pytest-asyncio==0.24.0
```

3. 建立 `.env.example`：
```env
# LLM Configuration
# LLM Configuration (local Qwen via llama.cpp llama-server)
LLM_BASE_URL=http://localhost:8080
LLM_MODEL=Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf
LLM_API_KEY=not-needed-for-local

# Database Paths
CHROMA_DB_PATH=./data/chroma
SQLITE_DB_PATH=./data/sqlite/fincompli.db

# System Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
MAX_RISK_SCORE=0.85          # 高於此分數觸發人工審核
AUTO_APPROVE_THRESHOLD=0.30  # 低於此分數自動放行

# Mock Settings
ENABLE_MOCK_DATA=true
TRANSACTION_STREAM_DELAY=0   # 秒，0 表示即時

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

4. 建立 `config/settings.py`（使用 Pydantic Settings 從環境變量讀取）

5. 建立 `.gitignore`（排除 `data/`、`audit_logs/*.db`、`.env`、`__pycache__` 等）

6. 建立 `setup.py` 一鍵初始化腳本：
   - 自動建立 `data/chroma`、`data/sqlite`、`audit_logs` 目錄
   - 複製 `.env.example` 為 `.env`（如果不存在）
   - 安裝依賴
   - 輸出下一步提示

**完成標準**：執行 `python setup.py` 無錯誤，`python -c "import langgraph; import chromadb; print('OK')"` 通過。

---

### TASK 2：Mock 企業數據生成

**目標**：生成所有真實可信的模擬企業數據，這是整個系統可信度的基礎。

**重要**：數據必須符合真實金融業場景，以下是每類數據的具體要求。

**2a. 客戶數據（`mock_data/generators/customers.py`）**

生成 100 個客戶，分為以下風險等級：
- **低風險（60人）**：本地居民/企業，長期穩定交易記錄，KYC 完整
- **中風險（30人）**：離岸公司或近期新開戶，有部分不完整資料
- **高風險（10人）**：PEP（政治敏感人士）或涉及 FATF 高風險名單國家

每個客戶包含：
```json
{
  "customer_id": "C-XXXXX",
  "name": "真實人名或公司名（用 Faker 生成中英文）",
  "type": "individual | corporate",
  "kyc_status": "verified | pending | expired",
  "risk_level": "low | medium | high",
  "country": "HK | SG | CN | KY | BVI | UK | US",
  "account_number": "HKXX XXXX XXXX XXXX",
  "account_open_date": "ISO date",
  "typical_transaction_range": {"min": 10000, "max": 500000},
  "typical_countries": ["HK", "SG"],
  "monthly_transaction_count": 5,
  "notes": "客戶備注（業務描述）"
}
```

**2b. 歷史 SAR 案件（`mock_data/generators/sar_cases.py`）**

生成 30 條歷史 SAR 案件，這些是情節記憶的核心。

每個案件包含：
```json
{
  "sar_id": "SAR-2023-XXXX",
  "filed_date": "ISO date",
  "customer_id": "關聯客戶",
  "case_type": "structuring | money_laundering | fraud | terrorist_financing | other",
  "transaction_pattern": "詳細描述交易模式（2-3句話）",
  "amount_total": 1470000,
  "jurisdictions_involved": ["HK", "SG", "KY"],
  "suspicious_indicators": ["indicator_1", "indicator_2"],
  "regulations_cited": ["HKMA AML § 35", "FSTB Notice 2024-01"],
  "outcome": "filed | dismissed | referred_to_police",
  "case_summary": "完整案件摘要（100-200字，供 RAG 檢索用）",
  "lessons_learned": "從這個案件學到什麼"
}
```

案件類型分佈：
- structuring（結構化分拆）：10 件
- money_laundering（洗錢）：8 件
- fraud（詐欺）：7 件
- terrorist_financing（恐怖融資）：3 件
- other：2 件

**2c. 法規條文（`mock_data/generators/regulations.py`）**

生成以下真實監管框架的模擬條文片段（**不要虛構法規名稱，使用真實存在的框架，內容可以簡化**）：

- HKMA 反洗錢指引（AML Guideline 2023）：15 條
- MAS 新加坡金管局 Notice MAS 626：10 條
- FinCEN BSA/AML 要求：10 條
- FATF 40 項建議相關條款：5 條

每條條文：
```json
{
  "regulation_id": "HKMA-AML-2023-§35",
  "jurisdiction": "HK | SG | US | INT",
  "authority": "HKMA | MAS | FinCEN | FATF",
  "section": "§ 35",
  "title": "可疑交易申報義務",
  "content": "完整條文內容（200字以內）",
  "applicability": "何種情況適用",
  "deadline": "3 個工作日內申報",
  "penalty": "最高罰款金額或說明"
}
```

**2d. 交易測試場景（`mock_data/generators/transactions.py`）**

生成 5 類交易場景，每類 5 筆，共 25 筆測試交易：

1. **正常跨境匯款**：客戶 A 向香港→新加坡匯款 $150,000，有明確商業目的
2. **結構化分拆（高風險）**：客戶 B 在 3 分鐘內從 HK、SG、KY 各轉出 $490,000
3. **異常地域組合（中風險）**：客戶 C 突然向 FATF 高風險國家轉帳，偏離歷史模式
4. **KYC 過期高額交易（中風險）**：客戶 D KYC 已過期但仍在進行大額交易
5. **假陽性場景**：看起來可疑但有合理解釋的交易（測試系統不誤報）

每筆交易：
```json
{
  "transaction_id": "TXN-YYYYMMDD-XXXXX",
  "timestamp": "ISO datetime",
  "customer_id": "C-XXXXX",
  "from_account": "帳號",
  "to_account": "帳號",
  "to_country": "目的地國家代碼",
  "amount": 490000,
  "currency": "HKD | USD | SGD",
  "purpose_code": "交易目的代碼",
  "channel": "swift | local_transfer | online",
  "ip_address": "如是線上交易",
  "device_fingerprint": "設備ID",
  "scenario_type": "normal | structuring | geo_anomaly | kyc_expired | false_positive",
  "expected_risk_score": 0.93,
  "expected_outcome": "flag | clear | human_review"
}
```

**2e. 建立 `mock_data/seed_database.py`**

讀取所有 seeds JSON 文件，完成：
1. 將客戶數據存入 SQLite
2. 將 SAR 案件 `case_summary` 向量化存入 ChromaDB `episodic_memory` collection
3. 將法規條文 `content` 向量化存入 ChromaDB `semantic_memory` collection
4. 將交易場景存入 SQLite
5. 輸出：`已導入 X 個客戶、X 條 SAR 案件、X 條法規、X 個交易場景`

**完成標準**：`python mock_data/seed_database.py` 成功，ChromaDB 和 SQLite 有數據，執行查詢測試通過。

---

### TASK 3：記憶層實現

**目標**：實現分層記憶系統，每層有清晰的讀寫接口，為後續接入可視化產品預留標準 hook 點。

**關鍵設計**：每個記憶操作都必須記錄到審計日誌，格式固定，後續產品只需讀取這個日誌就能可視化。

**3a. `memory/short_term.py`**

封裝 LangGraph Thread State，提供：
```python
class ShortTermMemory:
    """
    短期記憶：當前對話的上下文狀態
    存儲於 LangGraph Thread State，對話結束後自動清除
    
    [Business Purpose] 讓所有 sub-agent 能共享當前分析任務的上下文
    """
    def get_thread_state(self, thread_id: str) -> dict: ...
    def update_context(self, thread_id: str, key: str, value: Any) -> None: ...
```

**3b. `memory/episodic.py`**

封裝 ChromaDB `episodic_memory` collection：
```python
class EpisodicMemory:
    """
    情節記憶：過去 SAR 案件的完整記錄
    用於：「這筆交易與哪些過去案件相似？」
    
    [Business Purpose] 讓 Agent 能從歷史案件中學習判斷模式
    """
    def retrieve_similar_cases(
        self, 
        query: str, 
        n_results: int = 5
    ) -> list[SARCaseResult]:
        """
        返回格式包含：case_id, similarity_score, case_summary, outcome
        similarity_score 是後續可視化產品的關鍵數據，必須保留
        """
        ...
    
    def add_case(self, case: SARCase) -> str: ...
```

**3c. `memory/semantic.py`**

封裝 ChromaDB `semantic_memory` collection：
```python
class SemanticMemory:
    """
    語義記憶：法規條文知識庫
    用於：「本案件適用哪些監管條款？」
    
    [Business Purpose] 讓 Agent 能自動引用正確的法規依據，確保合規報告可被審計
    """
    def retrieve_relevant_regulations(
        self, 
        context: str, 
        jurisdiction: str | None = None,
        n_results: int = 3
    ) -> list[RegulationResult]: ...
```

**3d. `memory/procedural.py`**

SQLite 存儲 SOP 工作流：
```python
class ProceduralMemory:
    """
    程序記憶：標準合規操作程序（SOP）
    固定規則，如：「評分 > 0.85 必須提交 SAR」
    
    [Business Purpose] 確保所有 Agent 行為符合銀行內部合規流程
    """
    def get_workflow_rules(self, scenario_type: str) -> list[WorkflowRule]: ...
    def get_escalation_threshold(self) -> float: ...
```

**3e. `memory/user_prefs.py`**

SQLite 存儲合規官偏好：
```python
class UserPrefsMemory:
    """
    用戶記憶：合規官的個人偏好設定
    例如：偏好中文報告、特別關注某類風險
    
    [Business Purpose] 個性化合規官的工作界面，提升效率
    """
    def get_user_preferences(self, user_id: str) -> UserPreferences: ...
    def update_preference(self, user_id: str, key: str, value: Any) -> None: ...
```

**3f. 統一的 `MemoryAuditLog`（在 `tools/audit_logger.py`）**

**這是後續產品接入的關鍵接口，必須嚴格按此格式實現：**

```python
class MemoryAuditLog:
    """
    審計日誌：記錄所有記憶層操作
    
    [後續產品接入點] 可視化產品只需訂閱此日誌即可獲取完整記憶追蹤數據
    """
    def log_memory_event(self, event: MemoryEvent) -> None:
        """
        寫入格式（SQLite `memory_events` 表）：
        - event_id: UUID
        - timestamp: ISO datetime
        - event_type: "retrieve" | "write" | "delete" | "access_denied"
        - memory_type: "episodic" | "semantic" | "procedural" | "user_prefs"
        - agent_id: 哪個 agent 觸發了此操作
        - thread_id: 當前對話 thread
        - query: 查詢內容（retrieve 時）
        - memory_ids: 涉及的記憶 ID 列表（JSON）
        - similarity_scores: 相似度分數列表（retrieve 時，JSON）
        - output_snippet: 記憶內容摘要（前 200 字）
        - security_flag: null | "unauthorized_access" | "suspicious_write" | "pii_leak"
        """
        ...
```

**完成標準**：
```python
# 以下測試腳本能成功運行
from memory.episodic import EpisodicMemory
em = EpisodicMemory()
results = em.retrieve_similar_cases("客戶在三個轄區快速連續轉帳")
assert len(results) > 0
assert hasattr(results[0], 'similarity_score')
print(f"找到 {len(results)} 條相似案件，最高相似度：{results[0].similarity_score:.2f}")
```

---

### TASK 4：Graph State Schema 定義

**目標**：定義 LangGraph 的核心狀態 Schema，這是整個 Agent 系統的「共享工作台」。

**`graph/state.py`**

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator

class TransactionData(TypedDict):
    """一筆待分析的交易"""
    transaction_id: str
    customer_id: str
    amount: float
    currency: str
    from_country: str
    to_country: str
    timestamp: str
    channel: str
    # 批次分析時（如結構化分拆），包含相關聯的多筆交易
    related_transactions: list[dict]

class RiskAnalysis(TypedDict):
    """詐欺偵測 Agent 的分析結果"""
    risk_score: float                    # 0.0 - 1.0
    risk_level: str                      # "low" | "medium" | "high" | "critical"
    suspicious_indicators: list[str]     # 具體異常指標列表
    pattern_type: str                    # "structuring" | "geo_anomaly" | "normal" | ...
    analysis_reasoning: str             # Agent 的分析說明（業務語言）

class ComplianceResearch(TypedDict):
    """法規研究 Agent 的輸出"""
    applicable_regulations: list[dict]  # 適用法規列表（含引用來源）
    filing_deadline: str                # 申報期限
    required_actions: list[str]         # 必要行動清單
    jurisdiction: list[str]            # 涉及的司法管轄區

class HistoricalContext(TypedDict):
    """案例歷史 Agent 的輸出"""
    similar_cases: list[dict]           # 相似歷史案件（含相似度分數）
    historical_pattern: str            # 從歷史案件歸納的模式
    precedent_outcomes: list[str]       # 過去類似案件的處理結果

class SARReport(TypedDict):
    """SAR 報告生成 Agent 的輸出"""
    report_id: str
    status: str                         # "draft" | "approved" | "submitted" | "dismissed"
    report_content: str                # 完整 SAR 報告正文（業務語言，可提交格式）
    evidence_trail: list[dict]         # 證據鏈（含每條依據的記憶來源）
    submission_deadline: str

class MemoryTrace(TypedDict):
    """
    記憶追蹤：每次記憶調用的完整記錄
    [後續產品接入點] 這是可視化產品的核心數據結構
    """
    event_id: str
    memory_type: str                    # "episodic" | "semantic" | "procedural" | "user_prefs"
    agent_id: str                       # 哪個 agent 調用了此記憶
    query: str                         # 查詢內容
    retrieved_memory_ids: list[str]    # 取回的記憶 ID
    similarity_scores: list[float]     # 對應的相似度分數
    influenced_output: str             # 這條記憶影響了哪部分輸出
    timestamp: str

class HumanDecision(TypedDict):
    """人工審核節點的輸入"""
    reviewer_id: str
    decision: str                       # "approve" | "reject" | "modify"
    comments: str
    timestamp: str

class ComplianceState(TypedDict):
    """
    整個分析流程的共享狀態
    
    [Business Purpose] 這是所有 Agent 的「共享工作台」
    任何 Agent 都可以讀取其他 Agent 的工作成果，確保信息一致性
    """
    # 對話消息歷史（LangGraph 自動管理）
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # 當前分析的交易
    transaction_data: TransactionData | None
    
    # 各 Agent 的分析結果
    risk_analysis: RiskAnalysis | None
    compliance_research: ComplianceResearch | None
    historical_context: HistoricalContext | None
    sar_report: SARReport | None
    
    # 流程控制
    current_agent: str                  # 當前執行的 Agent
    next_agents: list[str]             # 下一步要執行的 Agent 列表
    requires_human_review: bool        # 是否需要人工審核
    human_decision: HumanDecision | None
    
    # 記憶追蹤（所有 Agent 的記憶調用都累積在這裡）
    memory_traces: Annotated[list[MemoryTrace], operator.add]
    
    # 安全事件（預留，本次不實現檢測邏輯，只預留結構）
    security_events: list[dict]
    
    # 最終輸出
    final_outcome: str | None          # "sar_filed" | "cleared" | "pending_review"
    execution_timeline: list[dict]     # 完整執行時間線（用於審計）
```

**`graph/builder.py`** — 定義完整的 LangGraph 流程圖：

```python
"""
FinCompli Agent 流程圖

流程設計：
1. 入口：接收交易 → Supervisor 路由
2. 並行分析：詐欺偵測 + 案例歷史 同時運行
3. 彙整：Supervisor 彙整結果，決定是否需要法規研究
4. 法規研究：根據風險類型查詢相關法規
5. 報告生成：彙整所有輸入，生成 SAR 草稿
6. 人工審核（高風險觸發）：interrupt() 等待合規官確認
7. 最終提交/存檔

圖結構：
START
  ↓
[supervisor_route]          ← 分析意圖，決定路由
  ↓
[fraud_detection] ←→ [case_history_retrieval]   ← 並行執行
  ↓
[supervisor_aggregate]      ← 彙整分析結果
  ↓ (if risk > threshold)
[compliance_research]       ← 查詢法規
  ↓
[report_generation]         ← 生成 SAR 草稿
  ↓ (if risk > MAX_RISK)
[human_review_interrupt]    ← 暫停等待人工
  ↓
[final_submission]          ← 提交/存檔
  ↓
END
"""
```

**完成標準**：`from graph.state import ComplianceState` 成功，State 所有欄位有正確類型注釋。

---

### TASK 5：四個 Sub-Agent 實現

**目標**：實現每個 Sub-Agent 的核心邏輯，確保每個 Agent 有清晰的職責邊界和記憶調用。

**設計原則**：
- 每個 Agent 只做一件事，輸入輸出都清晰定義
- 每次調用記憶層必須同時寫入 `MemoryTrace` 到 State
- System Prompt 用業務語言描述 Agent 的角色，不用技術術語

**5a. `agents/fraud_detection.py`**

```python
"""
詐欺偵測 Agent

業務職責：
- 分析單筆或多筆相關交易
- 識別可疑交易模式（結構化分拆、地域異常、行為偏差等）
- 輸出風險評分（0.0-1.0）和具體可疑指標

使用的記憶：
- 程序記憶：詐欺判斷規則（如：「同一客戶 30 分鐘內 3 筆交易 = 可疑」）
- 短期記憶：當前 thread 中的客戶信息

不使用：歷史案件（由 case_history agent 負責）
"""

FRAUD_DETECTION_SYSTEM_PROMPT = """
你是一名擁有 15 年經驗的資深反洗錢（AML）分析師。

你的職責是分析提交的交易數據，識別可能的可疑交易模式。

## 你要識別的模式

**結構化分拆（Structuring）**
- 多筆交易金額略低於法定申報門檻（如每筆 $499,000）
- 短時間內多轄區操作
- 目的是規避自動申報

**地域異常**
- 目的地國家與客戶歷史模式不符
- 涉及 FATF 高風險名單國家（如伊朗、朝鮮、緬甸）

**行為偏差**
- 交易金額超出客戶歷史範圍 3 倍以上
- 突然改變交易頻率或渠道

## 輸出格式要求

用業務語言解釋你的分析，合規官必須能看懂。
不要使用技術術語。
每個可疑指標必須附上具體數據支撐。
"""
```

實現 `detect_fraud(state: ComplianceState) -> ComplianceState`：
1. 讀取 `state["transaction_data"]`
2. 查詢 ProceduralMemory 獲取判斷規則，記錄到 `memory_traces`
3. 調用 LLM 分析（帶客戶歷史數據作為上下文）
4. 輸出 `RiskAnalysis` 並更新 State

**5b. `agents/case_history.py`**

```python
"""
歷史案件檢索 Agent

業務職責：
- 在歷史 SAR 案件庫中找到與當前交易最相似的案件
- 提取歷史案件的處理方式和結果
- 為報告生成提供「參考先例」

使用的記憶：
- 情節記憶（ChromaDB）：30 條歷史 SAR 案件

輸出的相似度分數是可視化產品的核心展示數據
"""
```

實現 `retrieve_case_history(state: ComplianceState) -> ComplianceState`：
1. 從 `state["risk_analysis"]` 提取交易特徵描述作為查詢
2. 查詢 EpisodicMemory，獲取 top-5 相似案件
3. **關鍵**：將完整的 `memory_trace` 記錄到 State，包含相似度分數
4. 輸出 `HistoricalContext`

**5c. `agents/compliance_research.py`**

```python
"""
法規研究 Agent

業務職責：
- 根據交易特徵和涉及轄區，找到適用的監管規定
- 確定申報期限和必要行動
- 引用具體法規條款（用於 SAR 報告）

使用的記憶：
- 語義記憶（ChromaDB）：HKMA/MAS/FinCEN 法規條文庫

這個 Agent 的輸出直接決定了 SAR 報告的法律依據質量
"""
```

**5d. `agents/report_generator.py`**

```python
"""
SAR 報告生成 Agent

業務職責：
- 彙整前三個 Agent 的分析結果
- 生成符合監管要求的 SAR 報告草稿
- 報告必須包含：事實陳述、可疑指標、法規依據、證據鏈

使用的記憶：
- 程序記憶：SAR 報告格式模板（HKMA 標準格式）
- 用戶偏好記憶：合規官的報告語言偏好（中文/英文）
- 短期記憶：當前對話中的所有分析結果

這是整個流程的最終輸出，質量直接影響監管申報的合規性
"""

SAR_REPORT_FORMAT = """
## 可疑交易申報報告草稿
**申報機構**：[機構名稱]
**申報日期**：[日期]
**案件編號**：[SAR-XXXX-XXXX]

### 一、可疑客戶/交易概況
[客戶基本信息 + 涉案交易摘要]

### 二、可疑行為描述
[具體可疑行為，用業務語言，時間線格式]

### 三、可疑性判斷依據
[結合歷史案件先例 + 詐欺分析結果]

### 四、適用法規
[引用具體法規條款]

### 五、建議行動
[申報期限 + 下一步行動]

### 六、記憶引用追蹤
[此報告基於的所有記憶來源，含記憶ID和相似度]
"""
```

**完成標準**：
```bash
python -c "
from agents.fraud_detection import FraudDetectionAgent
agent = FraudDetectionAgent()
print('FraudDetectionAgent 初始化成功')
"
```

---

### TASK 6：Supervisor 與 Graph 組裝

**目標**：用 LangGraph 將所有 Agent 連接成完整的工作流程，實現並行執行、條件路由、和 Human-in-the-loop。

**`agents/supervisor.py`**

Supervisor 的職責：
1. **接收任務**：分析用戶輸入，提取交易信息
2. **路由決策**：決定哪些 Sub-Agent 需要運行
3. **彙整結果**：等待並行 Agent 完成，整合輸出
4. **風險門控**：判斷是否需要人工審核
5. **最終決策**：在人工審核後執行最終動作

```python
SUPERVISOR_SYSTEM_PROMPT = """
你是 FinCompli 系統的主管協調員。

你的工作是協調以下四位專家分析師的工作：
1. 詐欺偵測分析師：評估交易風險
2. 案件歷史研究員：查找歷史先例
3. 法規合規顧問：確定適用法規
4. 報告撰寫員：生成 SAR 報告

你負責：
- 根據交易類型決定哪些分析師需要參與
- 彙整所有分析結果，形成統一判斷
- 在風險評分超過 {threshold} 時，暫停並請合規官審核

你不直接做分析，你是協調者。
"""
```

**`graph/builder.py`** — 完整 Graph 構建：

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Send, interrupt

def build_compliance_graph(memory_saver):
    """
    構建完整的合規分析 Graph
    
    並行執行設計：
    fraud_detection 和 case_history_retrieval 同時運行
    兩者完成後，supervisor 彙整結果再繼續
    """
    
    builder = StateGraph(ComplianceState)
    
    # 添加所有節點
    builder.add_node("supervisor_route", supervisor_route_node)
    builder.add_node("fraud_detection", fraud_detection_node)
    builder.add_node("case_history_retrieval", case_history_node)
    builder.add_node("supervisor_aggregate", supervisor_aggregate_node)
    builder.add_node("compliance_research", compliance_research_node)
    builder.add_node("report_generation", report_generation_node)
    builder.add_node("human_review", human_review_node)   # interrupt 在這裡
    builder.add_node("final_submission", final_submission_node)
    
    # 定義流程
    builder.add_edge(START, "supervisor_route")
    
    # 路由到並行執行
    builder.add_conditional_edges(
        "supervisor_route",
        lambda state: ["fraud_detection", "case_history_retrieval"],
        ["fraud_detection", "case_history_retrieval"]
    )
    
    # 並行結束後彙整
    builder.add_edge("fraud_detection", "supervisor_aggregate")
    builder.add_edge("case_history_retrieval", "supervisor_aggregate")
    
    # 條件路由：風險等級決定後續路徑
    builder.add_conditional_edges(
        "supervisor_aggregate",
        route_by_risk_level,
        {
            "low_risk": "final_submission",
            "needs_research": "compliance_research",
        }
    )
    
    builder.add_edge("compliance_research", "report_generation")
    
    # 條件路由：高風險需要人工審核
    builder.add_conditional_edges(
        "report_generation",
        route_by_human_required,
        {
            "human_required": "human_review",
            "auto_approve": "final_submission"
        }
    )
    
    builder.add_edge("human_review", "final_submission")
    builder.add_edge("final_submission", END)
    
    # 編譯，使用 SQLite checkpointer 實現狀態持久化
    return builder.compile(checkpointer=memory_saver)

def human_review_node(state: ComplianceState):
    """
    人工審核節點
    
    [Business Purpose] 當風險評分超過閾值時，系統暫停並等待合規官確認
    合規官在此節點看到：完整的 SAR 草稿 + 所有分析依據 + 記憶調用追蹤
    """
    # 使用 LangGraph interrupt 暫停執行，等待外部輸入
    decision = interrupt({
        "message": "需要合規官審核",
        "risk_score": state["risk_analysis"]["risk_score"],
        "sar_draft": state["sar_report"],
        "memory_traces": state["memory_traces"],  # 傳遞記憶追蹤給審核界面
        "required_action": "請審閱 SAR 草稿並選擇：approve / reject / modify"
    })
    
    return {"human_decision": decision}
```

**完成標準**：
```python
# 以下能成功執行（不需要 LLM，只測試 Graph 結構）
from graph.builder import build_compliance_graph
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("./data/sqlite/test.db") as saver:
    graph = build_compliance_graph(saver)
    print("Graph 編譯成功")
    print("節點：", list(graph.nodes.keys()))
```

---

### TASK 7：CLI 測試界面與完整場景腳本

**目標**：建立清晰的測試入口，讓任何人都能方便地運行演示場景，看懂系統在做什麼。

**`cli/interactive.py`**

使用 `rich` 庫實現漂亮的終端輸出，讓非技術人員也能理解系統運行過程：

```python
"""
交互式 CLI

每個 Agent 執行時，在終端顯示：
- Agent 名稱和職責（中文說明）
- 正在查詢的記憶類型
- 查詢結果摘要
- 輸出結論

記憶調用顯示格式：
┌─────────────────────────────────────┐
│  🧠 記憶調用：情節記憶              │
│  查詢：「三個轄區快速連續轉帳」     │
│  找到 3 條相似案件：                │
│  ├ SAR-2024-0033 相似度: 88%        │
│  ├ SAR-2023-0171 相似度: 82%        │
│  └ SAR-2022-0089 相似度: 71%        │
└─────────────────────────────────────┘

人工審核節點顯示：
┌─────────────────────────────────────┐
│  ⚠️  需要人工審核                   │
│  風險評分: 0.93 (極高)              │
│  請輸入決策 [approve/reject/modify]:│
└─────────────────────────────────────┘
"""
```

**`scenarios/scenario_02_structuring.py`**（最重要的演示場景，需最完整）

```python
"""
場景 02：結構化分拆（Structuring）

[業務背景]
客戶 C-00412（Sunrise Global Holdings Ltd，開曼群島離岸公司）
在 3 分鐘內從香港、新加坡、開曼群島三個帳戶各轉出 HKD 490,000
共計 HKD 1,470,000，每筆均略低於 HKD 500,000 的自動申報門檻

[預期流程]
1. Supervisor 接收交易 → 路由到並行分析
2. 詐欺偵測：識別結構化分拆模式，風險評分 0.93
3. 案件歷史：找到 SAR-2024-0033（相似度 88%）和 SAR-2023-0171（相似度 82%）
4. Supervisor 彙整：高風險，需要法規研究
5. 法規研究：HKMA §35（3工作日申報）、FinCEN §103.18
6. 報告生成：生成 SAR 草稿
7. 人工審核：合規官審核並批准
8. 最終提交：SAR 文件存檔

[期望輸出]
- 完整的 SAR 草稿（中英文）
- 5 條記憶調用記錄（含相似度分數）
- 完整的執行時間線
- 合規官決策記錄
"""

SCENARIO_TRANSACTION = {
    "transaction_id": "TXN-20250315-88411",
    "timestamp": "2025-03-15T14:23:00+08:00",
    "customer_id": "C-00412",
    "customer_name": "Sunrise Global Holdings Ltd",
    "transactions": [
        {
            "sub_id": "TXN-88411-A",
            "timestamp": "2025-03-15T14:23:00+08:00",
            "from_account": "HK82 0012 3456 7890",
            "to_account": "KY1-9999-0001",
            "amount": 490000,
            "currency": "HKD",
            "to_country": "KY",  # 開曼群島
            "channel": "swift"
        },
        {
            "sub_id": "TXN-88411-B",
            "timestamp": "2025-03-15T14:24:30+08:00",
            "from_account": "SG29 DBS9 0000 0001",
            "to_account": "KY1-9999-0002",
            "amount": 490000,
            "currency": "HKD",
            "to_country": "KY",
            "channel": "swift"
        },
        {
            "sub_id": "TXN-88411-C",
            "timestamp": "2025-03-15T14:26:00+08:00",
            "from_account": "KY2-8888-0001",
            "to_account": "BVI-0000-7777",
            "amount": 490000,
            "currency": "HKD",
            "to_country": "VG",  # 英屬維京群島
            "channel": "swift"
        }
    ]
}
```

**所有 5 個場景都需要建立，格式一致，但 scenario_02 需最詳細。**

**`scenarios/scenario_05_false_positive.py`**（假陽性場景，測試系統精準度）

```python
"""
場景 05：假陽性

[業務背景]
客戶 C-00088（正規上市公司財務部）
在季度末向 5 個國家子公司轉帳，金額較大
表面看似異常，但有完整商業文件支持

[預期流程]
詐欺偵測：初步評分 0.60（中風險）
案件歷史：找到的相似案件最終均為「正常業務」
Supervisor：中風險，進行法規研究
合規研究：確認有商業文件則無需申報
報告生成：出具「無需申報說明」文件
最終結果：cleared，不提交 SAR

[測試目的]
驗證系統不會過度敏感，能正確識別假陽性
"""
```

**完成標準**：
```bash
# 能完整運行演示場景
python cli/interactive.py --scenario 02
# 系統能完整走完全部流程並輸出 SAR 草稿
```

---

### TASK 8：FastAPI 服務 + README + 最終整合測試

**目標**：提供 API 接口，完善文檔，並進行端到端整合測試。

**`api/server.py`**

提供以下 API 端點：

```
POST /api/analyze
  Body: { transaction_data: {...} }
  Response: { thread_id: "xxx", status: "started" }

GET /api/status/{thread_id}
  Response: { status, current_agent, risk_score, requires_human_review }

POST /api/human-decision/{thread_id}
  Body: { reviewer_id, decision, comments }
  Response: { status, final_outcome }

GET /api/report/{thread_id}
  Response: { sar_report, memory_traces, execution_timeline }

GET /api/memory-traces/{thread_id}
  Response: { traces: [{ memory_type, agent_id, query, memories, similarity_scores }] }
  [後續產品接入點] 此端點是可視化產品的主要數據源

GET /api/audit-log
  Query: ?limit=50&memory_type=episodic
  Response: { events: [...] }

GET /api/health
  Response: { status: "ok", version, agents_loaded, memory_collections }
```

**`README.md`** — 完整的系統說明文檔（中英文）：

```markdown
# FinCompli Baseline

一個模擬真實金融機構合規自動化流程的企業級 Multi-Agent 系統。

## 系統架構圖（文字版）

用戶/系統輸入可疑交易
        ↓
  [Supervisor Agent]  ← 協調所有分析工作
  ↙           ↘
[詐欺偵測]  [案例歷史]  ← 並行執行
  ↘           ↙
  [Supervisor 彙整]
        ↓（風險中/高）
  [法規研究 Agent]    ← 查詢適用法規
        ↓
  [報告生成 Agent]    ← 生成 SAR 草稿
        ↓（高風險）
  [人工審核節點]      ← 合規官確認
        ↓
  [最終提交/存檔]

## 記憶層設計

| 記憶類型     | 存儲         | 使用場景                     | 後續可視化 |
|------------|-------------|----------------------------|-----------|
| 短期記憶    | Thread State | 當前對話上下文               | ✓         |
| 情節記憶    | ChromaDB     | 歷史 SAR 案件檢索           | ✓ 重點    |
| 語義記憶    | ChromaDB     | 法規條文查詢                 | ✓         |
| 程序記憶    | SQLite       | SOP 規則                    | ✓         |
| 用戶偏好    | SQLite       | 合規官個性化設定             | ✓         |

## 快速開始

[詳細的安裝和運行步驟]

## 測試場景說明

[5 個場景的業務說明]

## 後續產品接入點

[說明哪些 hook 點是為記憶可視化產品預留的]
```

**最終整合測試**：

```bash
# 1. 初始化
python setup.py

# 2. 生成並導入 Mock 數據
python mock_data/seed_database.py

# 3. 驗證記憶層
python -m pytest tests/ -v

# 4. 運行核心演示場景
python cli/interactive.py --scenario 02

# 5. 啟動 API 服務
uvicorn api.server:app --reload

# 6. API 測試
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d @scenarios/scenario_02_data.json
```

**最終完成標準**：
- [ ] 所有 5 個場景能完整運行
- [ ] Scenario 02（結構化分拆）完整輸出：SAR 草稿 + 記憶追蹤 + 執行時間線
- [ ] `GET /api/memory-traces/{thread_id}` 返回包含相似度分數的完整記憶記錄
- [ ] `GET /api/audit-log` 返回所有記憶操作日誌
- [ ] README 能讓完全不懂 AI 的合規官看懂系統在做什麼

---

## 後續產品接入說明（本次不實現，但需保留接口）

以下接口點在 Baseline 中只需記錄數據，不做展示：

```python
# 1. 記憶調用勾子（在 memory/ 各模塊中）
def _log_memory_event(self, event_type, query, results):
    """
    [PRODUCT HOOK POINT]
    後續記憶可視化產品在此處接入
    預計接入方式：替換此方法為帶 WebSocket 推送的版本
    """
    audit_logger.log_memory_event(...)  # 目前只寫日誌

# 2. State 中的 memory_traces 列表
# 後續產品讀取此列表進行可視化

# 3. GET /api/memory-traces/{thread_id}
# 後續產品的主要數據源

# 4. GET /api/audit-log
# 後續安全審計產品的數據源
```

---

## 開始執行

請從 **TASK 1** 開始。完成每個任務後，列出已建立的文件清單和驗證命令，等待我輸入 `繼續` 後再執行下一個任務。

如果在執行過程中遇到任何問題，先描述問題和兩個可能的解決方案，等待我確認後再繼續。
