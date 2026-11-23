import unittest
from frame_report import parse_frame_report
class FrameStatsTests(unittest.TestCase):
    def sample(self, **update):
        s={"schema":2,"status":"completed","effect":"beams","frames_written":120,"elapsed_seconds":2.0,"average_output_fps":60.0,"active_output_fps":62.0}
        s.update(update)
        return s
    def test_v2(self):
        self.assertEqual(parse_frame_report(self.sample(),"beams")["active_output_fps"],62.0)
    def test_v1(self):
        self.assertIsNone(parse_frame_report(self.sample(schema=1),"beams")["active_output_fps"])
    def test_mismatched_effect(self):
        self.assertIsNone(parse_frame_report(self.sample(),"rain"))
    def test_errors(self):
        self.assertIsNone(parse_frame_report(self.sample(status="error")))
    def test_bad_fps(self):
        self.assertIsNone(parse_frame_report(self.sample(average_output_fps=float("nan"))))
    def test_bad_count(self):
        self.assertIsNone(parse_frame_report(self.sample(frames_written=-1)))
if __name__ == "__main__": unittest.main()
