from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from backend.db.session import SessionLocal
from backend.models.base.enums import InteractionType, ShareLevel
from backend.models.community.community import Community
from backend.models.interaction.interaction import Interaction
from backend.models.interaction.topic import Topic
from backend.models.person.person import Person


DEFAULT_PREFIX = "[DEMO]"


@dataclass
class SeedResult:
    prefix: str
    community_count: int
    topic_count: int
    person_count: int
    interaction_count: int


def cleanup_demo_data(prefix: str = DEFAULT_PREFIX) -> None:
    db = SessionLocal()
    try:
        interactions = (
            db.query(Interaction)
            .filter(Interaction.note.is_not(None))
            .filter(Interaction.note.like(f"{prefix}%"))
            .all()
        )
        for interaction in interactions:
            db.delete(interaction)
        db.flush()

        people = (
            db.query(Person)
            .filter(Person.canonical_name.is_not(None))
            .filter(Person.canonical_name.like(f"{prefix}%"))
            .all()
        )
        for person in people:
            db.delete(person)
        db.flush()

        topics = (
            db.query(Topic)
            .filter(Topic.description.is_not(None))
            .filter(Topic.description.like(f"{prefix}%"))
            .all()
        )
        for topic in topics:
            db.delete(topic)
        db.flush()

        communities = (
            db.query(Community)
            .filter(Community.description.is_not(None))
            .filter(Community.description.like(f"{prefix}%"))
            .all()
        )
        for community in communities:
            db.delete(community)

        db.commit()
    finally:
        db.close()


