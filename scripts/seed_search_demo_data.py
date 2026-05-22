import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.account_context import get_current_account_id
from backend.db.session import SessionLocal
from backend.models.base.enums import InteractionType, ShareLevel
from backend.models.community.community import Community
from backend.models.interaction.interaction import Interaction
from backend.models.interaction.topic import Topic
from backend.models.person.person import Person
from backend.services.search import SearchService
from backend.testing.demo_data import cleanup_demo_data


PREFIX = "[SEARCH-DEMO]"
RANDOM_SEED = 20260519
# Keep the local dataset readable while still large enough to evaluate search.
# The base demo seed creates 30 interactions, so this makes the combined demo
# dataset about 150 interactions.
INTERACTION_COUNT = 120


PEOPLE = [
    "佐藤彩花",
    "中村悠斗",
    "鈴木美咲",
    "山本蓮",
    "小林奈々",
    "高橋海斗",
    "伊藤咲希",
    "渡辺健太",
    "加藤由奈",
    "田中颯太",
    "森田航",
    "藤井真央",
    "岡田梨央",
    "前田拓海",
    "清水遥",
    "石川大和",
    "橋本結衣",
    "斎藤陸",
    "松本杏奈",
    "井上直樹",
    "木村葵",
    "林優斗",
    "山崎紗季",
    "池田陽菜",
    "阿部翔",
    "村上琴音",
    "近藤瑞希",
    "長谷川湊",
    "遠藤花音",
    "青木亮",
]


TOPIC_TREE = {
    "就活": ["面接", "志望動機", "ガクチカ", "企業選び", "ES添削"],
    "アルバイト": ["シフト", "接客", "店長との相談", "バイト先の人間関係", "新人教育"],
    "恋愛": ["気になる人", "デート", "返信頻度", "価値観", "告白相談"],
    "日常": ["最近の予定", "趣味", "大学生活", "悩み相談"],
}


JOB_TEMPLATES = [
    "{person}とは{community}で会って、面接で話す志望動機の軸を一緒に整理した。第一志望の理由はまだ抽象的で、原体験を足すと良さそうだった。",
    "{person}がガクチカをアルバイトの接客改善で話したいと言っていて、数字よりも周囲を巻き込んだ流れを強調したい様子だった。",
    "{person}からESの自己PRを見てほしいと相談された。強みは継続力だが、具体例がサークルと授業で少し散らばっていた。",
    "{person}は企業選びで人材業界とIT業界を迷っていた。人と関わる仕事への興味が強く、営業職も候補にしている。",
    "{person}とOB訪問の準備について話した。質問リストは作っていたが、入社後の働き方をもっと聞きたいと言っていた。",
]


PART_TIME_TEMPLATES = [
    "{person}はカフェのアルバイトで新人教育を任され始めた。教え方がきつく見えないか少し気にしていた。",
    "{person}がバイトのシフト調整で店長と揉めかけた話をしてくれた。試験期間だけは早めに共有することにしたらしい。",
    "{person}とは接客中の失敗談で盛り上がった。クレーム対応で焦ったが、先輩がフォローしてくれて助かったとのこと。",
    "{person}は塾講師のアルバイトで、生徒の進路相談を聞くことが増えた。就活にもつながる経験だと感じている。",
    "{person}がバイト先の人間関係について相談してくれた。仲の良い先輩と距離が近くなりすぎて少し気まずいらしい。",
]


LOVE_TEMPLATES = [
    "{person}から気になる人への返信頻度について相談された。相手は同じコミュニティの人で、焦らず自然に誘いたい様子だった。",
    "{person}とは恋愛観の話をした。付き合うなら価値観の近さと生活リズムをかなり重視していると言っていた。",
    "{person}が初デートの場所を迷っていた。静かに話せるカフェか、映画のあとに軽くご飯に行く案で悩んでいた。",
    "{person}はサークルの先輩が気になっているらしい。ただ、周りに知られるのはまだ避けたいと言っていた。",
    "{person}から告白するタイミングについて聞かれた。相手の試験が終わってから、重くなりすぎない形が良さそうだった。",
]


DAILY_TEMPLATES = [
    "{person}とは最近の予定について話した。授業、バイト、就活が重なっていて、週末だけは空けたいと言っていた。",
    "{person}が最近ハマっている趣味について話してくれた。写真を撮るのが楽しく、次は旅行先でも撮りたいらしい。",
    "{person}とは大学生活の悩みを少し話した。周りと比べて焦るが、自分のペースで進めたいという気持ちがある。",
    "{person}が研究室やゼミの人間関係について少し疲れていると言っていた。深刻ではないが距離感を調整したい様子。",
]


