import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _bootstrap import ROOT


class ReleaseNotesTests(unittest.TestCase):
    def render(self, names):
        with tempfile.TemporaryDirectory() as tmp:
            assets = Path(tmp) / "assets"
            assets.mkdir()
            for name in names:
                (assets / name).touch()
            output = Path(tmp) / "notes.md"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/render-release-notes.py"),
                    str(assets),
                    "0.111.0",
                    "v0.111.0",
                    str(output),
                ],
                check=True,
            )
            return output.read_text(encoding="utf-8")

    def test_newest_packages_are_primary_and_older_are_collapsed(self):
        text = self.render(
            [
                "ascii-saver_0.111.0_amd64.deb",
                "ascii-saver-0.111.0-1.fc44.x86_64.rpm",
                "ascii-saver-0.111.0-1.fc45.x86_64.rpm",
                "ascii-saver-0.111.0-1-x86_64.pkg.tar.zst",
                "ascii-saver-0.111.0.tar.gz",
                "SHA256SUMS",
            ]
        )
        primary, details = text.split("<details>", 1)
        self.assertIn("Fedora 45", primary)
        self.assertNotIn("Fedora 44", primary)
        self.assertIn("Fedora 44", details)
        self.assertIn("All other distribution versions", text)
        self.assertIn("sudo dnf install ./ascii-saver-0.111.0-1.fc44.x86_64.rpm", text)
        self.assertIn("Source archives", text)
        self.assertIn("SHA256SUMS", text)
        self.assertNotIn("/tmp/", text)

    def test_details_are_omitted_when_no_older_versions_exist(self):
        text = self.render(
            [
                "ascii-saver_0.111.0_amd64.deb",
                "ascii-saver-0.111.0-1.fc45.x86_64.rpm",
                "ascii-saver-0.111.0-1-x86_64.pkg.tar.zst",
                "ascii-saver-0.111.0.tar.gz",
                "SHA256SUMS",
            ]
        )
        self.assertNotIn("All other distribution versions", text)
        self.assertIn("Source archives", text)


if __name__ == "__main__":
    unittest.main()
