from _bootstrap import SRC, read_source  # noqa: F401
import unittest
import tempfile
from pathlib import Path
from helpers import load_config

class SimulationHoldConfigTest(unittest.TestCase):
    def test_default(self):
        self.assertEqual(load_config(Path('/nonexistent/config.json'))['simulation_hold'],1)
    def test_valid(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'config.json';p.write_text('{"simulation_hold": 4}')
            self.assertEqual(load_config(p)['simulation_hold'],4)
    def test_invalid(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'config.json';p.write_text('{"simulation_hold": true}')
            self.assertEqual(load_config(p)['simulation_hold'],1)

if __name__=='__main__':unittest.main()
