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
    # 3 data rows (placeholder skipped) = 3 files
    assert len(yaml_files) == 3


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
