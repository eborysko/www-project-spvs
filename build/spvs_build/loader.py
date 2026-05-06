"""Walk a supplement directory, parse YAML, return Controls + errors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from spvs_build.model import (
    Category,
    ChangeTag,
    ChangeTagType,
    Control,
    Mapping,
    MappingItem,
    Metadata,
    Status,
    SubCategory,
)


@dataclass(frozen=True)
class LoadError:
    file: str
    line: int | None
    code: str
    message: str


def _natural_sort_key(path: Path) -> tuple[tuple[int, ...], str]:
    """Sort by V<n>.<n>.<n> numeric components, with the path string as a
    deterministic tiebreaker. Without the tiebreaker, two files with the same
    numeric prefix (e.g., a duplicate-id error case or a typo) would sort
    nondeterministically."""
    name = path.stem.split("-")[0]
    parts = name.lstrip("V").split(".")
    try:
        nums = tuple(int(p) for p in parts)
    except ValueError:
        nums = (0,)
    return (nums, path.as_posix())


def load_supplement(root: Path) -> tuple[list[Control], list[LoadError]]:
    """Walk `root`, parse all *.yaml files, build Control instances.

    Never raises; collects errors and returns them.
    """
    yaml = YAML(typ="safe")
    controls: list[Control] = []
    errors: list[LoadError] = []

    if not root.exists():
        return controls, [LoadError(str(root), None, "E000", f"path does not exist: {root}")]
    if not root.is_dir():
        return controls, [LoadError(str(root), None, "E000", f"path is not a directory: {root}")]

    yaml_files = sorted(root.rglob("*.yaml"), key=_natural_sort_key)

    for path in yaml_files:
        try:
            with path.open("r", encoding="utf-8") as f:
                raw = yaml.load(f)
        except YAMLError as e:
            line = getattr(getattr(e, "problem_mark", None), "line", None)
            errors.append(
                LoadError(str(path), line + 1 if line is not None else None, "E001", str(e))
            )
            continue
        except OSError as e:
            errors.append(LoadError(str(path), None, "E002", f"could not read file: {e}"))
            continue

        if not isinstance(raw, dict):
            errors.append(
                LoadError(
                    str(path),
                    None,
                    "E003",
                    f"document is not a YAML mapping (got {type(raw).__name__})",
                )
            )
            continue

        try:
            control = _build_control(raw, path)
            controls.append(control)
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            errors.append(LoadError(str(path), None, "E003", f"malformed control: {e}"))

    return controls, errors


def _build_control(raw: dict[str, object], path: Path) -> Control:
    raw_mappings = cast(dict[str, dict[str, object]], raw.get("mappings") or {})
    raw_metadata = cast(dict[str, object], raw.get("metadata") or {})
    raw_category = cast(dict[str, object], raw["category"])
    raw_sub_category = cast(dict[str, object], raw["sub_category"])

    return Control(
        id=cast(str, raw["id"]),
        category=Category(id=cast(str, raw_category["id"]), name=cast(str, raw_category["name"])),
        sub_category=SubCategory(
            id=cast(str, raw_sub_category["id"]), name=cast(str, raw_sub_category["name"])
        ),
        description=cast(str, raw["description"]),
        level=cast(int, raw["level"]),
        mappings={
            framework: Mapping(
                framework=framework,
                items=tuple(
                    _build_mapping_item(i) for i in cast(list[object], body.get("items", []))
                ),
            )
            for framework, body in raw_mappings.items()
        },
        metadata=_build_metadata(raw_metadata),
        source_path=str(path),
    )


def _build_mapping_item(raw: object) -> MappingItem:
    if isinstance(raw, str):
        return MappingItem(id=raw)
    if not isinstance(raw, dict):
        raise TypeError(
            f"mapping item must be a string or a dict with an 'id' field, "
            f"got {type(raw).__name__}: {raw!r}"
        )
    return MappingItem(id=raw["id"], description=raw.get("description"), note=raw.get("note"))


def _build_metadata(raw: dict[str, object]) -> Metadata:
    raw_change_tags = cast(list[dict[str, object]], raw.get("change_tags", []))

    return Metadata(
        status=cast(Status, raw.get("status", "active")),
        change_tags=tuple(
            ChangeTag(
                type=cast(ChangeTagType, t["type"]),
                reference=cast(str | None, t.get("reference")),
                from_level=cast(int | None, t.get("from_level")),
                to_level=cast(int | None, t.get("to_level")),
            )
            for t in raw_change_tags
        ),
        introduced_in=cast(str | None, raw.get("introduced_in")),
        last_modified_in=cast(str | None, raw.get("last_modified_in")),
        moved_to=cast(str | None, raw.get("moved_to")),
        owner=cast(str | None, raw.get("owner")),
    )
