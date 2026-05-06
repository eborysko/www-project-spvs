"""Tests for the Control data model."""

from spvs_build.model import (
    Category,
    ChangeTag,
    Control,
    MappingItem,
    Metadata,
    SubCategory,
)


def test_control_minimal_construction() -> None:
    control = Control(
        id="V1.1.1",
        category=Category(id="V1", name="Plan"),
        sub_category=SubCategory(id="V1.1", name="Identity and Access Management"),
        description="Verify that MFA is enabled.",
        level=2,
        mappings={},
        metadata=Metadata(status="active"),
    )
    assert control.id == "V1.1.1"
    assert control.level == 2
    assert control.metadata.status == "active"


def test_mapping_item_string_shorthand() -> None:
    item = MappingItem(id="IA-2(1)", description=None)
    assert item.id == "IA-2(1)"
    assert item.description is None


def test_mapping_item_full_form() -> None:
    item = MappingItem(id="CWE-308", description="Use of Single-Factor Authentication")
    assert item.id == "CWE-308"
    assert item.description == "Use of Single-Factor Authentication"


def test_change_tag_with_reference() -> None:
    tag = ChangeTag(type="MOVED_FROM", reference="V1.1.7")
    assert tag.type == "MOVED_FROM"
    assert tag.reference == "V1.1.7"


def test_metadata_with_change_tags_list() -> None:
    meta = Metadata(
        status="active",
        change_tags=(
            ChangeTag(type="MODIFIED"),
            ChangeTag(type="MOVED_FROM", reference="V1.1.7"),
        ),
    )
    assert len(meta.change_tags) == 2
    assert meta.change_tags[1].reference == "V1.1.7"
