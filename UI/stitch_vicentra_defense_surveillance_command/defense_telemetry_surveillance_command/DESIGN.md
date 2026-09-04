---
name: Defense Telemetry & Surveillance Command
colors:
  surface: '#131316'
  surface-dim: '#131316'
  surface-bright: '#39393c'
  surface-container-lowest: '#0e0e11'
  surface-container-low: '#1c1b1e'
  surface-container: '#201f22'
  surface-container-high: '#2a2a2d'
  surface-container-highest: '#353438'
  on-surface: '#e5e1e5'
  on-surface-variant: '#c6c6ca'
  inverse-surface: '#e5e1e5'
  inverse-on-surface: '#313033'
  outline: '#909094'
  outline-variant: '#45474a'
  surface-tint: '#c6c6ca'
  primary: '#f1f0f4'
  on-primary: '#2f3034'
  primary-container: '#d4d4d8'
  on-primary-container: '#5a5b5f'
  inverse-primary: '#5d5e62'
  secondary: '#c6c6cc'
  on-secondary: '#2f3035'
  secondary-container: '#46464c'
  on-secondary-container: '#b5b4bb'
  tertiary: '#f2eff5'
  on-tertiary: '#303034'
  tertiary-container: '#d6d3d8'
  on-tertiary-container: '#5b5b5f'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e2e2e6'
  primary-fixed-dim: '#c6c6ca'
  on-primary-fixed: '#1a1c1f'
  on-primary-fixed-variant: '#45474a'
  secondary-fixed: '#e3e2e8'
  secondary-fixed-dim: '#c6c6cc'
  on-secondary-fixed: '#1a1b20'
  on-secondary-fixed-variant: '#46464c'
  tertiary-fixed: '#e4e1e7'
  tertiary-fixed-dim: '#c8c5cb'
  on-tertiary-fixed: '#1b1b1f'
  on-tertiary-fixed-variant: '#47464b'
  background: '#131316'
  on-background: '#e5e1e5'
  surface-variant: '#353438'
typography:
  display-lg:
    fontFamily: spaceGrotesk
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: spaceGrotesk
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-xl:
    fontFamily: spaceGrotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 30px
    letterSpacing: 0.02em
  headline-md:
    fontFamily: spaceGrotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0.04em
  headline-sm:
    fontFamily: spaceGrotesk
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.06em
  body-lg:
    fontFamily: archivoNarrow
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: 0.01em
  body-md:
    fontFamily: archivoNarrow
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0.015em
  body-sm:
    fontFamily: archivoNarrow
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-telemetry-lg:
    fontFamily: spaceGrotesk
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.12em
  label-telemetry-sm:
    fontFamily: spaceGrotesk
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.14em
  code-tabular:
    fontFamily: archivoNarrow
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
spacing:
  zero: 0px
  hairline: 1px
  2xs: 2px
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  2xl: 32px
  3xl: 48px
  panel-gap: 1px
  grid-gutter: 8px
  screen-margin: 16px
---

## Brand & Style

The design system operates under an uncompromising, mission-critical ethos: absolute clarity, rapid visual parsing, and situational control in low-light tactical environments. Tailored for defense operators, real-time telemetry analysts, and perimeter surveillance directors, the interface prioritizes ocular fatigue reduction, zero optical distraction, and instant status comprehension.

The aesthetic fuses **Ultra-Minimalist Monotone Glassmorphism** with **Sharp Angular Brutalism**. By discarding all decorative radiuses in favor of a strict zero-radius architecture, the visual language mirrors military tactical displays, heads-up targeting reticles, and hardened field terminals. The palette is rigorously achromatic—anchored by pure pitch-black OLED depths and neutral glass tiers—ensuring that color is never ornamental. Chromatic energy is reserved strictly for immediate situational alerts: critical threat vectors, perimeter breaches, telemetry warnings, and live system status.

## Colors

The system employs a strict neutral achromatic baseline to ensure 100% color-free dark containment, preventing eye strain and eliminating chromatic aberration on OLED hardware.

### Monotone Surface Architecture
- **Root Canvas**: `#050507` (Near-true OLED pitch black, strictly free of purple, blue, or slate tinting).
- **Primary Glass Surface**: `#121215` with 70% opacity, overlaid with an 18px backdrop blur.
- **Elevated Glass Surface**: `#18181c` with 75% opacity, used for floating telemetry modules, context menus, and active command controls.
- **Hairline Framing**: `#2a2a2e` at 35% opacity (`rgba(42, 42, 46, 0.35)`). Under hover and focused interaction, border opacity brightens to neutral white highlights (`rgba(255, 255, 255, 0.18)`).
- **Surface Highlight Stroke**: Low-opacity neutral white (`rgba(255, 255, 255, 0.06)`) positioned along the top edge of glass modules to simulate precision-cut optical edge reflection.

