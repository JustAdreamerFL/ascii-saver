"""V60 preferences editor and strict separation from KDE-prefixed installations."""
from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]

class CleanIdentityTests(unittest.TestCase):
    def test_default_artwork_uses_native_editor_not_captured_terminal(self):
        shell = (ROOT / "preferences_shell.py").read_text()
        actions = (ROOT / "preferences_actions.py").read_text()
        menu = (ROOT / "app_menu.py").read_text()
        app_actions = (ROOT / "application_actions.py").read_text()
        self.assertIn('("Edit Artwork", "Open", self._edit_default_artwork)', (ROOT / 'preferences_pages.py').read_text())
        self.assertNotIn("'Edit Artwork', 'app.edit-artwork'", menu)
        self.assertIn('self.preferences_window._edit_default_artwork()', app_actions)
        self.assertIn('editor = ArtworkEditor(self, path, on_finished=finished, config_dir=ctl.config_dir)', actions)
        self.assertIn('editor.present()', actions)
        self.assertIn('if command == "edit":', actions)
        self.assertIn('self._edit_default_artwork(_button)', actions)
        ast.parse(actions)
    def test_no_implicit_legacy_migration_or_cleanup(self):
        for name in ("install.sh", "uninstall.sh"):
            with self.subTest(script=name):
                contents = (ROOT/name).read_text()
                # Only a comment mentioning legacy paths is acceptable.
                commands = "\n".join(line for line in contents.splitlines() if not line.strip().startswith("#"))
                self.assertNotIn('kde-ascii-saver', commands)
                self.assertNotIn('KDE_ASCII_SAVER', commands)
        installer = (ROOT/"install.sh").read_text()
        self.assertIn('"$cache_home/ascii-saver"', installer)
        self.assertIn('"$config_home/ascii-saver"', installer)
    def test_new_uninstall_preserves_configuration_and_does_not_purge_cache(self):
        uninstaller = (ROOT/'uninstall.sh').read_text()
        self.assertIn('are always preserved', uninstaller)
        self.assertNotIn('rm -rf -- "$cache_home', uninstaller)
        self.assertIn('ascii-saver-fullscreenEnabled false', uninstaller)
        self.assertNotIn('kde-ascii-saver-fullscreenEnabled', uninstaller)
