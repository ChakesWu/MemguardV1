# MemGuard Output-First Dashboard Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the table-first dashboard with the approved Keycloak-inspired output-first evidence investigation workspace without changing backend or authentication contracts.

**Architecture:** Keep data fetching, OIDC, polling, audit, conflicts, and event details in `frontend/app/page.tsx`. Extract the output navigator and inline trace investigation into focused React components that consume API-backed trace records, with shared types and display helpers in `frontend/lib/dashboard.ts`. Apply one token-based visual system from `frontend/app/globals.css` across the shell and existing overlays.

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS 3, Python `unittest` contract checks, Docker Compose browser verification.

## Global Constraints

- `frontend/` remains the canonical product UI.
- Every displayed output, evidence item, memory write, timestamp, hash, and ranking must come from the existing API response.
- Evidence lineage must be labeled as recorded context, not proof of model causality.
- No backend, database, OIDC, tenant-isolation, or API-contract changes.
- No new search endpoints, agent-first navigation, memory-first navigation, framework adapters, or Phase 3 infrastructure.
- Preserve unrelated `.DS_Store`, virtual-environment, and `tmp/` worktree changes.

---

### Task 1: Lock the output-first frontend contract

**Files:**
- Modify: `tests/test_frontend_oidc.py`
- Modify: `tests/test_phase1a_contract.py`

**Interfaces:**
- Consumes: source files under `frontend/`.
- Produces: regression checks for `OutputNavigator`, `EvidenceWorkspace`, `selectedTraceId`, the causality disclaimer, API-backed evidence fields, and removal of the old modal-first trace presentation.

- [ ] **Step 1: Add failing contract tests**

Add assertions equivalent to:

```python
components = project_root / "frontend" / "components"
page = (project_root / "frontend" / "app" / "page.tsx").read_text()
navigator = (components / "OutputNavigator.tsx").read_text()
workspace = (components / "EvidenceWorkspace.tsx").read_text()

self.assertIn("selectedTraceId", page)
self.assertIn("<OutputNavigator", page)
self.assertIn("<EvidenceWorkspace", page)
self.assertIn("evidence_items", workspace)
self.assertIn("missing_evidence_event_ids", workspace)
self.assertIn("not proof of model causality", workspace.lower())
self.assertNotIn("mock", navigator.lower())
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -m unittest tests.test_frontend_oidc tests.test_phase1a_contract -v`

Expected: FAIL because `OutputNavigator.tsx`, `EvidenceWorkspace.tsx`, and the output-first selection state do not exist.

- [ ] **Step 3: Commit the failing contract**

Run:

```bash
git add tests/test_frontend_oidc.py tests/test_phase1a_contract.py
git commit -m "test: define output-first dashboard contract"
```

### Task 2: Build shared trace presentation units

**Files:**
- Create: `frontend/lib/dashboard.ts`
- Create: `frontend/components/OutputNavigator.tsx`
- Create: `frontend/components/EvidenceWorkspace.tsx`
- Modify: `frontend/app/globals.css`
- Test: `tests/test_frontend_oidc.py`
- Test: `tests/test_phase1a_contract.py`

**Interfaces:**
- Produces: `DecisionTrace`, `EvidenceItem`, `MemoryEvent`, and `Stats` interfaces; `inputEvidence(trace)`, `outputEvidence(trace)`, and `evidenceContextLabel(item)` helpers.
- Produces: `OutputNavigator({ traces, selectedTraceId, onSelect, agentFilter, agentList, onAgentFilterChange })`.
- Produces: `EvidenceWorkspace({ trace })` rendering selected output, input evidence, missing evidence warning, recorded evidence ranking, and resulting writes.
- Consumes: real `DecisionTrace[]` returned by the current trace API.

- [ ] **Step 1: Add shared API-backed types and evidence helpers**

Move the existing trace, evidence, event, and stats interfaces into `frontend/lib/dashboard.ts`. Implement input/output selection using `evidence_items` first and the existing detail arrays only as an API compatibility fallback:

```ts
export function inputEvidence(trace: DecisionTrace): EvidenceItem[] {
  return trace.evidence_items?.filter(item => item.side === 'input')
    || trace.input_memory_details
    || []
}

export function outputEvidence(trace: DecisionTrace): EvidenceItem[] {
  return trace.evidence_items?.filter(item => item.side === 'output')
    || trace.output_memory_details
    || []
}
```

- [ ] **Step 2: Implement the output navigator**

Render one selectable row per real trace with agent, time, output preview, linked evidence count, write count, and ranking. Use a native button with `aria-pressed={trace.trace_id === selectedTraceId}` and call `onSelect(trace.trace_id)`.

- [ ] **Step 3: Implement the inline evidence workspace**

Render the approved three-stage layout from real fields. Include this permanent copy:

```tsx
Recorded evidence lineage shows what memory and retrieved context were available at generation time. It is not proof of model causality.
```

When `trace` is null, render the existing authenticated demo command and do not fabricate sample evidence.

- [ ] **Step 4: Add the Keycloak-inspired visual tokens and component classes**

