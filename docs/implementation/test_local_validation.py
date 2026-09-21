import unittest
from validate_local_tasks import differences, unexpected_changes


class BaselineTest(unittest.TestCase):
    def test_unchanged_and_intended_change(self):
        self.assertEqual(differences({'old':'a'}, {'old':'a'}), [])
        self.assertEqual(unexpected_changes({'old':'a'}, {'old':'b','new':'c'}, {'old','new'}), [])

    def test_unrelated_changes_additions_and_deletions_fail(self):
        self.assertEqual(unexpected_changes({'old':'a','removed':'b'},
            {'old':'b','new':'c'}, set()), ['new','old','removed'])

    def test_per_task_baseline_and_during_run_are_separate(self):
        baseline, before, after = {'old':'a'}, {'old':'b'}, {'old':'c'}
        self.assertEqual(unexpected_changes(baseline,before,set()), ['old'])
        self.assertEqual(unexpected_changes(before,after,set()), ['old'])
