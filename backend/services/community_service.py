from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete as sa_delete

from backend.app.account_context import get_current_account_id
from backend.db.session import db_session
from backend.models.community.community import Community
from backend.models.search.search_document import SearchDocument
from backend.services.search import SearchService


class CommunityService:
    def __init__(self):
        self._path_cache: dict[tuple[bool, str], str] = {}

    def create_community(
        self,
        name: str,
        description: str | None = None,
        parent_id: str | None = None,
    ):
        with db_session() as db:
            account_id = get_current_account_id()
            normalized_name = name.strip()
            if not normalized_name:
                raise HTTPException(status_code=400, detail="Community name is required")

            normalized_parent_id = self._validate_parent_id(db, parent_id, account_id)
            self._ensure_unique_sibling(
                db=db,
                account_id=account_id,
                name=normalized_name,
                parent_id=normalized_parent_id,
            )
            community = Community(
                account_id=account_id,
                name=normalized_name,
                description=description,
                parent_id=normalized_parent_id,
            )
            db.add(community)
            db.commit()
            db.refresh(community)
            SearchService.invalidate_cache(account_id)
            return community

    def list_communities(self, include_hidden: bool = False):
        with db_session() as db:
            account_id = get_current_account_id()
            all_communities = (
                db.query(Community)
                .filter(Community.account_id == account_id)
                .all()
            )
            if not include_hidden:
                communities = [
                    community
                    for community in all_communities
                    if not community.is_hidden
                ]
            else:
                communities = all_communities

            communities_by_id = {community.id: community for community in all_communities}
            self._path_cache = {
                (include_hidden, str(community.id)): self._build_path_from_map(
                    community=community,
                    communities_by_id=communities_by_id,
                    include_hidden=include_hidden,
                )
                for community in communities
            }
            communities.sort(
                key=lambda item: self._path_cache[(include_hidden, str(item.id))]
            )
            return communities

    def set_hidden(self, community_id: str, is_hidden: bool):
        with db_session() as db:
            account_id = get_current_account_id()
            community = self._get_community(db, community_id)
            community.is_hidden = is_hidden
            if is_hidden:
                db.execute(
                    sa_delete(SearchDocument).where(
                        SearchDocument.account_id == account_id,
                        (
                            (SearchDocument.target_type == "community")
                            & (SearchDocument.target_id == community.id)
                        )
                        | (SearchDocument.community_id == community.id),
                    )
                )
            db.commit()
            db.refresh(community)
            SearchService.invalidate_cache(account_id)
            return community

    def delete_community(self, community_id: str):
        with db_session() as db:
            account_id = get_current_account_id()
            community = self._get_community(db, community_id)
            db.execute(sa_delete(Community).where(Community.id == community.id))
            db.commit()
            SearchService.invalidate_cache(account_id)

    def get_path(self, community: Community, include_hidden: bool = False) -> str:
        cache_key = (include_hidden, str(community.id))
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]

        with db_session() as db:
            nodes = []
            current = db.get(Community, community.id)
            account_id = get_current_account_id()
            while current is not None and current.account_id == account_id:
                if current.is_hidden and not include_hidden:
                    current = db.get(Community, current.parent_id) if current.parent_id else None
                    continue
                nodes.append(current.name)
                current = db.get(Community, current.parent_id) if current.parent_id else None
            return " / ".join(reversed(nodes))

    def _build_path_from_map(
        self,
        community: Community,
        communities_by_id: dict[UUID, Community],
        include_hidden: bool = False,
    ) -> str:
        nodes = []
        current: Community | None = community
        while current is not None:
            if current.is_hidden and not include_hidden:
                current = communities_by_id.get(current.parent_id) if current.parent_id else None
                continue
            nodes.append(current.name)
            current = communities_by_id.get(current.parent_id) if current.parent_id else None
        return " / ".join(reversed(nodes))

    def _validate_parent_id(self, db, parent_id: str | None, account_id: UUID):
        if not parent_id:
            return None

        try:
            normalized_id = UUID(str(parent_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Parent community is invalid") from exc

        parent = db.get(Community, normalized_id)
        if parent is None or parent.account_id != account_id or parent.is_hidden:
            raise HTTPException(status_code=404, detail="Parent community not found")
        return normalized_id

    def _ensure_unique_sibling(
        self,
        db,
        account_id: UUID,
        name: str,
        parent_id: UUID | None,
    ):
        query = db.query(Community).filter(
            Community.account_id == account_id,
            Community.name == name,
        )
        if parent_id is None:
            query = query.filter(Community.parent_id.is_(None))
        else:
            query = query.filter(Community.parent_id == parent_id)

        if query.first() is not None:
            raise HTTPException(
                status_code=409,
                detail="Community already exists under the same parent",
            )

    def _normalize_community_id(self, community_id: str) -> UUID:
        try:
            return UUID(str(community_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Community is invalid") from exc

    def _get_community(self, db, community_id: str) -> Community:
        normalized_id = self._normalize_community_id(community_id)
        community = db.get(Community, normalized_id)
        if community is None or community.account_id != get_current_account_id():
            raise HTTPException(status_code=404, detail="Community not found")
        return community
