from _bootstrap import SRC, read_source  # noqa: F401
import unittest
from pathlib import Path
from performance_summary import summarize_performance


class SharedPerformanceIntegration(unittest.TestCase):
    def test_shared_sample_recorded(self):
        source = (Path(__file__).resolve().parents[1] / 'src' / 'app.py').read_text()
        self.assertIn('self.perf_sampler.sample(os.getpid(), "__shared__", "GTK/VTE renderer")', source)
        self.assertIn('"shared_process_sample"', source)

    def test_shared_not_attributed_to_a_child_monitor(self):
        records = [
            {'event': 'shared_process_sample', 'monitor': '__shared__',
             'effect': 'GTK/VTE renderer', 'cpu_percent': 12, 'rss_mib': 65},
            {'monitor': 'DP-1', 'effect': 'rain', 'cpu_percent': 23, 'rss_mib': 25},
        ]
        per_monitor, shared = summarize_performance(records)
        self.assertEqual(per_monitor['DP-1'][0]['cpu'], 23)
        self.assertEqual(per_monitor['DP-1'][0]['rss'], 25)
        self.assertEqual(shared['cpu'], 12)
        self.assertNotIn('__shared__', per_monitor)


if __name__ == '__main__':
    unittest.main()
