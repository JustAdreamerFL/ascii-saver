"""V101: renderer lifecycle is mode-aware, bounded and safe to stop."""
from __future__ import annotations

import ast
import io
import unittest
from pathlib import Path
from unittest import mock

import ctl
import status_model

ROOT = Path(__file__).resolve().parents[1]


class StartModeTests(unittest.TestCase):
    def test_existing_preview_is_idempotent_for_preview(self):
        output = io.StringIO()
        with mock.patch('ctl.current_pid', return_value=123), \
             mock.patch('ctl.is_windowed_preview', return_value=True), \
             mock.patch('ctl.subprocess.Popen') as spawn, \
             mock.patch('sys.stdout', output):
            self.assertTrue(ctl.command_start(windowed=True))
        spawn.assert_not_called()
        self.assertIn('already open', output.getvalue())

    def test_existing_fullscreen_is_idempotent_for_start(self):
        output = io.StringIO()
        with mock.patch('ctl.current_pid', return_value=123), \
             mock.patch('ctl.is_windowed_preview', return_value=False), \
             mock.patch('ctl.subprocess.Popen') as spawn, \
             mock.patch('sys.stdout', output):
            self.assertTrue(ctl.command_start(windowed=False))
        spawn.assert_not_called()
        self.assertIn('already running', output.getvalue())

    def test_preview_refuses_to_claim_fullscreen_is_a_preview(self):
        output = io.StringIO()
        with mock.patch('ctl.current_pid', return_value=123), \
             mock.patch('ctl.is_windowed_preview', return_value=False), \
             mock.patch('ctl.subprocess.Popen') as spawn, \
             mock.patch('sys.stdout', output):
            self.assertFalse(ctl.command_start(windowed=True))
        spawn.assert_not_called()
        self.assertIn('Stop it first', output.getvalue())
        self.assertIn('left untouched', output.getvalue())

    def test_fullscreen_refuses_to_claim_preview_is_fullscreen(self):
        output = io.StringIO()
        with mock.patch('ctl.current_pid', return_value=123), \
             mock.patch('ctl.is_windowed_preview', return_value=True), \
             mock.patch('ctl.subprocess.Popen') as spawn, \
             mock.patch('sys.stdout', output):
            self.assertFalse(ctl.command_start(windowed=False))
        spawn.assert_not_called()
        self.assertIn('preview is already running', output.getvalue())


class VerifiedStopTests(unittest.TestCase):
    def test_waits_until_original_process_is_no_longer_a_saver(self):
        with mock.patch('ctl.process_matches_installed_saver', side_effect=[True, True, False]) as matches, \
             mock.patch('ctl.time.sleep') as sleep:
            self.assertTrue(ctl.wait_for_renderer_exit(987))
        self.assertEqual(matches.call_count, 3)
        self.assertTrue(all(call.args == (987,) for call in matches.call_args_list))
        self.assertEqual(sleep.call_count, 2)

    def test_wait_times_out_without_killing_any_process(self):
        with mock.patch('ctl.process_matches_installed_saver', return_value=True), \
             mock.patch('ctl.time.monotonic', side_effect=[10.0, 11.0, 13.0]), \
             mock.patch('ctl.time.sleep') as sleep:
            self.assertFalse(ctl.wait_for_renderer_exit(987, timeout=2.0))
        sleep.assert_called_once()

    def test_stop_reports_success_only_after_exit(self):
        output = io.StringIO()
        with mock.patch('ctl.current_pid', return_value=987), \
             mock.patch('ctl.send_signal_if_matches', return_value=True) as send, \
             mock.patch('ctl.wait_for_renderer_exit', return_value=True) as wait, \
             mock.patch('sys.stdout', output):
            self.assertTrue(ctl.command_stop())
        send.assert_called_once_with(987, ctl.signal.SIGTERM, ctl.process_matches_installed_saver)
        wait.assert_called_once_with(987)
        self.assertIn('Stopped ASCII Saver', output.getvalue())

    def test_stop_timeout_reports_failed_and_never_force_kills(self):
        output = io.StringIO()
        with mock.patch('ctl.current_pid', return_value=987), \
             mock.patch('ctl.send_signal_if_matches', return_value=True), \
             mock.patch('ctl.wait_for_renderer_exit', return_value=False), \
             mock.patch('ctl.os.kill') as os_kill, \
             mock.patch('sys.stdout', output):
            self.assertFalse(ctl.command_stop())
        os_kill.assert_not_called()
        self.assertIn('still shutting down', output.getvalue())
        self.assertNotIn('Stopped ASCII Saver', output.getvalue())

    def test_no_wait_when_process_disappears_before_signal(self):
        with mock.patch('ctl.current_pid', return_value=987), \
             mock.patch('ctl.send_signal_if_matches', return_value=False), \
             mock.patch('ctl.wait_for_renderer_exit') as wait, \
             mock.patch('sys.stdout', io.StringIO()):
            self.assertTrue(ctl.command_stop())
        wait.assert_not_called()

    def test_permission_denied_preserves_error(self):
        output = io.StringIO()
        with mock.patch('ctl.current_pid', return_value=987), \
             mock.patch('ctl.send_signal_if_matches', side_effect=PermissionError), \
             mock.patch('ctl.wait_for_renderer_exit') as wait, \
             mock.patch('sys.stdout', output):
            self.assertFalse(ctl.command_stop())
        wait.assert_not_called()
        self.assertIn('permission denied', output.getvalue())


