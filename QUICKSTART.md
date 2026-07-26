# 🚀 Quick Start Guide

**Get the MemGuard demo running in 2 minutes**

---

## Prerequisites

You need Python 3.9+ with pip installed. That's it!

---

## Step 1: Install Dependencies

```bash
cd /Users/chakeswu/cursor/MemguardV1

# Install MemGuard SDK
pip install -e sdk/

# Install Rich for beautiful terminal output
pip install rich requests
```

---

## Step 2: Run the Demo

```bash
python3 demo.py
```

That's it! The demo will:
- ✅ Check for local Qwen (optional, on port 8080)
- ✅ Check for MemGuard backend (optional, on port 8000)
- ✅ Run FinCompli Scenario 02 (Structuring detection)
- ✅ Display beautiful colored output
- ✅ Show all memory operations in real-time
- ✅ Complete in ~7 seconds

---

## What You'll See

### Demo Output Preview

```
╭─────────────────────────────────────────────╮
│  MemGuard × FinCompli                       │
│  Enterprise Compliance Demo                 │
╰─────────────────────────────────────────────╯

✅ Local Qwen detected (http://localhost:8080)
✅ MemGuard backend connected (http://localhost:8000)

╭─ Scenario 02: Structuring Detection ────────╮
│  Customer: Sunrise Global Holdings Ltd      │
│  • HKD 490,000 × 3 transactions             │
│  • Total: HKD 1,470,000                     │
│  • Below HKD 500,000 threshold each         │
╰──────────────────────────────────────────────╯

Running Analysis...

→ Fraud Detection Agent
  🔵 READ    episodic:customer_history
  🔷 QUERY   episodic:transaction_patterns
  🟢 CREATE  working:fraud_analysis
  Risk Score: 0.89 (CRITICAL)

→ Case History Agent
  🔷 QUERY   episodic:sar_cases
  Retrieved: SAR-2024-0033 (88% match) ⭐

... (continues with compliance research & report)

╭─ Decision Trace ─────────────────────────────╮
│  MEMORY IN (Influence: 2.53)                │
│    episodic:sar_cases     ████████░░ 0.88   │
│    semantic:regulations   ███████░░░ 0.76   │
│    working:fraud_analysis ████████░░ 0.89   │
│                    ↓                         │
│  DECISION: FILE SAR (confidence: 0.92)      │
│                    ↓                         │
│  MEMORY OUT: sar_report created             │
╰──────────────────────────────────────────────╯

✅ Analysis Complete (6.7s)

Final Decision: FILE SAR (CRITICAL)
```

---

## Optional: Start Full Stack

### Start MemGuard Backend (Optional)

```bash
# In a new terminal
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then visit:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Start Local Qwen (Optional)

If you have llama.cpp server running:
```bash
# Start Qwen on port 8080
llama-server --model your-qwen-model.gguf --port 8080
```

**Note:** The demo works fine without Qwen or the backend! It will run in heuristic mode with simulated data.

---

## Understanding the Output

### Memory Operation Icons

- 🔵 **READ** - Reading from memory
- 🟢 **CREATE** - Writing new memory
- 🟡 **UPDATE** - Modifying existing memory
- 🔷 **QUERY** - Vector search query
- 🔴 **DELETE** - Removing memory

### Memory Types

- **episodic** - Historical cases (blue)
- **semantic** - Regulations (magenta)
- **procedural** - SOP rules (cyan)
- **working** - Current state (white)

### Influence Scores

```
Influence: ██████████████████░░ 0.88
           ^^^^^^^^^^^^^^^^^^    ^^^^
           Visual bar            Score
```

Higher scores = more influence on the decision

---

## What's Happening Behind the Scenes

1. **Supervisor Agent** coordinates the workflow
2. **Fraud Detection Agent** analyzes transaction patterns
3. **Case History Agent** searches similar past cases
4. **Compliance Research Agent** queries regulations
5. **Report Generation Agent** synthesizes everything
6. **MemGuard SDK** tracks all 11 memory operations
7. **Decision Trace** links memories to decisions

---

## Troubleshooting

### "No module named 'memguard'"

```bash
# Make sure you're in the right directory
cd /Users/chakeswu/cursor/MemguardV1

