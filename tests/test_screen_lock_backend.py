"""Session-specific screen lock is not the freedesktop idle inhibitor."""
import unittest
from screen_lock_backend import GNOME, KDE, select_screen_lock_backend

class ScreenLockBackendTests(unittest.TestCase):
    def test_gnome_uses_shell_lock_screen_interface(self):
        result = select_screen_lock_backend({'XDG_CURRENT_DESKTOP':'GNOME', 'XDG_SESSION_TYPE':'wayland'})
        self.assertEqual(result, GNOME)
        self.assertEqual(result.destination, 'org.gnome.ScreenSaver')
        self.assertEqual(result.path, '/org/gnome/ScreenSaver')
        self.assertEqual(result.interface, 'org.gnome.ScreenSaver')
        self.assertFalse(result.about_to_lock)

    def test_kde_uses_kscreenlocker(self):
        result = select_screen_lock_backend({'XDG_CURRENT_DESKTOP':'KDE'})
        self.assertEqual(result, KDE)
        self.assertTrue(result.about_to_lock)
        self.assertEqual(result.path, '/ScreenSaver')

    def test_explicit_gnome_backend_without_desktop_environment(self):
        self.assertEqual(select_screen_lock_backend({'ASCII_SAVER_BACKEND': 'gnome'}), GNOME)
        self.assertEqual(select_screen_lock_backend({'ASCII_SAVER_BACKEND': 'gnome', 'XDG_CURRENT_DESKTOP': 'KDE'}), GNOME)

    def test_fallback_variable_and_case(self):
        self.assertEqual(select_screen_lock_backend({'XDG_SESSION_DESKTOP':'gnome'}), GNOME)
        self.assertEqual(select_screen_lock_backend({'XDG_CURRENT_DESKTOP':'ubuntu:GNOME'}), GNOME)
        self.assertEqual(select_screen_lock_backend({'XDG_CURRENT_DESKTOP':'KDE:Plasma'}), KDE)
