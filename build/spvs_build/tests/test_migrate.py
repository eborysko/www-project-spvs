"""Tests for the CSV → YAML migration tool."""

from pathlib import Path

from ruamel.yaml import YAML

from spvs_build.migrate import MigrationError, migrate_baseline


def test_migrate_emits_one_yaml_per_data_row(tmp_path: Path, fixture_dir: Path) -> None:
    out = tmp_path / "controls" / "baseline"
    out.mkdir(parents=True)
    errors = migrate_baseline(fixture_dir / "sample_baseline.csv", out)
    assert errors == []

    yaml_files = sorted(out.rglob("*.yaml"))
    # 3 active rows + 1 placeholder (-> tombstone YAML) = 4 files
    assert len(yaml_files) == 4


def test_migrate_emits_tombstone_for_placeholder_row(tmp_path: Path, fixture_dir: Path) -> None:
    """Placeholder rows ('-,-,-,...') become tombstone YAMLs with the next
    sequential id in the last seen sub-category and status=deleted."""
    out = tmp_path / "controls" / "baseline"
    out.mkdir(parents=True)
    errors = migrate_baseline(fixture_dir / "sample_baseline.csv", out)
    assert errors == []

    # Sample CSV: placeholder follows V1.1.2 (last in V1.1) -> tombstone V1.1.3
    yaml = YAML(typ="safe")
    matched = list(out.rglob("V1.1.3-tombstone.yaml"))
    assert len(matched) == 1, f"expected one V1.1.3-tombstone.yaml, got {matched}"
    data = yaml.load(matched[0].read_text())
    assert data["id"] == "V1.1.3"
    assert data["metadata"]["status"] == "deleted"
    assert data["description"] == ""
    assert data["mappings"] == {}


def test_migrate_extracts_change_tag_from_description(tmp_path: Path, fixture_dir: Path) -> None:
    out = tmp_path / "controls" / "baseline"
    out.mkdir(parents=True)
    migrate_baseline(fixture_dir / "sample_baseline.csv", out)

    yaml = YAML(typ="safe")
    matched = list(out.rglob("V1.1.2-*.yaml"))
    assert len(matched) == 1
    data = yaml.load(matched[0].read_text())

    assert "[MODIFIED]" not in data["description"]
    tags = data["metadata"].get("change_tags", [])
    assert any(t["type"] == "MODIFIED" for t in tags)


def test_migrate_pairs_cwe_ids_with_descriptions(tmp_path: Path, fixture_dir: Path) -> None:
    out = tmp_path / "controls" / "baseline"
    out.mkdir(parents=True)
    migrate_baseline(fixture_dir / "sample_baseline.csv", out)

    yaml = YAML(typ="safe")
    matched = list(out.rglob("V1.1.1-*.yaml"))
    assert len(matched) == 1, f"expected exactly one V1.1.1 yaml, got {matched}"
    data = yaml.load(matched[0].read_text())

    cwe_items = data["mappings"]["cwe"]["items"]
    assert len(cwe_items) == 2
    assert cwe_items[0]["id"] == "CWE-308"
    assert cwe_items[0]["description"] == "Use of Single-Factor Authentication"


def test_migrate_fails_loudly_on_mismatched_cwe_lengths(tmp_path: Path) -> None:
    csv = tmp_path / "bad.csv"
    csv.write_text(
        "category_id,catagory_name,sub-category_id,sub-catagory_name,req_id,"
        "req_description,level 1,level 2,level 3,NIST,OWASP_CICD_Risk,"
        "cwe_mapping,cwe_description\n"
        "V1,Plan,V1.1,IAM,V1.1.1,desc,,X,,N,O,CWE-1;CWE-2;CWE-3,Only one desc\n"
    )
    out = tmp_path / "out"
    out.mkdir()
    errors = migrate_baseline(csv, out)
    assert any(isinstance(e, MigrationError) and "cwe" in e.message.lower() for e in errors)


def test_migrate_fails_loudly_on_no_level_marked(tmp_path: Path) -> None:
    """Regression: rows with no level column marked must fail rather than
    silently defaulting to L1, which previously hid bad CSV data."""
    csv = tmp_path / "bad.csv"
    csv.write_text(
        "category_id,catagory_name,sub-category_id,sub-catagory_name,req_id,"
        "req_description,level 1,level 2,level 3,NIST,OWASP_CICD_Risk,"
        "cwe_mapping,cwe_description\n"
        "V1,Plan,V1.1,IAM,V1.1.1,desc,,,,N,O,CWE-1,The CWE\n"
    )
    out = tmp_path / "out"
    out.mkdir()
    errors = migrate_baseline(csv, out)
    assert any(isinstance(e, MigrationError) and "level" in e.message.lower() for e in errors)


