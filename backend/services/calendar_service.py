from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.account_context import get_current_account_id
from backend.db.session import SessionLocal
from backend.models.calendar.calendar_event import CalendarEvent
from backend.models.calendar.event_participant import EventParticipant
from backend.models.person.person import Person


class CalendarService:
    def list_events(self, limit: int = 100) -> list[dict]:
        db: Session = SessionLocal()
        try:
            account_id = get_current_account_id()
            events = (
                db.query(CalendarEvent)
                .options(
                    joinedload(CalendarEvent.participants).joinedload(
                        EventParticipant.person
                    )
                )
                .filter(CalendarEvent.account_id == account_id)
                .order_by(CalendarEvent.start_at.desc())
                .limit(limit)
                .all()
            )
            return [self.serialize_event(event) for event in events]
        finally:
            db.close()

    def create_event(
        self,
        title: str,
        start_at: datetime,
        end_at: datetime,
        description: str | None = None,
        location: str | None = None,
        source: str | None = "manual",
        external_id: str | None = None,
        participants: list[dict] | None = None,
    ) -> dict:
        db: Session = SessionLocal()
        event: CalendarEvent | None = None
        try:
            account_id = get_current_account_id()
            if end_at < start_at:
                raise HTTPException(status_code=400, detail="Event end must be after start")

            event = CalendarEvent(
                account_id=account_id,
                external_id=external_id or f"manual:{uuid4()}",
                title=title.strip(),
                description=description.strip() if description else None,
                location=location.strip() if location else None,
                start_at=start_at,
                end_at=end_at,
                source=source,
            )
            db.add(event)
            db.flush()

            for participant in participants or []:
                person_id = participant.get("person_id")
                normalized_person_id = None
                if person_id:
                    normalized_person_id = self._validate_person(
                        db,
                        account_id=account_id,
                        person_id=person_id,
                    )
                db.add(
                    EventParticipant(
                        account_id=account_id,
                        calendar_event_id=event.id,
                        person_id=normalized_person_id,
                        display_name=participant.get("display_name"),
                        email=participant.get("email"),
                        role=participant.get("role") or "attendee",
                        is_inferred=bool(participant.get("is_inferred", False)),
                        confidence=participant.get("confidence"),
                    )
                )

            db.commit()
            db.refresh(event)
            payload = self.serialize_event(event)
        finally:
            db.close()

        from backend.services.search import SearchService

        if event is not None:
            SearchService().index_calendar_event(str(event.id))
        return payload

    def serialize_event(self, event: CalendarEvent) -> dict:
        return {
            "id": str(event.id),
            "external_id": event.external_id,
            "title": event.title,
            "description": event.description,
            "location": event.location,
            "start_at": event.start_at.isoformat(),
            "end_at": event.end_at.isoformat(),
            "source": event.source,
            "participants": [
                {
                    "id": str(participant.id),
                    "person_id": str(participant.person_id)
                    if participant.person_id
                    else None,
                    "person_name": participant.person.name
                    if participant.person
                    else None,
                    "display_name": participant.display_name,
                    "email": participant.email,
                    "role": participant.role,
                    "is_inferred": bool(participant.is_inferred),
                    "confidence": participant.confidence,
                }
                for participant in event.participants
            ],
            "created_at": event.created_at.isoformat(),
            "updated_at": event.updated_at.isoformat(),
        }

    def _validate_person(
        self,
        db: Session,
        account_id: UUID,
        person_id: str,
    ) -> UUID:
        try:
            normalized_id = UUID(str(person_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Person is invalid") from exc

        person = (
            db.query(Person)
            .filter(Person.id == normalized_id, Person.account_id == account_id)
            .first()
        )
        if person is None or person.is_hidden:
            raise HTTPException(status_code=404, detail="Person not found")
        return normalized_id
