# Style.md

Canonical style ledger for the DJI Drone Map UI. Use this file as the source of truth for all UI
work unless a later task explicitly adds a new token here first.

## Audit Scope

Reviewed all files under `src/`:

- `src/App.tsx`
- `src/App.css`
- `src/index.css`
- `src/main.tsx`
- `src/componets/modal.tsx`
- `src/componets/telementryElement.tsx`
- `src/data/demo.ts`
- `src/data/telementary.ts`
- `src/external_services/api.ts`
- `src/form_schema/upload_schema.ts`
- `src/helpers/helper_functions.ts`
- `src/types/api.d.ts`
- `src/types/flightpoint.d.ts`
- `src/types/modal.d.ts`
- `src/types/telementry.d.ts`
- `src/assets/hero.png`
- `src/assets/react.svg`
- `src/assets/vite.svg`

## Design Direction

- Dark, full-screen Cesium map shell with floating glass panels.
- Cyan is the primary accent; surfaces are dark blue-gray with soft transparency.
- Typography is compact and utilitarian, with monospace used for numeric readouts.
- Feather icons are the current icon set.

## Typography

### Font Families

- Sans: `"Roboto"`, `"Segoe UI"`, `sans-serif`
- Mono: `"JetBrains Mono"`, `"SFMono-Regular"`, `Consolas`, `monospace`

### Font Source Imports

- `@fontsource/roboto/400.css`
- `@fontsource/roboto/500.css`
- `@fontsource/roboto/700.css`
- `@fontsource/jetbrains-mono/400.css`
- `@fontsource/jetbrains-mono/500.css`
- `@fontsource/jetbrains-mono/700.css`

### Global Typography Rules

- `body` uses the sans font family.
- `button`, `input`, `select`, and `textarea` inherit the current font.
- Numeric readouts use the mono font stack via `.numeric` and `.results-code`.
- All counts, durations, timestamps, file sizes, and other numeric UI values should be rendered in the mono stack.

## Colors

### Base and Text

- `#000`
- `#ffffff`
- `#f8fafc`
- `#e2e8f0`
- `#cbd5e1`
- `#e0f2fe`
- `#bbf7d0`
- `#fca5a5`

### Accent and Highlight

- `#38bdf8`
- `#7dd3fc`
- `rgba(125, 211, 252, 0.92)`
- `rgba(125, 211, 252, 0.28)`
- `rgba(125, 211, 252, 0.20)`
- `rgba(56, 189, 248, 0.85)`
- `rgba(56, 189, 248, 0.48)`
- `rgba(56, 189, 248, 0.34)`
- `rgba(14, 165, 233, 0.10)`

### Dark Surface Tones

- `rgba(8, 12, 20, 0.76)`
- `rgba(11, 18, 28, 0.86)`
- `rgba(6, 10, 18, 0.50)`
- `rgba(6, 10, 18, 0.00)`
- `rgba(2, 6, 23, 0.90)`
- `rgba(2, 6, 23, 0.48)`
- `rgba(15, 23, 42, 0.92)`
- `rgba(15, 23, 42, 0.72)`
- `rgba(15, 23, 42, 0.66)`
- `rgba(15, 23, 42, 0.56)`
- `rgba(15, 23, 42, 0.54)`
- `rgba(15, 23, 42, 0.44)`
- `rgba(15, 23, 42, 0.40)`
- `rgba(30, 41, 59, 0.96)`
- `rgba(20, 83, 45, 0.22)`
- `rgba(34, 197, 94, 0.22)`
- `rgba(0, 0, 0, 0.28)`
- `rgba(0, 0, 0, 0.42)`
- `rgba(255, 255, 255, 0.16)`

### Warning / Error Tones

- `rgba(248, 113, 113, 0.34)`

## Layout, Spacing, and Sizing

### Global

- `html`, `body`, and `#root` are `width: 100%` and `height: 100%`.
- `body` uses `overflow: hidden`.
- `app-shell` is fixed to the viewport and fills the screen.
- `map-shell` is absolutely positioned to fill the app shell.

### Common Rem Spacing Values in Use

- `0.05rem`
- `0.12rem`
- `0.25rem`
- `0.26rem`
- `0.34rem`
- `0.35rem`
- `0.38rem`
- `0.40rem`
- `0.45rem`
- `0.46rem`
- `0.48rem`
- `0.50rem`
- `0.55rem`
- `0.56rem`
- `0.60rem`
- `0.62rem`
- `0.64rem`
- `0.65rem`
- `0.66rem`
- `0.68rem`
- `0.70rem`
- `0.72rem`
- `0.74rem`
- `0.75rem`
- `0.78rem`
- `0.82rem`
- `0.85rem`
- `0.88rem`
- `0.90rem`
- `0.98rem`
- `1.00rem`
- `1.90rem`
- `2.15rem`
- `2.40rem`
- `3.55rem`
- `4.55rem`
- `5.40rem`
- `9.00rem`
- `18.20rem`
- `20.20rem`
- `30.00rem`

