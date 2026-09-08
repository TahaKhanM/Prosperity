"""Numerical regression tests; run with python3 -m unittest discover -s tests."""
import importlib.util
import math
from pathlib import Path
import sys
import unittest

OPTIONS = Path(__file__).resolve().parents[1] / 'prosperity_rust_backtester/scripts/round4_options'
sys.path.insert(0, str(OPTIONS))
import bs
import exotic_pricers as ex


class VanillaPricingTests(unittest.TestCase):
    def test_textbook_price(self):
        self.assertAlmostEqual(bs.bs_call_price(100, 100, 1, .2, .05), 10.450583572185565, places=10)
        self.assertAlmostEqual(bs.bs_put_price(100, 100, 1, .2, .05), 5.573526022256971, places=10)

    def test_put_call_parity_including_zero_volatility(self):
        for rate in [-.08, 0, .08]:
            for vol in [0, .1, .4, 2]:
                for spot in [80, 100, 120]:
                    with self.subTest(rate=rate, vol=vol, spot=spot):
                        call = bs.bs_call_price(spot, 100, 1.5, vol, rate)
                        put = bs.bs_put_price(spot, 100, 1.5, vol, rate)
                        self.assertAlmostEqual(call - put, spot - 100 * math.exp(-rate * 1.5), places=10)

    def test_forced_bisection_recovers_input_volatility(self):
        for vol in [.03, .1, .2, .7, 1.5, 3.5]:
            for rate in [-.05, 0, .05]:
                price = bs.bs_call_price(100, 100, 1, vol, rate)
                result = bs.implied_vol_call(price, 100, 100, 1, rate, max_iter=0)
                self.assertAlmostEqual(result, vol, delta=1e-7)

    def test_newton_and_put_iv(self):
        for spot in [85, 100, 120]:
            price = bs.bs_put_price(spot, 100, .5, .4, -.03)
            self.assertAlmostEqual(bs.implied_vol_put(price, spot, 100, .5, -.03), .4, delta=1e-7)

    def test_iv_rejects_invalid_or_unbracketed_quotes(self):
        lower = 100 - 100 * math.exp(-.05)
        for price in [-1, lower - 1e-5, 100, 101, float('nan'), float('inf')]:
            self.assertTrue(math.isnan(bs.implied_vol_call(price, 100, 100, 1, .05)))
        price = bs.bs_call_price(100, 100, 1, 2)
        self.assertTrue(math.isnan(bs.implied_vol_call(price, 100, 100, 1, sigma_hi=1)))
        self.assertTrue(math.isnan(bs.implied_vol_call(10, 100, 100, 0)))
        self.assertEqual(bs.implied_vol_call(lower, 100, 100, 1, .05), 0)

    def test_invalid_pricing_parameters(self):
        for args in [(0, 100, 1, .2), (100, -1, 1, .2), (100, 100, -1, .2), (100, 100, 1, -.2)]:
            with self.assertRaises(ValueError):
                bs.bs_call_price(*args)

    def test_greeks_agree_with_finite_differences(self):
        s,k,t,v,r = 101,100,.8,.3,.02
        h = 1e-3
        self.assertAlmostEqual(bs.bs_call_delta(s,k,t,v,r), (bs.bs_call_price(s+h,k,t,v,r)-bs.bs_call_price(s-h,k,t,v,r))/(2*h), places=8)
        self.assertAlmostEqual(bs.bs_call_vega(s,k,t,v,r), (bs.bs_call_price(s,k,t,v+h,r)-bs.bs_call_price(s,k,t,v-h,r))/(2*h), places=4)

    def test_zero_volatility_greeks_use_deterministic_limits(self):
        rate, expiry, strike = .05, 1.0, 100.0
        self.assertAlmostEqual(bs.bs_call_theta(120, strike, expiry, 0, rate), -rate*strike*math.exp(-rate*expiry))
        self.assertEqual(bs.bs_call_theta(80, strike, expiry, 0, rate), 0)
        # At-the-money forward vega is a right derivative at sigma=0.
        self.assertAlmostEqual(bs.bs_call_vega(100, 100, 1, 0), 100/math.sqrt(2*math.pi))
        self.assertTrue(math.isnan(bs.bs_call_gamma(100, 100, 1, 0)))


