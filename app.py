"""Flask routes for analytical DC bias and the Lab 04 CE reference simulator.

This module owns HTTP concerns only: form parsing, unit conversion,
validation-error presentation, mode dispatch, and rendering. The engineering
equations live in dc_bias.py.
"""

from math import isfinite
from os import environ

from flask import Flask, render_template, request

from dc_bias import (
    BiasCalculationError,
    BiasInput,
    BiasValidationError,
    EmitterBiasInput,
    FixedBiasInput,
    calculate_divider_bias,
    calculate_emitter_bias,
    calculate_fixed_bias,
)
from spice_engine import (
    TRANSIENT_FREQUENCY_HZ,
    Circuit,
    SineSource,
    SpiceError,
    SpiceUnavailable,
    simulate,
)
from spice_plots import ac_display, transient_display


app = Flask(__name__)
app.config.from_mapping(
    NGSPICE_BIN=environ.get("NGSPICE_BIN", ""),
    BJT_MODEL_FILE=environ.get("BJT_MODEL_FILE", ""),
    BJT_MODEL_NAME=environ.get("BJT_MODEL_NAME", ""),
)

MODE_DIVIDER = "divider"
MODE_FIXED = "fixed"
MODE_EMITTER = "emitter"

MODE_LABELS = {
    MODE_DIVIDER: "Voltage Divider",
    MODE_FIXED: "Fixed Bias",
    MODE_EMITTER: "Emitter Bias",
}

MODE_REQUIRED_FIELDS = {
    MODE_DIVIDER: ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
    MODE_FIXED: ("vcc", "rb", "rc", "beta", "vbe"),
    MODE_EMITTER: ("vcc", "rb", "rc", "re", "beta", "vbe"),
}

MODE_RESISTOR_FIELDS = {
    MODE_DIVIDER: ("r1", "r2", "rc", "re"),
    MODE_FIXED: ("rb", "rc"),
    MODE_EMITTER: ("rb", "rc", "re"),
}

NUMERIC_FORM_FIELDS = ("vcc", "r1", "r2", "rb", "rc", "re", "beta", "vbe")

DEFAULT_FORM = {
    "mode": MODE_DIVIDER,
    "vcc": "12",
    "r1": "100000",
    "r2": "22000",
    "rb": "1000000",
    "rc": "2200",
    "re": "1000",
    "beta": "100",
    "vbe": "0.70",
    "resistor_unit": "ohm",
}

RESISTOR_UNIT_MULTIPLIERS = {"ohm": 1.0, "kohm": 1_000.0}

SPICE_ANALYSES = {"dc": "DC operating point", "ac": "AC frequency response", "tran": "Transient response"}
SPICE_FIELDS = {
    "vcc": ("VCC — supply (V)", "12", 1.0),
    "r1": ("R1 — upper divider (Ω/kΩ)", "100", None),
    "r2": ("R2 — lower divider (Ω/kΩ)", "22", None),
    "rc": ("RC — collector (Ω/kΩ)", "2.2", None),
    "re": ("RE — emitter (Ω/kΩ)", "1", None),
    "rl": ("RL — load (Ω/kΩ)", "10", None),
    "cin": ("Cin — input coupling (µF)", "10", 1e-6),
    "cout": ("Cout — output coupling (µF)", "10", 1e-6),
}
SOURCE_FIELDS = {
    "amplitude": ("Amplitude (mV peak)", "10", 1e-3),
    "frequency": ("Frequency (Hz)", "1000", 1.0),
}
DC_QUANTITIES = (
    ("VB", "vb_v", "V", 1), ("VE", "ve_v", "V", 1), ("VC", "vc_v", "V", 1),
    ("VCE", "vce_v", "V", 1), ("IC", "ic_a", "mA", 1e3),
)


def parse_mode(raw_mode: str | None) -> tuple[str | None, str | None]:
    """Resolve the submitted mode without guessing an unknown one.

    A missing mode keeps Lab 02 compatibility and means Voltage Divider.
    A present but unknown mode is an error and must not fall back to Divider.
    """

    if raw_mode is None or not raw_mode.strip():
        return MODE_DIVIDER, None

    candidate = raw_mode.strip()
    if candidate in MODE_LABELS:
        return candidate, None

    return (
        None,
        f"Unknown bias mode '{candidate}'. "
        "Choose Voltage Divider, Fixed Bias, or Emitter Bias.",
    )