Define semantic tokens in `globals.css`:

```css
:root {
  --mg-bg: #101010;
  --mg-surface: #151515;
  --mg-surface-raised: #1a1a1a;
  --mg-border: #2d2d2d;
  --mg-text: #f3f3f0;
  --mg-muted: #999993;
  --mg-blue: #4f8cff;
  --mg-success: #65c489;
  --mg-warning: #e1b36b;
}
```

Add responsive shell, navigator, lineage-stage, table, overlay, loading, and empty-state classes without global element rules that break Keycloak or browser controls.

- [ ] **Step 5: Run focused tests and the TypeScript production build**

Run:

```bash
python -m unittest tests.test_frontend_oidc tests.test_phase1a_contract -v
cd frontend && npm run build
```

Expected: tests may still fail only on page integration; the new components compile independently through the Next.js build once imported in Task 3.

- [ ] **Step 6: Commit the presentation units**

Run:

```bash
git add frontend/lib/dashboard.ts frontend/components/OutputNavigator.tsx frontend/components/EvidenceWorkspace.tsx frontend/app/globals.css
git commit -m "feat: add output-first evidence workspace"
```

### Task 3: Integrate the full dashboard redesign

**Files:**
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/components/AuditReport.tsx`
- Modify: `frontend/components/ConflictWarning.tsx`
- Modify: `frontend/components/MemoryDiffViewer.tsx`
- Test: `tests/test_frontend_oidc.py`
- Test: `tests/test_phase1a_contract.py`

**Interfaces:**
- Consumes: `DecisionTrace`, `MemoryEvent`, and `Stats` from `frontend/lib/dashboard.ts`.
- Consumes: `OutputNavigator` and `EvidenceWorkspace` props defined in Task 2.
- Produces: `selectedTraceId: string | null` and derived `selectedTrace` in the canonical page.

- [ ] **Step 1: Replace modal-first trace selection with persistent output selection**

Add state and derivation:

```ts
const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null)
const selectedTrace = traces.find(trace => trace.trace_id === selectedTraceId) || traces[0] || null
```

After each trace fetch, preserve the selected ID when it remains present and otherwise select the first trace ID. Do not place `selectedTraceId` in the polling effect dependency list.

- [ ] **Step 2: Replace the page shell**

Render the approved application header, `OutputNavigator` left rail, and `EvidenceWorkspace` main area. Keep Audit Report, Refresh, Sign Out, conflicts, database status, and agent filtering connected to their existing handlers and API data.

- [ ] **Step 3: Keep the event table as secondary evidence detail**

Move the existing event filters and table below the main trace workspace. Preserve the event click handler and the `MemoryDiffViewer` detail overlay.

- [ ] **Step 4: Restyle existing overlays**

Apply the shared flat dark surfaces, thin borders, typography, and semantic status colors to event detail, audit, conflict, and memory diff views. Do not change their data or actions.

- [ ] **Step 5: Run focused contract tests and verify GREEN**

Run: `python -m unittest tests.test_frontend_oidc tests.test_phase1a_contract -v`

Expected: PASS, including OIDC authorization, array trace response compatibility, database-driver display, output-first components, and truthfulness constraints.

- [ ] **Step 6: Run the frontend build**

Run: `cd frontend && npm run build`

Expected: Next.js production build completes with exit code 0 and no TypeScript errors.

- [ ] **Step 7: Commit the integrated redesign**

Run:

```bash
git add frontend/app/page.tsx frontend/components/AuditReport.tsx frontend/components/ConflictWarning.tsx frontend/components/MemoryDiffViewer.tsx tests/test_frontend_oidc.py tests/test_phase1a_contract.py
git commit -m "feat: redesign dashboard around agent outputs"
```

### Task 4: Full verification and browser acceptance

**Files:**
- Modify only if verification exposes an in-scope defect.

**Interfaces:**
- Consumes: the complete redesigned frontend and existing Docker Compose services.
- Produces: verified desktop and narrow-width behavior with real authenticated data.

- [ ] **Step 1: Run repository tests**

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 2: Rebuild and start the Compose frontend**

Run: `docker compose up -d --build frontend`

Expected: frontend, backend, PostgreSQL, and Keycloak are healthy; `http://localhost:3001` responds.

- [ ] **Step 3: Verify the authenticated desktop workflow**

Sign in with the existing local demo account, select two different API-backed outputs, and confirm output text, evidence items, resulting writes, trace metadata, refresh, audit, conflict, and sign-out controls render and behave correctly.

- [ ] **Step 4: Verify responsive behavior**

At a narrow viewport, confirm the output navigator stacks above the evidence workspace, lineage stages remain evidence-to-output-to-write, controls wrap, and the event table scrolls without clipping content.

- [ ] **Step 5: Inspect browser errors**

Confirm there are no new console errors, React key warnings, failed authenticated API requests, or visible hard-coded sample values.

- [ ] **Step 6: Commit any verification fixes**

If changes were necessary, stage only those files and run:

```bash
git commit -m "fix: polish output-first dashboard verification"
```
