from _bootstrap import SRC, read_source  # noqa: F401
import unittest
from performance_series import make_series,metric_range

class PerformanceSeriesTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.records = [
            {'monitor':'DP-1','wall_timestamp':950,'cpu_percent':40,'rss_mib':100,'gpu_percent':16},
            {'monitor':'HDMI-1','wall_timestamp':960,'cpu_percent':20,'rss_mib':80,'gpu_percent':None},
            {'monitor':'DP-1','wall_timestamp':970,'cpu_percent':30,'rss_mib':103,'gpu_percent':18},
            {'monitor':'DP-1','wall_timestamp':971,'event':'effect_start','cpu_percent':999,'gpu_percent':999},
        ]
    def test_monitor_isolation(self):
        values=make_series(self.records,'cpu_percent',self.now,monitor='DP-1')
        self.assertEqual(values,{'DP-1':[(950.,40.),(970.,30.)]})
    def test_gpu_unavailable_is_not_zero(self):
        self.assertEqual(make_series(self.records,'gpu_percent',self.now,monitor='HDMI-1'),{})
    def test_event_records_are_excluded(self):
        self.assertEqual(len(make_series(self.records,'cpu_percent',self.now)['DP-1']),2)
    def test_expired_samples(self):
        self.assertEqual(make_series(self.records,'cpu_percent',self.now,seconds=20),{})
    def test_nonfinite_and_boolean_rejected(self):
        values=[{'monitor':'X','wall_timestamp':1000,'gpu_percent':v} for v in (float('nan'),float('inf'),True,-1)]
        self.assertEqual(make_series(values,'gpu_percent',self.now),{})
    def test_multiple_engines_not_clipped(self):
        self.assertGreater(metric_range({'x':[(950,135)]}),135)
    def test_invalid_metric(self):
        with self.assertRaises(ValueError): make_series(self.records,'imaginary',self.now)
if __name__=='__main__': unittest.main()
