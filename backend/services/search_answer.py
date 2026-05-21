from __future__ import annotations

from backend.services.search_constants import (
    TARGET_CALENDAR_EVENT,
    TARGET_COMMUNITY,
    TARGET_INTERACTION,
    TARGET_PERSON,
    TARGET_TASK,
    TARGET_TOPIC,
)


def add_unique_reason(candidate: dict, reason: str) -> None:
    if reason and reason not in candidate["reasons"]:
        candidate["reasons"].append(reason)


def classify_answer_confidence(primary: dict, others: list[dict]) -> str:
    score = float(primary["score"])
    interaction_count = int(primary["interaction_count"])
    runner_up_score = float(others[0]["score"]) if others else 0.0
    margin = score - runner_up_score

    if score >= 0.75 and (interaction_count >= 2 or margin >= 0.25):
        return "high"
    if score >= 0.42:
        return "medium"
    return "low"


def empty_rag_answer() -> dict:
    return {
        "answer_model": "deterministic-rag-v1",
        "summary": "検索語を入力すると、人物・会話・タスク・予定の近い候補を整理します。",
        "confidence": "none",
        "primary_person": None,
        "people": [],
        "evidence": [],
        "follow_up_queries": [],
    }


def build_rag_answer(
    query: str,
    results: list[dict],
    groups: dict[str, list[dict]],
) -> dict:
    if not results:
        return {
            **empty_rag_answer(),
            "summary": "該当しそうな記録は見つかりませんでした。",
        }

    person_candidates = aggregate_person_candidates(results)
    if not person_candidates:
        return build_non_person_answer(query, results, groups)

    primary = person_candidates[0]
    other_people = person_candidates[1:3]
    confidence = classify_answer_confidence(primary, other_people)
    evidence = primary["evidence"][:3]
    reason_text = "、".join(primary["reasons"][:3])

    if confidence == "high":
        prefix = "可能性が高いのは"
    elif confidence == "medium":
        prefix = "可能性がありそうなのは"
    else:
        prefix = "まだ断定は弱いですが、近い候補は"

    summary_parts = [
        f"{prefix}{primary['person_name']}さんです。",
        f"理由は{reason_text}ことです。" if reason_text else "",
    ]
    if evidence:
        summary_parts.append(
            f"根拠として「{evidence[0]['title']}」の記録が近く出ています。"
        )
    if other_people:
        names = "、".join(item["person_name"] for item in other_people)
        summary_parts.append(f"次点では{names}さんも候補です。")

    return {
        "answer_model": "deterministic-rag-v1",
        "summary": "".join(summary_parts),
        "confidence": confidence,
        "primary_person": {
            "person_id": primary["person_id"],
            "person_name": primary["person_name"],
            "community_path": primary["community_path"],
            "score": round(primary["score"], 6),
        },
        "people": [
            {
                "person_id": item["person_id"],
                "person_name": item["person_name"],
                "community_path": item["community_path"],
                "score": round(item["score"], 6),
                "reasons": item["reasons"][:3],
            }
            for item in person_candidates[:3]
        ],
        "evidence": evidence,
        "follow_up_queries": build_follow_up_queries(query, person_candidates, groups),
    }