SHARE_LEVELS = [
    ShareLevel.SHARED,
    ShareLevel.SHARED,
    ShareLevel.SHARED,
    ShareLevel.PARTIAL,
    ShareLevel.WITHHELD,
]


INTERACTION_TYPES = [
    InteractionType.TALK,
    InteractionType.MEETING,
    InteractionType.MESSAGE,
    InteractionType.EVENT,
]


def slugify(index: int, name: str) -> str:
    return f"search-demo-{index:02d}-{name.encode('unicode_escape').decode('ascii')}"


def get_or_create_topic(db, account_id, name: str, parent: Topic | None = None) -> Topic:
    query = db.query(Topic).filter(Topic.account_id == account_id, Topic.name == name)
    if parent is None:
        query = query.filter(Topic.parent_id.is_(None))
    else:
        query = query.filter(Topic.parent_id == parent.id)
    topic = query.first()
    if topic is not None:
        return topic

    topic = Topic(
        account_id=account_id,
        title=name,
        name=name,
        description=f"{PREFIX} generated search demo topic",
        parent_id=parent.id if parent else None,
    )
    db.add(topic)
    db.flush()
    return topic


def pick_template(topic_root: str, rng: random.Random) -> str:
    if topic_root == "就活":
        return rng.choice(JOB_TEMPLATES)
    if topic_root == "アルバイト":
        return rng.choice(PART_TIME_TEMPLATES)
    if topic_root == "恋愛":
        return rng.choice(LOVE_TEMPLATES)
    return rng.choice(DAILY_TEMPLATES)


def main() -> None:
    cleanup_demo_data(PREFIX)

    rng = random.Random(RANDOM_SEED)
    now = datetime.now(timezone.utc)
    account_id = get_current_account_id()

    db = SessionLocal()
    try:
        communities = (
            db.query(Community)
            .filter(Community.account_id == account_id, Community.is_hidden.is_(False))
            .order_by(Community.name.asc())
            .all()
        )
        if not communities:
            raise RuntimeError("Visible communities are required before seeding demo data.")

        topic_roots: dict[str, Topic] = {}
        topic_children: dict[str, list[Topic]] = {}
        for root_name, child_names in TOPIC_TREE.items():
            root = get_or_create_topic(db, account_id, root_name)
            topic_roots[root_name] = root
            topic_children[root_name] = [
                get_or_create_topic(db, account_id, child_name, parent=root)
                for child_name in child_names
            ]

        people: list[Person] = []
        for index, name in enumerate(PEOPLE, start=1):
            person = Person(
                account_id=account_id,
                name=name,
                canonical_name=f"{PREFIX}:{slugify(index, name)}",
                description=f"{PREFIX} generated search demo person",
                primary_community_id=rng.choice(communities).id,
            )
            db.add(person)
            people.append(person)
        db.flush()

        interactions: list[Interaction] = []
        topic_root_names = list(TOPIC_TREE.keys())
        for index in range(INTERACTION_COUNT):
            person = rng.choice(people)
            community = rng.choice(communities)
            root_name = rng.choices(
                topic_root_names,
                weights=[36, 28, 24, 12],
                k=1,
            )[0]
            topic = rng.choice(topic_children[root_name])
            template = pick_template(root_name, rng)
            content = template.format(
                person=person.name,
                community=community.name,
            )
            days_ago = rng.randint(0, 210)
            hours_ago = rng.randint(0, 23)
            note = (
                f"{PREFIX} {root_name} / {topic.name} / "
                f"目視確認用デモ {index + 1:03d}"
            )
            interactions.append(
                Interaction(
                    account_id=account_id,
                    person_id=person.id,
                    community_id=community.id,
                    topic_id=topic.id,
                    type=rng.choice(INTERACTION_TYPES),
                    share_level=rng.choice(SHARE_LEVELS),
                    occurred_at=now - timedelta(days=days_ago, hours=hours_ago),
                    content=content,
                    note=note,
                )
            )

        db.add_all(interactions)
        db.commit()
    finally:
        db.close()

    indexed = SearchService().rebuild_account_index()
    print("Search demo data inserted successfully.")
    print(f"prefix: {PREFIX}")
    print(f"people: {len(PEOPLE)}")
    print(f"interactions: {INTERACTION_COUNT}")
    print(f"indexed_people: {indexed['people']}")
    print(f"indexed_communities: {indexed['communities']}")
    print(f"indexed_topics: {indexed['topics']}")
    print(f"indexed_interactions: {indexed['interactions']}")


if __name__ == "__main__":
    main()
