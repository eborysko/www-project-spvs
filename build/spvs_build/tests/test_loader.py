"""Tests for the YAML loader."""

from pathlib import Path

from spvs_build.loader import LoadError, load_supplement


def test_loader_parses_single_valid_control(tmp_path: Path, fixture_dir: Path) -> None:
    supplement = tmp_path / "controls" / "baseline" / "V1" / "V1.1"
    supplement.mkdir(parents=True)
    (supplement / "V1.1.1-verify-mfa-enabled.yaml").write_text(
        (fixture_dir / "valid_control.yaml").read_text()
    )

    controls, errors = load_supplement(tmp_path / "controls" / "baseline")

    assert errors == []
    assert len(controls) == 1
    assert controls[0].id == "V1.1.1"
    assert controls[0].level == 2
    assert controls[0].source_path is not None


def test_loader_collects_multiple_errors_without_raising(tmp_path: Path) -> None:
    supplement = tmp_path / "controls" / "baseline" / "V1" / "V1.1"
    supplement.mkdir(parents=True)
    (supplement / "broken1.yaml").write_text("id: V1.1.1\n  bad indent")
    (supplement / "broken2.yaml").write_text(": invalid yaml :")

    controls, errors = load_supplement(tmp_path / "controls" / "baseline")

    assert controls == []
    assert len(errors) == 2
    for err in errors:
        assert isinstance(err, LoadError)
        assert err.file is not None


def test_loader_ignores_non_yaml_files(tmp_path: Path, fixture_dir: Path) -> None:
    supplement = tmp_path / "controls" / "baseline" / "V1" / "V1.1"
    supplement.mkdir(parents=True)
    (supplement / "V1.1.1-x.yaml").write_text((fixture_dir / "valid_control.yaml").read_text())
    (supplement / "README.md").write_text("# notes")
    (supplement / ".DS_Store").write_text("")

    controls, errors = load_supplement(tmp_path / "controls" / "baseline")

    assert errors == []
    assert len(controls) == 1


def test_loader_walks_deterministically(tmp_path: Path, fixture_dir: Path) -> None:
    base = tmp_path / "controls" / "baseline"
    for sub_id, num in [("V1.1", 1), ("V1.1", 2), ("V1.2", 1), ("V2.3", 1)]:
        d = base / f"V{sub_id.split('.')[0][1:]}" / sub_id
        d.mkdir(parents=True, exist_ok=True)
        content = (fixture_dir / "valid_control.yaml").read_text()
        content = content.replace("id: V1.1.1", f"id: {sub_id}.{num}")
        (d / f"{sub_id}.{num}-x.yaml").write_text(content)

    controls, errors = load_supplement(base)

    assert errors == []
    ids = [c.id for c in controls]
    assert ids == sorted(ids)