def test_migrate_fails_loudly_on_multiple_levels_marked(tmp_path: Path) -> None:
    """Regression: rows with more than one level column marked must fail
    rather than silently using the first match, which previously hid bad data."""
    csv = tmp_path / "bad.csv"
    csv.write_text(
        "category_id,catagory_name,sub-category_id,sub-catagory_name,req_id,"
        "req_description,level 1,level 2,level 3,NIST,OWASP_CICD_Risk,"
        "cwe_mapping,cwe_description\n"
        "V1,Plan,V1.1,IAM,V1.1.1,desc,X,X,,N,O,CWE-1,The CWE\n"
    )
    out = tmp_path / "out"
    out.mkdir()
    errors = migrate_baseline(csv, out)
    assert any(isinstance(e, MigrationError) and "level" in e.message.lower() for e in errors)


def test_migrate_fails_loudly_on_descriptions_without_ids(tmp_path: Path) -> None:
    """Regression: description-only rows must fail rather than silently
    discarding the descriptions. The earlier check guarded only on non-empty
    cwe_ids, so a row with cwe_descriptions but empty cwe_mapping would
    silently lose data."""
    csv = tmp_path / "bad.csv"
    csv.write_text(
        "category_id,catagory_name,sub-category_id,sub-catagory_name,req_id,"
        "req_description,level 1,level 2,level 3,NIST,OWASP_CICD_Risk,"
        "cwe_mapping,cwe_description\n"
        "V1,Plan,V1.1,IAM,V1.1.1,desc,,X,,N,O,,Description without an id\n"
    )
    out = tmp_path / "out"
    out.mkdir()
    errors = migrate_baseline(csv, out)
    assert any(isinstance(e, MigrationError) and "cwe" in e.message.lower() for e in errors)


def test_migrate_fails_loudly_on_missing_required_header(tmp_path: Path) -> None:
    """Regression: missing required header columns must surface as
    MigrationError with csv_row=1 before any data row processing,
    rather than KeyError-ing mid-iteration on row['req_id']."""
    csv = tmp_path / "bad.csv"
    # Missing req_id, req_description, category_id, sub-category_id, and both
    # name columns. Has only level columns and mappings.
    csv.write_text(
        "level 1,level 2,level 3,NIST,OWASP_CICD_Risk,cwe_mapping,cwe_description\n"
        "X,,,N,O,CWE-1,The CWE\n"
    )
    out = tmp_path / "out"
    out.mkdir()
    errors = migrate_baseline(csv, out)
    assert errors, "expected header validation errors"
    assert all(e.csv_row == 1 for e in errors), "header errors must point to row 1"
    messages = " ".join(e.message for e in errors)
    assert "req_id" in messages
    assert "category_id" in messages


def test_migrate_accepts_old_or_new_category_header_spelling(tmp_path: Path) -> None:
    """Both 'category_name' (corrected) and 'catagory_name' (historical typo)
    are accepted; either alone passes header validation."""
    csv_old = tmp_path / "old.csv"
    csv_old.write_text(
        "category_id,catagory_name,sub-category_id,sub-catagory_name,req_id,"
        "req_description,level 1,level 2,level 3,NIST,OWASP_CICD_Risk,"
        "cwe_mapping,cwe_description\n"
        "V1,Plan,V1.1,IAM,V1.1.1,desc,X,,,N,O,CWE-1,The CWE\n"
    )
    out_old = tmp_path / "out_old"
    out_old.mkdir()
    errors_old = migrate_baseline(csv_old, out_old)
    assert errors_old == []

    csv_new = tmp_path / "new.csv"
    csv_new.write_text(
        "category_id,category_name,sub-category_id,sub-category_name,req_id,"
        "req_description,level 1,level 2,level 3,NIST,OWASP_CICD_Risk,"
        "cwe_mapping,cwe_description\n"
        "V1,Plan,V1.1,IAM,V1.1.1,desc,X,,,N,O,CWE-1,The CWE\n"
    )
    out_new = tmp_path / "out_new"
    out_new.mkdir()
    errors_new = migrate_baseline(csv_new, out_new)
    assert errors_new == []


def test_derive_slug_collision_progresses_when_base_at_max_length(tmp_path: Path) -> None:
    """Regression: counter suffix must always change the slug, even when base is 60 chars.

    Earlier `f"{base}-{counter}"[:60]` could truncate the suffix off the end
    when base was already at the 60-char limit, causing an infinite loop on
    collisions.
    """
    from spvs_build.migrate import _derive_slug

    long_desc = " ".join(["alphabetic"] * 8)
    taken: set[str] = set()
    s1 = _derive_slug(long_desc, taken)
    taken.add(s1)
    s2 = _derive_slug(long_desc, taken)
    taken.add(s2)
    s3 = _derive_slug(long_desc, taken)

    assert len(s1) <= 60
    assert len(s2) <= 60
    assert len(s3) <= 60
    assert len({s1, s2, s3}) == 3
