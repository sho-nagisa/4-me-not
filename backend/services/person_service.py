from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.orm import joinedload

from backend.db.session import SessionLocal
from backend.models.community.community import Community
from backend.models.person.person import Person


class PersonService:
    def create_person(
        self,
        name: str,
        canonical_name: str | None = None,
        primary_community_id: str | None = None,
    ):
        db = SessionLocal()
        try:
            normalized_primary_community_id = self._validate_primary_community(
                db=db,
                primary_community_id=primary_community_id,
            )
            person = Person(
                name=name,
                canonical_name=canonical_name,
                primary_community_id=normalized_primary_community_id,
            )
            db.add(person)
            db.commit()
            db.refresh(person)
            return person
        finally:
            db.close()

    def list_people(self, include_hidden: bool = False):
        db = SessionLocal()
        try:
            query = (
                db.query(Person)
                .options(joinedload(Person.primary_community))
                .order_by(Person.name.asc())
            )
            if not include_hidden:
                query = query.filter(Person.is_hidden.is_(False))
            return query.all()
        finally:
            db.close()

    def set_hidden(self, person_id: str, is_hidden: bool):
        db = SessionLocal()
        try:
            person = self._get_person(db, person_id)
            person.is_hidden = is_hidden
            db.commit()
            db.refresh(person)
            return person
        finally:
            db.close()

    def delete_person(self, person_id: str):
        db = SessionLocal()
        try:
            normalized_id = self._normalize_person_id(person_id)
            person = db.get(Person, normalized_id)
            if person is None:
                raise HTTPException(status_code=404, detail="Person not found")

            db.execute(
                sa_delete(Person).where(Person.id == normalized_id)
            )
            db.commit()
        finally:
            db.close()

    def update_profile(self, person_id, **kwargs):
        return None

    def get_primary_community_path(
        self,
        person: Person,
        include_hidden_community: bool = False,
    ) -> str | None:
        if person.primary_community_id is None:
            return None

        db = SessionLocal()
        try:
            nodes = []
            current = db.get(Community, person.primary_community_id)
            while current is not None:
                if current.is_hidden and not include_hidden_community:
                    return None
                nodes.append(current.name)
                current = db.get(Community, current.parent_id) if current.parent_id else None
            return " / ".join(reversed(nodes))
        finally:
            db.close()

    def _validate_primary_community(self, db, primary_community_id: str | None):
        if not primary_community_id:
            return None

        try:
            normalized_id = UUID(str(primary_community_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Primary community is invalid") from exc

        community = db.get(Community, normalized_id)
        if community is None or community.is_hidden:
            raise HTTPException(status_code=404, detail="Primary community not found")
        return normalized_id

    def _normalize_person_id(self, person_id: str) -> UUID:
        try:
            return UUID(str(person_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Person is invalid") from exc

    def _get_person(self, db, person_id: str) -> Person:
        normalized_id = self._normalize_person_id(person_id)
        person = db.get(Person, normalized_id)
        if person is None:
            raise HTTPException(status_code=404, detail="Person not found")
        return person
