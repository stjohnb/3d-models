# Visual Design Notes

**Depth: Deep dive.** Read this only when changing `index.html`'s visual
design — palette tokens, the display typeface, background layers, or motion
rules. For feature behavior read [web-viewer.md](web-viewer.md) instead.

The repo has no design system; this file records the deliberate choices made
for the gallery's user-facing chrome so later changes stay coherent instead of
drifting back to framework defaults. It covers `index.html` only — `embed.html`
and the generated standalone viewers are intentionally excluded (see below).

Introduced with the landing gallery (issue #345).

## Palette

Declared as custom properties on `:root` in `index.html`:

| Token | Value | Use |
|---|---|---|
| `--surface` | `#16213e` | Card and pane fill, one step up from the `#1a1a2e` page background |
| `--surface-raised` | `#1c2b4f` | The one element that sits above a card (the "+N more models" tile) |
| `--accent` | `#64b5f6` | Links, focus rings, hover borders — the single accent |
| `--text` | `#e0e0e0` | Body copy |
| `--text-dim` | `#9aa7c4` | Descriptions, metadata, tag chips |

A **single** accent, deliberately: `#64b5f6` was already the viewer's link and
focus colour, so adopting it as the sole accent kept the new gallery visually
continuous with the panes rather than introducing a second brand colour. There
is no gradient-on-white anywhere; the site is dark-only (`color-scheme: dark`,
`theme-color: #1a1a2e`).

The tokens are used by the **new** landing rules and the header wordmark only.
The pre-existing pane, tree, and customizer CSS still carries its literal hex
values — rewriting several hundred lines of working chrome was out of scope for
#345, and mixed literals/tokens is a smaller inconsistency than a half-finished
migration. New rules should use the tokens.

## Typography

- **Display face**: Space Grotesk (weights 500 and 700), loaded from Google
  Fonts with `display=swap` and a `preconnect` to `fonts.gstatic.com`. Applied
  to `header h1` and `.landing-card-title` — headings only.
- **Body face**: the existing system stack
  (`-apple-system, BlinkMacSystemFont, "Segoe UI", …`). Body copy is read at
  small sizes across many devices and the system face renders better there than
  a webfont at 0.75rem; it also means no font blocks the model list.

The size/weight contrast is the point: `header h1` and the card titles carry
the display face and weight, against 0.75rem `--text-dim` card metadata.
The landing gallery has no page heading or subtitle (removed in #381); cards
are the only headings on the page.

**Standalone viewers deliberately do not load the web font.** `site/standalone/`
pages are single self-contained files meant to work offline and off-network
(they also omit analytics for the same reason); a Google Fonts stylesheet would
break that guarantee. They keep the system stack throughout.

## Background

`#landing` carries a layered background rather than a flat fill: a
`radial-gradient(circle at 20% 0%, rgba(100,181,246,0.10), transparent 45%)`
tint over the page background, so the grid reads as a lit surface without
introducing a second colour. Cards themselves are flat `--surface` — the
thumbnails supply the visual interest.

## Motion

Motion is minimal and CSS-only: a 0.15s `transform`/`border-color` transition on
card hover (`translateY(-2px)` plus an accent border). Nothing animates on load,
and nothing animates without user input.

The existing `@media (prefers-reduced-motion: reduce)` block at the end of the
stylesheet neutralises `transition-duration` globally, so reduced-motion users
get the colour change with no movement. Any new motion must stay inside that
guard — i.e. use `transition`/`animation`, never JS-driven tweens.

## Focus and hit targets

Every *navigational* element in the gallery is a real `<a>`, so keyboard
navigation, middle-click, and "copy link address" work without JS. The sole
exception is the description More/Less `<button>` (#369): it is an in-page
disclosure toggle rather than a link, so it must not be an anchor. It is
styled as accent-coloured link text at 0.75rem with the same 2px `--accent`
focus ring as everything else, and it animates nothing. Focus is always
visible: `:focus-visible { outline: 2px solid var(--accent) }` with a 2px
offset, matching the rest of the viewer. Below 900px the grid drops to 200px
minimum columns and the page (not the gallery) scrolls.
