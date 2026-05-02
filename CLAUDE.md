# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Local Development

This is a Jekyll site hosted on GitHub Pages using the OWASP shared remote theme (`owasp/www--site-theme@main`).

```sh
bundle install
bundle exec jekyll serve
```

The site is then available at `http://localhost:4000`. The `_config.yml` sets the remote theme; there are no local layouts or includes to override.

## Repository Structure

The primary artifact is the requirements CSV in `1.5/`. The Jekyll site (`index.md`, `articles/`, `assets/`) is a presentation layer on top of that content.

- `1.5/OWASP_SPVS_1.0_-en_Requirements.csv` — canonical requirements for v1.0 (Oct 2025)
- `1.5/OWASP_SPVS_1.5-AI_-en_Requirements.csv` — v1.5 additions covering AI pipeline security
- `1.5/OWASP_SPVS_1.0_Categories_Overview.md` — authoritative reference for valid category IDs, sub-category IDs, and column semantics

## CSV Schema

All requirement changes happen in the CSV. The columns are:

| Column | Notes |
|---|---|
| `category_id` | V1–V5 (Plan, Develop, Integrate, Release, Operate) |
| `category_name` | Must match category_id exactly |
| `sub-category_id` | Format `V#.#` — first digit must match category_id |
| `sub-category_name` | Must use names listed in `Categories_Overview.md` |
| `req_id` | Format `V#.#.#` — must be unique and sequential within its sub-category |
| `req_description` | Full verifiable statement (no `req_name` column exists in the current CSV) |
| `level 1` / `level 2` / `level 3` | Mark with `X`; levels are cumulative (L2 includes L1, L3 includes L2) |
| `NIST` | NIST SP 800-53 identifiers, comma-separated |
| `OWASP_CICD_Risk` | OWASP CI/CD Top 10 identifiers (e.g., `CICD-SEC-1`) |
| `cwe_mapping` | CWE identifiers, semicolon-separated |
| `cwe_description` | Short CWE title(s) aligned to `cwe_mapping`, semicolon-separated |

## Contributing Rules

**Adding a control:** Append to the end of the relevant sub-category. Do not insert mid-list.

**Deleting or moving a control:** Keep a placeholder row at the original `req_id` — never reuse a number. Use change tags in `req_description`:

| Tag | When to use |
|---|---|
| `[ADDED]` | New requirement at end of sub-category |
| `[ADDED, SPLIT FROM x.y.z]` | Split from an existing requirement |
| `[MODIFIED]` | Description changed |
| `[MOVED FROM x.y.z]` | Moved, not modified |
| `[MODIFIED, MOVED FROM x.y.z]` | Both changed and moved |
| `[MOVED TO x.y.z]` | Placeholder where control used to live |
| `[DELETED]` | Placeholder for a removed control |
| `[DELETED, MERGED TO x.y.z]` | Placeholder for a merged control |
| `[LEVEL L1 > L2]` | Level assignment changed |

CWE and NIST mapping changes do not require change tags.

**PR target:** always `main`. Branch names should be descriptive (e.g., `add-sbom-verification-control`, `fix-v1.1.3-nist-mapping`).
