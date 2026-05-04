# SPVS Build Toolchain

This directory contains the Python toolchain that maintains the SPVS YAML
source-of-truth and regenerates the published CSV outputs.

## What lives here

- `spvs_build/` — Python package (loader, validator, renderers, migration tool, CLI)
- `pyproject.toml` — pinned dependencies, ruff/mypy/pytest config, dependency cool-down gate
- `uv.lock` — committed lockfile for reproducible builds
- `Makefile` — developer task runner (run `make help` for the full list)

The YAML source files themselves live one level up at `../controls/`, the JSON
Schema at `../schema/`, and the generated CSV outputs at `../1.5/`.

## Requirements

- **Python 3.11+** (pinned by `pyproject.toml: requires-python`)
- **[uv](https://docs.astral.sh/uv/)** for dependency and environment management
- **[pre-commit](https://pre-commit.com/)** for the optional local hooks (recommended)

Install uv:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick start

```sh
cd build
make install            # bootstrap venv + install pre-commit hooks
make check              # all read-only quality checks (lint + format-check + type-check)
make test               # full test suite with coverage gate (80%)
make help               # see all available targets
```

## Common workflows

### Editing or adding controls

1. Edit YAML files under `../controls/baseline/V<cat>/V<sub>/`
2. Run `make validate-baseline` to confirm the YAML passes schema + semantic checks
3. Run `make build-baseline` to regenerate `../1.5/OWASP_SPVS_1.0_-en_Requirements.csv`
4. Run `make check-baseline` to confirm the regenerated CSV matches the committed one
   (this is what CI runs — pass it locally before pushing)
5. Commit both the YAML and the regenerated CSV

### Pre-commit (recommended, opt-in)

After `make install`, every commit automatically runs:
- File hygiene (trailing whitespace, end-of-file, YAML/JSON/TOML syntax, merge conflict markers, large file rejection, private key detection)
- Ruff lint + format
- Mypy strict type check
- Gitleaks secret scan
- SPVS YAML schema validation
- SPVS CSV regeneration + drift check
- yamllint over `controls/`
- Conventional Commits format on the commit message

To run all hooks against every file (e.g., after pulling a large change):

```sh
make pre-commit-all
```

### Running tests

```sh
make test               # full suite with coverage (gate: 80%)
make test-fast          # quick feedback, no coverage
make test-file FILE=spvs_build/tests/test_loader.py  # one file
```

## Pre-commit checklist (before pushing a PR)

Run this sequence before pushing to ensure CI passes on the first try:

```sh
make check              # ruff + mypy
make test               # pytest with coverage gate
make validate-baseline  # YAML schema + semantic validation
make check-baseline     # CSV drift check
make yamllint           # block-style YAML rules
make security           # ruff bandit + gitleaks
```

If `make pre-commit-all` is green, the equivalent of all the above passed.

## CI behaviour

The GitHub Actions workflow at `.github/workflows/build-controls.yml`
runs core validation/build checks on every PR and on pushes to `main`:
ruff (lint + format), mypy, pytest with coverage gate, schema +
semantic validation of `controls/baseline/`, CSV drift check, and
yamllint over `controls/`. The job is named `validate-and-build` and
is required for merge.

A few hooks are pre-commit-only (not enforced by the GitHub Actions
job): the local `gitleaks` secret scan, Conventional Commits format
on the commit message, and `no-commit-to-branch`. Server-side secret
scanning is handled by GitHub native Secret Scanning + Push Protection
(see Supply chain hardening below).

CI runtime target: under 30 seconds cold install via `uv` plus all checks.

## Toolchain maintenance

### Updating dependencies

Routine `make install` / `make sync` install from the committed `uv.lock`
without re-resolving (`uv sync --dev --frozen`). The lockfile is
authoritative.

To intentionally pull updated package versions, run the maintenance
target:

```sh
make lock               # uv lock + uv sync --dev (re-resolve from pyproject.toml)
make check && make test # confirm nothing broke
```

Then commit the updated `uv.lock`.

The `[tool.uv] exclude-newer = "7 days"` cool-down gate in `pyproject.toml`
will block adoption of any package version published in the last 7 days,
giving the broader ecosystem time to surface compromised packages before
this project picks them up.

### Updating pre-commit hook versions

```sh
make pre-commit-update  # autoupdate revs in .pre-commit-config.yaml
make pre-commit-all     # confirm all hooks still pass
```

### Adding a new renderer (future phase)

1. Create `spvs_build/renderers/<name>.py` with a `render(controls, out_path)` function
2. Register it in `spvs_build/renderers/__init__.py` via the `RENDERERS` dict
3. Add tests under `spvs_build/tests/test_renderers.py`
4. Optionally add a Makefile target for the new output
5. Update CI workflow if the new renderer is part of the gate

No changes to the loader, validator, model, or schema are required for
adding renderers.

## Supply chain hardening

This toolchain follows defence-in-depth practices:

- **Pinned dependency versions** (`==`) in `pyproject.toml`
- **`uv.lock` committed** — reproducible installs across maintainers
- **Cool-down gate** — `exclude-newer = "7 days"` blocks brand-new package versions
- **Lockfile drift gate** — CI runs `uv sync --frozen`
- **Secrets scanning** — three layers:
  - **GitHub Secret Scanning** runs continuously server-side on every push,
    scans the full history, and surfaces alerts in the repo's Security tab.
    Free for public repos, no setup required.
  - **GitHub Push Protection** (must be enabled in repo Settings -> Code
    security) blocks pushes that would introduce secrets *before* they enter
    the repo. Stronger than CI-time blocking.
  - **`gitleaks` pre-commit hook** runs developer-side as a fast local check.
    Defense-in-depth — does not replace the GitHub-side controls.
- **Security linting** — ruff's `S` (flake8-bandit) rules in CI and pre-commit
- **Conventional Commits** — commit-msg hook validates format
- **No-direct-commit-to-main** — pre-commit hook enforces PR flow
- **AI-assisted code review** — runs on every PR to the toolchain

## Troubleshooting

**`uv sync --frozen` fails in CI but works locally.**
Your local lockfile is out of sync with `pyproject.toml`. Run `make lock` (the maintenance target) and commit the updated `uv.lock`.

**Drift check fails on a PR.**
You changed YAML but didn't regenerate the CSV. Run `make build-baseline`, then `git add` and commit the regenerated CSV.

**Pre-commit hook fails on commit message.**
Conventional Commits format required: `<type>: <description>`. Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `build`.

**Mypy reports errors I don't understand.**
Run `make type-check` for the full output. Strict mode means every public symbol needs annotations.

## Reference

- Design spec: [`../docs/specs/2026-05-03-spvs-yaml-source-of-truth-design.md`](../docs/specs/2026-05-03-spvs-yaml-source-of-truth-design.md)
- Implementation plan: [`../docs/specs/2026-05-03-spvs-yaml-source-of-truth-plan.md`](../docs/specs/2026-05-03-spvs-yaml-source-of-truth-plan.md)
