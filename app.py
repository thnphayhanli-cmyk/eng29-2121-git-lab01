"""Flask routes for the BJT common-emitter DC bias calculator.

This module owns HTTP concerns only: form parsing, unit conversion,
validation-error presentation, and rendering. The engineering equations
live in dc_bias.py.
"""

from flask import Flask, render_template, request

from dc_bias import BiasInput, BiasValidationError, calculate_dc_bias


app = Flask(__name__)

DEFAULT_FORM = {
    "vcc": "12",
    "r1": "100000",
    "r2": "22000",
    "rc": "2200",
    "re": "1000",
    "beta": "100",
    "vbe": "0.70",
    "resistor_unit": "ohm",
}

NUMERIC_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
RESISTOR_UNIT_MULTIPLIERS = {"ohm": 1.0, "kohm": 1_000.0}


def parse_form(form) -> tuple[dict[str, str], dict[str, float], dict[str, str]]:
    """Parse the form into raw values, numeric values, and field errors."""

    values = {field: form.get(field, "").strip() for field in NUMERIC_FIELDS}
    values["resistor_unit"] = form.get("resistor_unit", "ohm")

    parsed = {}
    errors = {}
    for field in NUMERIC_FIELDS:
        text = values[field]
        if not text:
            errors[field] = "Enter a value."
            continue
        try:
            parsed[field] = float(text)
        except ValueError:
            errors[field] = "Enter a number."

    return values, parsed, errors


def format_resistance(value_ohm: float) -> str:
    """Render a resistance in canonical ohms and its kΩ equivalent.

    Six significant digits keep fractional values such as 4.7 Ω exact, so the
    audit line never reports a resistance other than the one that was used.
    """

    return f"{value_ohm:,.6g} Ω ({value_ohm / 1000:g} kΩ)"


@app.get("/")
def index():
    return render_template(
        "index.html",
        values=DEFAULT_FORM,
        errors={},
        result=None,
        normalized=None,
        submitted_unit="ohm",
    )


@app.post("/calculate")
def calculate():
    values, parsed, errors = parse_form(request.form)

    unit = values["resistor_unit"]
    if unit not in RESISTOR_UNIT_MULTIPLIERS:
        errors["resistor_unit"] = "Choose Ω or kΩ."
        unit = "ohm"

    result = None
    normalized = None

    if not errors:
        factor = RESISTOR_UNIT_MULTIPLIERS[unit]
        inputs = BiasInput(
            vcc_v=parsed["vcc"],
            r1_ohm=parsed["r1"] * factor,
            r2_ohm=parsed["r2"] * factor,
            rc_ohm=parsed["rc"] * factor,
            re_ohm=parsed["re"] * factor,
            beta=parsed["beta"],
            vbe_v=parsed["vbe"],
        )

        try:
            result = calculate_dc_bias(inputs)
        except BiasValidationError as error:
            errors.update(error.errors)
        else:
            normalized = {
                "r1": format_resistance(inputs.r1_ohm),
                "r2": format_resistance(inputs.r2_ohm),
                "rc": format_resistance(inputs.rc_ohm),
                "re": format_resistance(inputs.re_ohm),
            }

    return (
        render_template(
            "index.html",
            values=values,
            errors=errors,
            result=result,
            normalized=normalized,
            submitted_unit=unit,
        ),
        400 if errors else 200,
    )
