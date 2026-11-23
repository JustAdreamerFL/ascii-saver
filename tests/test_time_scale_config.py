import unittest
from helpers import new_config, _apply_config
from pathlib import Path
class ScaleTests(unittest.TestCase):
    def test_default(self):
        self.assertEqual(new_config()["time_scale"], 1.0)
    def test_valid(self):
        self.assertEqual(_apply_config(new_config(), {"time_scale": 0.1}, Path("test"))["time_scale"], 0.1)
    def test_invalid(self):
        self.assertEqual(_apply_config(new_config(), {"time_scale": float("nan")}, Path("test"))["time_scale"], 1.0)
if __name__ == "__main__": unittest.main()