### Text & Glyphs
- **Primary Telemetry / Headers**: `#d4d4d8` (Neutral zinc/gray; crisp, high-contrast, strictly neutral).
- **Secondary / Sub-labels**: `#8a8a90` (Muted functional neutral).
- **Disabled / Structural Lines**: `#3f3f46` (Mid-tone boundary neutral).

### Tactical Signal Accents
Color is exclusively deployed as functional signaling telemetry:
- **Threat Red (`#ef4444` / `#dc2626`)**: Active target engagement, boundary intrusion, critical subsystem failure, restricted virtual zones.
- **Online Green (`#10b981`)**: Authenticated uplink, active radar beacon, normal telemetry, encrypted status.
- **Warning Amber (`#f59e0b`)**: Unverified track, sensor degradation, proximity buffer zones.
- **Sensor Wireframes (`rgba(212, 212, 216, 0.40)`)**: Spatial tracking grids and situational target vectors.

## Typography

The typographic hierarchy enforces a division between macro command structures and high-density telemetry streams.

1. **Headlines and Telemetry Meta (`spaceGrotesk`)**: Geometric, technical, and authoritative. Applied in all caps to primary sector titles, sensor designations, threat IDs, and tactical metric tags with wide tracking (`0.06em` to `0.14em`) to simulate heads-up telemetry instruments.
2. **Dense Data and Narrative Logs (`archivoNarrow`)**: A condensed grotesque selected for horizontal economy and legibility across high-density situational readouts, coordinates, audit lists, and real-time terminal payloads. Tabular numbers must be forced (`font-variant-numeric: tabular-nums`) across all data rows to prevent layout jitter during live value refreshes.

## Layout & Spacing

The layout is grounded in a modular, dense **Instrument Grid Layout** engineered for multi-monitor command walls, tactical laptops, and ruggedized field consoles.

- **Structural Grid System**: Built on a 4px base increment with high-density components utilizing tight 8px gutters and micro-gaps. The layout defaults to a 12- or 16-column flexible spatial layout capable of pinning multiple surveillance streams, map viewports, and audit timelines simultaneously.
- **Docking & Zero-Gap Tiling**: Adjacent telemetry modules snap together using 1px hairline divider lines (`#2a2a2e` at 35% opacity) rather than loose whitespace, maximizing data display within constrained operational space.
- **Responsive Adaptation**:
  - **Ultra-Wide / Desktop (>1440px)**: Multi-pane side-by-side arrangement. Primary tactical viewport pinned centrally, flanked by left-rail sensor telemetry and right-rail event logs.
  - **Tablet / Tactical Pad (768px - 1439px)**: Split vertical layout; map or primary visual occupies top 60%, with collapsible sliding telemetry trays stacked below.
  - **Mobile / Tactical Handheld (<767px)**: Single column stream with sticky top tactical status bar, full-width edge-to-edge glass cards, and bottom-pinned modal command actions.

## Elevation & Depth

Depth is established via **OLED Black Monotone Glassmorphism** layered directly above deep `#050507`. Elevation does not use traditional drop shadows or diffuse colorful glows; it relies strictly on layered optical translucency, refractive edge highlights, and deep black obscuration.

### Elevation Levels

- **Ground Level (Base Canvas - `z-0`)**: Pure `#050507` baseline. Displays raw geospatial maps, infrared camera pipelines, and coordinate wireframe planes.
- **Tier 1 (Persistent Panels & Docked Modules - `z-10`)**:
  - Fill: `#121215` at 70% opacity.
  - Backdrop Blur: `18px`.
  - Border: 1px solid `rgba(42, 42, 46, 0.35)`.
  - Top Highlight: Inset line `box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.06)`.
  - Ambient Shadow: `0 14px 36px -4px rgba(0, 0, 0, 0.85), 0 0 20px -2px rgba(255, 255, 255, 0.03)`.
- **Tier 2 (Floating Inspect Panels & Modal Intercepts - `z-20`)**:
  - Fill: `#18181c` at 78% opacity.
  - Backdrop Blur: `24px`.
  - Border: 1px solid `rgba(255, 255, 255, 0.12)`.
  - Top Highlight: `box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.10)`.
  - Ambient Shadow: `0 24px 48px -6px rgba(0, 0, 0, 0.95), 0 0 24px -2px rgba(255, 255, 255, 0.05)`.
