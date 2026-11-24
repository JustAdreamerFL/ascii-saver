import ast
import unittest

from _bootstrap import read_source


class PreferencesImportTests(unittest.TestCase):
    def test_gallery_view_imports_adaptive_action_row(self):
        tree = ast.parse(read_source("preferences_gallery_view.py"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "adwaita_ui":
                imported.update(alias.name for alias in node.names)
        used = {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }
        self.assertIn("adaptive_action_row", used)
        self.assertIn("adaptive_action_row", imported)


if __name__ == "__main__":
    unittest.main()
