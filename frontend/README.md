# MemGuard Frontend Dashboard - 启动指南

## 🚀 快速启动

### 1. 安装依赖

```bash
cd frontend
npm install
```

这会安装：
- Next.js 15
- React 19
- Tailwind CSS 3
- TypeScript 5

### 2. 启动开发服务器

```bash
npm run dev
```

Dashboard 运行在: **http://localhost:3000**

### 3. 确保 Backend 运行中

Frontend 需要连接 Backend API：

```bash
# 在另一个终端
cd backend
python3 -m uvicorn app.main:app --port 8000 --reload
```

Backend API: **http://localhost:8000**

---

## 📊 Dashboard 功能

### 已实现 ✅

1. **统计卡片**
   - 总事件数
   - CREATE 操作数
   - READ 操作数
   - 决策追踪数

2. **事件列表表格**
   - 时间戳
   - 操作类型 (颜色标记)
   - Agent ID
   - Memory Key
   - Content Hash
   - 可点击查看详情

3. **操作过滤器**
   - 全部事件
   - 按操作类型过滤 (CREATE/READ/UPDATE/DELETE/QUERY)

4. **事件详情 Modal**
   - 完整事件信息
   - Before/After 值对比
   - Context 元数据
   - JSON 格式化显示

5. **自动刷新**
   - 每 5 秒自动更新数据
   - 手动刷新按钮

6. **连接状态**
   - Backend 连接状态指示
   - 数据库路径显示

---

## 🎨 设计特点

- **深色主题**: 适合长时间查看
- **响应式布局**: 支持各种屏幕尺寸
- **颜色编码**:
  - 🟢 CREATE (绿色)
  - 🔵 READ (蓝色)
  - 🟡 UPDATE (黄色)
  - 🔴 DELETE (红色)
  - 🔷 QUERY (青色)
  - 🟣 SEARCH (紫色)

---

## 🔧 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 15.1.6 | React 框架 |
| React | 19.0.0 | UI 库 |
| Tailwind CSS | 3.4.17 | 样式 |
| TypeScript | 5.x | 类型安全 |

---

## 📁 文件结构

```
frontend/
├── app/
│   ├── page.tsx          ← 主 Dashboard 页面
│   ├── layout.tsx        ← Root layout
│   └── globals.css       ← 全局样式 (Tailwind)
├── components/           ← React 组件 (未来)
├── lib/                  ← 工具函数 (未来)
├── public/               ← 静态资源
├── tailwind.config.js    ← Tailwind 配置
├── postcss.config.js     ← PostCSS 配置
├── next.config.js        ← Next.js 配置
├── tsconfig.json         ← TypeScript 配置
└── package.json          ← 依赖配置
```

---

## 🐛 故障排除

### 问题 1: `npm install` 失败

```bash
# 清除缓存重试
rm -rf node_modules package-lock.json
npm install
```

### 问题 2: Tailwind 样式不生效

```bash
# 重启开发服务器
npm run dev
```

### 问题 3: 无法连接 Backend

```bash
# 检查 Backend 是否运行
curl http://localhost:8000/health

# 如果没有运行，启动它
cd backend
python3 -m uvicorn app.main:app --port 8000 --reload
```

### 问题 4: CORS 错误

Backend 已经配置了 CORS，但如果仍有问题：

```python
# backend/app/main.py 已经有这个配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚧 下一步开发

### 短期 (本周)

- [ ] 从 Backend 获取真实事件数据
- [ ] 添加 Session 选择器
- [ ] 实现事件搜索功能
- [ ] 添加时间范围过滤

### 中期 (下周)

- [ ] Timeline 时间线可视化 (D3.js)
- [ ] Memory Diff 对比视图
- [ ] Real-time WebSocket 更新
- [ ] Export 功能 (JSON/CSV)

### 长期 (未来)

- [ ] Memory Flow 流程图 (React Flow)
- [ ] Anomaly 异常检测可视化
- [ ] Decision Trace 决策追踪详情页
- [ ] 多语言支持 (中/英)

---

## 💡 使用建议

1. **生成测试数据**: 先运行 demo agent 生成事件
   ```bash
   python3 examples/demo_agent.py --mode auto
   ```

2. **实时监控**: 开两个浏览器窗口
   - 窗口1: Dashboard (http://localhost:3000)
   - 窗口2: Backend API Docs (http://localhost:8000/docs)

3. **调试**: 使用浏览器开发者工具查看网络请求

---

## 📞 需要帮助?

- **Backend API 文档**: http://localhost:8000/docs
- **项目文档**: `Documents/START_HERE.md`
- **开发计划**: `Documents/plans/MEMGUARD_STANDALONE_PLAN.md`

---

**版本**: 0.1.0  
**状态**: ✅ 基础功能完成，可以使用  
**最后更新**: 2026-07-01