def parse_form(form, mode: str) -> tuple[dict[str, str], dict[str, float], dict[str, str]]:
    """Parse the form into raw values, numeric values, and field errors.

    Only fields required by the selected mode are parsed. Raw values for the
    other fields are preserved so a user does not lose them while switching
    between modes.
    """

    values = {field: form.get(field, "").strip() for field in NUMERIC_FORM_FIELDS}
    values["mode"] = mode
    values["resistor_unit"] = form.get("resistor_unit", "ohm")

    parsed = {}
    errors = {}
    for field in MODE_REQUIRED_FIELDS[mode]:
        text = values[field]
        if not text:
            errors[field] = "Enter a value."
            continue
        try:
            parsed[field] = float(text)
        except ValueError:
            errors[field] = "Enter a number."

    return values, parsed, errors


def _format_number(value: float) -> str:
    """Format a resistance without scientific notation."""

    value = float(value)
    if value.is_integer():
        return f"{int(value):,}"
    return f"{value:,.6f}".rstrip("0").rstrip(".")


def format_resistance(value_ohm: float) -> str:
    """Render a resistance in canonical ohms and its kΩ equivalent.

    Six fractional digits keep values such as 4.7 Ω exact, so the audit line
    never reports a resistance other than the one that was used.
    """

    return f"{_format_number(value_ohm)} Ω ({_format_number(value_ohm / 1000)} kΩ)"


def _normalized_resistances(mode: str, inputs) -> dict[str, str]:
    normalized = {}
    for field in MODE_RESISTOR_FIELDS[mode]:
        normalized[field] = format_resistance(getattr(inputs, f"{field}_ohm"))
    return normalized


@app.get("/")
def index():
    mode, mode_error = parse_mode(request.args.get("mode"))
    errors = {}
    if mode_error:
        errors["mode"] = mode_error

    values = dict(DEFAULT_FORM)
    if mode:
        values["mode"] = mode

    response = render_template(
        "index.html",
        values=values,
        errors=errors,
        result=None,
        normalized=None,
        submitted_unit="ohm",
        mode=mode,
        mode_label=MODE_LABELS.get(mode),
        mode_options=list(MODE_LABELS.items()),
    )
    return response, 400 if errors else 200


@app.post("/calculate")
def calculate():
    mode, mode_error = parse_mode(request.form.get("mode"))

    if mode is None:
        values = dict(DEFAULT_FORM)
        values["resistor_unit"] = request.form.get("resistor_unit", "ohm")
        return (
            render_template(
                "index.html",
                values=values,
                errors={"mode": mode_error},
                result=None,
                normalized=None,
                submitted_unit="ohm",
                mode=None,
                mode_label=None,
                mode_options=list(MODE_LABELS.items()),
            ),
            400,
        )

    values, parsed, errors = parse_form(request.form, mode)

    unit = values["resistor_unit"]
    if unit not in RESISTOR_UNIT_MULTIPLIERS:
        errors["resistor_unit"] = "Choose Ω or kΩ."
        unit = "ohm"

    result = None
    normalized = None
    calculation_error = None

    if not errors:
        factor = RESISTOR_UNIT_MULTIPLIERS[unit]

        try:
            if mode == MODE_DIVIDER:
                inputs = BiasInput(
                    vcc_v=parsed["vcc"],
                    r1_ohm=parsed["r1"] * factor,
                    r2_ohm=parsed["r2"] * factor,
                    rc_ohm=parsed["rc"] * factor,
                    re_ohm=parsed["re"] * factor,
                    beta=parsed["beta"],
                    vbe_v=parsed["vbe"],
                )
                result = calculate_divider_bias(inputs)
            elif mode == MODE_FIXED:
                inputs = FixedBiasInput(
                    vcc_v=parsed["vcc"],
                    rb_ohm=parsed["rb"] * factor,
                    rc_ohm=parsed["rc"] * factor,
                    beta=parsed["beta"],
                    vbe_v=parsed["vbe"],
                )
                result = calculate_fixed_bias(inputs)
            else:
                inputs = EmitterBiasInput(
                    vcc_v=parsed["vcc"],
                    rb_ohm=parsed["rb"] * factor,
                    rc_ohm=parsed["rc"] * factor,
                    re_ohm=parsed["re"] * factor,
                    beta=parsed["beta"],
                    vbe_v=parsed["vbe"],
                )
                result = calculate_emitter_bias(inputs)
            if not all(isfinite(result[key] * scale) for key, scale in (
                ("ib_a", 1e6), ("ic_a", 1e3), ("ie_a", 1e3),
            )):
                raise BiasCalculationError("Current exceeded the display range. Use less extreme values.")
        except BiasValidationError as error:
            errors.update(error.errors)
        except BiasCalculationError as error:
            calculation_error = str(error)
            result = None
        else:
            normalized = _normalized_resistances(mode, inputs)

    return (
        render_template(
            "index.html",
            values=values,
            errors=errors,
            result=result,
            calculation_error=calculation_error,
            normalized=normalized,
            submitted_unit=unit,
            mode=mode,
            mode_label=MODE_LABELS[mode],
            mode_options=list(MODE_LABELS.items()),
        ),
        400 if errors else 422 if calculation_error else 200,
    )


