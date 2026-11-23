"""V63 component version and HIG menu regression tests (no GTK needed)."""
from _bootstrap import SRC, read_source  # noqa: F401
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from component_versions import (BUILD_VERSION, collect_versions, running_watcher_status,
                                troubleshooting_report, watcher_backend, _version_output)


class ComponentTests(unittest.TestCase):
    def test_install_packaging_and_embedded_build_id(self):
        installer = (ROOT / 'install.sh').read_text()
        self.assertIn('"$py_src/component_versions.py"', installer)
        self.assertIn('"$py_src/app_menu.py"', installer)
        self.assertIn('"$py_src/build_info.py"', installer)
        self.assertIn('"$staged_app/watcher-backend"', installer)
        self.assertEqual(BUILD_VERSION, (ROOT / 'VERSION').read_text().strip())

    def test_components_not_missing_even_when_runtime_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'VERSION').write_text(BUILD_VERSION + '\n')
            (root / 'watcher-backend').write_text('gnome\n')
            with patch('component_versions._watcher_pid', return_value=None):
                result = collect_versions(root)
            self.assertEqual(result['ui'], BUILD_VERSION)
            self.assertEqual(result['installed'], BUILD_VERSION)
            self.assertEqual(result['ui_status'], 'Current')
            self.assertEqual(result['backend'], 'GNOME / Mutter')
            self.assertIn('Not running', result['running'])
            self.assertIn('Running GUI: ' + BUILD_VERSION, troubleshooting_report(result))

    def test_version_only_binary_does_not_launch_daemon(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / 'ascii-saver-watcher'
            binary.write_text('#!/bin/sh\nprintf "ASCII Saver GNOME watcher 0.63.0\\n"\n')
            binary.chmod(0o755)
            self.assertEqual(_version_output(binary), 'ASCII Saver GNOME watcher 0.63.0')

    def test_old_binary_in_process_is_reported_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            installed = Path(tmp) / 'ascii-saver-watcher'
            installed.write_text('new')
            process = Path(tmp) / 'older-watcher'
            process.write_text('old')
            # For stat/readlink, simulate the kernel's /proc/PID/exe values.
            import component_versions
            orig_readlink = os.readlink
            orig_stat = Path.stat
            def link(path):
                if str(path) == '/proc/987654/exe':
                    return '/home/example/.local/share/ascii-saver/ascii-saver-watcher (deleted)'
                return orig_readlink(path)
            def stat(path, *args, **kwargs):
                if str(path) == '/proc/987654/exe':
                    return orig_stat(process)
                return orig_stat(path, *args, **kwargs)
            with patch.object(component_versions.os, 'readlink', side_effect=link), \
                 patch.object(Path, 'stat', stat):
                status = running_watcher_status(installed, 987654)
            self.assertIn('Restart required', status)

    def test_unknown_pid_is_never_assumed_to_be_our_watcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / 'ascii-saver-watcher'
            binary.write_text('binary')
            with patch('component_versions.os.readlink', return_value='/usr/bin/python3'):
                self.assertEqual(running_watcher_status(binary, 1234), 'Unable to verify running watcher')

    def test_shortcuts_are_real_application_actions(self):
        source = (SRC / 'application_actions.py').read_text()
        menu = (SRC / 'app_menu.py').read_text()
        for name in ('preferences', 'shortcuts', 'help', 'about', 'components', 'quit'):
            self.assertIn("'" + name + "'", source)
            self.assertIn("'app." + name + "'", menu)
        self.assertIn('Gtk.MenuButton', menu)
        self.assertIn('Adw.AboutDialog', menu)
        self.assertIn('Adw.ShortcutsDialog', menu)
        self.assertIn('Ctrl', (ROOT / 'docs/releases/RELEASE-V63.md').read_text())

    def test_native_watchers_identify_their_own_builds(self):
        for filename in ('gnome_idle_watcher.c', 'watcher.cpp'):
            self.assertIn('--version', read_source(filename))
        self.assertIn('ASCII_SAVER_VERSION', (ROOT / 'native/kde/CMakeLists.txt').read_text())
        self.assertIn('ASCII_SAVER_VERSION', (ROOT / 'install.sh').read_text())


if __name__ == '__main__':
    unittest.main()
