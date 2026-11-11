# Design Note — BJT Common-Emitter DC Bias Web App

## Intent

Lab 02 requires a real multi-file Flask application that computes the DC operating point of an NPN common-emitter amplifier with voltage-divider bias. The app demonstrates the separation between the browser form, Flask routing, pure Python engineering logic, Jinja templates, static CSS, and automated tests.

## Architecture

```text
Browser form
    ↓ POST /calculate
app.py: parse form, validate presence/numerics, convert kΩ→Ω, collect errors
    ↓
dc_bias.py: BiasInput → forward-active equations → BiasResult + region warning
    ↓
templates/index.html: render results or field errors
```

- `dc_bias.py` is pure Python and uses SI units (V, A, Ω). It has no Flask or HTML knowledge.
- `app.py` owns HTTP parsing, unit conversion, error presentation, and status codes.
- `templates/index.html` and `static/style.css` handle presentation only.
- `tests/test_dc_bias.py` verifies engineering math, validation, and region classification.
- `tests/test_web.py` verifies the Flask routes, unit conversion, errors, and warnings.

## Units

The canonical engineering unit is ohms (Ω). The form accepts Ω or kΩ through an explicit selector and converts all four resistances to Ω before calling `dc_bias.py`. Results are displayed in V, mA, and µA. The normalized Ω values are echoed on the results page so the conversion is auditable.

## Validation

The app follows the handout's rules: missing/non-numeric input, non-finite numeric input, `VCC ≤ 0`, any resistance `≤ 0`, and `β ≤ 0`. No additional VBE range restriction is applied. Invalid submissions return HTTP 400 while still rendering the page.

## Region Warnings

- `VTH ≤ VBE` → Cutoff warning.
- Otherwise `VCE < 0.3 V` → Saturation warning.
- Otherwise → Active.

Outside the active region, the forward-active equation output remains visible but is explicitly labeled as invalid. No separate cutoff or saturation solver is implemented.

## Full Design

See [`docs/superpowers/specs/2026-11-11-bjt-dc-bias-design.md`](superpowers/specs/2026-11-11-bjt-dc-bias-design.md).