def _parse_spice_inputs(form):
    numeric = SPICE_FIELDS | SOURCE_FIELDS
    values = {field: form.get(field, "").strip() for field in numeric}
    values["analysis"] = form.get("analysis", "")
    values["resistor_unit"] = form.get("resistor_unit", "")
    errors = {}
    analysis = values["analysis"]
    if analysis not in SPICE_ANALYSES:
        errors["analysis"] = "Choose DC, AC, or Transient."
    resistor_factor = RESISTOR_UNIT_MULTIPLIERS.get(values["resistor_unit"])
    if resistor_factor is None:
        errors["resistor_unit"] = "Choose Ω or kΩ."

    parsed = {}
    required = numeric if analysis == "tran" else SPICE_FIELDS
    for field, (label, _, factor) in required.items():
        if not values[field]:
            errors[field] = f"{label}: enter a value."
            continue
        try:
            value = float(values[field])
        except ValueError:
            errors[field] = f"{label}: enter a number."
            continue
        factor = factor if factor is not None else resistor_factor
        scaled = value * (factor if factor is not None else 1)
        if not isfinite(scaled) or scaled <= 0:
            errors[field] = f"{label}: enter a finite value greater than zero."
        elif field == "frequency" and not TRANSIENT_FREQUENCY_HZ[0] <= scaled <= TRANSIENT_FREQUENCY_HZ[1]:
            low, high = TRANSIENT_FREQUENCY_HZ
            errors[field] = f"Frequency must be between {low:,} and {high:,} Hz."
        else:
            parsed[field] = scaled
    return values, parsed, errors


def _analytical_reference(circuit):
    """Compare only where the independent Lab 03 approximation is applicable."""
    try:
        result = calculate_divider_bias(BiasInput(
            vcc_v=circuit.vcc_v, r1_ohm=circuit.r1_ohm, r2_ohm=circuit.r2_ohm,
            rc_ohm=circuit.rc_ohm, re_ohm=circuit.re_ohm, beta=100, vbe_v=0.70,
        ))
    except ArithmeticError:
        return None
    if result["region"] != "Active" or not all(
        isfinite(result[key] * multiplier) for _, key, _, multiplier in DC_QUANTITIES
    ):
        return None
    return result


@app.route("/simulate", methods=["GET", "POST"])
def simulate_ce():
    values = {field: info[1] for field, info in (SPICE_FIELDS | SOURCE_FIELDS).items()}
    values.update(analysis="dc", resistor_unit="kohm")
    errors = {}
    simulation = display = run_error = None
    status = 200
    if request.method == "POST":
        values, parsed, errors = _parse_spice_inputs(request.form)
        if errors:
            status = 400
        else:
            analysis = values["analysis"]
            circuit = Circuit(
                vcc_v=parsed["vcc"], r1_ohm=parsed["r1"], r2_ohm=parsed["r2"],
                rc_ohm=parsed["rc"], re_ohm=parsed["re"], rl_ohm=parsed["rl"],
                cin_f=parsed["cin"], cout_f=parsed["cout"],
            )
            source = SineSource(parsed["amplitude"], parsed["frequency"]) if analysis == "tran" else None
            try:
                run = simulate(
                    circuit, analysis, source,
                    executable=app.config["NGSPICE_BIN"], model_file=app.config["BJT_MODEL_FILE"],
                    model_name=app.config["BJT_MODEL_NAME"],
                )
                if analysis == "dc":
                    reference = _analytical_reference(circuit)
                    rows = [
                        (label, getattr(run.data, key) * factor, unit, reference[key] * factor if reference else None)
                        for label, key, unit, factor in DC_QUANTITIES
                    ]
                    if any(not isfinite(value) for _, value, _, _ in rows):
                        raise SpiceError("ngspice values are outside the display range.", run.log)
                    display = {"rows": rows, "has_reference": reference is not None}
                elif analysis == "ac":
                    display = ac_display(run.data)
                else:
                    display = transient_display(run.data, source.frequency_hz)
                    display["frequency_hz"] = source.frequency_hz
                    display["amplitude_mv"] = source.amplitude_v * 1e3
                simulation = run
            except SpiceUnavailable as error:
                run_error, status = error, 503
            except SpiceError as error:
                run_error, status = error, 502

    return render_template(
        "simulate.html", values=values, errors=errors, simulation=simulation, display=display,
        run_error=run_error, analyses=SPICE_ANALYSES, frequency_range=TRANSIENT_FREQUENCY_HZ,
        model_name=app.config["BJT_MODEL_NAME"] if app.config["BJT_MODEL_FILE"] else "",
    ), status