class DashboardAndStatusTests(unittest.TestCase):
    def test_status_distinguishes_fullscreen_preview_and_stopped(self):
        base = {'enabled': True}
        for pid, preview, label in [(None, False, 'Stopped'),
                                    (777, True, 'Preview running'),
                                    (777, False, 'Fullscreen running')]:
            with self.subTest(pid=pid, preview=preview), \
                 mock.patch('status_model.ctl.current_pid', return_value=pid), \
                 mock.patch('status_model.ctl.current_watcher_pid', return_value=None), \
                 mock.patch('status_model.ctl.is_windowed_preview', return_value=preview) as is_preview, \
                 mock.patch('status_model.load_config', return_value=base):
                result = status_model.current_status()
            self.assertEqual(result['renderer'], label)
            self.assertEqual(result['preview'], bool(pid and preview))
            if not pid:
                is_preview.assert_not_called()

    def test_cli_status_reports_playback_mode(self):
        output = io.StringIO()
        with mock.patch('ctl.current_pid', return_value=123), \
             mock.patch('ctl.is_windowed_preview', return_value=True), \
             mock.patch('ctl.load_config', return_value={'enabled': True, 'idle_delay': 120}), \
             mock.patch('ctl.integration_status', return_value='test watcher'), \
             mock.patch('sys.stdout', output):
            ctl.command_status()
        self.assertIn('playback mode: preview', output.getvalue())

    def test_gui_blocks_start_and_preview_during_running_command(self):
        source = (ROOT / 'settings.py').read_text()
        ast.parse(source)
        self.assertIn('self._playback_busy = True', source)
        self.assertIn('if self._closed or self._playback_busy:', source)
        self.assertIn('not self._playback_busy and', source)
        self.assertIn('self._playback_busy = False', source)
        self.assertIn('if not self._closed:', source)


if __name__ == '__main__':
    unittest.main()


class DashboardCommandTests(unittest.TestCase):
    def test_success_message_only_from_zero_exit(self):
        from dashboard_playback import run_dashboard_command
        with mock.patch('dashboard_playback.subprocess.run', return_value=mock.Mock(returncode=0)) as run:
            result = run_dashboard_command('preview-toggle', '/usr/bin/python3', Path('/fake/ctl.py'), lambda: False)
        self.assertEqual(result, 'Preview opened')
        self.assertEqual(run.call_args.args[0][-1], 'preview')
        self.assertEqual(run.call_args.kwargs['timeout'], 10)

    def test_nonzero_exit_shows_cli_failure_instead_of_success(self):
        from dashboard_playback import run_dashboard_command
        completion = mock.Mock(returncode=1, stderr='', stdout='Cannot start preview: fullscreen active')
        with mock.patch('dashboard_playback.subprocess.run', return_value=completion):
            self.assertIn('fullscreen active', run_dashboard_command('preview-toggle', 'python', Path('ctl.py'), lambda: False))

    def test_closed_preview_dispatches_stop(self):
        from dashboard_playback import run_dashboard_command
        with mock.patch('dashboard_playback.subprocess.run', return_value=mock.Mock(returncode=0)) as run:
            self.assertEqual(run_dashboard_command('preview-toggle', 'python', Path('ctl.py'), lambda: True), 'Preview closed')
        self.assertEqual(run.call_args.args[0][-1], 'stop')

    def test_timeout_is_not_a_false_success(self):
        from dashboard_playback import run_dashboard_command
        with mock.patch('dashboard_playback.subprocess.run', side_effect=__import__('subprocess').TimeoutExpired('ctl', 10)):
            result = run_dashboard_command('start', 'python', Path('ctl.py'), lambda: False)
        self.assertIn('timed out', result)

    def test_installer_copies_dashboard_action_module(self):
        self.assertIn('"$source_dir/dashboard_playback.py" "$staged_app/dashboard_playback.py"',
                      (ROOT / 'install.sh').read_text())