class ExoticPricingTests(unittest.TestCase):
    def test_barrier_reflection_does_not_overflow_or_drop_its_tail(self):
        # 80-digit mpmath evaluation of the analytic truncated-normal moments.
        # Drift ends the zero-volatility path exactly on the barrier: the
        # reflected tail matters even when its unscaled probability underflows.
        expected = {0.007: 5.467289468975442, 0.0069: 5.470813230119541,
                    0.005: 5.537800254559332, 0.001: 5.678976684293369}
        for sigma, price in expected.items():
            with self.subTest(sigma=sigma):
                self.assertAlmostEqual(ex.down_and_out_put(40,45,35,1,sigma,-math.log(40/35)), price, delta=2e-9)

    def test_exotic_delta_rejects_invalid_inputs(self):
        for args in [(40,45,-1,.2), (40,45,1,-.2), (0,45,1,.2)]:
            with self.assertRaises(ValueError):
                ex.digital_put_delta(*args)
        with self.assertRaises(ValueError):
            ex.digital_put_delta(40,45,1,.2,payoff=-1)
        for h in [0, -1, float('nan')]:
            with self.assertRaises(ValueError):
                ex.down_and_out_put_delta(40,45,35,1,.2,h=h)

    @staticmethod
    def integrate_absorbed_payoff(s, k, b, t, sigma, r):
        # Independent numerical quadrature of the killed GBM density: no use
        # of the production normal-CDF antiderivative or in/out parity.
        x = math.log(s / b)
        var = sigma*sigma*t
        drift = (r - sigma*sigma/2)*t
        upper = math.log(k / b)
        n = 4000
        h = upper/n
        def integrand(y):
            free = math.exp(-(y-x-drift)**2/(2*var))
            image = math.exp(-2*drift*x/var - (y+x-drift)**2/(2*var))
            return (k-b*math.exp(y))*(free-image)/math.sqrt(2*math.pi*var)
        acc = integrand(0)+integrand(upper)
        acc += sum((4 if i%2 else 2)*integrand(i*h) for i in range(1,n))
        return math.exp(-r*t)*acc*h/3

    def test_barrier_matches_independent_quadrature(self):
        for spot in [35.1, 36, 40, 45, 48]:
            for rate in [-.03, 0, .03]:
                with self.subTest(spot=spot,rate=rate):
                    args = spot,45,35,21/365,.2,rate
                    self.assertAlmostEqual(ex.down_and_out_put(*args), self.integrate_absorbed_payoff(*args), delta=1e-9)

    def test_barrier_boundary_limits(self):
        self.assertEqual(ex.down_and_out_put(35,45,35,1,.2),0)
        self.assertEqual(ex.down_and_out_put(50,30,35,1,.2),0)
        self.assertEqual(ex.down_and_out_put(40,45,35,0,.2),5)
        self.assertAlmostEqual(ex.down_and_out_put(40,45,1,1,.2),bs.bs_put_price(40,45,1,.2),places=10)
        self.assertEqual(ex.down_and_out_put(40,45,35,1,0,-.2),0)
        self.assertAlmostEqual(ex.down_and_out_put(40,45,35,1,0,.02),45*math.exp(-.02)-40)

    def test_chooser_decision_boundaries(self):
        s,k,t,v,r=48,50,.2,.3,.01
        self.assertAlmostEqual(ex.chooser_value(s,k,t,t,v,r),bs.bs_call_price(s,k,t,v,r)+bs.bs_put_price(s,k,t,v,r))
        self.assertAlmostEqual(ex.chooser_value(s,k,t,0,v,r),max(bs.bs_call_price(s,k,t,v,r),bs.bs_put_price(s,k,t,v,r)))
        h=1e-4
        numerical=(ex.chooser_value(s+h,k,t,0,v,r)-ex.chooser_value(s-h,k,t,0,v,r))/(2*h)
        self.assertAlmostEqual(ex.chooser_delta(s,k,t,0,v,r),numerical,places=7)

    def test_digital_zero_vol_uses_forward_and_discount(self):
        self.assertEqual(ex.digital_put_value(39,40,1,0,10,.05),0)
        self.assertAlmostEqual(ex.digital_put_value(41,40,1,0,10,-.05),10*math.exp(.05))


if __name__ == '__main__':
    unittest.main()
