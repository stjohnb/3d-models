# Intent log

This is a chronological, append-only record of the repo owner's (@stjohnb's) stated requirements, intentions, rationale, and rejections, distilled from the human-authored content of every GitHub issue and PR in this repo's history. It exists to give future engineers and agents the *why* behind design decisions that the code and other docs only show as *what*. New entries are appended under a dated `###` section as work happens; existing entries are never deleted or rewritten, even when a later entry supersedes them — supersession is noted inline where it occurs. Traceability references are issue/PR numbers in parentheses.

### 2026-02-16

- Project starts as a GitHub Actions pipeline that renders `.scad` files to STL and a Three.js viewer deployed via GitHub Pages (#1, #2).
- First real models are a toothbrush holder/tray and drip tray, establishing the pattern of parametric OpenSCAD models with named dimension variables (#4).

### 2026-02-22

- Power Workshop replacement-parts idea begins: screwdriver handle, flathead attachment, drill bit, all sharing a common hex/square-shaft connector system — the owner wants shared connector geometry reused across attachments rather than one-off designs per tool (#5).
- A sink-tray foot model is added from a hand sketch, establishing the "reference photo/sketch → dimensioned model" workflow used throughout the repo (#6).

### 2026-02-23

- Caliper measurements are applied to correct the Power Workshop connector dimensions, with a `CONNECTION_SPEC.md` added as the authoritative source of truth for the shared connection system — the owner wants specs kept in sync with code, a theme that recurs for the rest of the project's life (#7).
- Drill bit redesigned with shallower flutes and cog teeth to mesh with the workbench gear for "pop-thru drilling" — geometry driven by how the toy is actually used (#8).
- Connector dimensions re-measured and corrected again after the first pass proved off — an early sign that first-cut caliper measurements often need a second, more careful pass (#9).
- Toothbrush files reorganized into a `toothbrush/` subdirectory "for consistency with other model groups" — an early statement of the per-project-directory convention (#10).

### 2026-02-24

- Adjustable bracket/clamp model requested via a Slack-linked design brief, explicitly marked draft with a request to review the hook geometry before finalizing (#12).
- Toothbrush clip geometry corrected from circular to elliptical to match the actual toothbrush cross-section — a recurring theme: geometry should match the measured real object, not an idealized shape (#13).
- Gridfinity-compatible bases added under the toothbrush holder and tray, adopting the external gridfinity spec (kennetek/gridfinity-rebuilt-openscad) for stacking-lip compatibility (#14).

### 2026-02-26

- Issue #11 reports that the male/female connectors can't be pushed together — the female end is too small and both ends need beveled lead-ins to guide connection. This kicks off a long-running connector-fit saga that recurs through issues #78, #81, #85, #87, #99. Fixed in PR #15 (lead-in chamfer, wider socket clearance, stronger male chamfers).
- Hosting is switched from GitHub Pages to S3 (`www.bstjohn.net/3d-models`) via AWS OIDC, with per-PR SHA-versioned preview prefixes and automatic cleanup on PR close (#16). This establishes the durable hosting model used ever since.

### 2026-03-02

- Toothpaste clip redesigned from circular to a rounded rectangle with a front gap for tube access, and the whole assembly rotated `-90°` about X so it stands upright in the viewer — the origin of the "OpenSCAD is Z-up, Three.js expects Y-up" viewer-rotation convention now codified in CLAUDE.md (#17).
- PR-preview generation was silently broken for `.scad` files in subdirectories because the git pathspec only matched root-level files — fixed by switching to a `grep` match at any depth (#18).

### 2026-03-13

- Shared Power Workshop connection modules (`sq_shaft`, `sq_chamfer`, `collar`) are extracted out of duplicated per-attachment files into a library, an early instance of the "eliminate duplication across attachment files" refactor pattern that automated improvement PRs repeat throughout the project (#22).
- **Runner detour (later reverted):** a claws-authored PR switches CI to GitHub-hosted `ubuntu-latest` runners, installing OpenSCAD/xvfb on the fly, to work around a runner missing OpenSCAD (#23). The owner enables passwordless sudo on the runner and states "we can assume all future runners will have passwordless sudo" (#24, #26) — but as of #32 (see 2026-03-19) this GitHub-hosted-runner move is explicitly rejected and reverted; **self-hosted runners are a firm repo requirement**, not a preference.
- Comprehensive `docs/OVERVIEW.md` and `docs/ci-pipeline.md` added as the canonical architecture/pipeline references (#30).

### 2026-03-18

- Toothbrush clip refinement requested simply as "reassess given the latest changes in the repo" (#19) — an example of an issue whose substance is really "keep re-evaluating downstream of other changes," not a fixed spec.

### 2026-03-19

- **Self-hosted runner rule established as non-negotiable.** Issue #32 flags that `build.yml` uses `ubuntu-latest` and states plainly: "All GitHub Actions workflows should use `self-hosted` runners." PR #33 reverts the earlier GitHub-hosted detour (#23) back to `self-hosted`, adding an AWS CLI install step since it isn't preinstalled the way it is on GitHub-hosted images. This is the direct origin of the CLAUDE.md rule that GitHub-hosted runners must never be used in this repo.
- A batch of viewer/CI feature ideas is accepted from the idea-collector process, including a filament color picker (#34), lazy-loaded viewers via IntersectionObserver (#35), automated STL mesh validation via ADMesh in CI (#36), and STL size/triangle-count reporting in PR comments (#37) — alongside an accepted Open Graph/social-preview metadata idea (#38). A "print orientation indicator" and "parametric cable management clip" idea are explicitly rejected in the same batch (#40).

### 2026-03-20

- Mesh validation (ADMesh: watertight, no degenerate triangles, positive volume) lands in CI, gating the production deploy but not blocking the full pipeline — this is the first instance of the "deferred enforcement" pattern (record failures early, only block at the very end) that later gets formalized as an explicit CLAUDE.md convention (#36 → PR #44).
- Filament color picker, lazy-loaded viewers, touch-gesture hints, and keyboard/ARIA accessibility all land as client-side-only changes with no backend dependency, reflecting a preference for keeping the viewer a static, dependency-light site (#34, #35, #48, #49 → PRs #45, #46, #57, #58).
- SCAD dependency-graph generation is accepted (#50); the owner's own follow-up comment on the implementing PR asks that "instead of all dependency graphs in a central location, put each dependency graph in its project's directory" — the origin of the per-project `dependency-graph.md` convention rather than one central file (#56).
- Deep-linking via URL hash routing (`#project/model`) is accepted so individual models are shareable and scrollable-to directly (#53 → PR #59); this is also the origin commit for the `slugify()` helper that must now stay identical across `index.html`, `embed.html`, and the Python scripts.
- Schema.org 3DModel JSON-LD structured data is added for SEO, explicitly motivated by real-world discoverability — e.g. "parents searching 'Fisher-Price Power Workshop drill bit replacement 3D print'" finding the page directly (#52 → PR #55).
- Zip-bundle "Download All" idea is accepted for multi-file projects, with the owner suggesting "could we build the zip during release to simplify things" (#51). The first shipped implementation has a reported bug: the download-count label is wrong when a project displays a component both individually and pre-assembled (#60).
- A blog post draft is added covering the sketch → Claude Code → OpenSCAD → CI → viewer workflow (#61) — the seed of `docs/blog-post.md`, later substantially revised (see 2026-06-11).

### 2026-03-21

- Phillips-head screwdriver attachment requested to fill an obvious gap in the Power Workshop set, reusing the shared connector interface (#39).
- The dependency-graph verification step is found to fail the build before any preview artifacts exist, which the owner says needs to be "less intrusive somehow, probably just move to the end of the CI validation" (#63) — this concretely establishes the deferred-enforcement expectation as something the owner actively wants, not just an engineering nicety.

### 2026-03-22

- A recurring CI-failures-unrelated-to-PR tracking issue gets a clear directive: "We should fix the actual issue rather than ignoring it. The other branch can be merged once the issue has been fixed on main" (#64) — the owner does not want unrelated CI flakiness rubber-stamped away; it should be fixed at the source.
- Library `.scad` files that produce no top-level geometry were causing spurious CI failures; the owner asks "can we rename library files according to a convention that will make them easy to exclude?" (#68) — this is the direct origin of the underscore-prefix (`_*.scad`) library-file convention now in CLAUDE.md.

### 2026-03-23

- `CONNECTION_SPEC.md` and the actual `.scad` socket dimension are found to disagree (8.4mm spec vs 8.6mm code); flagged as likely an undocumented print-test iteration where the spec was never updated to match (#72) — reinforcing that specs must track code, not the reverse.
- Toothbrush-holder parameters were duplicated across three files because the holder file was both a library and a renderable; extracted into `_toothbrush_holder.scad` to match the established library convention (#73).

### 2026-03-24

- Small standalone test-print pieces (`test_male.scad`, `test_female.scad`) added specifically so snap-fit tolerance can be verified on a fast, small print before committing to a full tool print — establishing the "connection test print" pattern used throughout the connector-fitting saga (#62).
- Issue #78 reports a "strange circular piece" artifact on the male connector (later traced to a chamfer being unioned instead of subtracted) and that male/female transitions need beveling to guide the connection — fixed with `hull()`-based tapers, the origin of the "beveled transitions" convention documented in CLAUDE.md (#79).
- Issue #81 follows up that the male tip specifically still needs the same beveling treatment as the rest of the shaft (#82).
- A broad tools-research issue asks the owner to mine an external ChatGPT conversation for ideas applicable to this repo's workflow (#77) — low-signal on its own, but establishes that external tool research (dune3d, build123d, cadquery, gencad, vibe-modeling, etc.) is an ongoing, standing input to repo planning (see also #89, #113, #165, #198, #199, #200, #218).

### 2026-03-25

- `square_socket()` extracted from a duplicated pair of files into the shared `_connection.scad` library, continuing the "shared connection logic belongs in one library" pattern (#84).
- Issue #85: the male/female test prints still don't fit — "the widest part of the male connector fits nicely in the widest part of the female, but has no chance of making it through the narrowest part." The owner's own proposed fix: "Maybe the catch on the female side should only catch the corners of the male, rather than trying to fit the whole thing... pass but only with a little force." This is the origin of the corner-only octagonal snap-ridge design (PR #86), a deliberate acknowledgment that rigid 3D-printed plastic needs looser full-perimeter tolerances than injection-molded parts.
- BambuLab A1 direct-print integration is raised as a research idea via voice note — "send models directly to the printer from a pull request or from Claws" (#89), not yet implemented as of this writing.

### 2026-03-26

- Issue #87: even with the corner-only ridge, "the corners are just slightly too square to pass through... take the tiniest fraction off them, maybe round them." PR #88 adds `corner_r` rounding to the male shaft profile — but the owner iterates live on the PR itself: "Still too big, make the radius a little bigger to take more off," then "still doesn't fit, take a little more off." This is a clear example of dimensional tuning happening through iterative print-test feedback rather than being fully specified up front.

### 2026-03-27

- Documentation clarifies an intentional asymmetry: the female socket keeps sharp corners (as a subtracted void) while the male shaft gets rounded corners, because sharp corners on the void give the necessary clearance for the rounded shaft to clear the corner-only ridge (#98) — not a bug, a deliberate design tradeoff worth preserving.

### 2026-03-28

- A large batch of feature ideas is accepted in one sweep: print-time estimate per model (#91), OEmbed discovery endpoint for rich link previews (#92), self-contained single-file HTML export per model (#93, motivated by bloggers wanting to self-host previews and users wanting an offline reference), QR code per model card (#94, explicitly for "phone-to-desktop or desktop-to-phone" workflows and potential physical labels on printed parts), model metadata JSON schema with CI linting (#95, explicitly to prevent field-naming drift like "infill" vs "infill_percent" across projects — the origin of `meta.schema.json`), and an auto-generated README gallery (#96).
- In the same idea-review cycle, several ideas are explicitly rejected: semantic version tags in metadata, deprecation markers, bounding-box regression guards, golden-STL-hash comparisons, and GitHub issue templates for model requests (#97) — the owner does not want heavyweight versioning/regression machinery layered onto what is still a personal hobby repo.

### 2026-03-29

- Small UI polish: spacing looked bad around the print-time badge, fixed with a flex `gap` (#109).
- Drill bit widened by 1mm via voice-note issue — a reminder that many issues here originate as spoken, terse instructions rather than written specs (#111).
- Further idea-review rejections: model maturity lifecycle badges, scheduled re-render freshness checks, support-material estimation, multi-part cost rollup, recommended print sequencing, screenshot export, portable embed kits, no-JS static fallback, parametric boundary sweep rendering, render determinism verification, a shared `lib/` primitives directory, a community-models directory, and GitHub-Discussions-based model requests are all rejected in the same pass (#119) — a strong, repeated signal that the owner wants to keep the project's surface area lean and is wary of speculative infrastructure with no immediate concrete need.

### 2026-04-01

- Build123d (a CAD-as-Python alternative to OpenSCAD) is raised as a research topic, not adopted (#113).
- Drill socket schematics requested purely to document measurements before modeling — "just to produce schematics of the part with the measurements labelled" (#114), followed by owner corrections mid-thread ("some of the measurements will need to be corrected," "the nose is cylindrical, not conical").
- Follow-up refactor cleans up duplicated Python helper functions between build scripts and the standalone-viewer generator (#120), and `index.html`'s unhandled `models.json` fetch failure is fixed to show an error state instead of hanging on "Loading models..." forever (#121).
- On the drill-socket model itself, the owner questions the connector-code-sharing assumption directly: "The drill bit and the drill socket have quite different teeth. Was extracting common code between them definitely valid?" (#123) — a useful check against over-eager DRY refactors when the underlying geometry actually differs.

### 2026-04-02

- Three CI-validation ideas accepted together: OpenSCAD version compatibility tracking, motivated by the fact that OpenSCAD's CGAL→Manifold kernel migration changed `minkowski()`/`hull()` floating-point behavior and could silently affect the sub-millimeter connector tolerances (#116); minimum wall-thickness validation from STL cross-sections, to catch printability issues mesh validation alone can't (#117); and mating-part interference detection via Boolean mesh intersection for declared part pairs (#118).
- Drill socket dimension corrections continue in detail from caliper re-measurement: nose OD/ID, teeth extent, collar/shaft sizing, and a requirement that the flange and body actually be hollow rather than solid (#124, #131) — with a sharp correction on the geometry itself: "Flange isn't hollow although some sort of seam is visible" (#132), and on a lost 4mm bore: "bore_d is not equal to cyl_d" (#127).

### 2026-04-03

- The drill-socket shaft-to-cylindrical-piece transition is simplified per owner direction: "shaft should end with a square edge to make it a proper cuboid... no need for angled transition between the two" (#134) — not every joint needs a bevel; sometimes a flat, simple transition is correct.

### 2026-04-06

- Issue #133 corrects a geometry misunderstanding: the collar should run through the body as a continuous cylinder up to the teeth, not taper into a cone attaching to the nearest body face — fixed by extending the collar and removing a fragile frustum bridge (#139).
- PR-preview UX gap: only the latest commit's build was linked per PR; the owner wants every build linked (latest prominent, older ones collapsed) so reviewers can compare across pushes (#137).
- Cross-section clipping-plane viewer feature requested — "it would be useful to be able to see a cross section when viewing the 3d models" (#140) — implemented across `index.html`, `embed.html`, and the standalone-HTML generator, becoming a durable, oft-referenced viewer feature (recurs in #180/#181).

### 2026-04-07

- Drill-socket cavity needed to extend through the full body, not just the flange (#144); bevel gear tooth count corrected from an approximate 20 to a confirmed 24 based on direct part measurement (#148/#149).
- A "Pliers" model request is raised from a reference photo with the observation "the model is still very far away from the image. Could we run some processing on the image to extract a template?" (#145) — an unresolved idea about image-to-template pipelines for future model requests.

### 2026-04-08–2026-04-10

- Several small refactors continue the "one canonical implementation, no duplicated logic" pattern established earlier: Three.js version-consistency checking extended to cover `embed.html` as well as `index.html` (#151); a `_make_result` helper introduced to stop repeating result-dict construction in the interference checker (#152); `load_meta_failures()` consolidated into the shared `oembed_helpers.py` module (#153); a `visibilitychange` handler added to the standalone-viewer template so it pauses rendering when the tab is hidden, matching `embed.html`'s existing behavior (#159); and the `FILAMENT_COLORS` palette consolidated into a single `filament-colors.json` so `index.html` and `generate-standalone.py` can't drift apart (#160) — this is the direct origin of the escaping-layer requirement documented in CLAUDE.md's XSS/HTML-safety section.
- Drill socket boss geometry needs a 2mm stand-off gap from the flange so the drill housing has room to seat before contacting the boss, and the cavity needs to be bigger to actually fit onto the drill (#156).

### 2026-04-14–2026-04-17

- `generate-gallery.py` refactored to read descriptions from `models.json` (already populated by CI) instead of re-reading `meta.json` directly, closing a consistency gap where the two could drift if `models.json` wasn't regenerated (#162).
- Dependabot alerts found to be disabled for the repo; owner enables them for vulnerability visibility (#164).
- CadQuery (a Python-based CAD alternative to OpenSCAD) raised as a research link, not adopted (#165) — consistent with the pattern of periodically surveying alternative tools without switching away from OpenSCAD.

### 2026-05-01

- Vacuum hose reducer requested with a fully worked dimensional spec up front (50mm ID one end, 30mm OD the other, 2mm walls, ~100mm length, tapered ends for tolerance) — a rare issue that arrives essentially pre-speced (#166), though the owner still tunes it live: "the taper at the small end should be more gradual to fit snugly inside a 30mm socket" (#167).
- Wall-thickness CI warnings are found to be noisy and low-value in practice: "These warnings aren't useful. Lots of 0mm or 0.01mm but all the pieces have been printed and are working well" (#169) — a concrete case of the owner pushing back on a CI check's signal-to-noise ratio based on real-world print outcomes, not just theoretical geometry validity. He also separately asks that these warnings be surfaced as PR comments since they're "hard to see on CI" (#168).

### 2026-05-02–2026-05-08

- Vacuum adapter large end needs to be 1mm thinner (#171). A workshop-vacuum "blast gate" (flow shutoff) model is requested for 50mm-OD PVC pipe (#173), and goes through several rounds of concrete physical-fit corrections: the two gate-body halves need to be a single joined piece open on one side only for the blade (#174); the blade's cutoff hole was positioned wrong so airflow wasn't actually blocked when closed (#174); blade/handle alignment was off and the blade unnecessarily long (#174); the two sockets on each side of the gate body must share one consistent internal radius "so no dust accumulates" (#174) — a rationale grounded in the part's actual function, not just geometry cleanliness. Follow-up: gate diameter needs to be 1mm wider to actually fit the pipe, and a mounting plate with 4 screw holes is needed (#175), with the plate later needing to be bigger since the holes were too close to the body (#176). A catch/notch to hold the gate closed is requested (#177) but the first attempt visibly changes nothing ("I can't see any change to either the body or the blade," #179).
- Viewer UX: a "maximise" state (bigger than the default card view, short of full fullscreen, with the cross-section tool still available) is requested (#180), with a first attempt found to hide the cross-section slider when maximised — a regression against #140's earlier feature (#181).
- Hexagonal male-female connector requested with precise dimensions (7mm hex, 3mm walls, 20mm height) as a single one-piece part, then tuned live: male end widened 0.5mm, walls thinned from 3mm to 2mm, then the male end reverted back to exactly 7mm — an example of quick iterative dimensional back-and-forth within a single PR thread (#182/#183).
- Drill socket's internal bore found too shallow for the inserted rod, deepened, then found to have gone 2mm too far and pulled back by a precise `bore_extra = 1.5mm` (#184/#185) — again showing the owner tuning exact millimeter values interactively against a printed test rather than specifying them all up front. Drill socket also found to be missing bit-retention notches that the screwdriver handle already has (#191).

### 2026-05-11–2026-05-12

- A second vacuum adapter requested with its own taper spec (#195); the owner then insists the two vacuum-hose models be grouped together in a single directory in the UI, explicitly rejecting a metadata-based grouping mechanism once directory grouping worked: "moving them to the same directory had the required effect on the UI. Adding a group field to meta.schema.json seems irrelevant now. Is it used for anything at all?" (#196) — a clear preference for directory structure as the single source of truth for grouping, over a parallel metadata field that could drift out of sync.
- Open-ended prompt for what other Power Workshop attachments could be built now that the male/female connection system works reliably (#193) — signals the connector work (#11 → #99) is considered "done" as a foundation for further attachments.

### 2026-05-18–2026-05-19

- A cluster of research issues surveys adjacent tools and projects: cjtrowbridge/vibe-modeling (#198), an OpenSCAD libraries catalog to be documented so "future planning tasks are aware of the libraries" — the direct origin of `docs/OPENSCAD_LIBRARIES.md`, which CLAUDE.md now instructs agents to read before proposing new geometry (#199), and Gencad, with the owner asking whether the authors have made it usable/integrable (#200).
- From the vibe-modeling analysis, two follow-on ideas are raised. Multi-view inspection renders (rendering extra orthographic views into cavities for complex-interior parts) is scoped down deliberately from vibe-modeling's unconditional 17-views-per-part approach, reasoning explicitly that "S3 storage and CI time scale with the collection... most parts don't benefit" from that cost (#202). The owner's own comment reframes the actual need: "I think where this would be most useful is for Claude itself when iterating on a design, it should be able to render any angle it needs to verify its designs, they don't particularly need to be stored as build artifacts" — this is the direct rationale behind `scripts/render_view.py` being a local-only dev tool explicitly excluded from CI, as CLAUDE.md now states.
- JSON-driven parameter sets with `-D` injection is raised as a way to separate parameter values from geometry (e.g. rendering multiple PVC-diameter variants of a blast gate from sibling config files), with an "aspirational extension" of live web-viewer reconfiguration via OpenSCAD-WASM (#203). The owner directs: "Let's see how far we can get with openscad-wasm" — greenlighting the WASM customizer effort that follows in #206/#208/#209, and this issue is the origin of the `<basename>.parameters.json` manifest convention (numbers/booleans only, no strings, to avoid shell-quoting injection risk) now codified in CLAUDE.md.

### 2026-05-19 (WASM customizer)

- The WASM-based in-browser customizer (#206) hits real friction during PR-preview testing: repeated render failures with CGAL/Manifold errors surfaced in the browser console, prompting the owner to ask directly: "Can we add some automated tests so that this isn't a manual verification cycle?" (#206) — the origin of `scripts/test_wasm_customizer.mjs` as a required test target (per CLAUDE.md's Testing section) rather than relying on manual PR-preview clicking.
- Issue #208 reports the customizer "freezes the whole browser during re-renders" and asks for an explicit re-render button (rather than reacting to every slider tick) plus parameterizing more models — PR #209 has a lingering bug where "an automatic re-render still triggers on the first slider interaction" even after the explicit-trigger fix.

### 2026-05-23–2026-05-29

- An external OpenSCAD/LLM benchmark article is raised for research (#218); PR #219 addressing it draws a sharp correction: "This PR should be implementing the suggestions rather than reciting them" — the owner wants research issues to produce concrete action, not a restated summary.
- NZ ski-fields terrain model requested from a specific map-tool URL, with the owner directing which peaks/landmarks the terrain must fully contain and pointing to the source tool's own published code (ModelRift/terrain-to-3d) as possible inspiration (#222). Iterated live: the initial print of mountains looked too small, so a z-exaggeration factor is added and bumped from 1.5x to 2x (#229), and the model needed reorienting so it lies flat by default in the preview rather than requiring the user to spin it (#229).
- A general viewer-navigation issue is raised: orbit controls are hard to use when a model isn't defined on the expected axis; the owner asks not just for a fix but for the ability to switch between OrbitControls, TrackballControls, ArcballControls, "any other available options" (#230) — a preference for offering alternative interaction modes rather than one hardcoded control scheme.
- Issue #237, opened the same day, documents a serious operational incident: the claws issue-worker for #236 ran an unbounded full-resolution OpenSCAD render on the shared, memory-constrained claws build host (~3.8GB RAM), ballooning to ~2.4GB RSS and freezing the whole host — twice, because the task got re-dispatched and repeated the same mistake. This is the direct origin of the CLAUDE.md section "Rendering on the constrained build host," including the `systemd-run --user --scope -p MemoryMax=1G` / `ulimit -v` capping rules, the "prefer `--export-format csg -o /dev/null` for cheap syntax checks" guidance, and the explicit instruction not to blindly retry an OOM-killed render.

### 2026-05-31

- A public "website checklist" spec is used to self-audit the site's SEO/accessibility/performance posture (#245) — feeding into `docs/website-checklist-audit.md`.

### 2026-06-09

- Blog post revision requested with explicit voice direction: lead with the Power Workshop parts as the meatiest example, add real progress photos, and — critically — "the existing content does sound very LLM generated - short punch sentences, emphasising how great everything is. I'd prefer a more relaxed style, this is just a personal blog talking about my hobbies" (#243). This is the direct origin of the CLAUDE.md "Blog voice" section (first-person, no marketing cadence, admit friction, Claude/Claws as tools not the hero).
- Render caching is requested because renders had become slow with no mechanism to skip unchanged models (#250).

### 2026-06-11

- Blog post restructured per #243's direction: Power Workshop leads, sink-tray demoted to a shorter aside, the Claude/Claws workflow woven in matter-of-factly rather than centered, and the public viewer link planted early and paid off later. `CLAUDE.md` gains its formal "Blog voice" section codifying this style for future edits (#252).
- Owner wants to sync a public snapshot of the (private) repo to `stjohnb/3d-models` specifically so the blog post can reference real source code "without exposing ongoing development," with an explicit requirement that "no sensitive information is included" — the origin of the public-mirror/snapshot mechanism this repo now maintains (#253).
- Viewer collapses-by-default requested: "Too many 3d viewers loading at once. Collapse all sections when somebody loads the plain page without any deeplinks" (#254) — deep-linked visits should still auto-expand the target, per the earlier hash-routing convention (#53).

### 2026-06-23–2026-06-24

- GitHub's storage alert on Actions artifacts prompts the owner to ask "Can we use S3 instead of GH Actions? More relaxed budget there" (#259) — reflecting a general preference for S3 over GitHub-native storage where budget/quotas are a concern, consistent with the earlier Pages→S3 hosting switch (#16). In practice the immediate remediation is simpler: deleting ~1.31GB of stale accumulated artifacts and recommending shorter retention settings, without changing the storage backend (#262).

### 2026-06-26

- A new self-contained model, a parametric MacBook Pro laptop stand reverse-engineered from an imported STL-only reference mesh into a fully parametric model (slot width, stand dimensions as named variables), is added — notable as one of the few models built from a mesh reference rather than physical calipers (#263).
- The three-part NZ ski-fields terrain (lake/terrain/snow, per #270 below) is separated into distinct pieces so each can be printed in a different material/color, with a requirement that the lake floor descend at a realistic gradient in cross-section while still being structurally joined to the surrounding terrain outside the visible cut planes (#236). First attempt is rejected because "'ski fields' and 'terrain' look the same" when the owner expected terrain to stop at a flat snow-line plane and the ski-fields piece to begin there (#248). A follow-up refinement moves from one global snow line to per-mountain snow lines, with the owner giving a fairly precise geographic constraint (a plane from the lake to Arrow town definitely below the line; Coronet Peak mostly snow-capped; Flight Park only just below the line) to keep the problem tractable while staying "relatively consistent" (#236 comment thread).

### 2026-06-30

- Owner wants the `.scad` source for each model published to S3 alongside the built STLs — "I want to be able to publish the scad files for each model along with the STLs" — while explicitly not wanting to make the whole repo public (#265). A follow-up comment on the same issue instructs removing the preview site's existing links back to the (private) repo source, since "the site is public but the repo is not" — this is superseded three weeks later by #280, once a public source mirror actually exists to link to instead.

### 2026-07-07

- Issue #272 documents a second serious host-freeze incident, this time in CI itself: a PR added an `assembly.scad` combining all three NZ ski-fields parts, and the unbounded "Render STL files" step ran for ~56 minutes and froze the `ryzen` self-hosted runner hard enough to require a physical reboot. No step logs were uploaded because the job died mid-render, which blinded the automated CI-failure-diagnosis tooling entirely (three failed fix attempts, PR marked "Problematic," diagnoser unable to proceed with no log). A re-run on a second, healthy runner reproduced the same ~50-minute unbounded render before being SIGKILLed — proving it's not a one-off under-provisioning fluke but a real exposure in any cold-cache render of that file. The owner adds a critical caveat: any memory/time-cap fix "only makes sense if we constrain the job to the ryzen runner too," since the memory caps in `scripts/capped-openscad.sh` are calibrated against a runner of known RAM capacity — this is the direct origin of the `build.yml` `build` job's `[self-hosted, linux, ryzen]` runner pin that CLAUDE.md says must be preserved and never widened back to plain `[self-hosted, linux]`. The incident also surfaces a second, independent bug: a render killed by SIGKILL (exit 137) or `timeout` (exit 124) was being silently routed into the "suspected library, skip" branch instead of hard-failing — meaning a build could go green with a model silently missing from the deployed site.

### 2026-07-08

- Issue #270 asks for the NZ ski-fields assembly to ship as three distinctly colored materials (blue lake, grey terrain, white snow). Issue #275 finds that requirement only partly met: STL is a monochrome format, so `color()` calls in `assembly.scad` are discarded on export and the interactive/embed/standalone viewers all show a single flat material; even the one place `color()` does survive (the PNG thumbnail) is dominated by an edge-on view of a grey base slab because of the repo's standard Z-up→Y-up viewer rotation. The owner's suggested fix — declaring a composite "assembly" of existing per-part STLs with fixed per-part colors in `meta.json`, loaded by the viewer as separate colored meshes in one scene — respects two explicit CLAUDE.md constraints reiterated in the issue itself: `meta.schema.json` must be extended before `meta.json` grows the new field, and all DOM insertion must go through the DOM API, never `innerHTML`.
- Issue #277 requests a `README.public.md` written for a reader with no access to the private repo, once the (then-upcoming) automated public-snapshot sync lands — it must not reference the private-repo sync mechanism itself, must not link to files the snapshot scrubs (`.claude/`, `.plans/`, `ideas/`, internal automation docs), must contain no credentials/tokens, and is explicitly called out as something that "must be kept up to date manually from now on" since it no longer flows automatically from the private README. The owner's only comment: "Don't mention the public sync of a private repo bit" — keep the public-facing framing clean of internal process detail.

### 2026-07-09

- Preview-site model cards should link back to the model's source in the now-existing public mirror (`https://github.com/stjohnb/3d-models`), not the private repo (#280) — this both fulfills and supersedes the "remove source links" instruction from #265 (2026-06-30), now that a public source actually exists to link to. This is the origin of the "Public source links" invariant in CLAUDE.md requiring `PUBLIC_REPO`/`publicSourceUrl()` to stay identical across `index.html`, `embed.html`, and `scripts/oembed_helpers.py`.
- Plausible analytics is added to the `/3d-models` site, mirroring the integration already present on the main `bstjohn.net` site, using the exact same tracking script snippet (#282).

### 2026-07-13

- Issue #268 requests a case for an ESP32 board with an attached display, from reference photos; a follow-up comment asks that a stylus/pen that came with the touchscreen also be incorporated into the design (holder/slot), rather than treating the case as display-only.

### 2026-07-22

- Issue #288 flags GitHub's dependency-graph alert that the repo has no Dependabot configuration for its `github-actions` ecosystem, citing an unrelated repo's experience with unmanaged, un-updated dependencies as the cautionary example. Resolved by adding `.github/dependabot.yml` scoped to `github-actions` only (weekly, grouped into a single PR, no default label) — no other ecosystem (npm, pip) applies, since the repo has no root `package.json` and OpenSCAD/Python tooling isn't a Dependabot-supported ecosystem here (#288).
