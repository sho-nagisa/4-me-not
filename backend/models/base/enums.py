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
