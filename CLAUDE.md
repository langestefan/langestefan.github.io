# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Personal blog (`https://langestefan.github.io`, "De Vonk") built on
[al-folio](https://github.com/alshedivat/al-folio) **v1.2**, deployed to GitHub Pages.

Since al-folio v1.0 the theme is **not vendored**. `_layouts/`, `_includes/`, `_sass/` and the
theme's JS/CSS live in ~19 gems (`al_folio_core`, `al_folio_distill`, `al_icons`, `al_search`,
`al_comments`, …) pinned in the `Gemfile`. This repo is a thin starter: content, config, and a
small site-owned customization layer. `_config.yml` sets `theme: al_folio_core` plus an
`al_folio:` contract block (`api_version`, `style_engine: tailwind`, distill and compat settings)
that is enforced both by a build-time hook and by `al-folio upgrade audit` — don't delete keys
from it.

To read theme source, look inside the gem, not the repo:

```bash
podman run --rm al-folio-local:v1.2 bash -lc 'ls $(bundle show al_folio_core)/_layouts'
```

## Commands

**Docker on this machine needs root** (the user is not in the `docker` group), so use rootless
Podman. Podman also requires fully-qualified image names:

```bash
podman build --from docker.io/library/ruby:slim -t al-folio-local:v1.2 .

# Build the site. Note: each `podman run --rm` is a fresh container, so build and
# inspect the output in the SAME invocation or /tmp/_site will be gone.
podman run --rm -v "$PWD":/srv/jekyll:z -w /srv/jekyll al-folio-local:v1.2 \
  bash -lc 'JEKYLL_ENV=production bundle exec jekyll build --destination /tmp/_site'

# Serve on http://localhost:8080
podman run --rm -p 8080:8080 -v "$PWD":/srv/jekyll:z -w /srv/jekyll al-folio-local:v1.2 \
  bash -lc 'bundle exec jekyll serve --host 0.0.0.0 --port 8080 --destination /tmp/_site'
```

The container serves to a container-local `/tmp/_site`; nothing appears in the host `_site/`.

Formatting (CI runs pre-commit on every push and PR; prettier failures block):

```bash
npx prettier . --write
pre-commit run --all-files
```

Regenerate post artifacts — each post directory is its own self-contained project:

```bash
cd _posts/energy/day-ahead-prices-nl && uv run generate_charts.py   # -> assets/plotly/*.html
cd _posts/energy/hems && uv run --with jupyter jupyter lab hems.ipynb
julia --project=. _posts/guides/interactive-blog/plots.jl           # MUST run from repo root
```

There is no test suite.

## Upgrading the theme

This is now routine — the whole point of the v1 migration:

```bash
# 1. Edit the `= 1.0.x` pins in Gemfile (bundle update alone will NOT upgrade:
#    Bundler honours the exact pins already there and reports no error).
bundle update
bundle exec al-folio upgrade audit          # must end with "Blocking: 0"
bundle exec al-folio upgrade overrides audit
```

As of this migration the site has **zero local overrides of gem-owned files** and the audit is
clean. Keep it that way — see below.

## The site-owned customization layer

Everything custom is injected rather than shadowing gem files. This is deliberate: git cannot
raise a conflict when a gem updates a file your local copy shadows, so every shadowed file is a
silent-rot liability.

| File                                 | Role                                                                                                                                                                                       |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `_plugins/site_assets.rb`            | `post_render` hook. Injects the stylesheet and scripts into every layout (page, post, distill), sets `window.__alGithubSourceUrl` per distill page, and builds the `citation: true` block. Every injected URL carries a `?v=<md5>` built from the **source** file (`custom.scss`, not the compiled `custom.css`), so a changed asset is actually re-fetched. |
| `assets/css/custom.scss`             | All site CSS in one file (heading anchors, justified distill paragraphs, GitHub byline button, markdown alerts, theorem boxes, sidenotes). Compiled to `assets/css/custom.css`.            |
| `assets/js/heading-anchors.js`       | Click-to-copy heading anchors. Uses an inline SVG — v1's `al_icons` ships FontAwesome/Academicons/Scholar Icons but **not** Tabler.                                                        |
| `assets/js/distill-github-button.js` | "GitHub" source button in the distill byline. Waits for `<d-byline>` to hydrate.                                                                                                           |
| `_plugins/sidenote.rb`               | `{% sidenote %}…{% endsidenote %}` block tag. Emits only span-level markup at the point of use: a `.sidenote-ref` marker plus the note body in a hidden `.sidenote-body` sibling.          |
| `assets/js/sidenotes.js`             | Lifts each `.sidenote-body` into a real `<aside>` that is a **direct child** of `<d-article>`, then numbers marker/aside pairs via `data-sidenote`. Distill-only; loaded only on distill.  |
| `_plugins/include_code.rb`           | `{% include_code file="..." lang="julia" start=N end=M %}` — site-specific, no gem owns it.                                                                                                |
| `_plugins/markdown_alerts.rb`        | `{% alert note %}` block tag that renders markdown inside the alert.                                                                                                                       |

If you add CSS or JS, extend these files — do not create `_sass/` or copy a gem's
`_includes/`/`_layouts/` file unless there is genuinely no alternative. If you must shadow one,
run `bundle exec al-folio upgrade overrides accept <path>` and commit `.al-folio-overrides.yml`
so future gem updates flag drift.

