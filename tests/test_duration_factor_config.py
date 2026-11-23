import tempfile
import unittest
import json
from pathlib import Path
from helpers import load_config

class DurationConfigTests(unittest.TestCase):
    def test_valid_values(self):
        for value in (0.5, 1, 2.5, 10):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as d:
                p=Path(d)/"config.json";p.write_text(json.dumps({"duration_factor":value}))
                self.assertEqual(load_config(p)["duration_factor"],float(value))
    def test_invalid_values(self):
        for value in (0.1, 20, "2", True, None):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as d:
                p=Path(d)/"config.json";p.write_text(json.dumps({"duration_factor":value}))
                self.assertEqual(load_config(p)["duration_factor"],1.0)

if __name__ == "__main__": unittest.main()
