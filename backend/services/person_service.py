from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete as sa_delete
from sqlalchemy.orm import joinedload

from backend.app.account_context import get_current_account_id
from backend.db.session import SessionLocal
from backend.models.community.community import Community
from backend.models.person.person import Person
from backend.services.search import SearchService


class PersonService:
    def __init__(self):
        self._primary_community_path_cache: dict[tuple[bool, str], str | None] = {}

    def create_person(
        self,
        name: str,
        canonical_name: str | None = None,
        primary_community_id: str | None = None,
    ):
        db = SessionLocal()
        try:
            account_id = get_current_account_id()
            normalized_primary_community_id = self._validate_primary_community(
                db=db,
                primary_community_id=primary_community_id,
                account_id=account_id,
            )
            person = Person(
                account_id=account_id,
                name=name,
                canonical_name=canonical_name,
                primary_community_id=normalized_primary_community_id,
            )
            db.add(person)
            db.commit()
            db.refresh(person)
            SearchService.invalidate_cache(account_id)
            return person
        finally:
            db.close()

    def list_people(self, include_hidden: bool = False):
        db = SessionLocal()
        try:
            account_id = get_current_account_id()
            query = (
                db.query(Person)
                .options(joinedload(Person.primary_community))
                .filter(Person.account_id == account_id)
                .order_by(Person.name.asc())
            )
            if not include_hidden:
                query = query.filter(Person.is_hidden.is_(False))
            people = query.all()

            primary_community_ids = {
                person.primary_community_id
                for person in people
                if person.primary_community_id is not None
            }
            self._primary_community_path_cache = {}
            if primary_community_ids:
                communities = (
                    db.query(Community)
                    .filter(Community.account_id == account_id)
                    .all()
                )
                communities_by_id = {community.id: community for community in communities}
                for community_id in primary_community_ids:
                    community = communities_by_id.get(community_id)
                    if community is None:
                        continue
                    self._primary_community_path_cache[
                        (include_hidden, str(community_id))
                    ] = self._build_community_path_from_map(
                        community=community,
                        communities_by_id=communities_by_id,
                        include_hidden=include_hidden,
                    )

            return people
        finally:
            db.close()

    def set_hidden(self, person_id: str, is_hidden: bool):
        db = SessionLocal()
        try:
            account_id = get_current_account_id()
            person = self._get_person(db, person_id)
            person.is_hidden = is_hidden
            db.commit()
            db.refresh(person)
            SearchService.invalidate_cache(account_id)
            return person
        finally:
            db.close()

    def delete_person(self, person_id: str):
        db = SessionLocal()
        try:
            account_id = get_current_account_id()
            person = self._get_person(db, person_id)
            db.execute(sa_delete(Person).where(Person.id == person.id))
            db.commit()
            SearchService.invalidate_cache(account_id)
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

        cache_key = (include_hidden_community, str(person.primary_community_id))
        if cache_key in self._primary_community_path_cache:
            return self._primary_community_path_cache[cache_key]

        db = SessionLocal()
        try:
            account_id = get_current_account_id()
            nodes = []
            current = db.get(Community, person.primary_community_id)
            while current is not None and current.account_id == account_id:
                if current.is_hidden and not include_hidden_community:
                    return None
                nodes.append(current.name)
                current = db.get(Community, current.parent_id) if current.parent_id else None
            return " / ".join(reversed(nodes))
        finally:
            db.close()

    def _build_community_path_from_map(
        self,
        community: Community,
        communities_by_id: dict[UUID, Community],
        include_hidden: bool = False,
    ) -> str | None:
        nodes = []
        current: Community | None = community
        while current is not None:
            if current.is_hidden and not include_hidden:
                return None
            nodes.append(current.name)
            current = communities_by_id.get(current.parent_id) if current.parent_id else None
        return " / ".join(reversed(nodes))

    def _validate_primary_community(
        self,
        db,
        primary_community_id: str | None,
        account_id: UUID,
    ):
        if not primary_community_id:
            return None

        try:
            normalized_id = UUID(str(primary_community_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Primary community is invalid") from exc

        community = db.get(Community, normalized_id)
        if (
            community is None
            or community.account_id != account_id
            or community.is_hidden
        ):
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
        if person is None or person.account_id != get_current_account_id():
            raise HTTPException(status_code=404, detail="Person not found")
        return person
