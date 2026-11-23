import unittest
from final_frame import centered_frame

class FrameTests(unittest.TestCase):
    def test_centered_single_line(self):
        self.assertEqual(centered_frame('HI',10,5), b'\x1b[2J\x1b[H\x1b[3;5HHI')
    def test_original_alignment(self):
        frame = centered_frame('  /\\\n /__\\', 20, 6)
        self.assertIn(b'\x1b[3;8H  /\\', frame)
        self.assertIn(b'\x1b[4;8H /__\\', frame)
    def test_ansi_stripped(self):
        self.assertNotIn(b'\x1b[31m',centered_frame('\x1b[31mHELLO', 20,4))
    def test_nonpositive_geometry(self):
        self.assertEqual(centered_frame('HI',0,4),b'')
    def test_crop(self):
        self.assertIn(b'ABCDE',centered_frame('ABCDEFG',5,2))
    def test_cjk(self):
        self.assertIn('\x1b[2;4H界界'.encode(),centered_frame('界界',10,3))
    def test_double_width_crop(self):
        self.assertNotIn('界'.encode(),centered_frame('界',1,1))
    def test_combining(self):
        self.assertIn('\x1b[1;3Ha\u0301'.encode(),centered_frame('a\u0301',5,1))
    def test_tab_expansion_uses_columns(self):
        self.assertIn(b'A       B', centered_frame('A\tB', 18,3))
    def test_block_preserves_trailing_spaces(self):
        frame=centered_frame('XX  \n Y',10,4)
        self.assertIn(b'\x1b[2;4HXX  ',frame)
        self.assertIn(b'\x1b[3;4H Y',frame)

if __name__=='__main__': unittest.main()
