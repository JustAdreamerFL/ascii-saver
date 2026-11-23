"""V105: executable dispatcher and the GTK Preferences NameError regression."""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

import ast
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import cli


class EntryPointTests(unittest.TestCase):
    def routed(self, *argv):
        return cli.target_for(cli.make_parser().parse_args(list(argv)))

    def test_default_command_is_dashboard(self):
        self.assertEqual(self.routed(), ("settings.py", []))
        self.assertEqual(self.routed("dashboard"), ("settings.py", []))

    def test_preference_commands_open_only_preferences(self):
        for name in ("preferences", "prefs", "settings"):
            with self.subTest(name=name):
                self.assertEqual(self.routed(name), ("settings.py", ["--preferences"]))

    def test_playlist_routes_to_registered_gui(self):
        self.assertEqual(self.routed("playlist"), ("settings.py", ["--playlist-editor"]))

    def test_fullscreen_and_preview_control_use_ctl(self):
        for cmd in ("start", "preview", "stop", "status", "doctor", "components"):
            self.assertEqual(self.routed(cmd), ("ctl.py", [cmd]))

    def test_direct_foreground_and_legacy_flags(self):
        self.assertEqual(self.routed("play"), ("app.py", []))
        self.assertEqual(self.routed("play", "--once", "--windowed"),
                         ("app.py", ["--windowed", "--once"]))
        self.assertEqual(self.routed("--windowed"), ("app.py", ["--windowed"]))
        self.assertEqual(self.routed("--once"), ("app.py", ["--once"]))

    def test_ctl_subcommands_and_arguments(self):
        self.assertEqual(self.routed("delay", "200"), ("ctl.py", ["delay", "200"]))
        self.assertEqual(self.routed("dock", "restore"), ("ctl.py", ["dock", "restore"]))
        self.assertEqual(self.routed("dock"), ("ctl.py", ["dock", "status"]))

    def test_invalid_legacy_flags_cannot_accidentally_route_to_ctl(self):
        with self.assertRaises(ValueError):
            self.routed("--once", "start")

    def test_help_and_version_work_without_gi(self):
        for flag in ("--help", "--version"):
            result = subprocess.run([sys.executable, str(SRC / "cli.py"), flag],
                                    text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ASCII Saver", result.stdout)
        result = subprocess.run([sys.executable, str(SRC / "cli.py"), "start", "--help"],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0)

    def test_dispatch_execs_existing_script_with_expected_options(self):
        with patch.object(cli.os, 'execv', side_effect=RuntimeError('intercepted')) as spawn:
            with self.assertRaisesRegex(RuntimeError, 'intercepted'):
                cli.main(["preferences"])
            argv = spawn.call_args.args[1]
            self.assertEqual(Path(argv[1]).name, "settings.py")
            self.assertEqual(argv[-1], "--preferences")

    def test_installed_launchers_share_one_dispatcher(self):
        for binary in ("ascii-saver", "ascii-saver-settings", "ascii-saverctl"):
            self.assertIn("cli.py", (ROOT / "bin" / binary).read_text())
        self.assertIn('"play"', (SRC / "ctl.py").read_text())
        self.assertIn('"$py_src/cli.py"', (ROOT / "install.sh").read_text())
        self.assertIn('Exec=@APP@', (ROOT / 'data/io.github.robbybobby77.AsciiSaver.desktop.in').read_text())
        self.assertIn('@APP@', (ROOT / 'install.sh').read_text())


class GuiRegressionContracts(unittest.TestCase):
    def test_preferences_banner_controls_are_fields_across_methods(self):
        source = (SRC / 'preferences_shell.py').read_text()
        tree = ast.parse(source)
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'ShellBuilderMixin')
        methods = {n.name: ast.get_source_segment(source,n) for n in cls.body if isinstance(n, ast.FunctionDef)}
        shell, navigation = methods['_make_shell'], methods['_make_navigation']
        self.assertIn('self.banner_label = Gtk.Label(', shell)
        self.assertIn('self.banner_discard = Gtk.Button(', shell)
        self.assertIn('toolbar_view.add_bottom_bar(self.changes_tray)', navigation)
        self.assertIn('self.unsaved_banner.set_visible(False)', shell)
        # The original regression was a NameError in _make_navigation.
        self.assertNotIn('compact_actions.add_setter(banner_label', navigation)
        self.assertNotIn('compact_actions.add_setter(banner_discard', navigation)

    def test_preferences_command_does_not_create_dashboard_first(self):
        source = (SRC / 'settings.py').read_text()
        tree = ast.parse(source)
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'SettingsApplication')
        fn = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == 'do_command_line')
        ns = {}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'settings.py', 'exec'), ns)
        command = types.SimpleNamespace(get_arguments=lambda: ['settings.py','--preferences'])
        mock = types.SimpleNamespace(open_preferences=Mock(), open_playlist_editor=Mock(), activate=Mock())
        self.assertEqual(ns['do_command_line'](mock, command), 0)
        mock.open_preferences.assert_called_once_with('general')
        mock.activate.assert_not_called()
        command.get_arguments = lambda: ['settings.py']
        self.assertEqual(ns['do_command_line'](mock, command), 0)
        mock.activate.assert_called_once_with()

    def test_help_and_components_are_modal_and_escape_closable(self):
        src = (SRC / 'app_menu.py').read_text()
        self.assertIn("Adw.Window(title=title, transient_for=parent, modal=True)", src)
        self.assertIn('Gdk.KEY_Escape', src)
        self.assertIn("win.close()", src)
        self.assertNotIn("header.pack_end(close_button)", src)
        self.assertIn('header = Adw.HeaderBar()', src)
        for fn in ('show_components', 'show_help'):
            self.assertIn(f'def {fn}(parent):', src)
            self.assertIn("_window(parent,", src)


if __name__ == '__main__':
    unittest.main()
