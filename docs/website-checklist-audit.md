# Website Checklist Audit

Audit of [specification.website/checklist](https://specification.website/checklist/) for [bstjohn.net/3d-models](https://www.bstjohn.net/3d-models/).

**Key architectural fact**: the site is deployed to a sub-path (s3://www.bstjohn.net/3d-models/ via `aws s3 sync`). This repo controls only files under `/3d-models/` and the HTML markup of `index.html`/`embed.html`. Domain-root paths (`/robots.txt`, `/.well-known/*`), HTTP response headers (HSTS, CSP, compression, caching, HTTP/2-3), and TLS/DNS are all infra-scope (S3/CloudFront/Route53) and outside this repository.

**Status key**:
- ✅ Pass — fully satisfied
- ⚠️ Partial — partially satisfied, limitation noted
- ❌ Gap (in-scope) — missing, implemented in this PR
- 🏗️ Infra-scope — S3/CloudFront/DNS, not this repo
- N/A — not applicable to this site

---

## Foundations

| Item | Status | Notes |
|------|--------|-------|
| HTML doctype | ✅ | `<!DOCTYPE html>` |
| `lang` attribute | ✅ | `<html lang="en">` |
| Charset meta | ✅ | `<meta charset="UTF-8">` |
| Viewport meta | ✅ | `<meta name="viewport" content="width=device-width, initial-scale=1.0">` |
| `<title>` | ✅ | "3D Models" / "3D Model Embed" |
| Meta description | ✅ | Present in index.html |
| Canonical URL | ❌ → ✅ | Added `<link rel="canonical">` in this PR |
| Theme color | ❌ → ✅ | Added `<meta name="theme-color">` in this PR |
| Color scheme | ❌ → ✅ | Added `<meta name="color-scheme" content="dark">` in this PR |
| Favicon / app icon | ❌ → ✅ | Added SVG favicon and apple-touch-icon in this PR |
| Web app manifest | ❌ → ✅ | Added `site.webmanifest` and `<link rel="manifest">` in this PR |
| Open Graph tags | ✅ | og:type, og:url, og:title, og:description, og:image (1200×630) |
| Twitter Card | ✅ | summary_large_image with title, description, image |
| Feed discovery | N/A | No blog or feed; this is a model gallery |
| Popover API | N/A | Optional; not used |

## SEO

| Item | Status | Notes |
|------|--------|-------|
| robots.txt | ⚠️ | Shipped to `/3d-models/robots.txt` in this PR; crawlers only read origin root (`/robots.txt`). Origin-root copy is an infra follow-up. |
| sitemap.xml | ⚠️ | Generated to `/3d-models/sitemap.xml` in this PR; same sub-path caveat as robots.txt. |
| Meta robots (noindex) | ✅ | embed.html has `<meta name="robots" content="noindex">` |
| Heading hierarchy | ✅ | Semantic h1/h2 structure; h2 per project group |
| JSON-LD structured data | ✅ | CI injects Schema.org `CollectionPage` with `3DModel` items via `<!-- __STRUCTURED_DATA__ -->` |
| Breadcrumbs | N/A | Optional; single-page gallery with hash fragments |
| IndexNow | N/A | Optional; not implemented |

## Accessibility

| Item | Status | Notes |
|------|--------|-------|
| ARIA attributes | ✅ | project sections: role="group"/aria-label; headings: role="button"/aria-expanded; canvases: role="img"/aria-label; all interactive elements have aria-label |
| Focus styles | ✅ | :focus-visible outlines on cards, headings, buttons, swatches, links; :focus-within for fullscreen/QR visibility |
| Keyboard navigation | ✅ | Arrow keys between cards; F=fullscreen, D=download, C=cross-section, M=maximize, R=re-render, Escape=dismiss, Enter/Space=expand |
| prefers-reduced-motion | ❌ → ✅ | Added CSS media query in this PR (covers decorative transitions; WebGL OrbitControls are user-driven and intentionally untouched) |
| Accessibility overlays | N/A | Correctly absent (Avoid per checklist) |
| Alt text | ✅ | Thumbnail `<img>` elements have descriptive alt text via `displayName()` |

## Security

| Item | Status | Notes |
|------|--------|-------|
| HTTPS / HSTS | 🏗️ Infra-scope | Configured at CloudFront level |
| CSP header | 🏗️ Infra-scope | Response headers are S3/CloudFront config |
| X-Content-Type-Options | 🏗️ Infra-scope | Response header |
| X-Frame-Options | 🏗️ Infra-scope | Response header |
| Referrer-Policy | 🏗️ Infra-scope | Response header |
| Permissions-Policy | 🏗️ Infra-scope | Response header |
| SRI for Three.js CDN | ⚠️ | Three.js loaded via import map in index.html without SRI — import-map SRI support is limited across browsers. Standalone viewers inline Three.js as base64 (no CDN dependency at runtime). Known gap; tracked for future work. |
| No innerHTML for user data | ✅ | All dynamic DOM uses createElement/textContent/setAttribute; innerHTML only for static SVG icons and gesture hint overlays |
| DNS CAA / DNSSEC | 🏗️ Infra-scope | DNS configuration |

## Well-Known URIs

| Item | Status | Notes |
|------|--------|-------|
| `/.well-known/*` | 🏗️ Infra-scope | Must be at origin root; sub-path copy is not fetched by crawlers |
| security.txt | 🏗️ Infra-scope | Would live at `/.well-known/security.txt` at origin root |

## Agent Readiness

| Item | Status | Notes |
|------|--------|-------|
| llms.txt | ⚠️ | Shipped to `/3d-models/llms.txt` in this PR; same sub-path caveat as robots.txt |
| Structured data for agents | ✅ | JSON-LD Schema.org; `models.json` (machine-readable manifest); OEmbed endpoints |
| Machine-readable formats | ✅ | `models.json` lists all STLs with metadata; per-model OEmbed JSON at `/oembed/<project>/<model>.json` |
| MCP / A2A / agent-cards | N/A | Optional; not implemented |

## Performance

| Item | Status | Notes |
|------|--------|-------|
| Lazy loading (images) | ⚠️ → ✅ | IntersectionObserver already used; added `loading="lazy"` and `decoding="async"` on thumbnail img elements in this PR |
| Compression (gzip/brotli) | 🏗️ Infra-scope | S3/CloudFront configuration |
| Cache-Control headers | 🏗️ Infra-scope | Response headers; build hash already used for cache-busting JS references |
| HTTP/2 or HTTP/3 | 🏗️ Infra-scope | CloudFront configuration |
| Image optimisation | ✅ | PNG thumbnails generated by CI (800×600); OG hero 1200×630 |
| BFCache compatibility | 🏗️ Infra-scope | No `unload` handlers used; pauses on visibilitychange |
| View Transitions API | N/A | Optional; not implemented |
| Speculation Rules | N/A | Optional; not implemented |

## Privacy

| Item | Status | Notes |
|------|--------|-------|
| Privacy policy | N/A | Plausible is cookieless and stores no personal data — no consent banner or policy required |
| Cookie consent | N/A | Plausible is cookieless and does not use local storage |
| GPC (Global Privacy Control) | N/A | No cookies or tracking |
| Third-party scripts | ✅ | Three.js from CDN plus self-hosted Plausible at `plausible.bstjohn.net` (no ads, no cross-site tracking) |

## Resilience

| Item | Status | Notes |
|------|--------|-------|
| Custom 404 page | 🏗️ Infra-scope | S3/CloudFront error document configuration |
| Web app manifest | ❌ → ✅ | Added `site.webmanifest` in this PR |
| Service worker | N/A | Optional; not implemented |
| Monitoring | ✅ | `notify-failures.yml` opens/closes GitHub issues on build.yml failures |

## Internationalisation

| Item | Status | Notes |
|------|--------|-------|
| Language declaration | ✅ | `lang="en"` on `<html>` |
| Multi-language content | N/A | Single-language English site; no i18n planned |
| hreflang links | N/A | Not applicable |

---

## Recommended infra follow-ups (outside this repo)

These items require changes at S3/CloudFront/Route53/DNS — not changes to this repository:

1. **Origin-root robots.txt** — deploy `/robots.txt` at `www.bstjohn.net/` so crawlers honour it
2. **Origin-root sitemap.xml** — reference or deploy sitemap at `www.bstjohn.net/sitemap.xml`
3. **Origin-root llms.txt** — deploy `/llms.txt` for AI agent discoverability
4. **HTTP security headers** — add CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy via CloudFront response headers policy
5. **HSTS** — enable HTTP Strict Transport Security via CloudFront
6. **Custom 404 page** — configure S3/CloudFront error document
7. **Compression** — enable gzip/brotli at CloudFront
8. **Cache-Control tuning** — set appropriate max-age for static assets (STLs, PNGs, standalone viewers)
