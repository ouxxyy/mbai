import unittest

from scripts.score_report import aggregate_tasks, round_half_up_to_five


def task(level, time_share=None):
    return {
        "exposure_level": level,
        "time_share_percent": time_share,
    }


class RoundHalfUpTest(unittest.TestCase):
    def test_rounds_exact_half_up_instead_of_bankers_rounding(self):
        self.assertEqual(round_half_up_to_five(72.5), 75)
        self.assertEqual(round_half_up_to_five(77.5), 80)


class AggregateTasksTest(unittest.TestCase):
    def test_mixed_weights_exclude_unknown_and_match_frozen_example(self):
        tasks = [
            task("HIGH", 40),
            task("MEDIUM", 30),
            task("LOW"),
            task("UNKNOWN", 20),
            task("UNKNOWN"),
        ]

        metrics, enriched = aggregate_tasks(tasks)

        self.assertTrue(metrics["is_sufficient_info"])
        self.assertEqual(metrics["task_count_evaluable"], 3)
        self.assertAlmostEqual(metrics["raw_score"], 5500 / 71)
        self.assertEqual(metrics["exposure_index"], 75)
        self.assertEqual(metrics["exposure_level"], "MEDIUM")
        self.assertEqual(metrics["weight_mode"], "MIXED_WEIGHTED")
        self.assertEqual(enriched[0]["effective_weight"], 40)
        self.assertEqual(enriched[2]["effective_weight"], 1)
        self.assertIsNone(enriched[3]["effective_weight"])
        self.assertIsNone(enriched[3]["score"])

    def test_fewer_than_half_evaluable_tasks_hides_index(self):
        metrics, _ = aggregate_tasks(
            [task("HIGH"), task("UNKNOWN"), task("UNKNOWN")]
        )

        self.assertFalse(metrics["is_sufficient_info"])
        self.assertIsNone(metrics["raw_score"])
        self.assertIsNone(metrics["exposure_index"])
        self.assertEqual(metrics["exposure_level"], "UNKNOWN")

    def test_exactly_half_evaluable_tasks_show_index(self):
        metrics, _ = aggregate_tasks(
            [task("HIGH", 60), task("LOW", 40), task("UNKNOWN"), task("UNKNOWN")]
        )

        self.assertTrue(metrics["is_sufficient_info"])
        self.assertEqual(metrics["exposure_index"], 60)
        self.assertEqual(metrics["weight_mode"], "USER_WEIGHTED")

    def test_empty_task_list_is_information_insufficient(self):
        metrics, enriched = aggregate_tasks([])

        self.assertEqual(enriched, [])
        self.assertFalse(metrics["is_sufficient_info"])
        self.assertEqual(metrics["weight_mode"], "NOT_APPLICABLE")
        self.assertIsNone(metrics["exposure_index"])

    def test_rejects_invalid_level_and_time_share(self):
        with self.assertRaisesRegex(ValueError, "exposure_level"):
            aggregate_tasks([task("VERY_HIGH")])
        with self.assertRaisesRegex(ValueError, "time_share_percent"):
            aggregate_tasks([task("HIGH", 0)])


if __name__ == "__main__":
    unittest.main()