### Panel and Widget Sizing

- Telemetry HUD: `width: min(94vw, 58rem)`
- Upload panel: `width: min(86vw, 20.2rem)`
- Flight results panel: `width: min(86vw, 18.2rem)`
- Upload panel max height: `calc(100vh - 5.4rem)`
- Flight results max height: `min(60vh, 30rem)`
- Trigger button min width: `9rem`
- Close button size: `2.15rem x 1.9rem`
- File input minimum height: `2.4rem`
- Text input minimum height: `2.4rem`
- Telemetry time pill min-height uses the existing pill padding rather than an explicit height.

## Border Radius

- `0.46rem`
- `0.50rem`
- `0.66rem`
- `0.68rem`
- `0.72rem`
- `0.74rem`
- `0.98rem`
- `1rem`
- `999px`

## Shadows

- `0 18px 40px rgba(0, 0, 0, 0.28)`
- `0 22px 60px rgba(0, 0, 0, 0.42)`
- `0 18px 36px rgba(0, 0, 0, 0.36)`
- `0 0 0 3px rgba(14, 165, 233, 0.10)`
- `none`

## Z-Index

- `50` for the top-left and bottom-right trigger buttons
- `55` for the telemetry HUD and flight results panel
- `60` for the upload panel
- `70` for the telemetry popover

## Motion

### Transition Durations

- `160ms ease` is the standard transition across triggers, buttons, inputs, and popovers.

### Existing Keyframes

- `panel-in` transitions from `opacity: 0` and `transform: translateY(-10px)` to `opacity: 1` and `transform: translateY(0)`.

## Existing Component Patterns

### Trigger Buttons

- `upload-trigger` and `results-trigger` are inline-flex buttons with:
  - dark transparent glass background
  - 1px semi-transparent border
  - white text
  - rounded corners
  - backdrop blur and saturation
  - subtle hover lift of `translateY(-1px)`
- `results-trigger` uses `justify-content: space-between`.

### Panels

- `floating-panel` and `flight-results` share the same glass treatment:
  - 1px border with low-opacity slate color
  - `rgba(6, 10, 18, 0.5)` surface
  - `#e2e8f0` text
  - strong shadow
  - `backdrop-filter: blur(18px) saturate(130%)`
- Both panels use a rounded card shape and internal divider.
- The panel header layout is a flex row with title area on the left and a close button on the right.

### Telemetry Cards

- `TelemetryElement` renders each card as a `button.telemetry-item`.
- Current pattern:
  - icon at the left
  - hidden/hover tooltip in `.telemetry-popover`
  - compact vertical stack layout
  - hover lift and border tint on interaction
- Telemetry icons are Feather icons at `14px`.

### Forms

- Inputs use the same dark glass surface language as panels.
- File inputs use a custom `::file-selector-button` with a pill-like button.
- Submit button uses the same dark button treatment as close controls.

### Existing Modal Structure

- `src/componets/modal.tsx` already uses `createPortal` and expects a `#modal-root` container.
- Current behavior:
  - locks body scroll while open
  - closes on backdrop click
  - closes on `Escape`
  - stops pointer events from bubbling from the modal content
- The current component references `modal-overlay` and `modal-content` but those styles are not yet defined in CSS.
- `src/types/modal.d.ts` currently defines `isOpen`, `onClose`, and `children`; it does not yet include `title`.

## Current Data and Utility Notes

- `src/data/demo.ts` contains the sample flight path and target location used by the Cesium globe.
- `src/data/telementary.ts` contains the telemetry sample and the cards rendered into the HUD.
- `src/helpers/helper_functions.ts` provides distance, coordinate, file size, and datetime formatting.
- `src/external_services/api.ts` is currently a stub with an incomplete `ApiEndpoints` class.
- `src/types/api.d.ts` is empty.

## Required UI Values From AGENT.md

These values are mandated for the next implementation steps and should be treated as locked tokens.

### Shared Modal Shell

- Overlay z-index: `1000`
- Backdrop: `rgba(0, 0, 0, 0.55)`
- Modal panel uses a centered flex layout
- Modal open state uses fade + scale-up transition

### Flight Path Palette

```ts
export const FLIGHT_PATH_COLORS = [
  "#00E5FF",
  "#FF6D00",
  "#76FF03",
  "#EA80FC",
  "#FF1744",
  "#FFD740",
  "#40C4FF",
  "#69F0AE",
];
```

- Assign colours by index and wrap when there are more flights than colors.
- Flight paths use `width: 3`.
- Glow layer under each path uses `width: 6` and `Color.WHITE.withAlpha(0.15)`.
- Selected flight opacity is full; non-selected flight opacity is `0.45`.

## Implementation Rules

- Use the current dark glass aesthetic for all new UI.
- Keep Feather icons unless a later task explicitly introduces another icon system.
- Do not introduce a new UI color unless it is first added here.
- Keep the `componets` folder name unchanged.
- Preserve the current compact, map-first layout language when extracting or rebuilding components.
