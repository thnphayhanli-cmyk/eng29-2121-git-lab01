import math
import unittest

from dc_bias import (
    BiasInput,
    BiasValidationError,
    VCE_SATURATION_THRESHOLD_V,
    calculate_dc_bias,
)


def default_input(**overrides):
    values = dict(
        vcc_v=12.0,
        r1_ohm=100_000.0,
        r2_ohm=22_000.0,
        rc_ohm=2_200.0,
        re_ohm=1_000.0,
        beta=100.0,
        vbe_v=0.70,
    )
    values.update(overrides)
    return BiasInput(**values)


class TestDcBias(unittest.TestCase):

    def test_default_operating_point_matches_hand_calculation(self):
        result = calculate_dc_bias(default_input())
        self.assertAlmostEqual(result.vth_v, 2.163934426, places=6)
        self.assertAlmostEqual(result.rth_ohm, 18_032.786885, places=3)
        self.assertAlmostEqual(result.ib_a, 12.298581463e-6, places=12)
        self.assertAlmostEqual(result.ic_a, 1.229858146e-3, places=9)
        self.assertAlmostEqual(result.ie_a, 1.242156728e-3, places=9)
        self.assertAlmostEqual(result.ve_v, 1.242156728, places=6)
        self.assertAlmostEqual(result.vb_v, 1.942156728, places=6)
        self.assertAlmostEqual(result.vc_v, 9.294312078, places=6)
        self.assertAlmostEqual(result.vce_v, 8.052155351, places=6)
        self.assertEqual(result.region, "Active")
        self.assertEqual(result.warnings, ())

    def test_independent_ie_formula_matches_module(self):
        inp = default_input()
        vth = inp.vcc_v * inp.r2_ohm / (inp.r1_ohm + inp.r2_ohm)
        rth = inp.r1_ohm * inp.r2_ohm / (inp.r1_ohm + inp.r2_ohm)
        ie = (vth - inp.vbe_v) / (rth / (inp.beta + 1) + inp.re_ohm)
        ic = inp.beta / (inp.beta + 1) * ie
        ib = ie / (inp.beta + 1)

        result = calculate_dc_bias(inp)

        self.assertAlmostEqual(result.ie_a, ie, places=12)
        self.assertAlmostEqual(result.ic_a, ic, places=12)
        self.assertAlmostEqual(result.ib_a, ib, places=12)
        self.assertAlmostEqual(result.ve_v, ie * inp.re_ohm, places=9)
        self.assertAlmostEqual(
            result.vce_v,
            (inp.vcc_v - ic * inp.rc_ohm) - ie * inp.re_ohm,
            places=9,
        )

    def test_active_region_has_no_warning(self):
        result = calculate_dc_bias(default_input())
        self.assertEqual(result.region, "Active")
        self.assertEqual(result.warnings, ())

    def test_cutoff_warning_when_vth_at_or_below_vbe(self):
        result = calculate_dc_bias(default_input(r2_ohm=5_000.0))
        self.assertEqual(result.region, "Cutoff")
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("cutoff", result.warnings[0].lower())

    def test_saturation_warning_when_vce_below_threshold(self):
        result = calculate_dc_bias(default_input(rc_ohm=10_000.0))
        self.assertLess(result.vce_v, VCE_SATURATION_THRESHOLD_V)
        self.assertEqual(result.region, "Saturation")
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("saturation", result.warnings[0].lower())

    def test_rejects_non_positive_vcc(self):
        with self.assertRaises(BiasValidationError) as ctx:
            calculate_dc_bias(default_input(vcc_v=0.0))
        self.assertIn("vcc", ctx.exception.errors)

    def test_rejects_non_positive_resistors(self):
        for field in ("r1_ohm", "r2_ohm", "rc_ohm", "re_ohm"):
            for value in (0.0, -1.0):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(BiasValidationError) as ctx:
                        calculate_dc_bias(default_input(**{field: value}))
                    self.assertIn(field.removesuffix("_ohm"), ctx.exception.errors)

    def test_rejects_non_positive_beta(self):
        for value in (0.0, -5.0):
            with self.subTest(value=value):
                with self.assertRaises(BiasValidationError) as ctx:
                    calculate_dc_bias(default_input(beta=value))
                self.assertIn("beta", ctx.exception.errors)

    def test_rejects_non_finite_values(self):
        cases = (
            ("vcc_v", math.nan),
            ("r1_ohm", math.inf),
            ("beta", math.nan),
            ("vbe_v", math.inf),
        )
        for field, value in cases:
            with self.subTest(field=field):
                with self.assertRaises(BiasValidationError):
                    calculate_dc_bias(default_input(**{field: value}))

    def test_negative_vbe_is_not_rejected(self):
        result = calculate_dc_bias(default_input(vbe_v=-0.5))
        self.assertEqual(result.region, "Active")
        self.assertEqual(result.warnings, ())

    def test_vbe_above_vcc_is_not_rejected_but_warns(self):
        result = calculate_dc_bias(default_input(vbe_v=20.0))
        self.assertEqual(result.region, "Cutoff")
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("cutoff", result.warnings[0].lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
