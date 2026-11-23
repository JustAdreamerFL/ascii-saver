from _bootstrap import SRC, read_source  # noqa: F401
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
class InstallerRendererContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.install = (ROOT / "install.sh").read_text()
    def test_bundled_cargo_build(self):
        self.assertIn('cargo build', self.install)
        self.assertIn('ttfx-rust/Cargo.toml', self.install)
        self.assertIn('--release --locked', self.install)
    def test_required_capabilities(self):
        for option in ('--stats-file', '--time-scale', '--duration-factor'):
            self.assertIn(option, self.install)
    def test_no_implicit_system_fallback(self):
        self.assertNotIn('command -v ttfx || true', self.install)
    def test_staged_binary_install(self):
        self.assertIn('"$staged_app/venv/bin/ttfx"', self.install)

if __name__ == '__main__': unittest.main()