def aggregate_person_candidates(results: list[dict]) -> list[dict]:
    candidates: dict[str, dict] = {}

    for result in results:
        person_id = result.get("person_id")
        person_name = result.get("person_name")
        if not person_id or not person_name:
            continue

        candidate = candidates.setdefault(
            person_id,
            {
                "person_id": person_id,
                "person_name": person_name,
                "community_path": result.get("community_path"),
                "score": 0.0,
                "direct_person_score": 0.0,
                "interaction_count": 0,
                "task_count": 0,
                "event_count": 0,
                "reasons": [],
                "evidence": [],
            },
        )
        candidate["community_path"] = (
            candidate["community_path"] or result.get("community_path")
        )

        target_type = result.get("target_type")
        score = float(result.get("score") or 0)
        if target_type == TARGET_PERSON:
            candidate["score"] += score * 1.25
            candidate["direct_person_score"] = max(
                candidate["direct_person_score"],
                score,
            )
            add_unique_reason(candidate, "人物情報そのものが検索語に近い")
        elif target_type == TARGET_INTERACTION:
            candidate["score"] += score
            candidate["interaction_count"] += 1
            candidate["evidence"].append(result)
            add_unique_reason(candidate, "過去の会話内容が検索語に近い")
        elif target_type == TARGET_TASK:
            candidate["score"] += score * 0.9
            candidate["task_count"] += 1
            candidate["evidence"].append(result)
            add_unique_reason(candidate, "関連タスクが検索語に近い")
        elif target_type == TARGET_CALENDAR_EVENT:
            candidate["score"] += score * 0.8
            candidate["event_count"] += 1
            candidate["evidence"].append(result)
            add_unique_reason(candidate, "予定の内容が検索語に近い")
        else:
            candidate["score"] += score * 0.45

        if result.get("topic_path"):
            add_unique_reason(candidate, f"話題が「{result['topic_path']}」に近い")
        if result.get("community_path"):
            add_unique_reason(candidate, f"所属が「{result['community_path']}」に近い")

    for candidate in candidates.values():
        candidate["score"] += min(candidate["interaction_count"], 4) * 0.08
        candidate["score"] += min(candidate["task_count"], 3) * 0.06
        candidate["score"] += min(candidate["event_count"], 3) * 0.04
        candidate["evidence"].sort(key=lambda item: -float(item.get("score") or 0))

    return sorted(
        candidates.values(),
        key=lambda item: (
            -float(item["score"]),
            -int(item["interaction_count"]),
            -int(item["task_count"]),
            -int(item["event_count"]),
            item["person_name"],
        ),
    )


def build_non_person_answer(
    query: str,
    results: list[dict],
    groups: dict[str, list[dict]],
) -> dict:
    top_result = results[0]
    type_label = {
        TARGET_TASK: "タスク",
        TARGET_CALENDAR_EVENT: "予定",
        TARGET_INTERACTION: "会話",
        TARGET_COMMUNITY: "団体",
        TARGET_TOPIC: "話題",
    }.get(top_result.get("target_type"), "記録")

    related_labels = [
        item["title"]
        for item in [
            *groups.get("tasks", []),
            *groups.get("calendar_events", []),
            *groups.get("communities", []),
            *groups.get("topics", []),
        ][:3]
    ]
    if related_labels:
        summary = f"人物までは絞り込めませんでしたが、{type_label}「{top_result['title']}」が近い候補です。関連候補は{ '、'.join(related_labels) }です。"
    else:
        summary = f"人物までは絞り込めませんでしたが、{type_label}「{top_result['title']}」が近い候補です。"

    return {
        "answer_model": "deterministic-rag-v1",
        "summary": summary,
        "confidence": "low",
        "primary_person": None,
        "people": [],
        "evidence": results[:3],
        "follow_up_queries": build_follow_up_queries(query, [], groups),
    }


def build_follow_up_queries(
    query: str,
    person_candidates: list[dict],
    groups: dict[str, list[dict]],
) -> list[str]:
    suggestions = []
    if person_candidates:
        top_person = person_candidates[0]
        suggestions.append(f"{top_person['person_name']} {query}")
        if top_person.get("community_path"):
            suggestions.append(f"{top_person['community_path']} {query}")

    for item in groups.get("tasks", [])[:1]:
        suggestions.append(f"{item['title']} {query}")
    for item in groups.get("calendar_events", [])[:1]:
        suggestions.append(f"{item['title']} {query}")
    for item in groups.get("topics", [])[:1]:
        suggestions.append(f"{item['title']} {query}")
    for item in groups.get("communities", [])[:1]:
        suggestions.append(f"{item['title']} {query}")

    deduped = []
    for suggestion in suggestions:
        if suggestion and suggestion not in deduped:
            deduped.append(suggestion)
        if len(deduped) >= 3:
            break
    return deduped
