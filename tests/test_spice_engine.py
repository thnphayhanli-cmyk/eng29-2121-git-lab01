import math
import os
import re
import unittest
from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory

from spice_engine import (
    Circuit, Model, SineSource, SpiceError, SpiceUnavailable,
    _read_data, _run_batch, build_netlist, load_model, parse_raw,
)
from spice_plots import ac_display, transient_display


REFERENCE = Circuit(12, 100e3, 22e3, 2.2e3, 1e3, 10e3, 10e-6, 10e-6)
SOURCE = SineSource(0.01, 1000)
# Identifier for testing wiring only. It is not a BJT declaration or model.
WIRING_ONLY = Model("WIRING_ONLY", "not-a-model", "* Wiring check only")
NGSPICE = which(os.environ.get("NGSPICE_BIN") or "ngspice") or which("ngspice_con")


class TestSpiceEngine(unittest.TestCase):
    def test_netlist_uses_handout_topology_and_one_analysis(self):
        for analysis, directive in (("dc", ".op"), ("ac", ".ac "), ("tran", ".tran ")):
            with self.subTest(analysis=analysis):
                netlist = build_netlist(REFERENCE, WIRING_ONLY, analysis, SOURCE)
                directives = [line for line in netlist.splitlines() if line.startswith((".op", ".ac ", ".tran "))]
                self.assertEqual(len(directives), 1)
                self.assertTrue(directives[0].startswith(directive))
                for element in (
                    "R1 vcc b 100000", "R2 b 0 22000", "RC vcc c 2200", "RE e 0 1000",
                    "RL out 0 10000", "CIN in b", "COUT c out", "VSENSE c qc 0",
                    "Q1 qc b e WIRING_ONLY",
                ):
                    self.assertIn(f"\n{element}", netlist)
                if analysis == "tran":
                    self.assertIn("VIN in 0 SIN(0 0.01 1000)", netlist)

    def test_model_file_must_contain_the_requested_npn_declaration(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "model.lib"
            with self.assertRaisesRegex(SpiceUnavailable, "Cannot read"):
                load_model(str(path), "Requested")
            path.write_text("* No transistor model in this file\n.include not-loaded.lib\n", encoding="utf-8")
            with self.assertRaisesRegex(SpiceUnavailable, "one matching"):
                load_model(str(path), "Requested")

    def test_missing_executable_has_an_explicit_error(self):
        with self.assertRaisesRegex(SpiceUnavailable, "executable not found"):
            _run_batch("missing-lab04-ngspice-executable", "", 1)

    @unittest.skipUnless(NGSPICE, "ngspice is not available; set NGSPICE_BIN")
    def test_passive_probe_checks_real_ngspice_output_transport(self):
        # Reuse the generated analysis commands, but replace Q1 by a resistor.
        # This checks transport and units, not the BJT reference results.
        for analysis in ("dc", "ac", "tran"):
            with self.subTest(analysis=analysis):
                netlist = build_netlist(REFERENCE, WIRING_ONLY, analysis, SOURCE)
                netlist = netlist.replace("Q1 qc b e WIRING_ONLY", "RPROBE qc e 9k")
                log, raw = _run_batch(NGSPICE, netlist, 10)
                self.assertIn("result.raw", log)
                _, rows = parse_raw(raw, analysis)
                data = _read_data(rows, analysis, SOURCE)
                with self.assertRaises(SpiceError):
                    parse_raw(raw.rstrip().rsplit(None, 1)[0], analysis)
                if analysis == "dc":
                    self.assertAlmostEqual(data.ic_a, 12 / (2200 + 9000 + 1000), places=12)
                    self.assertAlmostEqual(data.vb_v, 12 * 22000 / 122000, places=10)
                elif analysis == "ac":
                    hz, magnitude, _, phase = ac_display(data)["sample"]
                    # Q1 is replaced and the base cannot drive the collector.
                    self.assertTrue(math.isclose(hz, 1000))
                    self.assertEqual(magnitude, 0)
                    self.assertIsNone(phase)
                else:
                    self.assertAlmostEqual(data[-1].time_s, 0.02)
                    self.assertAlmostEqual(transient_display(data, 1000)["vin_amplitude_mv"], 10, places=2)

    @unittest.skipUnless(NGSPICE, "ngspice is not available; set NGSPICE_BIN")
    def test_ac_ratio_and_phase_match_passive_rc_calculation(self):
        netlist = """Passive RC reference for AC parser and plot units
VIN in 0 AC 1
R1 in out 1000
C1 out 0 1u
.ac dec 40 0.1 100000000
.control
set filetype=ascii
run
write result.raw v(in) v(out)
quit
.endc
.end
"""
        _, raw = _run_batch(NGSPICE, netlist, 10)
        _, rows = parse_raw(raw, "ac")
        wrong_units, found = re.subn(r"(v\(out\)\s+)voltage\b", r"\1current", raw, count=1)
        self.assertEqual(found, 1)
        with self.assertRaisesRegex(SpiceError, "incomplete or invalid"):
            parse_raw(wrong_units, "ac")
        with self.assertRaisesRegex(SpiceError, "incomplete frequency sweep"):
            _read_data(rows[:40] + rows[41:], "ac", None)
        wrong_grid = rows[:40] + [(rows[40][0] * 1.01, *rows[40][1:])] + rows[41:]
        with self.assertRaisesRegex(SpiceError, "invalid AC scale"):
            _read_data(wrong_grid, "ac", None)
        display = ac_display(_read_data(rows, "ac", None))
        hz, magnitude, gain_db, phase_deg = display["sample"]
        omega_rc = 2 * math.pi * hz * 1e-3
        expected_magnitude = 1 / math.sqrt(1 + omega_rc ** 2)
        self.assertAlmostEqual(magnitude, expected_magnitude, places=9)
        self.assertAlmostEqual(gain_db, 20 * math.log10(expected_magnitude), places=8)
        self.assertAlmostEqual(phase_deg, -math.degrees(math.atan(omega_rc)), places=8)
        self.assertTrue(all(chart["series"][0]["segments"] for chart in display["charts"]))

    @unittest.skipUnless(NGSPICE, "ngspice is not available; set NGSPICE_BIN")
    def test_failed_ngspice_analysis_is_not_reported_as_success(self):
        netlist = build_netlist(REFERENCE, WIRING_ONLY, "dc")
        # Q1 refers to a deliberately absent model; the solver must reject it.
        with self.assertRaises(SpiceError) as context:
            _run_batch(NGSPICE, netlist, 10)
        self.assertIn("ngspice failed", str(context.exception))
        self.assertIn("wiring_only", context.exception.log.casefold())