# Install SDK
pip install -e sdk/
```

### "No module named 'rich'"

```bash
pip install rich
```

### "Connection refused" warnings

That's okay! The demo works without the backend. The warnings just mean:
- ⚠️ Qwen not running on port 8080 (uses heuristic mode)
- ⚠️ Backend not running on port 8000 (terminal-only output)

---

## Next Steps

### Explore the Code

- `demo.py` - Main demo script (312 lines)
- `fincompli-baseline/memguard_wrappers.py` - Memory instrumentation
- `sdk/memguard/core/influence.py` - Influence calculation
- `backend/app/reasoning_extractor.py` - Decision reasoning

### Read the Docs

- `DEMO_ARCHITECTURE.md` - System design
- `IMPLEMENTATION_SUMMARY.md` - What we built
- `LAYER1_IMPLEMENTATION.md` - Terminal demo guide
- `LAYER2_IMPLEMENTATION.md` - Decision trace guide

### Try the API

If backend is running:

```bash
# Get statistics
curl http://localhost:8000/v1/db/stats

# List memory events
curl http://localhost:8000/v1/events?limit=10

# Get decision trace detail
curl http://localhost:8000/v1/decision-traces/{trace_id}
```

### Modify the Demo

Edit `demo.py` to:
- Change the scenario
- Add more agents
- Customize the output
- Connect to real Qwen

---

## Performance

**Expected Runtime:**
- Initialization: ~1s
- Scenario execution: ~5.7s
- Display rendering: ~0.5s
- **Total: ~7s**

**Memory Overhead:**
- <5ms per memory operation
- Fire-and-forget event emission
- No blocking on backend

---

## Demo for Different Audiences

### For Investors / Product People

Focus on:
- Business scenario (money laundering detection)
- The "why" explanation (88% similarity to past case)
- Decision confidence (92%)
- Compliance value

### For Engineers / Technical People

Focus on:
- 11 memory operations tracked
- 5 memory types instrumented
- Influence score algorithm
- <5ms overhead
- Decision trace API

### For Compliance Officers

Focus on:
- SAR filing recommendation
- Regulatory violations (HKMA §35)
- Historical case matching
- Audit trail completeness

---

## FAQ

**Q: Do I need Qwen running?**  
A: No, the demo works without it. It'll use simulated data.

**Q: Do I need the MemGuard backend?**  
A: No, you'll just get terminal output instead of database storage.

**Q: Can I use a different LLM?**  
A: Yes! Edit the demo to use OpenAI, Claude, or any other LLM.

**Q: How long does it take?**  
A: ~7 seconds for the complete demo.

**Q: Can I customize the scenario?**  
A: Yes! Edit `demo.py` or check `fincompli-baseline/scenarios/`.

**Q: Is this production-ready?**  
A: Layers 1 & 2 are solid. Layer 3 (dashboard) is coming next.

---

## Get Help

**Documentation:**
- Architecture: `DEMO_ARCHITECTURE.md`
- Implementation: `IMPLEMENTATION_PROGRESS.md`
- Summary: `IMPLEMENTATION_SUMMARY.md`

**Code:**
- Demo: `demo.py`
- Wrappers: `fincompli-baseline/memguard_wrappers.py`
- SDK: `sdk/memguard/`
- Backend: `backend/app/`

---

## What's Next?

After running the demo:

1. ✅ **Explore the output** - Understand each memory operation
2. ✅ **Read the decision trace** - See how memories influence decisions
3. ✅ **Check the API** - Try the backend endpoints
4. ⏳ **Wait for Layer 3** - Beautiful dashboard coming soon!

---

**Enjoy the demo! 🎉**

Questions? Check the documentation files in the project root.
