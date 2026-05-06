# SPVS YAML Source-of-Truth — Business Case

**Status:** Draft for maintainer alignment
**Author:** Evan Borysko
**Date:** 2026-05-03
**Format:** Working-backwards (announcement → FAQ → risks/metrics/ask)
**Companion documents:**
- Design spec: [`2026-05-03-spvs-yaml-source-of-truth-design.md`](2026-05-03-spvs-yaml-source-of-truth-design.md)
- Implementation plan: [`2026-05-03-spvs-yaml-source-of-truth-plan.md`](2026-05-03-spvs-yaml-source-of-truth-plan.md)

---

## The Announcement

> *Written as if the change has shipped. Intended to anchor maintainer alignment in the future-state experience, not the implementation details.*

### SPVS Adopts YAML Source-of-Truth — Same CSV, Cleaner Authoring, Multi-Format Future

**The OWASP SPVS project today announces a structural change in how the standard is authored and published.** Beginning with this release, SPVS controls are written as per-control YAML files, validated by a JSON Schema, and rendered to the existing CSVs by a Python build pipeline. The CSV files at their canonical URLs are preserved unchanged — every external link, citation, and downstream integration continues to work without modification. Behind that compatibility, SPVS gains a foundation for richer outputs (Markdown, MkDocs site, PDF specification, AI-readable publishing, OSCAL Catalog) and an authoring experience aligned with how modern open security standards are maintained.

#### What changes for contributors

Adding or modifying a control is now editing a single, self-contained YAML file with a clear schema. Reviewers see a focused diff — one control, one file, no parallel CSV columns to mentally align. Filenames carry a short slug (`V1.1.1-verify-mfa-enabled.yaml`) so directory browsing tells the contributor what each file is about at a glance. The build pipeline regenerates the CSV automatically. CI gates each PR with a drift check that guarantees the YAML and CSV stay in sync. Contributors who want it can install pre-commit hooks to catch validation errors locally before pushing — opt-in, not required.

Compound change tags from CONTRIBUTING.md (`[MODIFIED, MOVED FROM x.y.z]`, `[ADDED, SPLIT FROM x.y.z]`) are now structured metadata fields, queryable by tooling and immune to typo-induced parsing errors. Tombstones for deleted or moved controls are first-class YAML files (`metadata.status: deleted | moved | deleted_merged_to`) — the migration tool synthesizes one per placeholder CSV row, and the renderer emits each tombstone back as the canonical `-,-,-,...` placeholder row, preserving byte-alignment with previous CSV consumers. Referential validation catches dangling `moved_to` pointers before merge.

#### What changes for consumers

Nothing breaks. The CSV at `github.com/OWASP/www-project-spvs/blob/main/1.5/OWASP_SPVS_1.0_-en_Requirements.csv` stays at the same URL with byte-identical content. Existing scripts, dashboards, citations, README links, and external documentation continue to work without modification.

New machine-readable outputs follow as renderers ship — each as its own opt-in milestone, not a single big commitment:

- **Markdown** + **AI-readable publishing** (`/llms.txt`, `/llms-full.txt`, per-control `.md`) + **packaged AI skills** for SPVS practitioners ("audit my GitHub Actions workflow against SPVS L2") and maintainers ("draft a control proposal in SPVS YAML") — bundled milestone making SPVS natively consumable by LLM agents, copilots, retrieval tools (Cursor, Claude, Continue, Context7-style indexers), and skill-based assistants.
- **Static documentation site** via MkDocs Material — the same model OWASP ASVS, sister projects, and federal control catalogs use.
- **PDF specification document** — publication-quality, generated from the same templates as the site.
- **OSCAL Catalog** — positions SPVS in the federal control-catalog ecosystem alongside NIST 800-53, FedRAMP, and CMMC, enabling automated cross-walks and SSP integration.

#### The strategic frame

SPVS now positions where modern security standards are heading: **authored as structured data, published in multiple formats from a single source, and intentionally readable by humans, machines, and AI tools alike.** The standard simultaneously contains AI-specific controls (1.5-AI) and is operationally evaluable by AI verification tooling — closing a satisfying loop between AI-as-subject and AI-as-tool in pipeline security.

The migration is one additive PR, byte-identically reversible, and unlocks every roadmap item the project has been quietly wanting for a year.

---

## Frequently Asked Questions

### For maintainers

