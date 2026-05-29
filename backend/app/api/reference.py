from fastapi import APIRouter

from backend.app.schemas.common import StatusResponse
from backend.app.schemas.reference import (
    CommunityCreateRequest,
    CommunityResponse,
    PersonCreateRequest,
    PersonResponse,
    TopicCreateRequest,
    TopicResponse,
    VisibilityUpdateRequest,
)
from backend.app.serializers.reference import (
    serialize_community,
    serialize_person,
    serialize_topic,
)
from backend.services.community_service import CommunityService
from backend.services.interaction_service import InteractionService
from backend.services.person_service import PersonService
from backend.services.topic_service import TopicService


router = APIRouter(tags=["reference"])


@router.get("/persons", response_model=list[PersonResponse])
def list_persons(include_hidden: bool = False) -> list[PersonResponse]:
    service = PersonService()
    persons = service.list_people(include_hidden=include_hidden)
    return [serialize_person(person, service, include_hidden=include_hidden) for person in persons]


@router.post("/persons", response_model=PersonResponse)
def create_person(payload: PersonCreateRequest) -> PersonResponse:
    service = PersonService()
    person = service.create_person(
        name=payload.name,
        canonical_name=payload.canonical_name,
        primary_community_id=payload.primary_community_id,
    )
    return serialize_person(person, service, include_hidden=True)


@router.patch("/persons/{person_id}", response_model=PersonResponse)
def update_person_visibility(
    person_id: str,
    payload: VisibilityUpdateRequest,
) -> PersonResponse:
    service = PersonService()
    person = service.set_hidden(person_id=person_id, is_hidden=payload.is_hidden)
    return serialize_person(person, service, include_hidden=True)


@router.delete("/persons/{person_id}", response_model=StatusResponse)
def delete_person(person_id: str) -> StatusResponse:
    service = PersonService()
    service.delete_person(person_id=person_id)
    return StatusResponse(status="ok")


@router.get("/persons/interaction-counts")
def list_person_interaction_counts(community_id: str | None = None):
    service = InteractionService()
    return service.list_person_interaction_counts(community_id=community_id)


@router.get("/persons/{person_id}/interactions")
def list_person_interactions(person_id: str):
    service = InteractionService()
    return service.list_interactions(person_id=person_id)


@router.get("/persons/{person_id}/dashboard")
def get_person_dashboard(person_id: str):
    service = InteractionService()
    return service.get_person_dashboard(person_id=person_id)


@router.get("/communities", response_model=list[CommunityResponse])
def list_communities(include_hidden: bool = False) -> list[CommunityResponse]:
    service = CommunityService()
    communities = service.list_communities(include_hidden=include_hidden)
    return [
        serialize_community(community, service, include_hidden=include_hidden)
        for community in communities
    ]


@router.post("/communities", response_model=CommunityResponse)
def create_community(payload: CommunityCreateRequest) -> CommunityResponse:
    service = CommunityService()
    community = service.create_community(
        name=payload.name,
        description=payload.description,
        parent_id=payload.parent_id,
    )
    return serialize_community(community, service, include_hidden=True)


@router.patch("/communities/{community_id}", response_model=CommunityResponse)
def update_community_visibility(
    community_id: str,
    payload: VisibilityUpdateRequest,
) -> CommunityResponse:
    service = CommunityService()
    community = service.set_hidden(community_id=community_id, is_hidden=payload.is_hidden)
    return serialize_community(community, service, include_hidden=True)


@router.delete("/communities/{community_id}", response_model=StatusResponse)
def delete_community(community_id: str) -> StatusResponse:
    service = CommunityService()
    service.delete_community(community_id=community_id)
    return StatusResponse(status="ok")


@router.get("/topics", response_model=list[TopicResponse])
def list_topics() -> list[TopicResponse]:
    service = TopicService()
    topics = service.list_topics()
    return [serialize_topic(topic, service) for topic in topics]


@router.post("/topics", response_model=TopicResponse)
def create_topic(payload: TopicCreateRequest) -> TopicResponse:
    service = TopicService()
    topic = service.create_topic(
        name=payload.name,
        description=payload.description,
        parent_id=payload.parent_id,
    )
    return serialize_topic(topic, service)
