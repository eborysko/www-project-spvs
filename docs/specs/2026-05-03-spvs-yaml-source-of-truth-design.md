# SPVS YAML Source-of-Truth — Design Spec

**Status:** Draft for maintainer review
**Author:** Evan Borysko
**Date:** 2026-05-03

## Problem

The Secure Pipeline Verification Standard (SPVS) authors and publishes its
controls today as flat CSV files (`1.5/OWASP_SPVS_1.0_-en_Requirements.csv`,
`1.5/OWASP_SPVS_1.5-AI_-en_Requirements.csv`). The CSV format has reached the
limits of what it can carry as the standard matures:

- **Per-supplement schema profiles need first-class support.** Different
  supplements intentionally capture different attributes optimized for their
  domain — the 1.0 baseline emphasizes maturity levels and traditional
  compliance mappings (13 CSV columns); the 1.5-AI supplement uses a leaner
  shape focused on AI-specific concerns (6 columns); future supplements (1.6
  supply chain, 2.0) will profile differently again. This variability is
  intentional and the framework must support it as a feature, not paper over
  it. The CSV format makes the variability expensive: each supplement gets
  its own bespoke column layout with no shared core, and adding cross-cutting
  concerns (NIST CSF, SSDF, CMMC, SAMM, DSOMM) requires coordinated
  column-schema edits across every supplement file. A structured YAML schema
  with optional fields and per-supplement renderer profiles models the
  intentional variability cleanly while preserving a shared semantic core.
  Within any single supplement, parallel-list pairs in the CSV
  (today's `cwe_mapping;CWE-308;CWE-287` paired with
  `cwe_description;Use of Single-Factor;Improper Auth`) remain a known
  data-quality hazard regardless of the cross-supplement question.
- **Limited authoring surface.** Long-form rationale, implementation guidance,
  worked examples, and external references have nowhere natural to live in CSV
  cells. The standard's documentation today is split across narrative
  Markdown files (`How_To_Use_SPVS.md`) that drift from the controls themselves.
- **No room for richer downstream outputs.** A PDF specification document, a
  static documentation site, or AI-readable publishing formats all need
  structured per-control content the CSV cannot provide.
- **Review and merge friction.** CSV row diffs are noisy; reviewers can't
  easily diff individual control changes; merge conflicts are common when
  multiple PRs touch the same area.

## Goal

Move the canonical authoring format from CSV to per-control YAML files,
backed by a build pipeline that regenerates the existing CSVs (preserving all
external consumer URLs) and is structured to support additional output formats
as the project grows.

The MVP delivers YAML authoring + CSV generation for the 1.0 baseline
supplement. Subsequent supplements (1.5-AI, 1.6 supply chain, 2.0) follow the
same pattern. Downstream output formats (Markdown, MkDocs site, PDF,
AI-readable publishing, OSCAL/SARIF) are designed-for but not implemented in
the MVP.

## Non-Goals (MVP)

- Implementing additional output formats beyond the existing CSVs
- Populating new compliance framework mappings (NIST CSF, SSDF, CMMC, SAMM,
  DSOMM); the schema reserves slots, content is a separate community effort
- Replacing or modifying the existing Jekyll-based marketing site
- Renumbering or restructuring control IDs
- Multi-language translations of control content

## Approach: Hybrid migration with full-schema design

Three approaches were considered:

| | **Baseline-only, defer AI** | **Both supplements together** | **Hybrid (chosen)** |
|---|---|---|---|
| MVP scope | 1.0 → YAML only | 1.0 + 1.5-AI together | 1.0 → YAML; schema covers both |
| Schema validation | 1.0 columns only | Both column sets | Both column sets |
| PR shape | One small PR | One large PR | Two focused PRs |
| Risk | Schema rework when 1.5-AI joins | Review fatigue, slow alignment | Coordination across two PRs |

**Hybrid** is the chosen approach. It de-risks the maintainer alignment
conversation by keeping the MVP PR focused on the more stable 1.0 baseline,
while ensuring the schema accommodates 1.5-AI's smaller column set so PR #2
is purely additive (new YAML tree + new renderer registration, no schema
changes).

## Architecture

### Repository layout (additive — nothing existing moves in MVP)

```text
controls/
  baseline/                          # 1.0 baseline supplement
    V1/V1.1/V1.1.1-verify-mfa-enabled.yaml
    V1/V1.1/V1.1.2-centralize-identity-provider.yaml
    ...
  ai/                                # 1.5-AI supplement (added in PR #2)
    V1/V1.1/...
schema/
  control.schema.json                # JSON Schema for one control file
build/
  pyproject.toml
  uv.lock
  spvs_build/
    __init__.py
    cli.py
    loader.py
    validator.py
    model.py
    renderers/
      __init__.py                    # registry
      csv_baseline.py
      csv_ai.py                      # added in PR #2
    migrate.py
  tests/
1.5/OWASP_SPVS_1.0_-en_Requirements.csv     # generated, committed; URL unchanged
1.5/OWASP_SPVS_1.5-AI_-en_Requirements.csv  # added in PR #2
.github/workflows/
  build-controls.yml
docs/specs/
  2026-05-03-spvs-yaml-source-of-truth-design.md
```