**Q: What does this change for me when reviewing a PR?**
A control change is now a single YAML file diff. No more reading 13 columns across a CSV row to understand what changed. The CI's drift check confirms the regenerated CSV matches the committed one — if it does, the YAML faithfully represents the intended controls. Reviewers focus on the YAML; the CSV is bookkeeping the build pipeline handles.

**Q: What if I prefer the CSV format?**
It's still there. Authored from YAML, regenerated on every change, identical to what it is today. External consumers see no difference. The shift is in the authoring surface, not the publishing surface.

**Q: Why now, before 1.6 and 2.0?**
Restructuring the source-of-truth gets harder as more controls land. 1.0 has 115 controls; 2.0 will add substantially more. Migrating the smaller, stable 1.0 baseline now is cheaper than migrating a larger, less-settled 2.0 catalog later, and gives the framework time to mature before 2.0 freeze in October 2026.

**Q: What's the migration risk?**
The migration PR has a critical pre-merge gate: the regenerated CSV must be byte-identical to the current committed CSV. If the migration is wrong anywhere, CI catches it. If the maintainers reject the model after merge, reverting is straightforward — the CSV is untouched, and the build infrastructure can be deleted in a single revert PR with zero recovery work.

**Q: What's the long-term commitment?**
Small. The build pipeline is ~1500 lines of Python with five popular dependencies, managed by `uv`. No external services, no hosted infrastructure, no ongoing operational cost. A maintainer who knows Python can debug the entire pipeline in an afternoon. New output formats ship as additional renderer modules — single-file additions to a registry — without touching the core.

**Q: Does this commit us to all the future-phase outputs (PDF, AI-readable, OSCAL)?**
No. Phase 1 ships YAML + CSV. Each subsequent renderer is its own opt-in milestone, decided independently by the maintainers. The architecture supports them; the core project doesn't have to ship them on any timeline.

**Q: Who owns this after PR #1 merges?**
The toolchain lives in the same repo as the standard. Anyone with merge rights can patch it. The migration tool is one-shot and can be deleted from the repo after both supplements have migrated, leaving only the build pipeline (loader, validator, renderer registry, CLI) — small, focused, and documented.

### For contributors

**Q: How do I add a new control?**
Create a YAML file under `controls/baseline/V<cat>/V<sub>/V<id>-<short-slug>.yaml`. Use an adjacent control as a template. Run `python -m spvs_build build` to regenerate the CSV. Commit both. Open a PR. CONTRIBUTING.md has the step-by-step.

**Q: How do compound change tags work in YAML?**
A list of structured entries under `metadata.change_tags`. `[MODIFIED, MOVED FROM V1.1.7]` becomes two list entries: `{type: MODIFIED}` and `{type: MOVED_FROM, reference: V1.1.7}`. The migration tool extracts existing change tags from CSV descriptions automatically. No reformatting work falls on existing contributors.

**Q: Do I need to install Python and uv to contribute?**
For control changes only, no — YAML edits in any text editor work. To run the build/validate locally before pushing (which the optional pre-commit hooks do), you need Python 3.11+ and `uv`. Both are quick to install; CONTRIBUTING.md has the one-liner.

**Q: What if my YAML is malformed?**
The validator catches it locally (if you use the optional pre-commit hooks) or in CI. Errors include the file path, line number, error code, and a fix-recipe link. The validator never raises on the first error — it accumulates all problems in one run so contributors don't play whack-a-mole.

### For consumers

**Q: Will the existing CSV URLs still work?**
Yes. The CSV stays at its current GitHub raw URL with byte-identical content.

**Q: Can I now consume SPVS as JSON / OSCAL / PDF?**
Not yet. Phase 1 ships YAML and CSV. Subsequent phases add Markdown, MkDocs Material site, PDF, AI-readable publishing (`/llms.txt`), and OSCAL Catalog. Each is a separate maintainer decision and milestone.

**Q: How do I track when each future format ships?**
The implementation plan and roadmap live in the repo at `docs/specs/`. Each milestone is its own PR with a clear scope statement. The design spec's "Future-state roadmap" section enumerates the seven phases.

**Q: Is there an MCP server or agent integration?**
Phase 2 (bundled with Markdown) adds static AI-readable publishing — `/llms.txt` plus per-control `.md` files — which Cursor, Claude, ChatGPT, Continue, Context7, and any `llms.txt`-aware tool can consume. A self-hostable MCP reference implementation is on the roadmap as a later phase, with no project-hosted infrastructure commitment.

---

