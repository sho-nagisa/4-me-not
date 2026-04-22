from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.community_service import CommunityService
from backend.services.interaction_service import InteractionService
from backend.services.person_service import PersonService
from backend.services.topic_service import TopicService


router = APIRouter(tags=["reference"])


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


def serialize_person(person, service: PersonService, include_hidden: bool = False):
    return {
        "id": str(person.id),
        "name": person.name,
        "is_hidden": bool(person.is_hidden),
        "primary_community_id": (
            str(person.primary_community_id)
            if person.primary_community_id
            and (
                include_hidden
                or not person.primary_community
                or not person.primary_community.is_hidden
            )
            else None
        ),
        "primary_community_path": service.get_primary_community_path(
            person,
            include_hidden_community=include_hidden,
        ),
    }


def serialize_community(community, service: CommunityService, include_hidden: bool = False):
    return {
        "id": str(community.id),
        "name": community.name,
        "is_hidden": bool(community.is_hidden),
        "parent_id": str(community.parent_id) if community.parent_id else None,
        "path": service.get_path(community, include_hidden=include_hidden),
    }


@router.get("/persons")
def list_persons(include_hidden: bool = False):
    service = PersonService()
    persons = service.list_people(include_hidden=include_hidden)
    return [serialize_person(person, service, include_hidden=include_hidden) for person in persons]


@router.post("/persons")
def create_person(payload: PersonCreateRequest):
    service = PersonService()
    person = service.create_person(
        name=payload.name,
        canonical_name=payload.canonical_name,
        primary_community_id=payload.primary_community_id,
    )
    return serialize_person(person, service, include_hidden=True)


@router.patch("/persons/{person_id}")
def update_person_visibility(person_id: str, payload: VisibilityUpdateRequest):
    service = PersonService()
    person = service.set_hidden(person_id=person_id, is_hidden=payload.is_hidden)
    return serialize_person(person, service, include_hidden=True)


@router.delete("/persons/{person_id}")
def delete_person(person_id: str):
    service = PersonService()
    service.delete_person(person_id=person_id)
    return {"status": "ok"}


@router.get("/persons/{person_id}/interactions")
def list_person_interactions(person_id: str):
    service = InteractionService()
    return service.list_interactions(person_id=person_id)


@router.get("/persons/{person_id}/dashboard")
def get_person_dashboard(person_id: str):
    service = InteractionService()
    return service.get_person_dashboard(person_id=person_id)


@router.get("/communities")
def list_communities(include_hidden: bool = False):
    service = CommunityService()
    communities = service.list_communities(include_hidden=include_hidden)
    return [
        serialize_community(community, service, include_hidden=include_hidden)
        for community in communities
    ]


@router.post("/communities")
def create_community(payload: CommunityCreateRequest):
    service = CommunityService()
    community = service.create_community(
        name=payload.name,
        description=payload.description,
        parent_id=payload.parent_id,
    )
    return serialize_community(community, service, include_hidden=True)


@router.patch("/communities/{community_id}")
def update_community_visibility(community_id: str, payload: VisibilityUpdateRequest):
    service = CommunityService()
    community = service.set_hidden(community_id=community_id, is_hidden=payload.is_hidden)
    return serialize_community(community, service, include_hidden=True)


@router.delete("/communities/{community_id}")
def delete_community(community_id: str):
    service = CommunityService()
    service.delete_community(community_id=community_id)
    return {"status": "ok"}


@router.get("/topics")
def list_topics():
    service = TopicService()
    topics = service.list_topics()
    return [
        {
            "id": str(topic.id),
            "name": topic.name,
            "parent_id": str(topic.parent_id) if topic.parent_id else None,
            "path": service.get_path(topic),
        }
        for topic in topics
    ]


@router.post("/topics")
def create_topic(payload: TopicCreateRequest):
    service = TopicService()
    topic = service.create_topic(
        name=payload.name,
        description=payload.description,
        parent_id=payload.parent_id,
    )
    return {
        "id": str(topic.id),
        "name": topic.name,
        "parent_id": str(topic.parent_id) if topic.parent_id else None,
        "path": service.get_path(topic),
    }
