# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

ENG29 2121 (Engineering Electronics) students completing Lab 04, working from the course handout and its B1–B8 acceptance criteria. They must preserve the Lab 03 analytical DC bias behaviour while adding simulation evidence. The instructor or TA evaluates the result against the handout.

## Product Purpose

Calculate the DC operating point of a single-supply NPN common-emitter stage for three bias modes — Voltage Divider, Fixed Bias, and Emitter Bias — under the forward-active approximation, and show the result with units, validation errors, and out-of-region warnings. The app also demonstrates the separation between a Flask HTTP layer, pure Python engineering code, a Jinja template, static CSS, and automated tests. Lab 04 extends the same app with real ngspice DC, AC, and transient simulations for one CE voltage-divider reference circuit. Success means the Lab 04 handout and its B1–B8 acceptance criteria are met without regressing Lab 03.

## Positioning

A handout-faithful teaching instrument rather than a general circuit simulator: three named analytical bias modes stay on one page with auditable unit conversion and Lab 03 warning criteria, while Lab 04 adds real ngspice simulation for a single reference voltage-divider circuit. A neighbouring generic simulator could not truthfully reproduce the course-specific modes, validation rules, and acceptance trail.

## Operating Context

- Course handouts drive scope: Lab 02 (voltage divider), Lab 03 (three modes and warning criteria), Lab 04 (ngspice DC, AC, transient simulation).
- The app runs locally through the Flask development server (`http://127.0.0.1:5000/`) and is opened in a browser; opening `templates/index.html` directly does not work.
- Python 3.10 or newer (tested with 3.14); Flask only. No Node.js, database, or external service for the analytical app.
- Verification follows the handouts' browser acceptance cases (A1–A5 for Lab 03) plus independent hand calculations recorded in `docs/validation.md`.
- Tests run with the standard library: `python -m unittest discover -s tests -v`.
- Repository workflow: focused commits, no secrets, Lab 01 files `electrical.py` and `test_electrical.py` untouched.

## Capabilities and Constraints

- Three analytical modes share one result contract: `mode`, `vb_v`, `ve_v`, `vc_v`, `vce_v`, `ib_a`, `ic_a`, `ie_a`, `region`, `warnings`. Region strings are exactly `Active`, `Cutoff`, or `Saturation`.
- Frozen dataclasses: `BiasInput`, `BiasResult`, `FixedBiasInput`, `EmitterBiasInput`.
- Canonical engineering units inside the application are V, A, and Ω. The form accepts Ω or kΩ through an explicit selector; conversion happens once in `app.py`, and normalized values are echoed for audit.
- Validation: missing/blank or non-numeric fields, non-finite numbers, `VCC <= 0`, any resistance used by the selected mode `<= 0`, and `beta <= 0`. No VBE range restriction. Invalid submissions return HTTP 400 while still rendering the page.
- Warning criteria (Lab 03): `IB <= 0` → `Cutoff`; otherwise `VCE <= 0.2 V` → `Saturation`; otherwise `Active`. Warnings are not input errors and keep HTTP 200. Out-of-region equation output stays visible but is labelled as not a validated operating point.
- Analytical scope is DC bias only under constant β and constant VBE: no thermal effect, Early effect, AC gain, transient, or frequency response in the analytical calculator.
- Lab 04 adds real ngspice DC, AC, and transient simulations for one CE voltage-divider reference circuit only. No circuit editor and no features beyond the Lab 04 handout. All three Lab 03 analytical modes are preserved.
- Architecture: `dc_bias.py` is pure engineering code with no Flask, template, or form concepts; `app.py` owns HTTP parsing, unit conversion, errors, and status codes; `templates/index.html` holds no engineering equations; `static/style.css` is presentation only.
- Stack: Flask + Jinja templates + plain CSS; standard-library `unittest`; no JavaScript framework.
- Lab 04 requirements and B1–B8 are in `docs/Lab04_BJT_Amplifier_Simulator_2-2569.html`. ngspice 47 is available in the checked Windows environment. Lab 04 results show engine/model provenance, the run log, and the netlist.

## Brand Commitments

- Product name: **BJT DC Bias Simulator**.
- The shared header uses **Common-Emitter Lab · ENG29 2121** and labels the Lab 03 analytical and Lab 04 simulation workspaces separately.
- Voice and language, confirmed: English interface and engineering terms; Thai explanatory prose in README and lab notes.

## Evidence on Hand

- `docs/validation.md` — Lab 03 A1–A5 browser acceptance results, additional checks E1–E4, independent hand calculations, and the 24-test log.
- `README.md` — scope, equations, defaults, setup, and the AI-assisted / student-verified breakdown.
- `docs/superpowers/specs/` and `docs/superpowers/plans/` — approved Lab 02 and Lab 03 designs and implementation plans.
- `docs/design-note.md` and `docs/reflection.md` — historical Lab 02 material, explicitly superseded where they conflict with Lab 03 criteria.
- `tests/test_dc_bias.py` (11 engineering tests) and `tests/test_web.py` (13 HTTP tests).
- No instructor model was provided. Real CE runs use the documented onsemi 2N3904 substitute (`Q2n3904`), not an instructor-approved model. See `docs/validation.md` for its provenance and the measured B2–B6 evidence. The passive probe remains adapter-only evidence.

## Product Principles

1. Preserve before extending: Lab 03 modes, defaults, results, and tests must not regress while Lab 04 work lands.
2. Keep the engineering auditable: canonical units, one conversion at the boundary, normalized values echoed, and independent reference calculations before any PASS claim.
3. Separate pure engineering code from HTTP and presentation so each layer can be tested and changed on its own.
4. Treat out-of-region operation as a warning, never as an input error.
5. Stay inside the handout: one reference circuit for simulation, three analytical modes, no editor or unrequested features.
