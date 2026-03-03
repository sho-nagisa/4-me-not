from uuid import UUID
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel


class CommunityTree(BaseModel):
    """
    Community 階層補助（親子関係の明示管理）
    - 多段階層（Closure Table / Adjacency補助）
    """

    __tablename__ = "community_trees"
    __table_args__ = (
        UniqueConstraint("parent_id", "child_id", name="uq_community_tree"),
        {"schema": "formegot"}
    )

    parent_id: Mapped[UUID] = mapped_column(
        ForeignKey("formegot.communities.id", ondelete="CASCADE"),
        nullable=False
    )

    child_id: Mapped[UUID] = mapped_column(
        ForeignKey("formegot.communities.id", ondelete="CASCADE"),
        nullable=False
    )

    parent: Mapped["Community"] = relationship(
        "Community",
        foreign_keys=[parent_id],
        backref="tree_children"
    )

    child: Mapped["Community"] = relationship(
        "Community",
        foreign_keys=[child_id],
        backref="tree_parents"
    )