### Filename convention

`controls/<supplement>/V<cat>/V<cat>.<sub>/V<cat>.<sub>.<n>-<slug>.yaml`

- **`<slug>`**: lowercase alphanumeric with hyphens, max 60 characters,
  regex `^[a-z][a-z0-9-]{0,59}$`
- **Source of truth for the slug is the filename**, not the YAML content; the
  validator enforces that the filename's ID prefix matches the YAML `id` field
- Initial migration auto-derives slugs from `req_description`; humans can
  rename later via standard PR

### Build flow (MVP)

```text
controls/baseline/**/*.yaml
        │
        ▼
   loader.py ──► JSON Schema validate ──► fail-fast on errors
        │
        ▼
   csv_baseline renderer ──► writes 1.5/OWASP_SPVS_1.0_-en_Requirements.csv
        │
        ▼
   CI drift-check: regenerate, `git diff --exit-code` on the CSV
```

### Key design properties

- **YAML is canonical, CSV is derived.** Maintainers and contributors author
  YAML; the CSV is committed only because external consumers link to its URL.
  The drift check enforces the relationship.
- **Renderer registry pattern.** Future Markdown, PDF, MkDocs, AI-readable,
  and OSCAL/SARIF renderers each become one file in `build/spvs_build/renderers/`.
  The loader, schema, and YAML model don't change.
- **Per-supplement renderer awareness.** The 1.0 baseline and 1.5-AI
  supplements share the same YAML schema but render different column subsets
  in their respective CSV outputs.
- **Nothing moves until rendered.** CSV output paths stay where they are
  today — preserves all external URLs, README links, and citations.

## YAML schema

### MVP-required fields

```yaml
id: V1.1.1
category:
  id: V1
  name: Plan
sub_category:
  id: V1.1
  name: Identity and Access Management
description: >
  Verify that Multi-Factor Authentication (MFA) is enabled for accessing
  developer laptops and critical systems.
level: 2                              # single integer: 1, 2, or 3
mappings:
  nist_800_53:
    items:
      - IA-2(1)
      - IA-2(2)
      - IA-2(12)
      - IA-5
  owasp_cicd:
    items:
      - CICD-SEC-2
  cwe:
    items:
      - id: CWE-308
        description: Use of Single-Factor Authentication
      - id: CWE-287
        description: Improper Authentication - Weak authentication mechanisms
metadata:
  status: active                      # active | deprecated | moved | deleted | deleted_merged_to
```

### Schema highlights