- **Tier 3 (Tactical Threat Overlays & Critical Alerts - `z-50`)**:
  - Fill: `#121215` at 92% opacity.
  - Border: 1px solid `#ef4444` with a sharp functional drop shadow `0 0 16px -2px rgba(239, 68, 68, 0.35)`.

## Shapes

The design system enforces an absolute **Zero-Radius (`0px`)** geometry across every element. 

Curvature softens interfaces, implying casual consumer products; sharp, right-angled geometry communicates tactical instrumentation, precision hardware manufacturing, and surveillance monitor perimeters. Buttons, input fields, badges, telemetry containers, modal drawers, and sensor grids must have completely flat 90-degree corners. 

When optical corner indicators are needed (e.g., target reticles or tactical frame bounds), utilize hairline 3px corner notch overlays rendered with neutral white or functional red accents to reinforce targeting aesthetics.

## Components

### 1. Buttons & Command Triggers
- **Shape**: Zero-radius rectangle (`0px`).
- **Primary Control**: Background `rgba(212, 212, 216, 0.10)`, 1px border `rgba(255, 255, 255, 0.18)`, text `#d4d4d8` in Space Grotesk uppercase with `0.10em` tracking. Top highlight: inset `0 1px 0 0 rgba(255, 255, 255, 0.08)`.
- **Primary Hover/Active**: Background transitions to `rgba(255, 255, 255, 0.16)`, border brightens to `rgba(255, 255, 255, 0.40)`, text to `#ffffff`.
- **Critical Action Button**: Background `rgba(239, 68, 68, 0.15)`, border `1px solid #ef4444`, text `#ef4444`. Hover switches to solid `#ef4444` background with pure `#050507` text.
- **Ghost/Tertiary**: Fully transparent background, 1px border `rgba(42, 42, 46, 0.40)`, text `#8a8a90`.

### 2. Telemetry Panels & Glass Cards
- **Construction**: 0px radius, `#121215` at 70% fill, 18px backdrop blur, 1px perimeter hairline border in `rgba(42, 42, 46, 0.35)`.
- **Top Glass Highlight**: Inset border `0 1px 0 0 rgba(255, 255, 255, 0.06)` fading downwards.
- **Card Header**: Border-bottom 1px solid `rgba(42, 42, 46, 0.35)`, housing the module title in uppercase Space Grotesk (12px, tracking `0.12em`) paired with live status indicators.

### 3. Status Badges & Threat Indicators
- **Architecture**: 0px flat rectangular indicators with compact padding (`2px 6px`).
- **Critical Threat**: Border 1px solid `#ef4444`, background `rgba(239, 68, 68, 0.15)`, text `#ef4444`, prefixed with a 4x4px solid square icon.
- **Online / Secure**: Border 1px solid `#10b981`, background `rgba(16, 185, 129, 0.15)`, text `#10b981`.
- **Warning**: Border 1px solid `#f59e0b`, background `rgba(245, 158, 11, 0.15)`, text `#f59e0b`.
- **Neutral Telemetry**: Border 1px solid `rgba(42, 42, 46, 0.60)`, background `rgba(18, 18, 21, 0.60)`, text `#8a8a90`.

### 4. Input Fields & Search Bars
- **Style**: Pitch-black interior (`#08080a`), zero roundedness, 1px hairline border `rgba(42, 42, 46, 0.50)`.
- **Text**: `archivoNarrow`, 13px, text color `#d4d4d8`, placeholder color `#52525b`.
- **Focus State**: Border transitions to crisp neutral white `rgba(255, 255, 255, 0.50)` with no colored glow. Outline: `none`.

### 5. Checkboxes & Radio Toggles
- **Box/Radio**: Sharp 0px square frame (14x14px), background `#0a0a0d`, 1px border `rgba(212, 212, 216, 0.30)`.
- **Selected State**: 1px border `#d4d4d8`, containing an interior 6x6px solid square glyph (`#d4d4d8`). No soft rounded checks or circular radios allowed.

### 6. Tactical Telemetry Data Tables
- **Grid Layout**: Edge-to-edge rows separated by 1px horizontal hairlines `rgba(42, 42, 46, 0.25)`.
- **Typography**: Header cells in Space Grotesk (11px, tracking `0.10em`, `#8a8a90`, uppercase). Row cells in Archivo Narrow (13px, tabular numbers, `#d4d4d8`).
- **Row Hover**: Subtle neutral luminance lift `rgba(255, 255, 255, 0.03)`. Selected row anchored by a 2px vertical neutral white accent bar along the left edge.