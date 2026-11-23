from _bootstrap import SRC, read_source  # noqa: F401
import tempfile
import unittest
from pathlib import Path
from gpu_accounting import read_engine_counters,GPUSampler

class DRMTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.fd=self.root/'123'/'fdinfo'
        self.fd.mkdir(parents=True)
    def write(self,n,client,ns,engine='gfx'):
        (self.fd/str(n)).write_text(f'drm-driver: amdgpu\ndrm-client-id: {client}\ndrm-pdev: 0000:03:00.0\ndrm-engine-{engine}: {ns} ns\n')
    def test_missing_fdinfo(self):
        self.assertIsNone(read_engine_counters(44,self.root))
    def test_no_drm_counters(self):
        (self.fd/'1').write_text('pos: 0\n')
        self.assertIsNone(read_engine_counters(123,self.root))
    def test_duplicate_fd_client_not_double_counted(self):
        self.write(1,'15',100)
        self.write(2,'15',100)
        self.assertEqual(read_engine_counters(123,self.root),{'gfx':100})
    def test_two_clients_aggregate(self):
        self.write(1,'15',100)
        self.write(2,'16',90)
        self.assertEqual(read_engine_counters(123,self.root),{'gfx':190})
    def test_delta_engine_time(self):
        self.write(1,'15',100000000)
        sampler=GPUSampler(self.root)
        self.assertIsNone(sampler.sample(123,42,1.0))
        self.write(1,'15',300000000)
        self.assertEqual(sampler.sample(123,42,2.0),{'gfx':20.0})
    def test_reused_pid_resets(self):
        self.write(1,'15',100)
        sampler=GPUSampler(self.root)
        sampler.sample(123,42,1.0)
        self.write(1,'15',300)
        self.assertIsNone(sampler.sample(123,43,2.0))
    def test_reset_counter_does_not_negative(self):
        self.write(1,'15',300)
        sampler=GPUSampler(self.root)
        sampler.sample(123,42,1.0)
        self.write(1,'15',100)
        self.assertIsNone(sampler.sample(123,42,2.0))

if __name__=='__main__': unittest.main()
