# UI standard

## Stack
| Target | Use |
|---|---|
| Web | Next.js (App Router), Tailwind, shadcn/ui (Radix), `cva` + `clsx` + `tailwind-merge`, `next-themes` for the `.dark` class |
| Mobile | Expo + Expo Router + NativeWind, `lucide-react-native`, `react-native-reanimated` |
| Docs | mkdocs-material, palette `primary`/`accent` = project accent, light/dark toggle, project icon as logo + favicon |

## Tokens
Run `python3 scripts/build.py --accent <name> --out <dir> [--tailwind 3|4]`. It writes `house-style.css` (CSS variables, `:root`, `.dark`, OS-dark fallback, focus ring, reduced-motion) and, for Tailwind 3, `house-style.preset.js` (`presets: [require("./house-style.preset.js")]`; NativeWind too). Import the CSS once in the root layout/global CSS. Never edit it by hand; regenerate.
Accents: green (default), blue, red, violet, amber, teal. All are contrast-validated in both schemes.
Semantic names: background, foreground, card, popover, primary, secondary, muted, accent (neutral hover surface, not the brand accent), destructive, success, border (decorative), input (control border, >=3:1), ring.

## Look
- Neutral zinc surfaces, one accent used sparingly: primary actions, links, focus ring, active nav, key data.
- Radius `--radius` (10px) on controls and cards; thin 1px `border-border`; soft shadows only on floating layers (popover, sheet).
- Type: Geist Sans body, Geist Mono for code/numbers. Scale 12/14/16/20/24/32; body 15-16px, line-height 1.45-1.6.
- Spacing on a 4px grid. Max content width ~ 72ch for prose.
- Light and dark both ship from day one; default follows OS.
- Motion: 150ms ease-out for hover/press, 200-300ms for enter. Press = `scale-[0.98]`. Nothing loops except loading indicators.

## Icons and brand
- Lucide only, `size-4` (16) inline / `size-5` (20) buttons / `size-6` headers, stroke 2, `aria-hidden` unless it is the only label.
- Each project has ONE Lucide glyph on an accent tile: `/house-style:init` generates `brand/icon.svg` + PNG/ico set from `scripts/brand.py`.
  Use it for: favicon (`app/icon.svg`, `favicon.ico`), `app/apple-icon.png`, Expo `icon`/adaptive icon, manifest icons, mkdocs `logo`/`favicon`, README header, login/empty/error screens, OG image.
- Never use emoji or ASCII (`>`, `x`, `*`, `[ ]`) as icons or bullets in UI.

## Components
Prefer shadcn primitives over custom. Required shared pieces (templates in `templates/nextjs` and `templates/expo`): Skeleton, Spinner, ActionButton (spinner inside), EmptyState, ErrorState (retry), ThemeToggle.
Forms: visible labels (not placeholder-only), inline error text tied with `aria-describedby`, disabled+spinner on submit, preserve input on error.
Destructive: prefer optimistic action + undo toast over confirm dialogs; use a confirm dialog only for irreversible data loss.
Navigation: current page marked (`aria-current`), mobile uses bottom tabs or a sheet menu, never hover-only menus.
