"""Tests for the renderer registry and CSV renderers."""

from pathlib import Path

from spvs_build.model import (
    Category,
    Control,
    Mapping,
    MappingItem,
    Metadata,
    SubCategory,
)
from spvs_build.renderers import RENDERERS
from spvs_build.renderers.csv_baseline import render as render_baseline


def _sample_v1_1_1() -> Control:
    return Control(
        id="V1.1.1",
        category=Category(id="V1", name="Plan"),
        sub_category=SubCategory(id="V1.1", name="Identity and Access Management"),
        description=(
            "Verify that Multi-Factor Authentication (MFA) is enabled for "
            "accessing developer laptops and critical systems."
        ),
        level=2,
        mappings={
            "nist_800_53": Mapping(
                framework="nist_800_53",
                items=(
                    MappingItem("IA-2(1)"),
                    MappingItem("IA-2(2)"),
                    MappingItem("IA-2(12)"),
                    MappingItem("IA-5"),
                ),
            ),
            "owasp_cicd": Mapping(framework="owasp_cicd", items=(MappingItem("CICD-SEC-2"),)),
            "cwe": Mapping(
                framework="cwe",
                items=(
                    MappingItem("CWE-308", "Use of Single-Factor Authentication"),
                    MappingItem(
                        "CWE-287",
                        "Improper Authentication - Weak authentication mechanisms",
                    ),
                ),
            ),
        },
        metadata=Metadata(status="active"),
    )


def test_csv_baseline_renders_single_control(tmp_path: Path, fixture_dir: Path) -> None:
    out = tmp_path / "out.csv"
    render_baseline([_sample_v1_1_1()], out)

    actual = out.read_bytes()
    expected = (fixture_dir / "expected_baseline.csv").read_bytes()
    assert actual == expected


def test_csv_baseline_is_deterministic(tmp_path: Path) -> None:
    out_a = tmp_path / "a.csv"
    out_b = tmp_path / "b.csv"
    render_baseline([_sample_v1_1_1()], out_a)
    render_baseline([_sample_v1_1_1()], out_b)
    assert out_a.read_bytes() == out_b.read_bytes()


def test_renderer_registry_has_csv_baseline() -> None:
    assert "csv-baseline" in RENDERERS
    assert callable(RENDERERS["csv-baseline"])


def test_csv_baseline_renders_tombstone_as_dashes_row(tmp_path: Path) -> None:
    """Tombstones (status=deleted/moved/etc.) render as the all-dashes
    placeholder row that the published baseline CSV uses to reserve
    deleted/moved id numbers — preserves byte-alignment with previous CSV
    consumers."""
    tombstone = Control(
        id="V1.5.4",
        category=Category(id="V1", name="Plan"),
        sub_category=SubCategory(id="V1.5", name="Source Code Management Hardening"),
        description="",
        level=1,
        mappings={},
        metadata=Metadata(status="deleted"),
    )
    out = tmp_path / "tombstone.csv"
    render_baseline([tombstone], out)

    lines = out.read_text(encoding="utf-8").splitlines()
    # First line is the column header; second is the tombstone row.
    assert len(lines) == 2
    assert lines[1] == "-,-,-,-,-,-,-,-,-,-,-,-,-"
