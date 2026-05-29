from backend.app.schemas.reference import (
    CommunityResponse,
    PersonResponse,
    TopicResponse,
)
from backend.models.community.community import Community
from backend.models.interaction.topic import Topic
from backend.models.person.person import Person
from backend.services.community_service import CommunityService
from backend.services.person_service import PersonService
from backend.services.topic_service import TopicService


def serialize_person(
    person: Person,
    service: PersonService,
    include_hidden: bool = False,
) -> PersonResponse:
    primary_community_id = None
    if person.primary_community_id and (
        include_hidden
        or not person.primary_community
        or not person.primary_community.is_hidden
    ):
        primary_community_id = str(person.primary_community_id)

    return PersonResponse(
        id=str(person.id),
        name=person.name,
        is_hidden=bool(person.is_hidden),
        primary_community_id=primary_community_id,
        primary_community_path=service.get_primary_community_path(
            person,
            include_hidden_community=include_hidden,
        ),
    )


def serialize_community(
    community: Community,
    service: CommunityService,
    include_hidden: bool = False,
) -> CommunityResponse:
    return CommunityResponse(
        id=str(community.id),
        name=community.name,
        is_hidden=bool(community.is_hidden),
        parent_id=str(community.parent_id) if community.parent_id else None,
        path=service.get_path(community, include_hidden=include_hidden),
    )


def serialize_topic(topic: Topic, service: TopicService) -> TopicResponse:
    return TopicResponse(
        id=str(topic.id),
        name=topic.name,
        parent_id=str(topic.parent_id) if topic.parent_id else None,
        path=service.get_path(topic),
    )
