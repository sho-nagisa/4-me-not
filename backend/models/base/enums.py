from enum import Enum


class TaskStatus(str, Enum):
    TODO = "todo"
    DONE = "done"
    SKIPPED = "skipped"


class InteractionType(str, Enum):
    TALK = "talk"
    MEETING = "meeting"
    CALL = "call"
    MESSAGE = "message"


class RelationType(str, Enum):
    INTRODUCED_BY = "introduced_by"
    FRIEND = "friend"
    MENTOR = "mentor"
    COWORKER = "coworker"
    FAMILY = "family"
    CONFLICT = "conflict"


class ReminderPurpose(str, Enum):
    MEETING_PREPARATION = "meeting_preparation"
    FOLLOW_UP = "follow_up"
    LOG_PROMPT = "log_prompt"
    BIRTHDAY = "birthday"
    TOPIC_EXPIRY = "topic_expiry"
from enum import IntEnum
class CommunityRole(IntEnum):
    OWNER = 1
    ADMIN = 2
    MEMBER = 3
    GUEST = 4

class InteractionType(IntEnum):
    TALK = 1
    MEETING = 2
    MESSAGE = 3
    EVENT = 4

class InsightType(IntEnum):
    LIKE = 1
    DISLIKE = 2
    TRAIT = 3
    WARNING = 4

class RelationType(IntEnum):
    FRIEND = 1
    COLLEAGUE = 2
    FAMILY = 3
    SUPERIOR = 4
    SUBORDINATE = 5