from pydantic import BaseModel


class PersonCreateRequest(BaseModel):
    name: str
    canonical_name: str | None = None
    primary_community_id: str | None = None


class CommunityCreateRequest(BaseModel):
    name: str
    description: str | None = None
    parent_id: str | None = None


class TopicCreateRequest(BaseModel):
    name: str
    description: str | None = None
    parent_id: str | None = None


class VisibilityUpdateRequest(BaseModel):
    is_hidden: bool


class PersonResponse(BaseModel):
    id: str
    name: str
    is_hidden: bool
    primary_community_id: str | None
    primary_community_path: str | None


class CommunityResponse(BaseModel):
    id: str
    name: str
    is_hidden: bool
    parent_id: str | None
    path: str


class TopicResponse(BaseModel):
    id: str
    name: str
    parent_id: str | None
    path: str
