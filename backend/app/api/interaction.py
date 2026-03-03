from fastapi import APIRouter, Depends
from backend.services.interaction_service import InteractionService
from backend.services.ai_service import AIService
from backend.services.insight_service import InsightService
from backend.services.relation_service import RelationService

router = APIRouter(prefix="/interactions", tags=["interaction"])


@router.post("/")
def record_interaction(
    person_id: str,
    interaction_type: int,
    content: str | None = None,
):
    interaction_service = InteractionService()
    ai_service = AIService()
    insight_service = InsightService()
    relation_service = RelationService()

    # ① 事実を保存
    interaction = interaction_service.record_interaction(
        person_id=person_id,
        interaction_type=interaction_type,
        content=content,
    )

    # ② AI 解析（任意）
    parsed = ai_service.analyze_interaction(interaction.id)

    # ③ 気づきに昇格（今回は自動採用例）
    insight = insight_service.create_insight_from_ai(parsed.id)

    # ④ 関係更新（ルールは Service 側）
    relation_service.update_relation(
        from_person_id=person_id,
        to_person_id=person_id,  # 仮：将来は相手ID
        relation_type=1,
    )

    return {"status": "ok", "interaction_id": interaction.id}
