"""Flask routes for the BJT common-emitter DC bias calculator.

This module owns HTTP concerns only: form parsing, unit conversion,
validation-error presentation, mode dispatch, and rendering. The engineering
equations live in dc_bias.py.
"""

from flask import Flask, render_template, request

from dc_bias import (
    BiasInput,
    BiasValidationError,
    EmitterBiasInput,
    FixedBiasInput,
    calculate_divider_bias,
    calculate_emitter_bias,
    calculate_fixed_bias,
)


app = Flask(__name__)

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
        except BiasValidationError as error:
            errors.update(error.errors)
        else:
            normalized = _normalized_resistances(mode, inputs)

    return (
        render_template(
            "index.html",
            values=values,
            errors=errors,
            result=result,
            normalized=normalized,
            submitted_unit=unit,
            mode=mode,
            mode_label=MODE_LABELS[mode],
            mode_options=list(MODE_LABELS.items()),
        ),
        400 if errors else 200,
    )