def seed_demo_data(prefix: str = DEFAULT_PREFIX) -> SeedResult:
    cleanup_demo_data(prefix)

    db = SessionLocal()
    try:
        marker = f"{prefix} generated demo data"
        now = datetime.now(timezone.utc)

        communities: dict[str, Community] = {}
        topics: dict[str, Topic] = {}
        people: dict[str, Person] = {}

        def add_community(
            key: str, name: str, parent_key: str | None = None
        ) -> Community:
            community = Community(
                name=name,
                description=marker,
                parent_id=communities[parent_key].id if parent_key else None,
            )
            db.add(community)
            db.flush()
            communities[key] = community
            return community

        def add_topic(key: str, name: str, parent_key: str | None = None) -> Topic:
            topic = Topic(
                title=name,
                name=name,
                description=marker,
                parent_id=topics[parent_key].id if parent_key else None,
            )
            db.add(topic)
            db.flush()
            topics[key] = topic
            return topic

        def add_person(
            key: str, name: str, slug: str, primary_community_key: str | None
        ) -> Person:
            person = Person(
                name=name,
                canonical_name=f"{prefix}:{slug}",
                description=marker,
                primary_community_id=(
                    communities[primary_community_key].id
                    if primary_community_key
                    else None
                ),
            )
            db.add(person)
            db.flush()
            people[key] = person
            return person

        add_community("university", "青峰大学")
        add_community("tennis_circle", "テニスサークル", "university")
        add_community("practice", "練習", "tennis_circle")
        add_community("after_party", "飲み会", "tennis_circle")
        add_community("economics_seminar", "経済ゼミ", "university")
        add_community("research_lab", "研究室", "university")
        add_community("internship", "長期インターン")
        add_community("product_team", "プロダクトチーム", "internship")
        add_community("recruiting_team", "採用広報チーム", "internship")
        add_community("hometown", "地元のつながり")
        add_community("hometown_friends", "高校の友人", "hometown")

        add_topic("career", "就活")
        add_topic("interviews", "面接", "career")
        add_topic("motivation", "志望動機", "career")
        add_topic("job_story", "ガクチカ", "career")
        add_topic("daily", "日常")
        add_topic("recent_schedule", "最近の予定", "daily")
        add_topic("hobbies", "趣味", "daily")
        add_topic("university_topic", "大学")
        add_topic("classes", "授業", "university_topic")
        add_topic("research", "研究", "university_topic")

        add_person("ayaka", "佐藤彩花", "sato-ayaka", "practice")
        add_person("yuto", "中村悠斗", "nakamura-yuto", "after_party")
        add_person("misaki", "鈴木美咲", "suzuki-misaki", "product_team")
        add_person("ren", "山本蓮", "yamamoto-ren", "economics_seminar")
        add_person("nana", "小林奈々", "kobayashi-nana", "product_team")
        add_person("kaito", "高橋海斗", "takahashi-kaito", "recruiting_team")
        add_person("saki", "伊藤咲希", "ito-saki", "research_lab")
        add_person("kenta", "渡辺健太", "watanabe-kenta", "practice")
        add_person("yuna", "加藤由奈", "kato-yuna", "after_party")
        add_person("sota", "田中颯太", "tanaka-sota", "hometown_friends")

        def build_interaction(
            *,
            person_key: str,
            community_key: str | None,
            topic_key: str | None,
            interaction_type: InteractionType,
            share_level: ShareLevel,
            days_ago: int,
            hours_ago: int = 0,
            content: str,
            note: str,
        ) -> Interaction:
            return Interaction(
                person_id=people[person_key].id,
                community_id=communities[community_key].id if community_key else None,
                topic_id=topics[topic_key].id if topic_key else None,
                type=interaction_type,
                share_level=share_level,
                occurred_at=now - timedelta(days=days_ago, hours=hours_ago),
                content=content,
                note=f"{prefix} {note}",
            )

        interactions = [
            build_interaction(
                person_key="ayaka",
                community_key="practice",
                topic_key="interviews",
                interaction_type=InteractionType.MEETING,
                share_level=ShareLevel.SHARED,
                days_ago=28,
                content="面接で話した自己紹介の流れと、学生時代に力を入れたことの組み立て方を一緒に整理した。",
                note="次回は逆質問の候補も聞いてみる。",
            ),
            build_interaction(
                person_key="ayaka",
                community_key="after_party",
                topic_key="motivation",
                interaction_type=InteractionType.TALK,
                share_level=ShareLevel.PARTIAL,
                days_ago=26,
                hours_ago=3,
                content="企業選びの軸は教えてくれたが、第一志望まではまだ絞れていないと言っていた。",
                note="志望業界はIT寄りまで共有済み。",
            ),
            build_interaction(
                person_key="ayaka",
                community_key="practice",
                topic_key="recent_schedule",
                interaction_type=InteractionType.MESSAGE,
                share_level=ShareLevel.WITHHELD,
                days_ago=24,
                hours_ago=6,
                content="今週は面接が立て込んでいて練習参加が難しいと連絡あり。",
                note="具体的な社名は伏せたまま。",
            ),
            build_interaction(
                person_key="yuto",
                community_key="after_party",
                topic_key="hobbies",
                interaction_type=InteractionType.TALK,
                share_level=ShareLevel.SHARED,
                days_ago=27,
                content="最近はカメラにはまっていて、休日は街歩きをしながら写真を撮っているらしい。",
                note="次は写真展の話を振ると盛り上がりそう。",
            ),
            build_interaction(
                person_key="yuto",
                community_key="practice",
                topic_key="recent_schedule",
                interaction_type=InteractionType.TALK,
                share_level=ShareLevel.SHARED,
                days_ago=23,
                hours_ago=2,
                content="来週はサークルの新歓準備でかなり忙しいとのことだった。",
                note="新歓後にまたゆっくり話せそう。",
            ),
            build_interaction(
                person_key="yuto",
                community_key="after_party",
                topic_key="interviews",
                interaction_type=InteractionType.MESSAGE,
                share_level=ShareLevel.WITHHELD,
                days_ago=20,
                hours_ago=5,
                content="面接に落ちた企業があったと言っていたが、詳細はあえて聞かなかった。",
                note="落ち込んでいたので励まし中心に対応。",
            ),
            build_interaction(
                person_key="misaki",
                community_key="product_team",
                topic_key="motivation",
                interaction_type=InteractionType.MEETING,
                share_level=ShareLevel.SHARED,
                days_ago=25,
                content="インターン先でプロダクトを選んだ理由をかなり言語化していて、そのまま面接でも使えそうだった。",
                note="ユーザー視点の話が強み。",
            ),
            build_interaction(
                person_key="misaki",
                community_key="product_team",
                topic_key="job_story",
                interaction_type=InteractionType.TALK,
                share_level=ShareLevel.PARTIAL,
                days_ago=19,
                content="インターンで改善提案を出した話をしてくれたが、数値の部分はまだぼかしていた。",
                note="成果の定量値は未確認。",
            ),
            build_interaction(
                person_key="misaki",
                community_key="recruiting_team",
                topic_key="interviews",
                interaction_type=InteractionType.EVENT,
                share_level=ShareLevel.PARTIAL,
                days_ago=15,
                hours_ago=7,
                content="社内イベントで人事との座談会に参加し、面接で見られる観点を少し聞けたらしい。",
                note="評価項目は抽象度高めに共有済み。",
            ),
            build_interaction(
                person_key="ren",
                community_key="economics_seminar",
                topic_key="classes",
                interaction_type=InteractionType.TALK,
                share_level=ShareLevel.SHARED,
                days_ago=22,
                content="ゼミの発表準備で資料作成を進めており、データの見せ方で悩んでいた。",
                note="発表後に感想を聞くとよさそう。",
            ),
            build_interaction(
                person_key="ren",
                community_key="research_lab",
                topic_key="research",
                interaction_type=InteractionType.MEETING,
                share_level=ShareLevel.SHARED,
                days_ago=18,
                content="研究では地域経済の分析をしていて、定量だけでなくインタビューも使っていると言っていた。",
                note="話の切り口が丁寧で印象が良かった。",
            ),
            build_interaction(
                person_key="ren",
                community_key="economics_seminar",
                topic_key="job_story",
                interaction_type=InteractionType.MESSAGE,
                share_level=ShareLevel.PARTIAL,
                days_ago=12,
                hours_ago=8,
                content="ガクチカはゼミ運営の改善でまとめる予定と聞いた。",
                note="役割分担の調整を担った点が軸。",
            ),
            build_interaction(
                person_key="nana",
                community_key="product_team",
                topic_key="recent_schedule",
                interaction_type=InteractionType.MESSAGE,
                share_level=ShareLevel.SHARED,
                days_ago=21,
                content="今月後半はリリース対応で忙しく、夜は返信が遅れそうとのこと。",
                note="メッセージは短めがよさそう。",
            ),
            build_interaction(
                person_key="nana",
                community_key="product_team",
                topic_key="hobbies",
                interaction_type=InteractionType.TALK,
                share_level=ShareLevel.SHARED,
                days_ago=17,
                content="コーヒー巡りが好きで、休日は新しいカフェを探しているらしい。",
                note="おすすめの店を聞くと会話しやすい。",
            ),
            build_interaction(
                person_key="nana",
                community_key="recruiting_team",
                topic_key="interviews",
                interaction_type=InteractionType.MEETING,
                share_level=ShareLevel.PARTIAL,
                days_ago=10,
                hours_ago=4,
                content="最終面接前でかなり緊張していたが、逆質問の準備は進んでいた。",
                note="面接先の詳細は伏せられている。",
            ),
            build_interaction(
                person_key="kaito",
                community_key="recruiting_team",
                topic_key="motivation",
                interaction_type=InteractionType.MEETING,
                share_level=ShareLevel.SHARED,
                days_ago=16,
                content="採用広報に興味を持った理由が一貫していて、人に伝える仕事が好きだと話していた。",
                note="言語化がうまいタイプ。",
            ),
            build_interaction(
                person_key="kaito",
                community_key="recruiting_team",
                topic_key="job_story",
                interaction_type=InteractionType.TALK,
                share_level=ShareLevel.SHARED,
                days_ago=13,
                content="オープンキャンパスの運営で後輩をまとめた経験をガクチカに使う予定とのこと。",
                note="リーダー経験の深掘りができそう。",
            ),
            build_interaction(
                person_key="kaito",
                community_key="hometown_friends",
                topic_key="recent_schedule",
                interaction_type=InteractionType.MESSAGE,
                share_level=ShareLevel.PARTIAL,
                days_ago=8,
                hours_ago=5,
                content="今週末は地元に帰るらしく、就活の話は少し休みたいと言っていた。",
                note="近況確認は来週以降がよさそう。",
            ),
            build_interaction(
                person_key="saki",
                community_key="research_lab",
                topic_key="research",
                interaction_type=InteractionType.MEETING,
                share_level=ShareLevel.SHARED,
                days_ago=14,
                content="研究テーマの進捗報告を聞き、仮説検証の流れがかなり整理されていた。",
                note="発表スライドも見やすかった。",
            ),
            build_interaction(
                person_key="saki",
                community_key="research_lab",
                topic_key="classes",
                interaction_type=InteractionType.MESSAGE,
                share_level=ShareLevel.PARTIAL,
                days_ago=11,
                hours_ago=6,
                content="卒業要件の関係で履修を組み直していると連絡があった。",
                note="時間割の細かい事情までは聞いていない。",
            ),
            build_interaction(
                person_key="saki",
                community_key="university",
                topic_key="motivation",
                interaction_type=InteractionType.TALK,
                share_level=ShareLevel.WITHHELD,
                days_ago=7,
                hours_ago=3,
                content="志望動機の方向性は見えてきた様子だったが、まだ途中段階とのことだった。",
                note="企業名や業界の本命は未確認。",
            ),
            build_interaction(
                person_key="kenta",
                community_key="practice",
                topic_key="hobbies",
                interaction_type=InteractionType.EVENT,
                share_level=ShareLevel.SHARED,
                days_ago=9,
                content="サークル終わりにスポーツ観戦の話で盛り上がり、応援しているチームを教えてくれた。",
                note="次は試合結果の話題を振れる。",
            ),
            build_interaction(
                person_key="kenta",
                community_key="practice",
                topic_key="recent_schedule",
                interaction_type=InteractionType.TALK,
                share_level=ShareLevel.SHARED,
                days_ago=6,
                hours_ago=4,
                content="アルバイトのシフトが増えていて、平日はかなり忙しいらしい。",
                note="返信速度は遅めでも気にしなくてよさそう。",
            ),
            build_interaction(
                person_key="kenta",
                community_key="after_party",
                topic_key="job_story",
                interaction_type=InteractionType.MESSAGE,
                share_level=ShareLevel.PARTIAL,
                days_ago=4,
                hours_ago=9,
                content="接客バイトの改善経験をガクチカに使うつもりだと話していた。",
                note="具体的な数字はまだ整理中。",
            ),
            build_interaction(
                person_key="yuna",
                community_key="after_party",
                topic_key="hobbies",
                interaction_type=InteractionType.TALK,
                share_level=ShareLevel.SHARED,
                days_ago=8,
                content="旅行が好きで、次は金沢に行きたいと話していた。",
                note="写真を見せてもらった流れあり。",
            ),
            build_interaction(
                person_key="yuna",
                community_key="after_party",
                topic_key="motivation",
                interaction_type=InteractionType.TALK,
                share_level=ShareLevel.PARTIAL,
                days_ago=5,
                hours_ago=2,
                content="人と関わる仕事がしたいという軸は強いが、職種はまだ比較中とのこと。",
                note="営業と人事で迷っていそう。",
            ),
            build_interaction(
                person_key="yuna",
                community_key="hometown_friends",
                topic_key="recent_schedule",
                interaction_type=InteractionType.MESSAGE,
                share_level=ShareLevel.SHARED,
                days_ago=3,
                hours_ago=7,
                content="地元の友人と会う予定が続いていて、今週はかなり予定が埋まっているらしい。",
                note="会う頻度が高いので地元トークがしやすい。",
            ),
            build_interaction(
                person_key="sota",
                community_key="hometown_friends",
                topic_key="recent_schedule",
                interaction_type=InteractionType.TALK,
                share_level=ShareLevel.SHARED,
                days_ago=4,
                content="帰省の予定と、地元で会う友人の話をしていた。",
                note="次回は高校時代の話を広げやすい。",
            ),
            build_interaction(
                person_key="sota",
                community_key="hometown_friends",
                topic_key="job_story",
                interaction_type=InteractionType.MESSAGE,
                share_level=ShareLevel.PARTIAL,
                days_ago=2,
                hours_ago=8,
                content="高校の文化祭運営の経験を就活で話すか悩んでいるとのこと。",
                note="大学での経験とどうつなぐかが課題。",
            ),
            build_interaction(
                person_key="sota",
                community_key="recruiting_team",
                topic_key="interviews",
                interaction_type=InteractionType.MEETING,
                share_level=ShareLevel.WITHHELD,
                days_ago=1,
                hours_ago=6,
                content="面接練習を少し手伝ったが、受ける企業の詳細までは聞かなかった。",
                note="本人がまだ伏せたい様子だった。",
            ),
        ]

        db.add_all(interactions)
        db.commit()

        return SeedResult(
            prefix=prefix,
            community_count=len(communities),
            topic_count=len(topics),
            person_count=len(people),
            interaction_count=len(interactions),
        )
    finally:
        db.close()
