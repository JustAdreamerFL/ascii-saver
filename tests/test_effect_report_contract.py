import re
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class EffectReportContract(unittest.TestCase):
    def test_all_effects_have_stable_names(self):
        text=(ROOT / "ttfx-rust/src/effects/mod.rs").read_text()
        variants=re.findall(r"^    ([A-Z][A-Za-z0-9]*)\(",text.split("pub enum EffectCommand {",1)[1].split("\n}",1)[0],re.M)
        mappings=re.findall(r'Self::([A-Za-z0-9]+)\(\.\.\) => "([a-z0-9]+)"',text)
        self.assertEqual(len(variants),37)
        self.assertEqual(dict(mappings),{name:name.lower() for name in variants})
    def test_no_debug_format_as_effect_name(self):
        text=(ROOT / "ttfx-rust/src/main.rs").read_text()
        self.assertIn('effect_command.effect_name()',text)
        self.assertNotIn('format!("{:?}", effect_command)',text)
if __name__ == "__main__": unittest.main()
