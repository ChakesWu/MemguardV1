# MemGuard Frontend Dashboard - Startup Guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

This installs:
- Next.js 15
- React 19
- Tailwind CSS 3
- TypeScript 5

### 2. Start Development Server

```bash
npm run dev
```

Dashboard runs at: **http://localhost:3000**

### 3. Ensure Backend is Running

Frontend needs to connect to Backend API:

```bash
# In another terminal
cd backend
python3 -m uvicorn app.main:app --port 8000 --reload
```

Backend API: **http://localhost:8000**

---

## 📊 Dashboard Features

### Implemented ✅

1. **Stats Cards**
   - Total Events
   - CREATE Operations
   - READ Operations
   - Decision Traces

2. **Events Table**
   - Timestamp
   - Operation Type (color-coded)
   - Agent ID
   - Memory Key
   - Content Hash
   - Clickable for details

3. **Operation Filter**
   - All Events
   - Filter by operation type (CREATE/READ/UPDATE/DELETE/QUERY)

4. **Event Detail Modal**
   - Full Event Information
   - Before/After Value Comparison
   - Context Metadata
   - JSON Formatted Display

5. **Auto Refresh**
   - Auto-updates every 5 seconds
   - Manual refresh button

6. **Connection Status**
   - Backend connection status indicator
   - Database path display

---

## 🎨 Design Features

- **Dark Theme**: Comfortable for extended viewing
- **Responsive Layout**: Supports various screen sizes
- **Color Coding**:
  - 🟢 CREATE (Green)
  - 🔵 READ (Blue)
  - 🟡 UPDATE (Yellow)
  - 🔴 DELETE (Red)
  - 🔷 QUERY (Cyan)
  - 🟣 SEARCH (Purple)

---

## 🔧 Tech Stack

| Technology | Version | Purpose |
|------|------|------|
| Next.js | 15.1.6 | React Framework |
| React | 19.0.0 | UI Library |
| Tailwind CSS | 3.4.17 | Styling |
| TypeScript | 5.x | Type Safety |

---

## 📁 File Structure

```
frontend/
├── app/
│   ├── page.tsx          ← Main Dashboard Page
│   ├── layout.tsx        ← Root layout
│   └── globals.css       ← Global Styles (Tailwind)
├── components/           ← React Components (future)
├── lib/                  ← Utility Functions (future)
├── public/               ← Static Assets
├── tailwind.config.js    ← Tailwind Config
├── postcss.config.js     ← PostCSS Config
├── next.config.js        ← Next.js Config
├── tsconfig.json         ← TypeScript Config
└── package.json          ← Dependency Config
```

---

## 🐛 Troubleshooting

### Issue 1: `npm install` fails

```bash
# Clear cache and retry
rm -rf node_modules package-lock.json
npm install
```

### Issue 2: Tailwind styles not working

```bash
# Restart dev server
npm run dev
```

### Issue 3: Cannot connect to Backend

```bash
# Check if Backend is running
curl http://localhost:8000/health

# If not running, start it
cd backend
python3 -m uvicorn app.main:app --port 8000 --reload
```

### Issue 4: CORS Errors

Backend has CORS configured, but if issues persist:

```python
# backend/app/main.py already has this config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in dev
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚧 Next Steps

### Short-term (This Week)

- [ ] Fetch real event data from Backend
- [ ] Add Session Selector
- [ ] Implement Event Search
- [ ] Add Time Range Filter

### Mid-term (Next Week)

- [ ] Timeline Visualization (D3.js)
- [ ] Memory Diff Comparison View
- [ ] Real-time WebSocket Updates
- [ ] Export Feature (JSON/CSV)

### Long-term (Future)

- [ ] Memory Flow Diagram (React Flow)
- [ ] Anomaly Detection Visualization
- [ ] Decision Trace Detail Page
- [ ] Multi-language Support (EN/ZH)

---

## 💡 Usage Tips

1. **Generate Test Data**: Run demo agent first to generate events
   ```bash
   python3 examples/demo_agent.py --mode auto
   ```

2. **Live Monitoring**: Open two browser windows
   - Window 1: Dashboard (http://localhost:3000)
   - Window 2: Backend API Docs (http://localhost:8000/docs)

3. **Debugging**: Use browser dev tools to inspect network requests

---

## 📞 Need Help?

- **Backend API Docs**: http://localhost:8000/docs
- **Project Docs**: `Documents/START_HERE.md`
- **Development Plan**: `Documents/plans/MEMGUARD_STANDALONE_PLAN.md`

---

**Version**: 0.1.0  
**Status**: ✅ Basic features complete, ready to use  
**Last Updated**: 2026-07-01
