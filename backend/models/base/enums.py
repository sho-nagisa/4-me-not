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


class TaskStatus(IntEnum):
    TODO = 1
    DONE = 2
    SKIPPED = 3


class ShareLevel(IntEnum):
    SHARED = 1
    PARTIAL = 2
    WITHHELD = 3


class ReminderPurpose(IntEnum):
    MEETING_PREPARATION = 1
    FOLLOW_UP = 2
    LOG_PROMPT = 3
    BIRTHDAY = 4
    TOPIC_EXPIRY = 5
