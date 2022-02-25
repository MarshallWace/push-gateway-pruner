import unittest
from unittest.mock import patch
import push_gateway_pruner


EXAMPLE_METRICS = """
        example_metric{job="j", instance="i", "label_with_space"="l w s value", "label_with_comma"="l,w,c"} 5
        push_time_seconds{job="j", instance="i", "label_with_space"="l w s value", "label_with_comma"="l,w,c"} 5
    """


EXAMPLE_METRICS_LABEL = {
    "job": "j",
    "instance": "i",
    '"label_with_space"': "l w s value",
    '"label_with_comma"': "l,w,c",
}


class TestBasic(unittest.TestCase):
    def test_basic(self):
        result = list(push_gateway_pruner.parse_raw_metrics(EXAMPLE_METRICS))
        self.assertEqual(len(result), 2)

        samples = result[0].samples
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].name, "example_metric")

        labels = samples[0].labels
        self.assertEqual(labels, EXAMPLE_METRICS_LABEL)

    def test_pruning(self):
        prune_metric_name = "push_time_seconds"
        prune_threshold_seconds = 5
        metrics = push_gateway_pruner.parse_raw_metrics(EXAMPLE_METRICS)
        filtered_samples = list(
            push_gateway_pruner.filter_metrics(
                metrics, prune_metric_name, prune_threshold_seconds
            )
        )
        self.assertEqual(len(filtered_samples), 1)
        self.assertEqual(filtered_samples[0].labels, EXAMPLE_METRICS_LABEL)


if __name__ == "__main__":
    unittest.main()
