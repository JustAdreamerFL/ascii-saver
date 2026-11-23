import unittest
from artwork_fit import artwork_cells, fit_ratio, suggested_point_size


class ArtworkFitTests(unittest.TestCase):
    def test_unicode_and_tabs_use_terminal_cell_width(self):
        self.assertEqual(artwork_cells('界x\nA\tB'), (9, 2))

    def test_empty(self):
        self.assertEqual(artwork_cells(''), (0, 0))

    def test_ratio_does_not_enlarge_fonts(self):
        self.assertEqual(fit_ratio(10, 4, 20, 20), 1.0)
        self.assertEqual(suggested_point_size(18, (10, 4), (20, 20)), 18)

    def test_portrait_monitor_requires_shrinking(self):
        self.assertEqual(fit_ratio(100, 20, 50, 100), 0.5)
        self.assertLess(suggested_point_size(18, (100, 20), (50, 100)), 9)

    def test_unmeasured_terminal_does_not_guess(self):
        self.assertEqual(fit_ratio(100, 20, 0, 0), 1.0)

    def test_minimum_font_size(self):
        self.assertEqual(suggested_point_size(18, (999, 100), (20, 10)), 7.0)


if __name__ == '__main__':
    unittest.main()
