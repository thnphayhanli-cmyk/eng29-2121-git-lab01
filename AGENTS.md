# AGENTS.md

## Project Scope

This repository contains the ENG29 2121 Lab 02 / Lab 03 BJT common-emitter DC bias web app. The scope is deliberately narrow: three single-supply bias modes, forward-active approximation, DC operating point only.

Supported modes:

- Voltage Divider Bias
- Fixed Bias
- Emitter Bias

Do not add AC analysis, transient analysis, Bode plots, signal generators, SPICE/ngspice, DC load lines, FETs, further bias templates beyond these three, a circuit editor, a database, authentication, or a JavaScript framework.

## Architecture Rules

- `dc_bias.py` is pure engineering code. It must not import Flask, templates, HTTP, or form concepts.
- `app.py` owns HTTP concerns: reading `request.form`, parsing strings, converting units, collecting errors, choosing HTTP status, and rendering.
- `templates/index.html` displays values and messages. It must not contain the engineering equations.
- `static/style.css` contains presentation only.
- Keep canonical engineering units inside the application: V, A, Ω. Convert A to mA/µA only for display.
- Accept `Ω` or `kΩ` through the form's resistor-unit selector and convert once in `app.py`.

## Naming and Types

- Use unit suffixes in engineering names: `_v`, `_a`, `_ohm`.
- Keep `BiasInput`, `BiasResult`, `FixedBiasInput`, and `EmitterBiasInput` as frozen dataclasses.
- Validation errors use field keys `vcc`, `r1`, `r2`, `rb`, `rc`, `re`, `beta`, `vbe`.
- Region strings are exactly `Active`, `Cutoff`, or `Saturation`.
- Every mode returns the common result dictionary with keys `mode`, `vb_v`, `ve_v`, `vc_v`, `vce_v`, `ib_a`, `ic_a`, `ie_a`, `region`, and `warnings`.

## Validation

Required validation follows the Lab 02 / Lab 03 handouts:

- Missing/blank or non-numeric fields.
- Non-finite numeric input.
- `VCC <= 0`.
- Any resistance used by the selected mode `<= 0`.
- `beta <= 0`.

Do not add a VBE range restriction. Do not require the circuit to be in the active region. Out-of-region operation is a warning, not an input error.

The Lab 03 warning criteria are:

- `IB <= 0` → `Cutoff`
- Otherwise `VCE <= 0.2 V` → `Saturation`
- Otherwise → `Active`

## Testing

- Use the standard library `unittest`.
- Engineering tests live in `tests/test_dc_bias.py`.
- HTTP tests use Flask's test client and live in `tests/test_web.py`.
- Run before every commit:

```bash
python -m unittest discover -s tests -v
```

- On Windows without activation:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Git and Repository Hygiene

- Do not commit `.venv/`, `.env`, secrets, API keys, or credentials.
- Keep Lab 01 files `electrical.py` and `test_electrical.py` untouched.
- Review `git status` and `git diff --staged` before committing.
- Keep commits focused on one task or concern.

## Documentation

- README prose is Thai; commands and equations remain in English.
- Update `docs/validation.md` when reference values or tests change.
- The design and plan live under `docs/superpowers/`.