- **`level` is a single integer.** Each control belongs to exactly one
  maturity level. Cumulative semantics ("level 2 implementations include
  applicable level 1 controls") is consumer behavior, not a per-control
  attribute. Empty-level cases are tombstones (see `metadata.status`).
- **Universal `items` shape — polymorphic per framework.** Every
  `mappings.<framework>.items` is a list. Entries may be:
    - **Shorthand**: bare string when only the ID is needed
      (`"IA-2(1)"`, `CICD-SEC-2`)
    - **Full form**: object with `id` + optional `description` + optional
      `note` (used for CWE today; usable by any framework where descriptions
      add value)
  Schema validator accepts both forms. CSV renderers requiring descriptions
  for a particular framework (e.g., the `cwe_description` column) require
  full-form items for that framework only.
- **Block-style YAML enforced.** A `yamllint` config in CI rejects
  flow-style maps and inline arrays in source files, keeping diffs readable
  and contributor-friendly.

### Future-state schema (designed-in, ignored by MVP renderer)

These slots are reserved in the schema specifically so future renderer work
is purely additive — no schema migration required when they're populated.

```yaml
# Lifecycle / change tracking — replaces today's [ADDED]/[MODIFIED]/[MOVED_FROM]
# tags-prefixed-onto-description convention from CONTRIBUTING.md.
# `change_tags` is a list to support CONTRIBUTING.md's compound tags like
# "[MODIFIED, MOVED FROM x.y.z]" and "[ADDED, SPLIT FROM x.y.z]".
metadata:
  status: active                      # see status enum above
  change_tags:
    - type: MODIFIED                  # ADDED | MODIFIED | MOVED_FROM | MOVED_TO |
                                      # DELETED | DELETED_MERGED_TO | LEVEL_CHANGE | SPLIT_FROM
    - type: MOVED_FROM
      reference: V1.1.7               # the related id, when applicable
    # LEVEL_CHANGE example:
    # - type: LEVEL_CHANGE
    #   from_level: 1
    #   to_level: 2
  introduced_in: "1.0"                # release the control first appeared in
  last_modified_in: "1.5"
  moved_to: V2.3.1                    # when status: moved
  owner: "@spvs-maintainers"          # GitHub team or handle (optional)

# Long-form authoring content — feeds PDF / site / AI-readable renderers
details:
  long_description: |
    Multi-paragraph elaboration of the control beyond the short `description`.
  rationale: |
    Why this control matters; threat model context.
  implementation_guidance: |
    How to implement; tool examples; common pitfalls.
  examples:
    - title: "GitHub Actions example"
      content: |
        # YAML or code block

# External references / citations
references:
  - title: "NIST SP 800-63B"
    url: "https://pages.nist.gov/800-63-3/sp800-63b.html"
    type: standard                    # standard | research | tool | blog | rfc

# Site / renderer hints
site:
  slug: verify-mfa-enabled            # override filename-derived slug if needed
  feature_image: assets/...
  category_order: 1

# Future framework mappings — slots reserved, MVP renderer ignores them
mappings:
  nist_csf:
    items:
      - id: PR.AC-7
        description: "..."
  nist_ssdf:
    items: [...]
  cmmc:
    items: [...]
  owasp_samm:
    items: [...]
  owasp_dsomm:
    items: [...]
```

### Schema versioning

The JSON Schema's `$id` carries a version: `https://owasp.org/spvs/schemas/control/v1.json`.

- **Additive optional fields**: no version bump, no migration
- **New required fields**: minor version bump; migration script provided;
  CI grace period
- **Removed/renamed fields**: major version bump; rare; explicit
  deprecation cycle

CONTRIBUTING.md gets a "schema changes" section spelling this out so future
maintainers don't accidentally break the contract.

### Renderer contract

Each renderer declares the fields it consumes. The MVP CSV renderer consumes
only the fields its CSV columns need; everything else is a tolerated
pass-through. This is what allows future fields to land progressively without
forcing renderer rewrites.

## Build script

### Tooling

- **Python 3.11+** — modern type hints, dataclasses, ergonomic features;
  available on all GitHub Actions runners
- **`uv`** — project and dependency management; `pyproject.toml` + `uv.lock`
  committed for reproducible builds; ~5–10× faster cold install than pip in CI
- **`ruamel.yaml`** — preserves ordering, supports round-trip; matters for
  the migration tool and for deterministic diffs
- **`jsonschema`** — schema validation
- **`click`** — CLI ergonomics with subcommands
- **`pytest`** — test runner
- **`yamllint`** (dev dep) — block-style enforcement and style checks on
  `controls/**/*.yaml`; invoked separately in CI rather than from the
  `spvs_build` package
- **`ruff`** (dev dep) — Python linting and formatting; enables the `S`
  (flake8-bandit security) and `T20` (no-print) rule families
- **`mypy`** (dev dep) — strict static type checking on the `spvs_build`
  package
- **`pytest-cov`** (dev dep) — coverage gate (target: 80% minimum)

### Supply chain hardening

The build pipeline introduces executable code into the SPVS repo for the
first time. The toolchain adopts a defense-in-depth posture appropriate
for a security-focused open standard:

- **Pinned dependency versions** — every dependency in `pyproject.toml` is
  pinned to an exact version (`==`), and `uv.lock` is committed. No
  silent floating-version churn.
- **Dependency cool-down gate** — `[tool.uv] exclude-newer = "7 days"` in
  `pyproject.toml` blocks adoption of any package version published in the
  last 7 days. Defends against compromised-package-just-published attacks
  (TeamPCP, Axios npm compromise patterns) without requiring active
  vetting on every dependency update.
- **Lockfile drift gate** — CI runs `uv sync --frozen` which fails if
  `uv.lock` does not match `pyproject.toml`. No undocumented dep changes.
- **Secrets scanning** — three layers: GitHub native Secret Scanning runs
  continuously server-side on every push and scans full history (free for
  public repos); GitHub Push Protection blocks pushes that introduce secrets
  before they enter the repo (enabled in repo settings); and a local
  `gitleaks` pre-commit hook for fast developer-side feedback.
- **Conventional commits enforcement** — `commit-msg` hook validates
  commit message format; produces clean changelog/release notes downstream.
- **No-direct-commit-to-main** — pre-commit hook blocks direct commits to
  `main`; all changes flow through PRs that the CI gate validates.
- **Bandit-equivalent security linting** — Ruff's `S` (flake8-bandit) rule
  family runs in CI and pre-commit; rejects common Python security
  anti-patterns (hardcoded credentials, unsafe subprocess invocation, weak
  cryptography, etc.).
- **AI-assisted code review** — PR review pipeline includes an AI code
  reviewer and an AI security review skill
  for second-opinion validation of every
  change to the toolchain.
- **Private package mirror (optional, for future hardening)** — the
  pyproject configuration is structured to support pointing at a private
  PyPI mirror via `[[tool.uv.index]]` if maintainers want to add that
  layer later. Public PyPI plus the cool-down gate is the MVP posture.

### CLI surface

```sh
python -m spvs_build validate                  # schema + semantic validation only
python -m spvs_build build                     # regenerate all CSV outputs
python -m spvs_build build --supplement baseline   # one supplement only
python -m spvs_build check                     # build + drift check (CI mode)
python -m spvs_build migrate <csv> <out_dir>   # one-shot CSV → YAML; used once per supplement
```

### Loader contract

`load_supplement(path) -> tuple[list[Control], list[Error]]`. The loader:

1. Walks `controls/<supplement>/V*/V*.*/V*.*.*-*.yaml` deterministically
   (sorted)
2. Parses each YAML file; YAML parse errors become structured `Error` objects
   with file path + line number
3. Builds typed `Control` dataclasses from raw dicts (rejects unknown
   top-level keys with a clear message)
4. **Never raises mid-walk** — accumulates all errors and returns them.
   CLI prints all problems in one run; contributors don't play whack-a-mole.

### Validator pipeline

Three stages, each producing errors with `{file, line, code, message}`:

1. **Schema validation** (`jsonschema`) — types, required fields, enum
   values, slug regex
2. **Naming semantics** — filename ID prefix matches `id:` field, slug regex
   compliance, ID format `V<n>.<n>.<n>`
3. **Referential semantics** — `metadata.moved_to` and any
   `metadata.change_tags[].reference` point to controls that exist (or are
   themselves tombstones); no orphan moves; per-supplement uniqueness of `id`

### Renderer registry

```python
# build/spvs_build/renderers/__init__.py
RENDERERS = {
    "csv-baseline": csv_baseline.render,    # MVP
    "csv-ai":       csv_ai.render,          # PR #2
    # Future:
    # "markdown":     markdown.render,
    # "llms-txt":     llms_txt.render,
    # "mkdocs":       mkdocs.render,
    # "pdf":          pdf.render,
    # "oscal":        oscal.render,
    # "sarif":        sarif.render,
}
```

Each renderer is `render(controls: list[Control], out_path: Path) -> None`.
Pure function, no global state. Adding a new output format is a one-file
change plus an entry here.

### Determinism

The CSV renderer:

- Sorts controls by `id` (lexicographic on `V<int>.<int>.<int>`, with numeric
  component handling)
- Emits CSV with explicit dialect: `\n` line endings, `csv.QUOTE_MINIMAL`,
  no trailing newline drift
- Does NOT emit a generated-on timestamp or any non-content field

Two consecutive `build` runs produce byte-identical CSVs. The CI drift check
(`build && git diff --exit-code`) is reliable.

### Error reporting

Example output:

```text
controls/baseline/V1/V1.1/V1.1.1-verify-mfa-enabled.yaml:7
  E001 [schema] field `level` must be 1, 2, or 3 (got: "two")

controls/baseline/V1/V1.1/V1.1.7-tombstone.yaml:3
  E102 [referential] metadata.moved_to "V2.3.99" does not match any control

3 errors in 2 files. See https://owasp.org/spvs/contributing#error-codes
```

Each error has a stable code; CONTRIBUTING.md gets an error-codes section
linking each to a fix recipe.

## Migration plan

### MVP migration (PR #1, baseline supplement)

A one-shot script (`python -m spvs_build migrate`) that:

1. Reads the existing CSV using its known column shape
2. For each data row (skipping placeholder `-,-,-,...` rows):
   - Parses the row into a `Control` dataclass
   - Auto-derives a slug from `req_description` (lowercase, strip stopwords,
     hyphen-join, trim to 60 chars; collision detection within sub-category)
   - Splits `cwe_mapping` (`;`-separated) and `cwe_description` (`;`-separated)
     into paired `mappings.cwe.items[]`. **Fails loudly if those two fields
     have unequal counts** — surfaces existing data quality bugs as part of
     the migration, doesn't paper over them.
   - Splits `NIST` and `OWASP_CICD_Risk` into
     `mappings.nist_800_53.items[]` and `mappings.owasp_cicd.items[]`
   - Detects and strips `[ADDED]`, `[MODIFIED]`, `[MOVED FROM x.y.z]`, etc.
     from `req_description`; converts to structured `metadata.change_tags`
   - Determines `level` from which of the three level columns has `X`
3. Placeholder rows (`req_id == "-"`) are *skipped*: the original CSV uses
   them to reserve deleted/moved id numbers, but the YAML model does not
   need them. The id sequence is allowed to have gaps. (A future supplement
   that needs explicit deletion semantics could introduce tombstone YAML
   files via `metadata.status: deleted | moved | deleted_merged_to` —
   not part of MVP.)
4. Writes one YAML file per active control to
   `controls/baseline/V<cat>/V<sub>/V<id>-<slug>.yaml` using `ruamel.yaml`
   for stable formatting

### Migration PR shape

PR #1 (the MVP) is one large additive PR containing:

- `build/` directory (entire toolchain)
- `schema/control.schema.json`
- `controls/baseline/` — full YAML tree (~115 files)
- `.github/workflows/build-controls.yml` — CI: validate + drift-check
- `.pre-commit-config.yaml` — opt-in local hooks (contributors run
  `pre-commit install` to enable; not required for PR acceptance)
- Regenerated `1.5/OWASP_SPVS_1.0_-en_Requirements.csv` — **byte-identical**
  to the current file (proves round-trip)
- `CONTRIBUTING.md` updates: new authoring path is YAML; CSV is generated;
  how to run the local validator; how to enable pre-commit hooks
- Commit history within the PR sequenced as logical units (toolchain →
  schema → migrated YAML → CI gate → pre-commit → docs)

**Critical pre-merge gate:** the regenerated CSV must match the current
committed CSV byte-for-byte. If it doesn't, the migration is wrong somewhere.
The drift-check job in CI proves this every time the PR is updated.

### Migration risks and mitigations

| Risk | Mitigation |
|---|---|
| Slug collisions within a sub-category | Migration tool detects collisions and appends an incremental numeric suffix (`-2`, `-3`, ...) to the colliding slug; if the slug exhausts the 60-char limit (extreme edge case), falls back to `control-<n>`. Slug derivation reserves space for the suffix each iteration so the loop always makes progress. All collisions are surfaced in the migrated YAML filenames for human review before commit. |
| Existing CSV data quality bugs (mismatched CWE id/description counts) | Tool fails loudly with file/row references; data is fixed in CSV first, then migration re-run |
| Lossy round-trip | Drift-check in CI catches this; PR cannot merge |
| Reviewer fatigue on a 115-file PR | PR is reviewed primarily for the build/schema/CI portions; YAML files reviewed by spot-check + the byte-identical CSV check (which proves no semantic change) |
| Future contributor unsure where to author after migration | CONTRIBUTING.md updated *in the same PR*; old CSV-editing instructions replaced |
| 1.5-AI migration in PR #2 reveals schema gaps | Schema designed with optional fields specifically anticipating the AI supplement's smaller column set; PR #2 is additive (new renderer, new YAML tree), not schema-modifying |

### Rollback path

If maintainers reject the model after merge, reverting is straightforward:

- The CSV was preserved unchanged (drift-check guaranteed it)
- A revert PR removes `build/`, `schema/`, `controls/`, and the CI workflow
- No external-consumer breakage at any point in the workflow

## CI/CD flow

### Workflow

`.github/workflows/build-controls.yml`, triggered on:

- PRs that touch `controls/**`, `schema/**`, `build/**`, or the generated CSVs
- Pushes to `main` (defense-in-depth)

### Job: `validate-and-build`

```text
1. Checkout (fetch-depth: 1)
2. Install uv (single curl-based step, ~2s)
3. cd build && uv sync --frozen          # verify lockfile + install deps
4. uv run python -m spvs_build validate  # schema + semantic + referential errors
5. uv run python -m spvs_build check     # build all renderers, then `git diff --exit-code`
6. yamllint controls/                    # style enforcement on block-form YAML
```

Total runtime target: **under 30 seconds cold**.

### Branch protection

`main` requires `validate-and-build / validate-and-build` as a status check.
Drift errors block merge. Schema/semantic/referential errors block merge.

### Drift-detected UX

When a contributor edits YAML but forgets to regenerate the CSV, the `check`
step fails with a tailored message via GitHub Actions annotations:

```text
1.5/OWASP_SPVS_1.0_-en_Requirements.csv:#L42
::error::CSV drift detected. The committed CSV does not match what your YAML
would produce. Run this locally and commit the result:

  cd build && uv run python -m spvs_build build

Then `git add` the regenerated CSV and push.
```

**Rationale for contributor-regenerates-locally vs. CI-bot-regenerates:**
predictable (what the contributor sees in their PR is what lands), no bot-push
permissions to manage, trivially scriptable into a pre-commit hook.

### Pre-commit config (ships in PR #1, opt-in for contributors)

A `.pre-commit-config.yaml` at the repo root provides local hooks for
contributors who want them; the file ships with the MVP. Hooks are
opt-in — contributors must run `pre-commit install` once after cloning.
CONTRIBUTING.md documents the setup. Catches schema/semantic/drift issues
locally before push instead of waiting for CI.

## Future-state roadmap

The MVP locks in three durable interfaces that all future work plugs into
without renegotiation:

1. **YAML schema** with reserved-but-optional sections (`details`,
   `references`, `site`, future framework mappings)
2. **Renderer registry** with a uniform `(controls, out_path) → None` signature
3. **Loader/validator** that produces typed `Control` objects regardless of
   what consumes them

Anything added later is a new file in `build/spvs_build/renderers/` plus an
entry in the registry.

### Phase 1 — MVP (this design)

- Baseline supplement migration to YAML (PR #1)
- 1.5-AI supplement migration to YAML (PR #2, follow-on)
- CSV renderers preserve existing consumer URLs
- CI drift-check enforces YAML-CSV consistency

### Phase 2 — Markdown + AI-readable publishing + AI skills (bundled milestone)

**Markdown renderer** — emits one `.md` per control plus an index page;
foundation for all subsequent rendering.

**AI-readable publishing** — bundled with Markdown to deliver a coordinated
"AI-native security standard" milestone. Inspired by:

- [llmstxt.org](https://llmstxt.org/) — the proposed `llms.txt` standard
- [Cloudflare Docs for Agents](https://developers.cloudflare.com/docs-for-agents/)
  — "Agent Score" measure of agent-readability
- [Upstash Context7](https://github.com/upstash/context7) — agent-facing
  retrieval for library docs

**Outputs (static publishing on GitHub Pages):**

- `/llms.txt` — unified project-root manifest listing all currently
  authoritative supplements (1.0 baseline, 1.5-AI, etc.) as enumerated
  sections
- `/llms-full.txt` — full concatenated content across all supplements for
  single-shot context retrieval
- `/<supplement>/llms-full.txt` — per-supplement full content
- `/<supplement>/V<id>.md` — per-control Markdown files with structured
  frontmatter (id, level, mappings, supplement scope) for agent navigation
- Stable URLs and section anchors so retrievals can deep-link

**Consumer use cases (broad ecosystem positioning):**

- Pipeline-building / pipeline-auditing agents that consult SPVS as policy
- Compliance copilots ("are we SPVS-compliant?")
- Code review / PR assistants that flag SPVS violations in proposed changes
- Generic LLM context retrieval (Cursor, Claude, ChatGPT, Continue, Cody)
- Authoring assistants for SPVS contributors

**AI skills for practitioners and maintainers** — packaged Claude Skills /
agent skills that consume the AI-readable publishing layer and provide
opinionated, task-oriented entry points:

- *Practitioner skills* — "audit my GitHub Actions workflow against SPVS L2",
  "explain what V3.4 controls require for my SBOM workflow", "find SPVS
  controls applicable to my supply chain incident". Skills wrap the standard
  in actionable workflows.
- *Maintainer skills* — "draft a control proposal in SPVS YAML", "review this
  PR for SPVS conventions", "find gaps between the baseline and AI supplements",
  "validate change tags follow the standard". Reduces friction in maintainer
  workflows without altering the standard itself.

These skills are versioned and enhanced as subsequent phases ship — Phase 3
adds richer site-driven retrieval, Phase 6 enables OSCAL-aware skills,
Phase 7 enables operational verification skills. Phase 2 ships the
foundational set.

### Phase 3 — Static site (MkDocs Material)

`build/spvs_build/renderers/mkdocs.py` generates an `mkdocs.yml` + content
tree, then optionally invokes `mkdocs build`. Why MkDocs Material:

- Used by several adjacent OWASP projects and security standards
- First-class navigation generation, search, dark mode, versioning (matches
  SPVS's release-versioned model)
- Renders the same Markdown the standalone Markdown renderer produces

Output: `site/` directory; published to GitHub Pages on tagged releases.

### Phase 4 — PDF specification document

`build/spvs_build/renderers/pdf.py` uses WeasyPrint to render the same
Markdown→HTML pipeline (with print stylesheets) into a publication-quality
PDF. Output: `dist/SPVS-<version>-<supplement>.pdf`, attached as a release
asset. Shares templates with the static site renderer; print-specific CSS
handles page breaks, headers/footers, and table of contents.

### Phase 5 — MCP server reference implementation (AI-readable extension)

A self-hostable MCP (Model Context Protocol) server in the repo, using the
Python `mcp` SDK. Runs locally or in Docker. SPVS does not host it; users and
organizations run it themselves. Project ships the reference implementation
but commits to no SLA. Documents the schema-to-MCP mapping authoritatively
so any agent that speaks MCP can query SPVS controls.

### Phase 6 — Machine-readable interchange formats (JSON + OSCAL Catalog)

The other phases (Markdown, MkDocs, PDF, AI-readable) all serve *human
reading* — directly or via LLM intermediaries. Phase 6 serves *machine
consumption with no human in the loop*: dashboards, policy engines,
regulatory tooling, federal compliance platforms. Different audience,
different format expectations.

**JSON (full schema dump)**

YAML is excellent for authoring, mediocre for runtime consumption. Every
web tool, dashboard, BI platform, and no-code integration speaks JSON
natively. CSV serves humans glancing at a spreadsheet; JSON serves
programs querying structured data.

Outcomes:

- **Programmatic APIs without infrastructure.** A static `controls.json`
  at a stable URL is sufficient; consumers don't need a Python runtime to
  read SPVS data.
- **JSONPath / `jq` queries** unlock filtering use cases ("all L1 controls
  that map to NIST AC-2") without custom tooling.
- **Web and JavaScript tooling.** Browser extensions, dashboards, custom
  Slack bots can consume SPVS data with `fetch()`.
- **Schema discoverability.** A JSON Schema accompanies the data so
  consumers can validate their own integrations against authoritative shape.

**OSCAL Catalog (the strategically significant output)**

OSCAL is NIST's emerging standard for representing control catalogs. NIST
800-53 ships as OSCAL. FedRAMP profiles 800-53 in OSCAL. DOD, civilian
agencies, and an increasing share of GRC/compliance tooling are converging
on OSCAL as the *machine-readable lingua franca for controls*. SPVS's
planned NIST CSF, SSDF, and CMMC mappings (reserved schema slots in MVP)
make OSCAL Catalog publication the natural way to expose them at scale.

Outcomes:

- **Federal interoperability.** SPVS becomes publishable inside the same
  ecosystem GovCloud, FedRAMP, and CMMC tooling already speaks.
  Organizations doing federal work can include SPVS controls in their
  OSCAL-based System Security Plans without manual transcription.
- **Automated cross-walks.** "How does SPVS V1.1.1 relate to 800-53 IA-2?"
  stops being a manual mapping exercise. Tools that consume both OSCAL
  catalogs answer it programmatically.
- **Positioning alongside sister standards.** OWASP ASVS is moving toward
  OSCAL. NIST SSDF is OSCAL. Being in OSCAL puts SPVS at the same
  data-model table as the standards it cites — and elevates SPVS from a
  community spec into the federal-grade catalog ecosystem.

Each output is a renderer module of <200 LOC. None require schema changes.

**SARIF was considered and dropped.** SARIF (Static Analysis Results
Interchange Format) is the natural format for *tool findings* that
reference SPVS control IDs, not a publishing format for the standard
itself. Tools that produce SARIF can reference SPVS controls by ID using
the JSON output above; no SPVS-specific SARIF artifact is needed.

### Phase 7 — Forward-looking: ecosystem tooling that enables operational adoption

The renderers in Phases 1–6 publish the standard in formats consumers
read or load. The artifacts in this phase are *different in kind* — they
are **implementation tooling that helps organizations operationalize SPVS
in their own pipelines and compliance programs**. These may be better
stewarded as separate community efforts (working groups, sibling repos,
or OWASP-flag projects) rather than as built-in renderers in the core
build pipeline. Listed here for planning awareness, not as commitments
of the core project.

**OSCAL Profile reference set**

Beyond the OSCAL Catalog (the controls themselves), publish reference
OSCAL Profiles for common adoption shapes. The "How to Use SPVS" guide
already sketches these scenarios:

- "SPVS L1 baseline for startups"
- "SPVS L2 for SaaS with regulated customers"
- "SPVS L3 for federal-adjacent enterprises"

OSCAL Profile is the machine-readable encoding of them. Organizations
adopt a named profile rather than re-mapping levels for every engagement.

**Operational verification toolkit (OPA/Rego + GRC integration patterns)**

A mixed-modality toolkit for operationalizing SPVS verification across
the full control set, not just the directly file-inspectable subset.
Modern GRC engineering and continuous compliance practices make the
governance and process controls evidence-able through API integration
with systems organizations already operate.

- **Direct technical checks via OPA / Rego.** Pre-baked policy-as-code
  rules for SPVS controls that map cleanly to file or configuration
  inspection (e.g., V1.5.2 "verify .gitignore is present" maps to a
  trivial OPA rule). Roughly the 30–40% of controls that are purely
  artifact-inspectable. Published as a Conftest/OPA bundle.

- **GRC and continuous compliance integration patterns.** The remaining
  60–70% — governance, process, training, audit cadence — become
  *evidence-able* through API integration with the systems
  organizations already use for GRC and continuous compliance. Example
  integration patterns:

    - Documented policies → Confluence / SharePoint / Notion API queries
    - Quarterly access audits → Okta / Auth0 / Azure AD audit log queries
    - Security training completion → KnowBe4 / SANS / internal LMS
      completion records
    - Incident response playbook exercises → PagerDuty / Opsgenie
      tabletop exercise tracking
    - Endpoint protection updates → Jamf / Intune / Kandji MDM compliance
      reports
    - Pipeline tool inventory → ServiceNow / Atlassian Jira asset records

  Reference implementations for these patterns (Steampipe queries,
  Cloud Custodian policies, evidence-collector recipes in the style of
  Drata / Vanta / Tugboat Logic) make the path from "this control says
  verify X" to "here is an automated test for X in our environment"
  approachable for teams without a dedicated GRC engineering practice.

- **AI-assisted substance verification (emerging modality).** Modern
  AI-based GRC and continuous compliance tools are moving beyond boolean
  existence checks ("is the policy present?") toward *substance
  evaluation* ("does this policy actually address the control's intent;
  is this audit log sufficient evidence; does this training cover the
  required scope?"). The integration patterns above provide the
  evidence-collection pipelines; AI evaluators operate over those
  pipelines. Examples:

    - Policy documents queried from Confluence/Notion are evaluated
      against the control's required elements rather than only
      confirmed-to-exist
    - Audit log entries are inspected for sufficiency of detail and
      appropriate cadence, not merely counted
    - Training completion records are cross-referenced against
      role-based requirements with content-aware filtering
    - Incident response exercise notes are evaluated for genuine
      adversarial rigor, not just acknowledgment

  The implementation test examples in this phase do *double duty*: they
  are ready-made evidence pipelines AI verifiers can plug into, *and*
  test fixtures and benchmarks for AI verification approaches across
  the full SPVS control set.

- **Implementation test examples across approaches.** A reference
  catalog showing how the same control can be verified using OPA, GRC
  platform integrations, AI substance evaluators, or custom tooling
  (Steampipe, Cloud Custodian, OSCAL Assessment Plan), depending on
  the consumer's existing stack and maturity. Choose-your-own-adventure
  rather than a single prescribed implementation.

Outcomes:

- Organizations apply SPVS controls in CI and continuous compliance
  pipelines without writing rules and integrations from scratch.
- A canonical reference implementation reduces interpretation drift
  between organizations claiming "SPVS-compliant".
- Lowers the GRC engineering barrier for small and mid-size teams that
  cannot staff dedicated compliance automation programs — democratizes
  the kind of continuous compliance posture historically only feasible
  for enterprise SOC 2 / ISO 27001 / FedRAMP programs.
- Aligns SPVS adoption with the GRC-engineering and continuous-compliance
  movement gaining traction across organization sizes.
- Provides scaffolding for the emerging AI-GRC tooling space:
  substance-evaluating AI verifiers can use SPVS as a benchmark surface
  and the Phase 7 evidence pipelines as ready-made integrations.
- Closes a tight consistency loop: SPVS contains AI-specific controls
  (1.5-AI) and the operational tooling that helps organizations adopt
  SPVS can use AI as a verification modality. The standard is
  simultaneously *authored for the AI era and evaluated by AI tooling*.

Scope is intentionally broad because the goal is *enabling adoption in
operational ecosystems*, not authoring the standard itself. This is the
strongest reason for stewarding it as a separate community working
group or sibling project.

**Why these are positioned as forward-looking and possibly external**

Both artifacts depend on *opinionated interpretation* of how SPVS is
adopted in practice — what "L1 baseline" means for a startup, what
"verify a control is implemented" means for an OPA rule. These are
contestable claims that benefit from broad community input rather than
maintainer-defined defaults baked into the core repo. A separate working
group or sibling project gives space for that conversation without
gating SPVS standard releases on the timing of operational tooling.

### Future framework mappings (NIST CSF, SSDF, CMMC, SAMM, DSOMM)

The schema reserved these slots in MVP. Populating them is purely a content
effort (community contributions), not a code change. New mapping entries
appear in YAML files under `mappings.nist_csf.items[]`, etc. Existing
renderers ignore them until a renderer/column is updated to consume them.
A community could maintain a single mapping framework as their contribution
focus (e.g., "the CMMC mapping working group") without coordinating with
anyone updating the controls themselves.

### Out of long-term scope

- Multi-language translations of `description` and `details.*` — possible
  eventually but requires a translation strategy. Deliberate future project.
- Per-organization-overlay controls (company-specific tweaks of SPVS) —
  possible via a separate `overlays/` tree but explicitly out of scope for
  the standard itself.
- Live integration with vulnerability databases for CWE descriptions — opens
  an external-dependency can. Out of scope.

## Open questions

None blocking MVP. To revisit during implementation:

- Final slug auto-derivation algorithm (stopword list, n-gram fallback rules)
  — refined during migration testing
- Specific JSON Schema `$id` URL pattern (likely `https://owasp.org/spvs/schemas/...`)
  — to be confirmed with OWASP project page maintainers

## Decision log

| Decision | Choice | Rationale |
|---|---|---|
| Multiple supplements model | Parallel supplements (separate top-level modules per release tier) | Matches actual project release pattern; avoids cross-namespace renumbering |
| CSV role going forward | Generated, committed alongside YAML, with CI drift check | Lowest-risk migration; zero break for current CSV consumers |
| Build runtime | Python with `uv` | OWASP ASVS precedent; broad library ecosystem; alignment with audience expertise |
| YAML mapping shape | Structured `mappings.<framework>.items` block-style list | Fixes today's parallel-list alignment fragility; forward-compatible for per-item metadata |
| `level` field shape | Single integer | Matches actual data — each control belongs to exactly one maturity level |
| Migration approach | Hybrid (full schema, 1.0 first, 1.5-AI follows) | De-risks maintainer alignment; smaller focused MVP PR |
| AI-readable phasing | Bundled with Markdown renderer (Phase 2) | Markdown is the foundation; combined milestone is a stronger story |
| AI-readable surface | Static first; self-hostable MCP server later | Zero-ops for OWASP project; MCP follow-on is a content-positioning upgrade |
| AI-readable URL structure | Unified `/llms.txt` at project root | Single discovery point; supplements as internal taxonomy, not external versioning |
| Pre-commit config in MVP | Ship `.pre-commit-config.yaml` in PR #1 | Lower contributor friction from day one; opt-in via `pre-commit install`; catches issues locally instead of in CI |
