"""Regression tests for automatic watcher ownership and stale PID recovery.

Actually compile the platform-neutral process-check header as both C and C++.
This does not claim a full Qt/KIdleTime or GNOME/GIO build.
"""
from __future__ import annotations
from _bootstrap import SRC, read_source  # noqa: F401

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeProcessIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("cc") or not shutil.which("g++"):
            raise unittest.SkipTest("a C and C++ compiler are required for native watcher probes")
        cls.folder = tempfile.TemporaryDirectory(prefix="ascii-v102-")
        cls.temp = Path(cls.folder.name)
        cls.binaries = []
        for compiler, flags, name in (
            ("cc", ["-std=gnu11"], "probe_c"),
            ("g++", ["-std=c++17", "-x", "c++"], "probe_cpp"),
        ):
            output = cls.temp / name
            subprocess.run(
                [compiler, *flags, "-Wall", "-Wextra", "-Werror", "-I", str(ROOT / "native" / "kde"),
                 str(ROOT / "tests" / "native_watcher_identity_probe.c"), "-o", str(output)],
                check=True, capture_output=True, timeout=20,
            )
            cls.binaries.append(output)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "folder"):
            cls.folder.cleanup()

    def probe(self, binary, *args):
        return subprocess.run([str(binary), *map(str, args)], capture_output=True, timeout=5)

    def test_pidfile_accepts_own_decimal_pid(self):
        file = self.temp / "renderer.pid"
        file.write_text(f"{os.getpid()}\n")
        for binary in self.binaries:
            completed = self.probe(binary, "read", file)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout.strip(), str(os.getpid()).encode())

    def test_pidfile_rejects_invalid_overflow_and_nonregular_files(self):
        file = self.temp / "renderer.pid"
        for value in ["", "-1\n", "0\n", "1;rm -rf /", "11 22", "a23", "9" * 90,
                      "99999999999999999999999999\n"]:
            with self.subTest(value=value[:20]):
                file.write_text(value)
                for binary in self.binaries:
                    self.assertNotEqual(self.probe(binary, "read", file).returncode, 0)
        for binary in self.binaries:
            self.assertNotEqual(self.probe(binary, "read", self.temp).returncode, 0)

    def test_pidfile_rejects_symlink(self):
        real = self.temp / "real.pid"
        linked = self.temp / "linked.pid"
        real.write_text(f"{os.getpid()}\n")
        linked.symlink_to(real)
        for binary in self.binaries:
            self.assertNotEqual(self.probe(binary, "read", linked).returncode, 0)

    def test_renderer_requires_exact_script_argument_one(self):
        script = self.temp / "app.py"
        script.write_text("import time\ntime.sleep(30)\n")
        another = self.temp / "different.py"
        another.write_text("import time\ntime.sleep(30)\n")
        child = subprocess.Popen([sys.executable, str(script)], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        try:
            for binary in self.binaries:
                self.assertEqual(self.probe(binary, "renderer", child.pid, script).returncode, 0)
                self.assertNotEqual(self.probe(binary, "renderer", child.pid, another).returncode, 0)
                self.assertNotEqual(self.probe(binary, "renderer", child.pid, "app.py").returncode, 0)
                self.assertNotEqual(self.probe(binary, "renderer", os.getpid(), script).returncode, 0)
        finally:
            child.terminate()
            child.wait(timeout=5)
        for binary in self.binaries:
            self.assertNotEqual(self.probe(binary, "renderer", child.pid, script).returncode, 0)

    def test_renderer_does_not_accept_filename_as_third_argument(self):
        script = self.temp / "app.py"
        child = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)", str(script)],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for binary in self.binaries:
                self.assertNotEqual(self.probe(binary, "renderer", child.pid, script).returncode, 0)
        finally:
            child.terminate()
            child.wait(timeout=5)

    def test_watcher_requires_same_native_executable(self):
        for binary in self.binaries:
            child = subprocess.Popen([str(binary), "hold", "x"], stdout=subprocess.DEVNULL)
            try:
                self.assertEqual(self.probe(binary, "watcher", child.pid).returncode, 0)
                other = next(x for x in self.binaries if x != binary)
                self.assertNotEqual(self.probe(other, "watcher", child.pid).returncode, 0)
                self.assertNotEqual(self.probe(binary, "watcher", os.getpid()).returncode, 0)
            finally:
                child.terminate()
                child.wait(timeout=5)


class WatcherIntegrationContracts(unittest.TestCase):
    def test_kde_defers_on_manual_renderer_before_launch_and_retry(self):
        source = (ROOT / "native/kde/watcher.cpp").read_text()
        self.assertIn('#include "watcher_process_identity.h"', source)
        self.assertIn('blockedByActivity() || rendererAlreadyRunning()', source)
        self.assertIn('&& !blockedByActivity() && !rendererAlreadyRunning()', source)
        start = source.split('void startSaver()', 1)[1].split('void pollState()', 1)[0]
        self.assertLess(start.index('rendererAlreadyRunning()'), start.index('m_process.start()'))
        self.assertIn('m_idleDeferred = true;', start)

    def test_gnome_holds_nonblocking_pid_lock_and_checks_legacy_watcher(self):
        source = (ROOT / "native/gnome/gnome_idle_watcher.c").read_text()
        self.assertIn('#include "watcher_process_identity.h"', source)
        self.assertIn('flock(fd, LOCK_EX | LOCK_NB)', source)
        self.assertIn('ascii_saver_pid_is_watcher(old_pid)', source)
        self.assertIn('ascii_saver_pid_is_renderer(pid, script)', source)
        self.assertIn('release_pid(&w);', source)
        self.assertIn('held.st_ino == path_info.st_ino', source)


if __name__ == "__main__":
    unittest.main()
