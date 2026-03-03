from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base.base import BaseModel
from backend.models.base.enums import TaskStatus


class TaskHistory(BaseModel):
    """
    タスク状態履歴
    - 完了 / スキップなどの遷移記録
    """

    __tablename__ = "task_histories"
    __table_args__ = {"schema": "formegot"}

    task_id: Mapped[str] = mapped_column(
        ForeignKey("formegot.relationship_tasks.id", ondelete="CASCADE"),
        nullable=False
    )

    status: Mapped[TaskStatus] = mapped_column(
        Integer,
        nullable=False
    )

    task = relationship("RelationshipTask", backref="histories")
