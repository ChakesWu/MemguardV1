# MemGuard - 执行工具清单

**创建时间**: 2026-07-01  
**状态**: 已准备就绪，可以执行

---

## 📋 已创建的执行工具

### 1. 快速启动脚本

| 脚本 | 用途 | 命令 |
|------|------|------|
| `START_BACKEND.sh` | 启动 Backend | `./START_BACKEND.sh` |
| `RUN_DEMO.sh` | 运行 Demo Agent | `./RUN_DEMO.sh` |
| `test_all.sh` | 完整测试套件 | `./test_all.sh` |
| `verify_installation.sh` | 验证安装 | `./verify_installation.sh` |

### 2. Python 测试脚本

| 脚本 | 用途 | 命令 |
|------|------|------|
| `test_sdk_backend_integration.py` | SDK→Backend 集成测试 | `python3 test_sdk_backend_integration.py` |
| `examples/demo_agent.py` | Demo Agent（3种模式） | `python3 examples/demo_agent.py --mode auto` |

---

## 🚀 执行步骤（按顺序）

### Step 1: 启动 Backend ⭐

```bash
# 方式1: 使用脚本
./START_BACKEND.sh

# 方式2: 手动启动
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**验证 Backend 启动成功**:
```bash
curl http://localhost:8000/health
# 期望输出: {"status":"ok", ...}
```

---

### Step 2: 运行测试套件 ✅

```bash
./test_all.sh
```

**这个脚本会测试**:
- ✅ Python 环境
- ✅ SDK 安装
- ✅ Backend 可访问性
- ✅ 数据库存在
- ✅ API endpoints
- ✅ SDK 导入

**期望结果**: `All tests passed! ✅`

---

### Step 3: 运行 Demo Agent 🤖

```bash
./RUN_DEMO.sh
```

**或者手动运行**:
```bash
cd examples

# 模式1: 自动演示（推荐）
python3 demo_agent.py --mode auto

# 模式2: 交互式对话
python3 demo_agent.py --mode interactive

# 模式3: 对比模式（with/without MemGuard）
python3 demo_agent.py --mode compare
```

**期望输出**:
```
======================================================================
  MemGuard Demo Agent - Automated Mode
======================================================================

Running pre-scripted conversation to demonstrate memory tracing...

📝 Session ID: auto-demo-20260701-XXXXXX

[Turn 1]
You: Hello!
Agent: Hello! I'm a demo agent with memory tracing. What's your name?

[Turn 2]
You: My name is Alice
Agent: Nice to meet you, Alice! I'll remember that.

...

✅ Demo complete!
📊 Total turns: 5
📊 Memory events: Check backend API
```

---

### Step 4: 验证事件捕获 🔍

```bash
# 查看数据库统计
curl http://localhost:8000/v1/db/stats | python3 -m json.tool

# 期望输出:
{
  "db_path": "backend/memguard.db",
  "total_events": 15,
  "total_decision_traces": 0,
  "persisted": true
}
```

**查看数据库内容**:
```bash
sqlite3 backend/memguard.db "SELECT event_id, operation, agent_id, memory_key FROM memory_events LIMIT 5;"
```

---

### Step 5: 测试 SDK 集成 🔌

```bash
python3 test_sdk_backend_integration.py
```

**这个脚本会**:
1. ✅ 创建 MemGuard interceptor
2. ✅ 发送测试事件到 Backend
3. ✅ 验证事件存储
4. ✅ 查询统计数据

**期望输出**:
```
======================================================================
TEST: SDK → Backend Integration
======================================================================

📤 Sending test events to backend...
  1. CREATE event
  2. READ event
  3. UPDATE event
  4. Agent workflow simulation (5 events)

✅ Sent 8 events to backend

🔍 Verifying events in database...
  ✅ Database stats:
     - Total events: 23
     - Total traces: 0
     - DB path: backend/memguard.db

