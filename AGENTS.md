# AGENTS.md

## Project Scope

This repository contains the ENG29 2121 BJT common-emitter web app across Lab 02, Lab 03, and Lab 04.

The analytical calculator is deliberately narrow: three single-supply bias modes, forward-active approximation, DC operating point only.

Supported analytical modes:

- Voltage Divider Bias
- Fixed Bias
- Emitter Bias

Lab 04 adds real ngspice DC, AC, and transient simulation for exactly one CE voltage-divider reference circuit. That simulation surface is scoped by the Lab 04 handout; see "Lab 04 Simulation Scope" below.

Do not add DC load lines, FETs, further bias templates beyond these three, a circuit editor, a database, authentication, or a JavaScript framework. Do not add signal generators. Do not add Bode plots unless the Lab 04 handout requires them. AC analysis, transient analysis, and ngspice are permitted only inside the Lab 04 simulation scope.

## Architecture Rules

- `dc_bias.py` is pure engineering code. It must not import Flask, templates, HTTP, or form concepts.
- `app.py` owns HTTP concerns: reading `request.form`, parsing strings, converting units, collecting errors, choosing HTTP status, and rendering.
- `templates/index.html` displays values and messages. It must not contain the engineering equations.
- `static/style.css` contains presentation only.
- Keep canonical engineering units inside the application: V, A, Ω. Convert A to mA/µA only for display.
- Accept `Ω` or `kΩ` through the form's resistor-unit selector and convert once in `app.py`.

## Lab 04 Simulation Scope

Lab 04 is the only permitted exception to the analytical-only rule. It adds real ngspice DC, AC, and transient simulation for one CE voltage-divider reference circuit.

- Simulation output must come from an actual ngspice run. Never fabricate, hard-code, interpolate, or hand-wave a simulated value, waveform, or measurement.
- The Lab 04 handout and its B1–B8 acceptance criteria define the simulation surface. Do not add analyses, circuits, controls, or exports beyond them.
- The three Lab 02 / Lab 03 analytical modes, their result contract, validation, and warning criteria must not regress.
- Analytical results and simulated results must stay visibly distinct. Never present a simulated value as an analytical one, or vice versa.
- Keep simulation code out of `dc_bias.py`. Netlist generation, ngspice invocation, and result parsing belong in their own module; `app.py` keeps the HTTP concerns.
- Treat ngspice availability and version as environment facts to verify, not assumptions.
- If ngspice is unavailable, report that honestly instead of substituting a Python approximation.

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
- Simulation tests must run against real ngspice output. A test that claims to verify simulation must not mock or hard-code the ngspice result.
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
- Record Lab 04 simulation evidence separately from the Lab 03 analytical evidence, so historical Lab 03 PASS results stay auditable.
- The design and plan live under `docs/superpowers/`.
