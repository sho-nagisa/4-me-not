from uuid import UUID

from fastapi import HTTPException

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
            normalized_parent_id = self._validate_parent_id(db, parent_id)
            community = Community(
                name=name,
                description=description,
                parent_id=normalized_parent_id,
            )
            db.add(community)
            db.commit()
            db.refresh(community)
            return community
        finally:
            db.close()

    def list_communities(self):
        db = SessionLocal()
        try:
            communities = db.query(Community).all()
            communities.sort(key=lambda item: self.get_path(item))
            return communities
        finally:
            db.close()

    def get_path(self, community: Community) -> str:
        nodes = []
        current = community
        while current is not None:
            nodes.append(current.name)
            current = current.parent
        return " / ".join(reversed(nodes))

    def _validate_parent_id(self, db, parent_id: str | None):
        if not parent_id:
            return None

        try:
            normalized_id = UUID(str(parent_id))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Parent community is invalid") from exc

        parent = db.get(Community, normalized_id)
        if parent is None:
            raise HTTPException(status_code=404, detail="Parent community not found")
        return normalized_id
