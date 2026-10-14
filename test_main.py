import json
import tempfile
import unittest
from pathlib import Path
from main import analyse, downstream_impact, find_cycles, load_tasks, topological_order

class RippleTests(unittest.TestCase):
    def setUp(self):
        self.tasks = {"design": [], "api": ["design"], "ui": ["design"], "test": ["api", "ui"], "release": ["test"]}

    def test_downstream_impact_is_transitive(self):
        self.assertEqual(downstream_impact(self.tasks, "design"), ["api", "release", "test", "ui"])

    def test_unrelated_task_has_no_impact(self):
        self.assertEqual(downstream_impact(self.tasks, "release"), [])

    def test_unknown_changed_task_raises(self):
        with self.assertRaisesRegex(ValueError, "Unknown task"):
            downstream_impact(self.tasks, "missing")

    def test_valid_dependency_order(self):
        order = topological_order(self.tasks)
        self.assertIsNotNone(order)
        positions = {task: i for i, task in enumerate(order)}
        for task, deps in self.tasks.items():
            for dep in deps:
                self.assertLess(positions[dep], positions[task])

    def test_cycle_is_detected(self):
        self.assertTrue(find_cycles({"a": ["b"], "b": ["a"]}))
        self.assertIsNone(topological_order({"a": ["b"], "b": ["a"]}))

    def test_analysis_counts_and_impact(self):
        result = analyse(self.tasks, "design")
        self.assertEqual(result["task_count"], 5)
        self.assertEqual(result["dependency_count"], 5)
        self.assertEqual(len(result["downstream_impact"]), 4)
        self.assertEqual(result["cycles"], [])

    def test_load_tasks_from_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tasks.json"
            path.write_text(json.dumps(self.tasks), encoding="utf-8")
            self.assertEqual(load_tasks(path), self.tasks)

    def test_unknown_dependency_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text('{"build": ["missing"]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown dependencies"):
                load_tasks(path)

    def test_duplicate_dependency_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text('{"build": ["prep", "prep"], "prep": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "more than once"):
                load_tasks(path)

if __name__ == "__main__":
    unittest.main()