======================================================================
✅ TEST PASSED: SDK → Backend integration working!
======================================================================
```

---

## 📊 验证清单

执行完上述步骤后，确认以下项目：

- [ ] **Backend 运行中**: `curl http://localhost:8000/health` 返回 OK
- [ ] **Demo 运行成功**: 看到完整对话输出
- [ ] **事件已捕获**: `total_events > 0`
- [ ] **数据库可查询**: SQLite 命令返回数据
- [ ] **SDK 集成测试通过**: 看到 "TEST PASSED"

**如果全部通过 → Stage 1 基础功能验证完成！** ✅

---

## 🛠️ 故障排除

### 问题1: Backend 启动失败

```bash
# 检查端口占用
lsof -i :8000

# 如果被占用，杀死进程
kill -9 $(lsof -t -i:8000)

# 重新启动
./START_BACKEND.sh
```

### 问题2: Demo Agent 报错 "ModuleNotFoundError: No module named 'langgraph'"

```bash
# 安装 LangGraph
pip3 install langgraph langchain-core

# 重新运行
./RUN_DEMO.sh
```

### 问题3: SDK 导入失败

```bash
# 重新安装 SDK
cd sdk
pip3 install -e . --force-reinstall
cd ..

# 验证安装
python3 -c "from memguard.core.event import MemoryEvent; print('✅ OK')"
```

### 问题4: 数据库无事件

```bash
# 检查 Backend 日志
tail -20 backend.log

# 查看数据库
sqlite3 backend/memguard.db "SELECT COUNT(*) FROM memory_events;"

# 重新运行 Demo
./RUN_DEMO.sh
```

### 问题5: curl 命令失败

```bash
# 检查 Backend 是否运行
ps aux | grep uvicorn

# 检查端口监听
netstat -an | grep 8000

# 重启 Backend
./START_BACKEND.sh
```

---

## 🎯 下一步行动

当所有测试通过后，你可以：

### 1. 开发 Frontend Dashboard（本周重点）⭐

```bash
cd frontend
npm install
npm run dev
```

创建以下页面：
- `app/timeline/[sessionId]/page.tsx` - Timeline 页面
- `components/EventDetailModal.tsx` - 事件详情 Modal
- `components/SessionSelector.tsx` - Session 选择器

### 2. 完善 Backend API

检查并实现：
- `GET /v1/sessions` - 返回所有 session 列表
- `GET /v1/sessions/{session_id}/timeline` - 返回 session 的 timeline
- 添加分页和过滤支持

### 3. 编写文档

创建：
- `docs/api-reference.md` - API 文档
- `docs/integrations/langgraph.md` - LangGraph 集成指南
- 录制演示视频（5-10分钟）

### 4. 准备发布

- 打包 SDK: `cd sdk && python3 setup.py sdist bdist_wheel`
- 创建 Docker 镜像
- 编写 CHANGELOG.md
- 准备 beta 测试计划

---

## 📚 文档索引

| 文档 | 内容 |
|------|------|
| `START_HERE.md` | 从这里开始 |
| `QUICKSTART.md` | 5分钟快速教程 |
| `MEMGUARD_STANDALONE_PLAN.md` | 完整开发计划 |
| `TASK_EXECUTION_COMPLETE.md` | 任务完成总结 |
| `README.md` | 项目概述 |

---

## ✅ 成功标志

**当你完成以下所有项，Stage 1 核心就完成了**:

1. ✅ Backend 稳定运行
2. ✅ Demo agent 成功演示
3. ✅ 事件成功捕获
4. ✅ API 可以查询数据
5. ✅ SDK 集成只需 3 行代码
6. ✅ 所有测试通过

**然后就可以**:
- 🎨 构建 Frontend 可视化
- 📚 编写详细文档
- 🚀 发布 beta 版本
- 📢 邀请外部测试者

---

## 🎉 立即开始

**运行这个命令开始验证**:

```bash
# 终端1: 启动 Backend
./START_BACKEND.sh

# 终端2: 运行测试
./test_all.sh

# 终端3: 运行 Demo
./RUN_DEMO.sh
```

**祝你开发顺利！** 🚀

---

**最后更新**: 2026-07-01  
**状态**: ✅ 工具就绪，可以执行  
**下一个里程碑**: Frontend Dashboard
