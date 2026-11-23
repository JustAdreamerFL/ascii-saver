from _bootstrap import SRC, read_source  # noqa: F401
import unittest
from spawn_events import spawn_event

class SpawnLoggingTests(unittest.TestCase):
    def setUp(self):
        self.pending={"effect":"rain","monitor":"HDMI-A-1","fps_cap":60,"speed_multiplier":1.0}
    def test_success(self):
        event=spawn_event(self.pending,True,pid=123,timestamp=100.0)
        self.assertEqual(event["event"],"effect_start")
        self.assertEqual(event["pid"],123)
        self.assertEqual(self.pending["effect"],"rain")
    def test_failure(self):
        event=spawn_event(self.pending,False,message="no binary",timestamp=100.0)
        self.assertEqual(event["event"],"effect_spawn_failed")
        self.assertNotIn("pid",event)
        self.assertEqual(event["error"],"no binary")
    def test_no_duplicate_without_pending(self):
        self.assertIsNone(spawn_event(None,True,pid=123,timestamp=100.0))
    def test_pid_validation(self):
        with self.assertRaises(ValueError):
            spawn_event(self.pending,True,pid=-1,timestamp=100.0)
