from backend.models.interaction.interaction import Interaction
from backend.db.session import SessionLocal
from sqlalchemy.orm import Session


class InteractionService:

    def record_interaction(
        self,
        person_id,
        interaction_type,
        content: str | None = None,
        tag_ids: list[str] | None = None,
    ):
        db: Session = SessionLocal()
        try:
            interaction = Interaction(
                person_id=person_id,
                type=interaction_type,
                content=content,
            )
            db.add(interaction)
            db.commit()
            db.refresh(interaction)
            return interaction
        finally:
            db.close()
