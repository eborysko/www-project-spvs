"""Typed dataclasses for SPVS controls."""

from __future__ import annotations

from collections.abc import Mapping as ABCMapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

ChangeTagType = Literal[
    "ADDED",
    "MODIFIED",
    "MOVED_FROM",
    "MOVED_TO",
    "DELETED",
    "DELETED_MERGED_TO",
    "LEVEL_CHANGE",
    "SPLIT_FROM",
]

Status = Literal["active", "deprecated", "moved", "deleted", "deleted_merged_to"]


@dataclass(frozen=True)
class Category:
    id: str
    name: str


@dataclass(frozen=True)
class SubCategory:
    id: str
    name: str


@dataclass(frozen=True)
class MappingItem:
    """A single mapping entry. `description` is None when a framework's items
    are bare-string shorthand."""

    id: str
    description: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class Mapping:
    """All entries for one framework (e.g., nist_800_53, cwe)."""

    framework: str
    items: tuple[MappingItem, ...]


@dataclass(frozen=True)
class ChangeTag:
    type: ChangeTagType
    reference: str | None = None
    from_level: int | None = None
    to_level: int | None = None


@dataclass(frozen=True)
class Metadata:
    status: Status = "active"
    change_tags: tuple[ChangeTag, ...] = ()
    introduced_in: str | None = None
    last_modified_in: str | None = None
    moved_to: str | None = None
    owner: str | None = None


@dataclass(frozen=True)
class Control:
    id: str
    category: Category
    sub_category: SubCategory
    description: str
    level: int  # 1, 2, or 3 — single value
    # `mappings` is wrapped in MappingProxyType by __post_init__ for runtime
    # read-only enforcement. The annotation uses the abc.Mapping protocol so
    # callers see a read-only API; passing a regular dict in is fine — the
    # constructor will copy + wrap it.
    mappings: ABCMapping[str, Mapping]  # framework_name -> Mapping
    metadata: Metadata
    source_path: str | None = None  # set by loader for error reporting

    def __post_init__(self) -> None:
        # frozen=True prevents field reassignment but does not prevent mutation
        # of a passed-in dict. Copy to detach from the caller's reference, then
        # wrap in MappingProxyType so .mappings is read-only at runtime.
        if not isinstance(self.mappings, MappingProxyType):
            object.__setattr__(self, "mappings", MappingProxyType(dict(self.mappings)))
