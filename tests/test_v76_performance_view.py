"""V76 regression checks for truthful per-monitor performance presentation."""
import ast
from pathlib import Path
import unittest

from performance_summary import summarize_performance

ROOT = Path(__file__).resolve().parents[1]


class GroupedPerformanceTests(unittest.TestCase):
    def test_child_metrics_are_distinct_from_shared_ui(self):
        records = [
            {'event': 'shared_process_sample', 'monitor': '__shared__',
             'effect': 'GTK/VTE renderer', 'cpu_percent': 8, 'rss_mib': 49, 'gpu_percent': None},
            {'monitor': 'DP-1', 'effect': 'matrix', 'cpu_percent': 24, 'rss_mib': 32, 'gpu_percent': 12},
            {'monitor': 'DP-1', 'effect': 'matrix', 'cpu_percent': 16, 'rss_mib': 36, 'gpu_percent': None},
            {'monitor': 'DP-2', 'effect': 'rain', 'cpu_percent': 15, 'rss_mib': 18, 'gpu_percent': None},
        ]
        monitors, shared = summarize_performance(records)
        self.assertEqual(tuple(monitors), ('DP-1', 'DP-2'))
        self.assertEqual(monitors['DP-1'][0]['cpu'], 20)
        self.assertEqual(monitors['DP-1'][0]['rss'], 36)
        self.assertEqual(monitors['DP-1'][0]['gpu'], 12)
        self.assertIsNone(monitors['DP-2'][0]['gpu'])
        self.assertEqual(shared['cpu'], 8)
        self.assertEqual(shared['rss'], 49)
        self.assertNotIn('__shared__', monitors)

    def test_only_renderer_reports_count_as_fps_not_cap(self):
        records = [
            {'monitor': 'DP-1', 'effect': 'rain', 'event': 'effect_start', 'fps_cap': 120},
            {'monitor': 'DP-1', 'effect': 'rain', 'event': 'frame_stats', 'active_output_fps': 45},
            {'monitor': 'DP-1', 'effect': 'rain', 'event': 'frame_stats', 'active_output_fps': 55},
        ]
        monitors, shared = summarize_performance(records)
        self.assertIsNone(shared)
        self.assertEqual(monitors['DP-1'][0]['fps'], 50)
        self.assertEqual(monitors['DP-1'][0]['fps_runs'], 2)
        self.assertEqual(monitors['DP-1'][0]['cap'], 120)
        self.assertEqual(monitors['DP-1'][0]['samples'], 0)

    def test_durations_exclude_aborted_events(self):
        rows = [
            {'monitor': 'DP-1', 'effect': 'beams', 'event': 'effect_duration',
             'success': True, 'duration_seconds': 12.4},
            {'monitor': 'DP-1', 'effect': 'beams', 'event': 'effect_duration',
             'success': False, 'duration_seconds': 900},
            {'monitor': 'DP-1', 'effect': 'beams', 'event': 'effect_duration',
             'success': True, 'duration_seconds': 13.6},
        ]
        result, _ = summarize_performance(rows)
        self.assertAlmostEqual(result['DP-1'][0]['duration'], 13.0)
        self.assertEqual(result['DP-1'][0]['duration_runs'], 2)

    def test_missing_gpu_does_not_become_zero(self):
        rows = [{'monitor': 'DP-1', 'effect': 'rain', 'rss_mib': 20}]
        result, _ = summarize_performance(rows)
        self.assertIsNone(result['DP-1'][0]['gpu'])
        self.assertIsNone(result['DP-1'][0]['cpu'])

    def test_bad_values_and_unrelated_events_do_not_poison_samples(self):
        rows = [
            {'monitor': 'DP-1', 'effect': 'rain', 'cpu_percent': float('nan'), 'rss_mib': True},
            {'monitor': 'DP-1', 'effect': 'rain', 'event': 'effect_spawn_failed',
             'cpu_percent': 900, 'rss_mib': 900},
            {'monitor': 'DP-1', 'effect': 'rain', 'cpu_percent': -20, 'rss_mib': 19},
            {'monitor': 'DP-1', 'effect': 'rain', 'cpu_percent': 30, 'rss_mib': 21},
            {'monitor': 'DP-1', 'effect': 'rain', 'event': 'frame_stats',
             'active_output_fps': float('inf')},
        ]
        result, _ = summarize_performance(rows)
        self.assertEqual(result['DP-1'][0]['cpu'], 30)
        self.assertEqual(result['DP-1'][0]['rss'], 21)
        self.assertEqual(result['DP-1'][0]['samples'], 2)
        self.assertIsNone(result['DP-1'][0]['fps'])

    def test_shared_event_cannot_inflate_child_stats(self):
        rows = [{'monitor': 'DP-1', 'effect': 'rain', 'event': 'shared_process_sample',
                 'cpu_percent': 80, 'rss_mib': 110}]
        per_monitor, shared = summarize_performance(rows)
        self.assertEqual(per_monitor, {})
        self.assertIsNone(shared)


class ViewContractTests(unittest.TestCase):
    def test_native_scrolling_and_separate_groups(self):
        src = (ROOT / 'performance_ui.py').read_text()
        ast.parse(src)
        self.assertIn('scroll.set_vexpand(True)', src)
        self.assertIn('Adw.PreferencesGroup(title=', src)
        self.assertIn('self.summary_groups', src)
        self.assertIn('self._rebuild_summary(grouped, shared)', src)
        self.assertIn('self._view_signature', src)
        self.assertNotIn("self.table=Gtk.Label", src)

    def test_four_chart_axes_and_discrete_fps(self):
        src = (ROOT / 'performance_ui.py').read_text()
        self.assertIn("('Resident memory (MiB)', 'rss_mib')", src)
        self.assertIn("('GPU process-engine busy (%)', 'gpu_percent')", src)
        self.assertIn("('ttfx output FPS (completed effects)', 'active_output_fps')", src)
        self.assertIn("metric == 'active_output_fps'", src)
        self.assertIn('cr.arc(x, y,', src)
        self.assertIn("if monitor == '__shared__'", src)
        self.assertIn('self._update_legend(visible_monitors)', src)

    def test_new_summary_module_installed_and_syntax_checked(self):
        self.assertIn('performance_summary effect_timing', (ROOT / 'install.sh').read_text())
        ast.parse((ROOT / 'performance_summary.py').read_text())


if __name__ == '__main__':
    unittest.main()
