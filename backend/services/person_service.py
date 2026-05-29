from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete as sa_delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from backend.app.account_context import get_current_account_id
from backend.db.session import db_session
from backend.models.community.community import Community
from backend.models.person.person import Person
from backend.models.search.search_document import SearchDocument
from backend.services.hierarchy_path import (
    build_hierarchy_path,
    build_hierarchy_path_from_map,
)
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
        with db_session() as db:
            account_id = get_current_account_id()
            normalized_name = name.strip()
            if not normalized_name:
                raise HTTPException(status_code=400, detail="Person name is required")
            normalized_canonical_name = (
                canonical_name.strip() if canonical_name and canonical_name.strip() else None
            )
            if normalized_canonical_name:
                existing = (
                    db.query(Person.id)
                    .filter(
                        Person.account_id == account_id,
                        Person.canonical_name == normalized_canonical_name,
                    )
                    .first()
                )
                if existing is not None:
                    raise HTTPException(status_code=409, detail="Person already exists")
            normalized_primary_community_id = self._validate_primary_community(
                db=db,
                primary_community_id=primary_community_id,
                account_id=account_id,
            )
            person = Person(
                account_id=account_id,
                name=normalized_name,
                canonical_name=normalized_canonical_name,
                primary_community_id=normalized_primary_community_id,
            )
            db.add(person)
            try:
                db.commit()
            except IntegrityError as exc:
                db.rollback()
                raise HTTPException(status_code=409, detail="Person already exists") from exc
            db.refresh(person)
            SearchService.invalidate_cache(account_id)
            return person

    def list_people(self, include_hidden: bool = False):
        with db_session() as db:
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
                    ] = build_hierarchy_path_from_map(
                        community,
                        communities_by_id,
                        include_hidden=include_hidden,
                        hidden_mode="block",
                    )

            return people

    def set_hidden(self, person_id: str, is_hidden: bool):
        with db_session() as db:
            account_id = get_current_account_id()
            person = self._get_person(db, person_id)
            person.is_hidden = is_hidden
            if is_hidden:
                db.execute(
                    sa_delete(SearchDocument).where(
                        SearchDocument.account_id == account_id,
                        (
                            (SearchDocument.target_type == "person")
                            & (SearchDocument.target_id == person.id)
                        )
                        | (SearchDocument.person_id == person.id),
                    )
                )
            db.commit()
            db.refresh(person)
            SearchService.invalidate_cache(account_id)
            return person

    def delete_person(self, person_id: str):
        with db_session() as db:
            account_id = get_current_account_id()
            person = self._get_person(db, person_id)
            db.execute(sa_delete(Person).where(Person.id == person.id))
            db.commit()
            SearchService.invalidate_cache(account_id)

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

        with db_session() as db:
            account_id = get_current_account_id()
            current = db.get(Community, person.primary_community_id)
            return build_hierarchy_path(
                current,
                parent_getter=lambda item: (
                    db.get(Community, item.parent_id) if item.parent_id else None
                ),
                include_hidden=include_hidden_community,
                hidden_mode="block",
                scope_filter=lambda item: item.account_id == account_id,
            )

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
