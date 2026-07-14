# AGENTS.md — DJI Drone Map UI

## Project

Cesium + React + TypeScript + Vite app for viewing DJI drone flight paths and crop/disease
heatmaps on a 3-D globe. The scaffold is already in place. You are extending it.

**Folder layout that matters:**

```
src/
  App.tsx
  App.css
  index.css
  componets/        ← existing components live here (note: typo in folder name, fix it)
  types/
  helpers/
  form_schema/
  data/
  external_services/
```

---

## Step 0 — Audit First, Code Second (mandatory)

Before writing a single line of code:

1. Read every file in `src/` recursively.
2. From `App.css` and `index.css` extract: all colour values, font families, spacing
   values, border radii, box shadows, z-index values, transition durations.
3. From `src/componets/` extract: button class patterns, panel/header patterns, icon usage,
   any existing modal structure.
4. Write all findings into a new file called `Style.md` at the project root.
5. **Do not proceed to any other step until `Style.md` exists.**

`Style.md` is the single source of truth for all UI decisions in every subsequent step.
If you need a new value not already in `Style.md`, add it there first, then use it.


## Step 0.5 — Split App.tsx Before Touching Anything Else

`App.tsx` currently contains most of the application logic. Before writing any new code,
refactor it by extracting each concern into the folder it belongs in. Do not change any
logic during this step — only move code.

**Rules for this step:**
- Extract, do not rewrite. Every function, type, and component must behave identically
  after the move.
- Update all import paths after moving.
- `App.tsx` should end up as a thin orchestration shell: it holds `activeModal` state,
  renders the Cesium viewer, renders the toolbar, and renders the three modals. Nothing
  else.
- Run `npx tsc --noEmit` after this step before moving on.

**Where things go:**

| What to extract | Destination |
|---|---|
| TypeScript interfaces and types | `src/types/index.ts` |
| Zod schemas / form schemas | `src/form_schema/` — one file per form |
| Fetch calls, API wrappers, backend helpers | `src/external_services/` — one file per endpoint group |
| Pure utility functions (date formatting, coordinate parsing, etc.) | `src/helpers/` — one file per concern |
| Cesium entity / polyline / heatmap logic | `src/helpers/cesium.ts` |
| Static mock or seed data | `src/data/` |
| Every UI component (panels, buttons, toolbar, modals) | `src/componets/` — one file per component |

**Specific extractions Codex must perform:**

1. Every `interface` and `type` declaration → `src/types/index.ts`. Export them all.

2. Every `fetch` / `axios` / HTTP call → named async function in `src/external_services/`.
   Name the file after the resource (e.g. `flights.ts`, `heatmaps.ts`). Export each function.

3. Every Zod schema or form validation object → `src/form_schema/`, one file per form,
   named after what it validates.

4. Every pure helper function (takes inputs, returns a value, no React state or DOM side
   effects) → `src/helpers/`, grouped by concern.

5. Every Cesium-specific function (adding entities, drawing polylines, heatmap materials)
   → `src/helpers/cesium.ts`.

6. Every self-contained JSX block (toolbar, panels, existing modal markup) → its own
   `.tsx` file in `src/componets/` with typed props.

7. After all extractions, `App.tsx` must contain only:
   - Imports
   - `activeModal` state and top-level UI state
   - The Cesium `<Viewer>` root element
   - The toolbar component
   - The three modal components (placeholders if not yet built)
   - The keyboard shortcut `useEffect` (placeholder if not yet built)

---

## Step 1 — Shared Modal Shell

Create `src/componets/Modal.tsx`. Every modal in this project uses this component — do not
build modal chrome anywhere else.

**Required behaviour:**

- Uses `ReactDOM.createPortal` to render into a `<div id="modal-root">` appended to
  `document.body`. Add `<div id="modal-root"></div>` to `index.html` if it is not already
  there.
- Renders a fixed full-screen overlay: `position: fixed; inset: 0; z-index: 1000`.
- Backdrop: `rgba(0, 0, 0, 0.55)`. Clicking the backdrop calls `onClose`.
- Panel is centred on the overlay: `display: flex; align-items: center; justify-content: center`.
- Open → fade + scale-up CSS transition on the panel (no animation libraries).
- Close → reverse transition, then unmount after transition completes (`onTransitionEnd`).
- Close button: Feather `X` icon, anchored to the **left edge** of the modal header bar.

**Props interface:**

```ts
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}
```

---

## Step 2 — Upload Modal (exists → refactor)

