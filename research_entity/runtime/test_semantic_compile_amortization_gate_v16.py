from __future__ import annotations
import unittest
from .semantic_compile_amortization_gate_v16 import CompileEconomics, decide_compile

class CompileAmortizationGateV16Tests(unittest.TestCase):
    def base(self,reads=2000,**kw):
        x=dict(build_cost_us=72295.54633333333,online_query_us=60.76010636666667,
               compiled_query_us=4.294575966666667,online_quality=1.0,compiled_quality=1.0,
               expected_reads_before_invalidation=reads,safety_factor=1.20)
        x.update(kw); return CompileEconomics(**x)
    def test_low_lifetime_stays_online(self):
        self.assertEqual(decide_compile(self.base(1000)).mode,'ONLINE')
    def test_high_lifetime_compiles(self):
        self.assertEqual(decide_compile(self.base(2000)).mode,'COMPILE')
    def test_quality_regression_never_compiles(self):
        d=decide_compile(self.base(10000,compiled_quality=.99)); self.assertEqual(d.mode,'ONLINE'); self.assertEqual(d.reason,'COMPILED_QUALITY_WORSE')
    def test_no_query_saving_never_compiles(self):
        d=decide_compile(self.base(10000,compiled_query_us=70)); self.assertEqual(d.mode,'ONLINE'); self.assertEqual(d.reason,'NO_POSITIVE_QUERY_SAVING')
    def test_measured_break_even(self):
        d=decide_compile(self.base(2000)); self.assertAlmostEqual(d.break_even_reads,1280.3483084493141); self.assertAlmostEqual(d.guarded_break_even_reads,1536.417970139177)

if __name__=='__main__': unittest.main()
