import unittest
from electrical import analyze_dc


class TestElectrical(unittest.TestCase):

    def test_current(self):
        result = analyze_dc(12, 6)
        self.assertEqual(result["current_a"], 2)

    def test_power(self):
        result = analyze_dc(12, 6)
        self.assertEqual(result["power_w"], 24)

    def test_zero_resistance(self):
        with self.assertRaises(ValueError):
            analyze_dc(12, 0)

    def test_negative_resistance(self):
        with self.assertRaises(ValueError):
            analyze_dc(12, -6)


if __name__ == "__main__":
    unittest.main(verbosity=2)