import unittest

from app import app


DEFAULT_PAYLOAD = {
    "vcc": "12",
    "r1": "100000",
    "r2": "22000",
    "rc": "2200",
    "re": "1000",
    "beta": "100",
    "vbe": "0.70",
    "resistor_unit": "ohm",
}

SCHEMATIC_IDS = (
    "schematic-vcc",
    "schematic-r1",
    "schematic-r2",
    "schematic-rc",
    "schematic-re",
    "schematic-q1",
    "schematic-emitter-arrow",
    "schematic-ground-r2",
    "schematic-ground-re",
)


class TestWeb(unittest.TestCase):

    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_get_index_returns_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('name="vcc"', body)
        self.assertIn('name="r1"', body)
        self.assertIn('name="beta"', body)
        self.assertIn('name="vbe"', body)
        self.assertIn('name="resistor_unit"', body)
        self.assertIn('value="100000"', body)

    def test_get_index_shows_circuit_schematic(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('id="circuit-schematic"', body)
        self.assertIn("NPN common-emitter voltage-divider bias circuit", body)
        for marker in SCHEMATIC_IDS:
            self.assertIn(f'id="{marker}"', body)

    def test_post_result_keeps_circuit_schematic(self):
        response = self.client.post("/calculate", data=DEFAULT_PAYLOAD)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('id="circuit-schematic"', body)
        for marker in SCHEMATIC_IDS:
            self.assertIn(f'id="{marker}"', body)

    def test_post_valid_ohm_values_returns_results(self):
        response = self.client.post("/calculate", data=DEFAULT_PAYLOAD)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("DC Operating Point", body)
        self.assertIn("1.230", body)
        self.assertIn("8.052", body)
        self.assertIn("Active", body)

    def test_post_kohm_values_matches_ohm_operating_point(self):
        payload = dict(DEFAULT_PAYLOAD)
        payload.update(
            {
                "r1": "100",
                "r2": "22",
                "rc": "2.2",
                "re": "1",
                "resistor_unit": "kohm",
            }
        )
        response = self.client.post("/calculate", data=payload)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("1.230", body)
        self.assertIn("8.052", body)
        self.assertIn("100,000 Ω (100 kΩ)", body)

    def test_post_missing_value_returns_400_with_error(self):
        payload = dict(DEFAULT_PAYLOAD)
        payload["r1"] = ""
        response = self.client.post("/calculate", data=payload)
        self.assertEqual(response.status_code, 400)
        body = response.get_data(as_text=True)
        self.assertIn("Enter a value.", body)
        self.assertNotIn("DC Operating Point", body)

    def test_post_missing_value_preserves_other_values_and_unit(self):
        payload = {
            "vcc": "9",
            "r1": "",
            "r2": "33",
            "rc": "4.7",
            "re": "1.5",
            "beta": "250",
            "vbe": "0.65",
            "resistor_unit": "kohm",
        }
        response = self.client.post("/calculate", data=payload)
        self.assertEqual(response.status_code, 400)
        body = response.get_data(as_text=True)
        for value in ("9", "33", "4.7", "1.5", "250", "0.65"):
            self.assertIn(f'value="{value}"', body)
        self.assertIn('value="kohm" selected', body)

    def test_post_fractional_ohm_resistance_is_reported_exactly(self):
        payload = dict(DEFAULT_PAYLOAD)
        payload["re"] = "4.7"
        response = self.client.post("/calculate", data=payload)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("4.7 Ω (0.0047 kΩ)", body)
        self.assertNotIn("5 Ω (0.0047 kΩ)", body)

    def test_post_non_numeric_returns_400_with_error(self):
        payload = dict(DEFAULT_PAYLOAD)
        payload["beta"] = "abc"
        response = self.client.post("/calculate", data=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Enter a number.", response.get_data(as_text=True))

    def test_post_zero_resistor_returns_400_with_error(self):
        payload = dict(DEFAULT_PAYLOAD)
        payload["r1"] = "0"
        response = self.client.post("/calculate", data=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("greater than zero", response.get_data(as_text=True))

    def test_post_invalid_unit_returns_400(self):
        payload = dict(DEFAULT_PAYLOAD)
        payload["resistor_unit"] = "mohm"
        response = self.client.post("/calculate", data=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Choose Ω or kΩ.", response.get_data(as_text=True))

    def test_post_cutoff_case_shows_warning(self):
        payload = dict(DEFAULT_PAYLOAD)
        payload["r2"] = "5000"
        response = self.client.post("/calculate", data=payload)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Cutoff", body)
        self.assertIn("not valid", body)

    def test_post_saturation_case_shows_warning(self):
        payload = dict(DEFAULT_PAYLOAD)
        payload["rc"] = "10000"
        response = self.client.post("/calculate", data=payload)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Saturation", body)
        self.assertIn("not valid", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
