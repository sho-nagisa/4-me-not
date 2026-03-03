class InsightService:

    def create_insight_from_interaction(
        self,
        person_id,
        insight_type,
        content: str,
        confidence: int | None = None,
    ):
        pass

    def create_insight_from_ai(self, parsed_note_id):
        pass
