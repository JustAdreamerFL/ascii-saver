from _bootstrap import SRC, read_source  # noqa: F401
import unittest
from performance_series import make_series

class MeasuredFPS(unittest.TestCase):
    def test_frame_stats_are_only_fps_source(self):
        records=[{'event':'frame_stats','monitor':'DP-1','effect':'beams','active_output_fps':58.5,'wall_timestamp':100},
                 {'event':'effect_start','monitor':'DP-1','fps_cap':240,'active_output_fps':240,'wall_timestamp':100},
                 {'event':'frame_stats','monitor':'DP-2','effect':'rain','active_output_fps':30,'wall_timestamp':100}]
        self.assertEqual(make_series(records,'active_output_fps',100,monitor='DP-1'),{'DP-1':[(100.,58.5)]})
        self.assertEqual(len(make_series(records,'active_output_fps',100)),2)
    def test_missing_or_corrupt(self):
        records=[{'event':'frame_stats','monitor':'DP-1','active_output_fps':float('nan'),'wall_timestamp':100},
                 {'event':'frame_stats','monitor':'DP-1','active_output_fps':-1,'wall_timestamp':100}]
        self.assertEqual(make_series(records,'active_output_fps',100),{})
    def test_stats_not_aggregated_as_resource_samples(self):
        records=[{'event':'frame_stats','monitor':'DP-1','cpu_percent':99,'wall_timestamp':100}]
        self.assertEqual(make_series(records,'cpu_percent',100),{})
if __name__=='__main__': unittest.main()
