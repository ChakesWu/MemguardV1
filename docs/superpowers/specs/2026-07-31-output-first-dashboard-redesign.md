# MemGuard Output-First Dashboard Redesign

## Goal

Redesign the canonical `frontend/` dashboard to match the visual language of the Keycloak login page while making the primary workflow output-first: select an agent output, then inspect the persisted evidence available at generation time and the memory writes that followed.

The redesign changes presentation and navigation only. It does not change backend contracts, persistence, authentication, tenant isolation, or the meaning of evidence.

## Approved direction

The approved visual direction is a full dashboard redesign with:

- a near-black background and restrained off-white typography;
- uppercase labels and wide letter spacing inspired by the Keycloak login page;
- thin neutral borders and flat surfaces instead of colorful rounded cards;
- blue reserved for selection, links, and focused evidence states;
- green and amber used only for meaningful integrity or conflict status;
- a desktop investigation workspace with responsive single-column behavior.

## Information architecture

### Application header

The header contains the `MEMGUARD` wordmark, an `EVIDENCE CONSOLE` product label, backend connection status, Audit Report, Refresh, and Sign Out actions. Existing actions retain their current behavior.

### Output navigation

The left rail lists decision traces as agent outputs. Each row shows:

- agent ID and generation time;
- a concise output preview;
- linked evidence count;
- resulting write count;
- recorded evidence ranking.

Selecting a row makes that trace the active investigation. The first available trace becomes active after data loads. Refreshes preserve the active trace when its ID still exists; otherwise, the first available trace becomes active.

The first version includes an agent selector using existing data. Search and new backend filters are outside this visual redesign because the current API does not expose a dedicated output search contract.

### Investigation workspace

The main area answers `Why did it output this?` for the active trace. It contains:

1. Trace, agent, session, and generation metadata.
2. A permanent truthfulness notice explaining that recorded lineage is not model-causal attribution.
3. The selected agent output.
4. A three-stage evidence lineage:
   - evidence available at generation time;
   - the selected agent output and recorded evidence ranking;
   - resulting memory writes.
5. Missing evidence warnings when linked event records are unavailable.
6. Related memory events and integrity information already present in the API response.

The evidence lineage is rendered inline as the primary page content. It replaces the current workflow where traces appear below the event table and open in a modal.

### Secondary memory-event view

The existing memory-event table remains available below the primary investigation area. Operation and agent filters continue to work. Clicking an event continues to open its detailed state and diff view.

Conflict and audit overlays remain functional and receive the same visual system.

## Component behavior

### Data loading

Authentication and API requests remain unchanged. The page continues polling at the current interval. Trace selection is derived from the real trace API response and never from hard-coded sample content.

### Empty state

When no traces exist, the main workspace explains that no outputs have been recorded and shows the existing generic demo command. Events may still be viewed when present.

### Loading and authentication failure

Loading and authentication failure states use the same Keycloak-inspired shell and typography. They remain explicit and do not show stale or fabricated evidence.

### Responsive behavior

At narrower widths, the output rail becomes a compact section above the investigation workspace. The lineage stages stack vertically in evidence-to-output-to-write order. Tables retain bounded horizontal scrolling where columns cannot fit.

## Styling implementation

Shared visual tokens will be defined in `frontend/app/globals.css` for background, surfaces, borders, text, muted text, selection blue, success green, and warning amber. The canonical page and existing overlays will use semantic CSS classes backed by those tokens.

Emoji-based decoration will be removed from the primary application chrome and replaced by clear text labels. Operation and memory-type meaning will still be conveyed by text and restrained status color, so the UI does not depend on color alone.

## Truthfulness constraints

- Every output, evidence item, write, event, hash, timestamp, and ranking displayed in the production path must originate from the existing API response.
- The UI must continue to state that evidence lineage is not proof of model causality.
- Missing persisted evidence must remain visible and must never be replaced by inferred content.
- No mock decision data will be added to the production frontend.

## Testing and verification

Automated tests will verify:

- the production dashboard remains output-first;
- the active trace is selected from API data;
- the truthfulness notice remains present;
- evidence and resulting writes render from trace fields;
- no hard-coded mock decision content is introduced;
- existing authentication, tenant, trace, audit, and event contracts remain intact.

Verification will include the frontend production build, the relevant Python contract tests, the complete test suite when practical, and browser inspection at desktop and narrow responsive widths against a running Docker Compose stack.

## Out of scope

- backend or database schema changes;
- new search endpoints;
- agent-first or memory-first navigation;
- new framework adapters;
- RBAC, multi-region, AWS, or Phase 3 infrastructure;
- claims of model-internal causal attribution.
