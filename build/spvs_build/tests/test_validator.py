"""Tests for the three-stage validator pipeline."""

import json
from pathlib import Path

from spvs_build.model import (
    Category,
    Control,
    Metadata,
    SubCategory,
)
from spvs_build.validator import validate


def _ctrl(
    id: str = "V1.1.1",
    sub_id: str = "V1.1",
    level: int = 2,
    metadata: Metadata | None = None,
    source_path: str = "controls/baseline/V1/V1.1/V1.1.1-x.yaml",
) -> Control:
    return Control(
        id=id,
        category=Category(id="V1", name="Plan"),
        sub_category=SubCategory(id=sub_id, name="IAM"),
        description="x",
        level=level,
        mappings={},
        metadata=metadata or Metadata(status="active"),
        source_path=source_path,
    )


def test_validate_passes_for_well_formed_control(schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text())
    controls = [_ctrl()]
    errors = validate(controls, schema)
    assert errors == []


def test_validate_catches_invalid_level_via_schema(schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text())
    controls = [_ctrl(level=5)]
    errors = validate(controls, schema)
    assert any(e.code == "E101" for e in errors)


def test_validate_catches_filename_id_mismatch(schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text())
    controls = [_ctrl(source_path="controls/baseline/V1/V1.1/V1.1.2-x.yaml")]
    errors = validate(controls, schema)
    assert any(e.code == "E201" for e in errors)


def test_validate_catches_bad_slug(schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text())
    controls = [_ctrl(source_path="controls/baseline/V1/V1.1/V1.1.1-Bad_Slug!.yaml")]
    errors = validate(controls, schema)
    assert any(e.code == "E202" for e in errors)


def test_validate_catches_duplicate_ids(schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text())
    controls = [
        _ctrl(id="V1.1.1", source_path="controls/baseline/V1/V1.1/V1.1.1-a.yaml"),
        _ctrl(id="V1.1.1", source_path="controls/baseline/V1/V1.1/V1.1.1-b.yaml"),
    ]
    errors = validate(controls, schema)
    assert any(e.code == "E301" for e in errors)


def test_validate_catches_orphan_moved_to(schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text())
    controls = [_ctrl(id="V1.1.1", metadata=Metadata(status="moved", moved_to="V9.9.9"))]
    errors = validate(controls, schema)
    assert any(e.code == "E302" for e in errors)
