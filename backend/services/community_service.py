from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete as sa_delete

from backend.db.session import SessionLocal
from backend.models.community.community import Community


class CommunityService:
    def create_community(
        self,
        name: str,
        description: str | None = None,
        parent_id: str | None = None,
    ):
        db = SessionLocal()
        try:
            normalized_name = name.strip()
            if not normalized_name:
                raise HTTPException(status_code=400, detail="Community name is required")

            normalized_parent_id = self._validate_parent_id(db, parent_id)
            self._ensure_unique_sibling(
                db=db,
                name=normalized_name,
                parent_id=normalized_parent_id,
            )
            community = Community(
                name=normalized_name,
                description=description,
                parent_id=normalized_parent_id,
            )
            db.add(community)
            db.commit()
            db.refresh(community)
            return community
        finally:
            db.close()

    def list_communities(self, include_hidden: bool = False):
        db = SessionLocal()
        try:
            query = db.query(Community)
            if not include_hidden:
                query = query.filter(Community.is_hidden.is_(False))
            communities = query.all()
            communities.sort(key=lambda item: self.get_path(item, include_hidden=include_hidden))
            return communities
        finally:
            db.close()

    def set_hidden(self, community_id: str, is_hidden: bool):
        db = SessionLocal()
        try:
            community = self._get_community(db, community_id)
            community.is_hidden = is_hidden
            db.commit()
            db.refresh(community)
            return community
        finally:
            db.close()

    def delete_community(self, community_id: str):
        db = SessionLocal()
        try:
            normalized_id = self._normalize_community_id(community_id)
            community = db.get(Community, normalized_id)
            if community is None:
                raise HTTPException(status_code=404, detail="Community not found")

            db.execute(
                sa_delete(Community).where(Community.id == normalized_id)
            )
            db.commit()
        finally:
            db.close()

    def get_path(self, community: Community, include_hidden: bool = False) -> str:
        db = SessionLocal()
        try:
            nodes = []
            current = db.get(Community, community.id)
            while current is not None:
                if current.is_hidden and not include_hidden:
                    current = db.get(Community, current.parent_id) if current.parent_id else None
                    continue
                nodes.append(current.name)
                current = db.get(Community, current.parent_id) if current.parent_id else None
            return " / ".join(reversed(nodes))
        finally:
            db.close()

    def _validate_parent_id(self, db, parent_id: str | None):
        if not parent_id:
            return None

        try:
            normalized_id = UUID(str(parent_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Parent community is invalid") from exc

        parent = db.get(Community, normalized_id)
        if parent is None or parent.is_hidden:
            raise HTTPException(status_code=404, detail="Parent community not found")
        return normalized_id

    def _ensure_unique_sibling(self, db, name: str, parent_id: UUID | None):
        query = db.query(Community).filter(Community.name == name)
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
        if community is None:
            raise HTTPException(status_code=404, detail="Community not found")
        return community
