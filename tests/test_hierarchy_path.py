from __future__ import annotations

from dataclasses import dataclass
import unittest

from backend.services.hierarchy_path import (
    build_hierarchy_path,
    build_hierarchy_path_from_map,
)


@dataclass
class Node:
    id: str
    name: str
    parent_id: str | None = None
    parent: "Node | None" = None
    is_hidden: bool = False


class HierarchyPathTest(unittest.TestCase):
    def test_build_hierarchy_path_skips_hidden_nodes_by_default(self) -> None:
        root = Node(id="root", name="Root")
        hidden = Node(id="hidden", name="Hidden", parent=root, is_hidden=True)
        child = Node(id="child", name="Child", parent=hidden)

        self.assertEqual(build_hierarchy_path(child), "Root / Child")
        self.assertEqual(
            build_hierarchy_path(child, include_hidden=True),
            "Root / Hidden / Child",
        )

    def test_build_hierarchy_path_can_block_on_hidden_nodes(self) -> None:
        root = Node(id="root", name="Root")
        hidden = Node(id="hidden", name="Hidden", parent=root, is_hidden=True)
        child = Node(id="child", name="Child", parent=hidden)

        self.assertIsNone(build_hierarchy_path(child, hidden_mode="block"))

    def test_build_hierarchy_path_from_map_uses_parent_ids(self) -> None:
        root = Node(id="root", name="Root")
        child = Node(id="child", name="Child", parent_id="root")
        records_by_id = {node.id: node for node in (root, child)}

        self.assertEqual(
            build_hierarchy_path_from_map(child, records_by_id),
            "Root / Child",
        )

    def test_build_hierarchy_path_stops_on_cycles(self) -> None:
        root = Node(id="root", name="Root")
        child = Node(id="child", name="Child", parent=root)
        root.parent = child

        self.assertEqual(build_hierarchy_path(child), "Root / Child")


if __name__ == "__main__":
    unittest.main(verbosity=2)
