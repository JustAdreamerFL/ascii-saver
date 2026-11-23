"""Offline structural guard for the Rust compiler error exposed in V44.

Rust's `for .. in` takes an IntoIterator; repeat_count already returns a Range.
The real compile check still takes place in verify-build.sh when Cargo is installed.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
EFFECT_SRC = ROOT / 'ttfx-rust' / 'src' / 'engine' / 'effect.rs'


class RustSimulationHoldSourceTest(unittest.TestCase):
    def test_repeat_count_is_iterator_directly(self):
        code = EFFECT_SRC.read_text(encoding='utf-8')
        self.assertRegex(code, r'fn\s+repeat_count\s*\([^)]*\)\s*->\s*std::ops::Range<u32>')
        self.assertRegex(code, r'for\s+_\s+in\s+repeat_count\s*\(')
        self.assertNotRegex(code, r'for\s+_\s+in\s+1\s*\.\.\s*repeat_count\s*\(')


if __name__ == '__main__':
    unittest.main()
