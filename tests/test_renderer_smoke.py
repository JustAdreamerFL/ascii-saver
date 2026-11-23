import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent

class SmokeIntegrationTests(unittest.TestCase):
    def test_smoke_script_parses(self):
        ast.parse((ROOT/'scripts/smoke-renderer.py').read_text())
    def test_application_cleans_both_spawn_failures(self):
        module=ast.parse((ROOT/'app.py').read_text())
        method=next(n for c in module.body if isinstance(c,ast.ClassDef) and c.name=='SaverWindow'
                    for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='_on_spawned')
        source=ast.get_source_segment((ROOT/'app.py').read_text(),method)
        self.assertEqual(source.count('self._discard_pending_frame_report()'),2)
    def test_integrated_verifier_runs_smoke_after_build(self):
        text=(ROOT/'verify-build.sh').read_text()
        self.assertLess(text.index('cargo build'), text.index('scripts/smoke-renderer.py'))

if __name__=='__main__': unittest.main()
