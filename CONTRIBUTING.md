# Contributing Guidelines

Thank you for your interest in contributing to SPVS. We welcome all contributions and appreciate your efforts to improve the standard.

## Contributing to SPVS

### Types of Contributions

- **New controls:** Proposing a control that does not exist in the current standard
- **Control edits:** Corrections to existing controls (wording, mappings, level assignment)
- **Documentation:** README, contributing guide, or other non-control content

### How to Submit

1. Fork this repository and create a branch named descriptively (e.g., `add-sbom-verification-control`, `fix-v1.1.3-nist-mapping`).

2. Add your proposed control(s) as a new YAML file under
   `controls/baseline/V<cat>/V<sub>/V<id>-<short-slug>.yaml`. Use an
   adjacent control as a template. The slug is a short kebab-case
   description, max 60 characters, action-first when possible
   (e.g. `verify-mfa-enabled`).

   The CSV at `1.5/OWASP_SPVS_1.0_-en_Requirements.csv` is **generated
   from the YAML** by the build pipeline. Do not edit the CSV directly —
   the CI drift check will reject any PR where the committed CSV does
   not match what the YAML produces.

   For new controls, the YAML's `description` field is the verification
   statement, `level` is 1 / 2 / 3, and `mappings` carries the
   compliance framework references. See [`build/README.md`](build/README.md)
   for the full schema and toolchain documentation.

3. Regenerate the CSV before pushing:

   ```sh
   cd build && make build-baseline
   ```

   Then `git add 1.5/OWASP_SPVS_1.0_-en_Requirements.csv` alongside your
   YAML changes.

4. (Recommended) Install the local pre-commit hooks for fast feedback:

   ```sh
   cd build && make install
   ```

   The hooks run schema validation, regenerate the CSV, run yamllint,
   ruff/mypy on the build toolchain, gitleaks for secrets, and validate
   Conventional Commits format on the commit message. CI runs the same
   checks regardless — pre-commit is opt-in but catches issues before
   you push.

5. Open a pull request against the `main` branch. CI runs the full
   build/validate/drift-check sequence; merging requires a green check.
   For new controls, your PR description should address:
   - What the control verifies
   - Which pipeline phase it belongs to and why
   - The threat or risk it addresses (OWASP CICD Top 10 reference preferred)
   - Suggested level (1 = baseline, 2 = standard, 3 = advanced) with rationale
   - NIST 800-53, OWASP CICD Risk, and CWE mappings (best effort is fine)

6. If you're proposing something that doesn't fit cleanly into an existing category, say so in the PR. That's useful signal for the maintainers.

### Numbering Rules

- New controls must be placed at the end of their sub-category
- Deleted controls must retain a placeholder row to prevent number reuse

### Change Tags

In the YAML model, change tags are structured metadata fields, not bracketed
prefixes on the description. When modifying or moving an existing control, add
entries to the `metadata.change_tags` list — the description text stays clean.

Allowed `type` values: `ADDED`, `MODIFIED`, `MOVED_FROM`, `MOVED_TO`,
`DELETED`, `DELETED_MERGED_TO`, `LEVEL_CHANGE`, `SPLIT_FROM`.

Compound changes use multiple list entries. The CSV rendering reflects these
back into the prefix format consumers expect.

```yaml
metadata:
  status: active
  change_tags:
    - type: MODIFIED
    - type: MOVED_FROM
      reference: V1.1.7
```

For deleted/moved controls, the YAML file is removed (or its `metadata.status`
is set to `moved` / `deleted` / `deleted_merged_to`); the build pipeline does
not require a placeholder row to reserve the deleted id.

CWE and NIST mapping changes do not require change_tags entries.

### Example: New Control Submission

**YAML file being added** at `controls/baseline/V3/V3.4/V3.4.3-sbom-generated-signed.yaml`:

```yaml
id: V3.4.3
category:
  id: V3
  name: Integrate (CI*)
sub_category:
  id: V3.4
  name: Integrity of Artifacts
description: >
  Verify that a Software Bill of Materials (SBOM) is generated and stored
  as a signed pipeline artifact on every build.
level: 3
mappings:
  nist_800_53:
    items:
      - SA-12
  owasp_cicd:
    items:
      - CICD-SEC-3
  cwe:
    items:
      - id: CWE-1104
        description: Use of Unmaintained Third Party Components
      - id: CWE-345
        description: Insufficient Verification of Data Authenticity - SBOM integrity
metadata:
  status: active
  change_tags:
    - type: ADDED
```

**PR description:**

> **What this verifies:** That every build produces a machine-readable SBOM (e.g., CycloneDX or SPDX format) and that it's cryptographically signed alongside the build artifact.
>
> **Why this belongs in SPVS:** SBOM generation is currently implied by V2.6 (dependency auditing) and V3.4 (artifact integrity) but never explicitly required as a pipeline output. Without it, downstream consumers can't verify what's in a release.
>
> **Threat:** CICD-SEC-3. If a build-time dependency is compromised, the SBOM gives you the data to scope the blast radius.
>
> **Level:** Proposing L3. Most orgs aren't doing signed SBOMs yet. Open to L2 if the community disagrees.
>
> **Mappings:** NIST SA-12, CICD-SEC-3, CWE-1104, CWE-345.

---

Questions before you open a PR? Join [#owasp-spvs](https://owasp.slack.com/archives/C0AQW879656) on OWASP Slack.

## Code of Conduct

We ask that all contributors to OWASP projects abide by our [Code of Conduct](https://owasp.org/www-policy/operational/code-of-conduct).
This code outlines our expectations for behavior within the project community and helps us maintain a welcoming and inclusive environment for all contributors.

Thank you for your interest in contributing to an OWASP project. We appreciate your efforts to help us improve and grow our projects.