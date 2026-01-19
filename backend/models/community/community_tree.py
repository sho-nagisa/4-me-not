from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base.base import BaseModel


class CommunityTree(BaseModel):
    """
    Community 階層補助（親子関係の明示管理）
    - 多段階層の高速取得用
    """

    __tablename__ = "community_trees"

    parent_id: Mapped[str] = mapped_column(
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False
    )

    child_id: Mapped[str] = mapped_column(
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False
    )

    parent = relationship(
        "Community",
        foreign_keys=[parent_id],
        backref="tree_children"
    )

    child = relationship(
        "Community",
        foreign_keys=[child_id],
        backref="tree_parents"
    )