## Risks, Success Metrics, and the Ask

### What could go wrong

| Risk | Mitigation |
|---|---|
| **Existing CSV data quality issue surfaces during migration** (e.g., mismatched CWE id/description count). | The migration tool fails loudly with file/row references rather than silently corrupting the YAML. Fix the source CSV, re-run the migration. Surfaces real bugs without papering over them. |
| **Reviewer fatigue on the migration PR** (~115 YAML files, plus toolchain, plus CI). | The byte-identical CSV check proves no semantic change. Reviewers focus on the build/schema/CI portions; YAML files reviewed by spot-check. Commit history within the PR is sequenced (toolchain → schema → migrated YAML → CI → docs) so reviewers can move section by section. |
| **Schema rigidity for future supplements**. | Additive optional fields don't bump the schema version. The 1.5-AI supplement (PR #2) is purely additive — a new renderer, a new YAML tree, no schema changes. The schema's reserved slots (`details`, `references`, `site`, future framework mappings) are designed-in specifically to absorb forward additions. |
| **Toolchain abandonment** if the contributor walks away. | Small surface (one Python package, popular deps). Public OWASP precedent (ASVS uses the same pattern). Explicit revert path makes "go back to CSV" a one-PR operation, not a recovery project. |
| **External consumer breakage** from the change. | None expected. CSV URLs are byte-stable. README links unchanged. The PR explicitly forbids merging if the CSV regeneration produces any byte-level difference. |

### Success metrics — 90 days post-merge

- **Contribution velocity stable or improving.** Time-to-merge for control PRs and PR review duration trend stable. Schema validator and CI drift check catch issues earlier than human review.
- **Zero CWE-mapping data quality bugs introduced** in new contributions. The schema makes the parallel-list misalignment class of error impossible.
- **Schema flexibility validated.** PR #2 (1.5-AI supplement) ships without schema modifications, only renderer additions.
- **Adoption signal.** At least one downstream consumer — community member, internal tool, or sister OWASP project — integrates with the YAML or generated JSON output.

### Success metrics — 12 months post-merge

- **At least two output formats beyond CSV ship.** Typically Markdown + AI-readable (`/llms.txt`), per the bundled Phase 2 milestone — the most natural next step.
- **OSCAL Catalog publication scoped or shipped.** Positions SPVS in the federal compliance ecosystem alongside its sister standards.
- **NIST CSF, SSDF, or CMMC mapping starts populating.** Validates that the schema's reserved framework slots are usable in practice.
- **Contributor base broadens.** Lower friction for first-time control authors (one file, clear schema, fast feedback) translates to more sustained community contribution.

### What this 3-pager is asking for

1. **Read the design spec** ([`2026-05-03-spvs-yaml-source-of-truth-design.md`](2026-05-03-spvs-yaml-source-of-truth-design.md)). It's structured to be skimmable: Problem → Approach → Architecture → Schema → Build → Migration → CI → Roadmap → Decision Log.
2. **Provide directional input on Phase 1 specifically:** parallel-supplements model, generated CSV preserved, Python/uv toolchain, hybrid migration approach. Push back on anything that feels wrong before the migration PR opens.
3. **Block on substantive concerns; ratify on the rest.** The spec is detailed precisely so the conversation can focus on the few decisions that matter for project direction, not implementation minutiae.
4. **Once aligned, the migration PR opens.** It's reversible, additively scoped, and the byte-identical CSV check makes it provably correct before merge.

### What this 3-pager is *not* asking for

- A commitment to any future-phase output (PDF, MkDocs site, AI-readable, OSCAL, MCP server, OPA tooling). Each is a separate go/no-go decision later.
- A change to the existing release cadence. October stays October.
- Any infrastructure hosting commitment. Phase 1 has zero ongoing operational cost. AI-readable publishing in Phase 2 is static GitHub Pages content. The MCP server, if it ships in a later phase, is self-hostable by users — not project-operated.
- A timeline. The maintainers set the merge timing.

### The bet

SPVS's value increases as it becomes more *structurally readable* — by humans, by tools, by AI. The CSV format got the standard to where it is today; YAML lets it go further without breaking what's there. The cost is one additive, reversible PR. The upside is the ability to publish SPVS in every format the next decade of security tooling, compliance automation, and AI-native pipelines will expect.

---

*End of 3-pager. Companion documents (design spec and implementation plan) provide the technical detail; this document is intended to anchor the alignment conversation.*
