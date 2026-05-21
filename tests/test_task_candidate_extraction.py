import unittest
from datetime import datetime, timezone

from backend.services.task_service import extract_task_candidates


class TaskCandidateExtractionTest(unittest.TestCase):
    def test_extracts_task_candidate_with_japanese_due_date(self) -> None:
        base_at = datetime(2026, 5, 21, 10, 0, tzinfo=timezone.utc)

        candidates = extract_task_candidates(
            "山田さんと相談した。5月25日までに発表資料を送ることになった。",
            base_at=base_at,
        )

        self.assertEqual(len(candidates), 1)
        self.assertIn("発表資料を送る", candidates[0].title)
        self.assertEqual(candidates[0].due_at.year, 2026)
        self.assertEqual(candidates[0].due_at.month, 5)
        self.assertEqual(candidates[0].due_at.day, 25)
        self.assertGreaterEqual(candidates[0].confidence, 0.8)

    def test_ignores_sentences_without_task_signal(self) -> None:
        candidates = extract_task_candidates(
            "山田さんと研究室で雑談した。最近の授業について話した。",
            base_at=datetime(2026, 5, 21, tzinfo=timezone.utc),
        )

        self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
