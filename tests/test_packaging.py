import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _bootstrap import ROOT, read_source


class PackagingTests(unittest.TestCase):
    def test_package_versions_match(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        changelog = (ROOT / "debian/changelog").read_text(encoding="utf-8")
        spec = (ROOT / "packaging/fedora/ascii-saver.spec").read_text(encoding="utf-8")
        pkgbuild = (ROOT / "packaging/arch/PKGBUILD").read_text(encoding="utf-8")
        self.assertIn(f"({version})", changelog.splitlines()[0])
        self.assertIn(f"Version:        {version}", spec)
        self.assertIn(f"pkgver={version}", pkgbuild)

    def test_identity_matches_package_assets(self):
        app = read_source("app.py")
        payload = (ROOT / "packaging/linux/build-payload.sh").read_text(encoding="utf-8")
        self.assertIn('APP_ID = "com.github.justadreamerfl.asciisaver"', app)
        self.assertIn("com.github.justadreamerfl.asciisaver.desktop", payload)
        self.assertIn("com.github.justadreamerfl.asciisaver.svg", payload)

    def test_payload_builds_without_installed_toolchain(self):
        payload = (ROOT / "packaging/linux/build-payload.sh").read_text(encoding="utf-8")
        self.assertIn("TTFX_BINARY", payload)
        self.assertIn("ascii-saver-watcher-kde", payload)
        self.assertIn("ascii-saver-watcher-gnome", payload)
        self.assertNotIn("venv", payload)
        self.assertIn("src/*.py", payload)
        self.assertIn("preview-packs/*.aspr", payload)

    def test_launchers_use_system_python_and_package_paths(self):
        for name in (
            "ascii-saver.in",
            "ascii-saverctl.in",
            "ascii-saver-settings.in",
            "ascii-saver-watcher.in",
        ):
            text = (ROOT / "packaging/linux/launchers" / name).read_text(encoding="utf-8")
            self.assertIn("ASCII_SAVER_PACKAGE_DIR", text)
            self.assertNotIn("venv", text)
            if name != "ascii-saver-watcher.in":
                self.assertIn('"@PYTHON@"', text)

    def test_package_definitions_target_three_distros(self):
        self.assertTrue((ROOT / "debian/control").is_file())
        self.assertTrue((ROOT / "packaging/fedora/ascii-saver.spec").is_file())
        self.assertTrue((ROOT / "packaging/arch/PKGBUILD").is_file())
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn("Debian package", workflow)
        self.assertIn("Fedora ${{ matrix.version }} package", workflow)
        self.assertIn("Arch package", workflow)
        self.assertIn("ttfx-linux-x86_64", workflow)
        self.assertIn("release-assets", workflow)
        self.assertIn("debian_version", workflow)
        self.assertIn("fedora_versions", workflow)
        self.assertIn("arch_image", workflow)
        self.assertIn("default: latest", workflow)
        self.assertIn("docker run --rm fedora:latest", workflow)
        self.assertIn("latest - 1", workflow)
        self.assertIn("default: base-devel", workflow)


    def test_packaged_controller_resolves_system_launchers(self):
        with tempfile.TemporaryDirectory() as tmp:
            bindir = Path(tmp) / "bin"
            appdir = Path(tmp) / "lib" / "ascii-saver"
            bindir.mkdir()
            appdir.mkdir(parents=True)
            for name in ("ascii-saver", "ascii-saver-settings"):
                launcher = bindir / name
                launcher.write_text("#!/bin/sh\n", encoding="utf-8")
                launcher.chmod(0o755)
            env = os.environ.copy()
            env["ASCII_SAVER_PACKAGE_DIR"] = str(appdir)
            env["PATH"] = f"{bindir}:{env['PATH']}"
            env["XDG_CURRENT_DESKTOP"] = "KDE"
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import ctl; print(ctl.launcher); print(ctl.settings_launcher); "
                    "print(ctl.watcher_binary); print(ctl.ttfx_binary)",
                ],
                cwd=ROOT / "src",
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            lines = result.stdout.splitlines()
            self.assertEqual(lines[0], str(bindir / "ascii-saver"))
            self.assertEqual(lines[1], str(bindir / "ascii-saver-settings"))
            self.assertEqual(lines[2], str(appdir / "ascii-saver-watcher-kde"))
            self.assertEqual(lines[3], str(appdir / "ttfx"))

    def test_package_cache_is_ignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".package-ttfx", ignore)


if __name__ == "__main__":
    unittest.main()
