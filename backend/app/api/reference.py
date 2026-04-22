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


@router.get("/persons")
def list_persons():
    service = PersonService()
    persons = service.list_people()
    return [
        {
            "id": str(person.id),
            "name": person.name,
            "primary_community_id": str(person.primary_community_id) if person.primary_community_id else None,
            "primary_community_path": service.get_primary_community_path(person),
        }
        for person in persons
    ]


@router.post("/persons")
def create_person(payload: PersonCreateRequest):
    service = PersonService()
    person = service.create_person(
        name=payload.name,
        canonical_name=payload.canonical_name,
        primary_community_id=payload.primary_community_id,
    )
    return {
        "id": str(person.id),
        "name": person.name,
        "primary_community_id": str(person.primary_community_id) if person.primary_community_id else None,
        "primary_community_path": service.get_primary_community_path(person),
    }


@router.get("/persons/{person_id}/interactions")
def list_person_interactions(person_id: str):
    service = InteractionService()
    return service.list_interactions(person_id=person_id)


@router.get("/persons/{person_id}/dashboard")
def get_person_dashboard(person_id: str):
    service = InteractionService()
    return service.get_person_dashboard(person_id=person_id)


@router.get("/communities")
def list_communities():
    service = CommunityService()
    communities = service.list_communities()
    return [
        {
            "id": str(community.id),
            "name": community.name,
            "parent_id": str(community.parent_id) if community.parent_id else None,
            "path": service.get_path(community),
        }
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
    return {
        "id": str(community.id),
        "name": community.name,
        "parent_id": str(community.parent_id) if community.parent_id else None,
        "path": service.get_path(community),
    }


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
