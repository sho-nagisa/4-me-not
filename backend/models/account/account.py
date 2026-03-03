# models/account/account.py
from typing import Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from models.base.base import BaseModel
from models.person.person import Person


class Account(BaseModel):
    """
    Supabase Auth と 1:1 で対応するログイン主体
    - id は Supabase の user.id (UUID) をそのまま使う
    """

    __tablename__ = "accounts"
    __table_args__ = {"schema": "formegot"}

    # Supabase Auth 由来
    email: str = Field(
        nullable=False,
        index=True,
        unique=True,
    )

    is_active: bool = Field(default=True)

    # 自分自身を表す Person
    person_id: Optional[UUID] = Field(
        default=None,
        foreign_key="formegot.persons.id",
        nullable=True,
        index=True,
    )

    person: Optional[Person] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}
    )
