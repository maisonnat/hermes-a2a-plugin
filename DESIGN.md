# Design System — Hermes A2A Plugin

> Developer-centric dark theme inspired by OpenCode.
> Black canvas, amber accents, crafted for documentation.

## Brand

| Token | Value | Usage |
|-------|-------|-------|
| `--brand-black` | `#0a0a0f` | Primary background |
| `--brand-black-soft` | `#12121a` | Card/surface background |
| `--brand-black-muted` | `#1a1a25` | Sidebar, code blocks |
| `--brand-amber` | `#F59E0B` | Primary accent (links, highlights) |
| `--brand-amber-light` | `#FBBF24` | Hover states |
| `--brand-amber-dark` | `#D97706` | Active states |
| `--brand-amber-glow` | `rgba(245, 158, 11, 0.15)` | Subtle glow effects |
| `--brand-white` | `#F5F5F5` | Primary text |
| `--brand-white-soft` | `#A0A0B0` | Secondary text |
| `--brand-white-muted` | `#6B6B80` | Metadata, captions |

## Typography

| Token | Value | Usage |
|-------|-------|-------|
| `--font-sans` | `'Inter', system-ui, sans-serif` | Body text |
| `--font-mono` | `'JetBrains Mono', 'Fira Code', monospace` | Code blocks |
| `--font-size-sm` | `0.875rem` | Small text |
| `--font-size-base` | `1rem` | Body |
| `--font-size-lg` | `1.125rem` | Large text |
| `--font-size-xl` | `1.5rem` | H3 |
| `--font-size-2xl` | `2rem` | H2 |
| `--font-size-3xl` | `2.5rem` | H1 |

## Spacing

| Token | Value |
|-------|-------|
| `--space-xs` | `0.25rem` |
| `--space-sm` | `0.5rem` |
| `--space-md` | `1rem` |
| `--space-lg` | `1.5rem` |
| `--space-xl` | `2rem` |
| `--space-2xl` | `3rem` |

## Borders

| Token | Value |
|-------|-------|
| `--radius-sm` | `4px` |
| `--radius-md` | `8px` |
| `--radius-lg` | `12px` |
| `--border-color` | `rgba(255, 255, 255, 0.08)` |
| `--border-hover` | `rgba(245, 158, 11, 0.3)` |

## Shadows

| Token | Value |
|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.3)` |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,0.4)` |
| `--shadow-lg` | `0 8px 30px rgba(0,0,0,0.5)` |
| `--shadow-glow` | `0 0 20px rgba(245,158,11,0.1)` |

## Components

### Navigation

- Background: `--brand-black-muted`
- Active item: amber left border
- Hover: subtle amber tint

### Code Blocks

- Background: `#0d0d14` with subtle amber left border
- Copy button: amber icon on hover
- Line numbers: `--brand-white-muted`

### Cards

- Background: `--brand-black-soft`
- Border: `--border-color`
- Hover: `--border-hover`
- Optional: subtle amber top border on hover

### Admonitions

- Note: blue-tinged border
- Warning: amber-tinged border
- Danger: red-tinged border
- Tip: green-tinged border

### Links

- Default: `--brand-amber`
- Hover: `--brand-amber-light` with underline
- Active: `--brand-amber-dark`

## Diagrams

Use Mermaid for all diagrams:
- Background: transparent or `--brand-black-muted`
- Node fill: `--brand-black-soft` with amber stroke
- Text: `--brand-white`
- Edge: `--brand-white-muted`
- Primary edge: `--brand-amber`

## Logo Usage

- Light background: standard logo
- Dark background: same logo (designed for dark)
- Favicon: `docs/assets/logo.png` (converted)
- Nav bar: 32px height
- Footer: 48px height