`site_assets.rb` builds the citation block because `al_folio_distill`'s render template ignores
`page.citation` (only `al_folio_core`'s `post.liquid` honours it). If upstream fixes that, this
hook becomes redundant; it guards on `language-bibtex` so it won't duplicate.

Sidenotes are split across a Liquid tag and a script for two reasons that are easy to "fix" back
into breakage: Distill positions a margin note with `grid-column: gutter`, which only applies to
direct children of `<d-article>`, so an `<aside>` emitted inline (inside the annotated paragraph
or list item) never reaches the margin — hence the runtime lift. And kramdown escapes raw block
tags in an inline context, so the tag reduces the rendered note to span-level HTML (`</p><p>` →
`<br><br>`) before emitting it. Numbering is done in JS rather than with a CSS counter because
marker and aside end up in different branches of the tree.

## Post structure

Posts are **directories** under `_posts/<category>/<slug>/`, holding the markdown plus the code
that produced its figures. Jekyll flattens nested `_posts/`, so nesting is organisational only;
URLs come from `permalink: /blog/:year/:title/`.

All posts use `layout: distill` with a hand-maintained `toc:` list in front matter that must be
kept in sync with the `##` headings. `published: false` keeps a draft out of the build.

Three ways a post embeds interactive content:

1. **Plotly, pre-rendered** (`day-ahead-prices-nl`) — `generate_charts.py` writes standalone HTML
   to `assets/plotly/`, embedded via `<iframe>` inside `<div class="l-page">`. Each chart carries
   an injected `THEME_SCRIPT` that reads the parent page's `data-theme` attribute and restyles
   the figure; new charts need the same treatment or they break in dark mode.
   `al_folio_core`'s `theme.js` still sets `data-theme` on `<html>` in v1, so this keeps working.
2. **Pyodide, in-browser** (`hems`) — runs CVXPY + HiGHS as WebAssembly client-side.
   ⚠️ The Python it executes is a **hand-maintained copy** of `_posts/energy/hems/src/HEMS/*.py`,
   pasted into `pyodide.FS.writeFile(...)` template literals inside the markdown. Editing the
   `src/` package alone changes nothing on the published page. `src/` is what the notebook
   imports; the inlined copy is what readers run.
3. **WGLMakie/Bonito, pre-rendered** (`interactive-blog`) — `plots.jl` writes static HTML next to
   the post, pulled in with `{% include_relative %}`. Bonito session ordering matters: the first
   rendered session carries the shared setup, so the write order in `plots.jl` must match the
   include order in the post.

Julia deps are the repo-root `Project.toml`/`Manifest.toml`; `src/Blog.jl` just loads them.
Python deps are per-post `pyproject.toml` + `uv.lock` — there is no repo-wide Python environment.

## CI

Four workflows gate a push or PR to `main`; all four must be green:

| Workflow            | What it runs                                                                                |
| ------------------- | ------------------------------------------------------------------------------------------- |
| `pre-commit.yml`    | `pre-commit` — prettier (`npx prettier . --write`) plus whitespace/YAML/large-file checks.  |
| `upgrade-check.yml` | `bundle exec al-folio upgrade audit`, uploading `al-folio-upgrade-report.md` as an artifact. |
| `broken-links.yml`  | lychee over every `.md`/`.html`, `fail: true`.                                               |
| `deploy.yml`        | `jekyll build` (production) → PurgeCSS → GitHub Pages. Builds on PRs, deploys only on push.  |

Locally: `npx prettier . --write` (or `npm run lint:prettier` to check without writing) and
`pre-commit run --all-files`.

The link checker's excludes live in two places — `.lycheeignore` (hosts that 403 bots, and the
`${` pattern for URLs built in post JavaScript) and the `--exclude-path` list inlined in
`broken-links.yml`. A new post whose links are Liquid-templated or runtime-built needs an entry in
one of them.

## Gotchas

- `{% include_code %}` slices a file by **absolute line number**. Editing `plots.jl` silently
  shifts what the post displays — re-check every range after touching a referenced file.
- `Gemfile.lock` is tracked and `bin/entry_point.sh` restores it on container start, so a Gemfile
  that diverges from the lock fights the container. Change both together.
- `_posts/energy/day-ahead-prices-nl/data` is gitignored, so `generate_charts.py` cannot be re-run
  without re-fetching the source price data.
- `_config.yml` excludes `_posts/**/*.ipynb` — notebooks are dev tooling, not site content.
- PurgeCSS runs in the deploy workflow against `_site/assets/css/*.css`. Classes injected only at
  runtime must be added to the `safelist` in `purgecss.config.js` or they get stripped. Its
  content glob covers `_site/**/*.js` too, so a class that appears as a literal string in site JS
  survives; one assembled from fragments at runtime does not. Only production builds purge, so a
  missing safelist entry is invisible locally and only shows up on the deployed site.
- A `{% sidenote %}` marker and its aside are paired **by document order**, not by id. If the two
  counts ever diverge, `sidenotes.js` logs `[sidenotes] N marker(s) but M aside(s)` and everything
  past the mismatch is misnumbered. Sidenotes do nothing outside a distill post — the script is
  injected only there.
- Generated HTML under `_posts/**` and `assets/**` is prettier-ignored; do not hand-format it.
- Front matter dates are in the future relative to real time in this repo; that is intentional.