File: `src/componets/UploadModal.tsx` (or whatever it is currently named — find it).

- Wrap it in `<Modal>` from Step 1.
- Keep all existing form logic and field names exactly as they are.
- No other changes.

---

## Step 3 — Flight Viewer Modal (exists → refactor)

File: find the existing flight viewer component in `src/componets/`.

- Wrap it in `<Modal>` from Step 1.
- **Replace the body entirely** with a drone image carousel:
  - Prop: `shots: string[]` — array of image URLs supplied by the parent.
  - Full-width image display, one image at a time.
  - Prev / Next buttons on left and right edges of the image.
  - Dot row indicator below the image showing current position.
  - Caption (filename or index) below the dots.
  - Keyboard: `←` previous, `→` next. Register on `window` while this modal is open,
    remove on close.
- This modal no longer displays flight data tables or stats — only the image carousel.

---

## Step 4 — Flight Picker Modal (does not exist → create)

Create `src/componets/FlightPickerModal.tsx`.

**Purpose:** lets the user browse and load previously uploaded flights.

**Trigger — two ways:**
1. A button in the existing toolbar/header. Label: "Flights". Icon: Feather `List`.
   Match the style of every other existing toolbar button exactly (check `Style.md`).
2. Keyboard shortcut `Ctrl + K` — register in `App.tsx` (see Step 6).

**Body:**

- Fetches flight list from the backend on open (use whatever fetch helper already exists
  in `src/external_services/` or `src/helpers/`).
- Renders a scrollable list. Each row:
  - Flight name
  - Date
  - Duration
  - A "Load" button (right-aligned)
- Clicking "Load" closes this modal and calls a prop `onLoad(flightId: string)` so the
  parent can plot the flight on the globe.

**Style:** must match Upload Modal and Flight Viewer Modal exactly — same header bar height,
same border radius, same shadow, same close button position. Use `Style.md` values.

---

## Step 5 — Flight Path Colours on the Globe

In whatever file currently draws polylines on the Cesium viewer, apply this colour array:

```ts
export const FLIGHT_PATH_COLORS = [
  '#00E5FF', // cyan
  '#FF6D00', // amber
  '#76FF03', // lime
  '#EA80FC', // lavender
  '#FF1744', // red
  '#FFD740', // gold
  '#40C4FF', // sky blue
  '#69F0AE', // mint
];
```

Rules:
- Assign colours by index, wrapping around if there are more flights than colours.
- Each polyline: `width: 3`.
- Under each polyline, add a glow layer: same path, `width: 6`,
  `material: Color.WHITE.withAlpha(0.15)`.
- Active / selected flight: full opacity. All others: `opacity: 0.45`.

---

## Step 6 — Keyboard Shortcuts in App.tsx

Add a single `useEffect` in `App.tsx` that registers all global shortcuts:

| Key | Action |
|---|---|
| `Ctrl + K` | Toggle Flight Picker Modal |
| `Escape` | Close whichever modal is currently open |

Clean up with `removeEventListener` in the `useEffect` return.

---

## Step 7 — QA

Run before finishing:

```bash
npx tsc --noEmit        # zero type errors required
```

Also verify manually:
- No unused imports.
- No `console.log` left in production paths.
- No hardcoded colour hex values outside `Style.md` and `FLIGHT_PATH_COLORS`.
- All three modals dim the background, centre on screen, and animate open/close.
- `Ctrl + K` opens Flight Picker. `Escape` closes any open modal.

---

## Hard Rules

- **React Portals are required** for every modal. All three modals must render via
  `ReactDOM.createPortal` into `#modal-root`. Any modal not using a portal is wrong.
- **Only one modal open at a time.** `App.tsx` owns a single `activeModal` state:
  ```ts
  type ModalName = 'upload' | 'viewer' | 'picker' | null;
  const [activeModal, setActiveModal] = useState<ModalName>(null);
  ```
  Opening any modal sets `activeModal` to its name. The `<Modal>` component receives
  `isOpen={activeModal === 'upload'}` etc. Opening one modal automatically closes any
  other because only one name can be active at a time.
- **No new npm dependencies** unless strictly necessary — if you add one, leave a comment
  explaining why no existing tool could do the job.
- **No inline styles** for values that belong in CSS classes or variables.
- **No placeholder comments** (`// TODO`, `// fix later`) — implement it or leave it out.
- **The `componets` folder typo is intentional** — do not rename it.
- Every value you introduce into the UI must first exist in `Style.md`.


After you are done with that check `Notes.md`
