from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Literal, TypeVar


T = TypeVar("T")
HiddenMode = Literal["skip", "block"]


def build_hierarchy_path(
    record: T | None,
    *,
    parent_getter: Callable[[T], T | None] | None = None,
    name_getter: Callable[[T], str | None] | None = None,
    include_hidden: bool = False,
    hidden_mode: HiddenMode = "skip",
    scope_filter: Callable[[T], bool] | None = None,
    separator: str = " / ",
) -> str | None:
    if record is None:
        return None

    get_parent = parent_getter or _get_parent
    get_name = name_getter or _get_name
    nodes: list[str] = []
    seen_ids: set[object] = set()
    current: T | None = record

    while current is not None:
        current_id = getattr(current, "id", id(current))
        if current_id in seen_ids:
            break
        seen_ids.add(current_id)

        if scope_filter is not None and not scope_filter(current):
            break

        is_hidden = bool(getattr(current, "is_hidden", False))
        if is_hidden and not include_hidden:
            if hidden_mode == "block":
                return None
        else:
            name = get_name(current)
            if name:
                nodes.append(name)

        current = get_parent(current)

    if not nodes:
        return None
    return separator.join(reversed(nodes))


def build_hierarchy_path_from_map(
    record: T | None,
    records_by_id: Mapping[object, T],
    **kwargs,
) -> str | None:
    return build_hierarchy_path(
        record,
        parent_getter=lambda item: records_by_id.get(getattr(item, "parent_id", None)),
        **kwargs,
    )


def _get_parent(record: T) -> T | None:
    return getattr(record, "parent", None)


def _get_name(record: T) -> str | None:
    name = getattr(record, "name", None)
    return str(name) if name is not None else None
