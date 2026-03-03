from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel
from backend.models.base.enums import CommunityRole


class Membership(BaseModel):
    """
    Person × Community × Role
    - 所属と役割の核
    """

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("person_id", "community_id", name="uq_person_community"),
        {"schema": "formegot"},
    )

    person_id: Mapped[str] = mapped_column(
        ForeignKey("formegot.persons.id", ondelete="CASCADE"),
        nullable=False
    )

    community_id: Mapped[str] = mapped_column(
        ForeignKey("formegot.communities.id", ondelete="CASCADE"),
        nullable=False
    )

    role: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=CommunityRole.MEMBER,
        comment="community role"
    )

    person = relationship("Person", backref="memberships")
    community = relationship("Community", backref="memberships")
