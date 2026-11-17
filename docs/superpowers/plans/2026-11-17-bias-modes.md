# BJT Bias Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Fixed Bias and single-supply Emitter Bias to the Flask DC bias app while preserving the existing Voltage Divider result and tests, and verify through the browser.

**Architecture:** `dc_bias.py` keeps the existing divider API and adds two pure engineering dataclasses, validators, and calculators returning a common dictionary. `app.py` parses the mode, validates only mode-relevant fields, converts resistance units once, and dispatches to the matching calculator. `templates/index.html` renders mode-specific fields, schematic, and the common result dictionary.

**Tech Stack:** Python 3.10+, Flask 3.1.3, Jinja2, HTML/CSS, standard-library `unittest` (existing tests only).

**Spec:** `docs/superpowers/specs/2026-11-17-bias-modes-design.md`

## Global Constraints

- Preserve `BiasInput`, `BiasResult`, `calculate_dc_bias()`, `validate_dc_bias_inputs()`, and all 24 existing tests.
- Canonical units inside Python: V, A, Ω. Convert A to mA/µA only in the template.
- Convert all form resistances from Ω/kΩ to Ω once in `app.py`.
- Warning criteria: `IB <= 0` or `VCE <= 0.2 V`; warnings are not input errors.
- No VBE range restriction.
- No new `unittest` tests.
- Do not modify `electrical.py` or `test_electrical.py`.
- Do not commit or push until the user explicitly authorises it.
- Verify through the browser before writing PASS into `docs/validation.md`.

## Review Focus

1. **Divider regression.** The default Divider submission must still produce `IC = 1.230 mA` and `VCE = 8.052 V`; pinned by the existing `test_post_valid_ohm_values_returns_results` and the browser A1/A3 check.
2. **Mode-specific required fields.** Fixed must not require `R1`, `R2`, or `RE`; Emitter must not require `R1` or `R2`; missing required fields must still return 400.
3. **Unit conversion by mode.** `RB`, `R1`, `R2`, `RC`, and `RE` are converted exactly once; kΩ and Ω submissions must agree.
4. **Warning vs input error.** `IB <= 0` and `VCE <= 0.2 V` must render a warning with HTTP 200, while zero/negative resistors render input errors with HTTP 400.
5. **Common dictionary shape.** Every mode returns the same keys and canonical units, and the template never reads divider-only `vth_v`/`rth_ohm`.

---

## Task 1: Extend the Pure Engineering Module

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py` (existing tests only, no edits)

**Interfaces:**
- Consumes: existing `BiasValidationError`, `BiasInput`, `BiasResult`, `calculate_dc_bias()`.
- Produces:
  - `VCE_SATURATION_THRESHOLD_V = 0.2`
  - `FixedBiasInput(vcc_v, rb_ohm, rc_ohm, beta, vbe_v)`
  - `EmitterBiasInput(vcc_v, rb_ohm, rc_ohm, re_ohm, beta, vbe_v)`
  - `validate_fixed_bias_inputs(inputs) -> None`
  - `validate_emitter_bias_inputs(inputs) -> None`
  - `calculate_divider_bias(inputs: BiasInput) -> dict[str, object]`
  - `calculate_fixed_bias(inputs: FixedBiasInput) -> dict[str, object]`
  - `calculate_emitter_bias(inputs: EmitterBiasInput) -> dict[str, object]`

- [ ] **Step 1: Change the warning threshold and centralise classification**

Set `VCE_SATURATION_THRESHOLD_V = 0.2`. Add a private `_classify_operating_point(ib_a, vce_v)` helper:

```python
if ib_a <= 0:
    region = "Cutoff"
    warning = (
        "IB ≤ 0 A: the base-emitter junction is not forward biased. "
        "The transistor is in cutoff, so the forward-active approximation is not valid."
    )
elif vce_v <= VCE_SATURATION_THRESHOLD_V:
    region = "Saturation"
    warning = (
        f"VCE ≤ {VCE_SATURATION_THRESHOLD_V} V: the transistor is in saturation "
        "or at the edge of saturation. The forward-active approximation is not valid."
    )
else:
    region = "Active"
    warning = None
```

Return `(region, (warning,) if warning else ())`.

- [ ] **Step 2: Keep the divider calculation compatible**

Use `_classify_operating_point(ib_a, vce_v)` in `calculate_dc_bias()`. Do not change the divider equations or the `BiasResult` fields. Add `calculate_divider_bias()` that calls `calculate_dc_bias()` and maps its fields into the common dictionary.

- [ ] **Step 3: Add Fixed Bias input, validation, and calculation**

`validate_fixed_bias_inputs()` checks `vcc`, `rb`, `rc`, `beta`, and finite `vbe` with the existing message style. `calculate_fixed_bias()` uses:

```python
ib_a = (vcc_v - vbe_v) / rb_ohm
ic_a = beta * ib_a
ie_a = (beta + 1.0) * ib_a
ve_v = 0.0
vb_v = vbe_v
vc_v = vcc_v - ic_a * rc_ohm
vce_v = vc_v
```

- [ ] **Step 4: Add Emitter Bias input, validation, and calculation**

`validate_emitter_bias_inputs()` checks `vcc`, `rb`, `rc`, `re`, `beta`, and finite `vbe`. `calculate_emitter_bias()` uses:

```python
ib_a = (vcc_v - vbe_v) / (rb_ohm + (beta + 1.0) * re_ohm)
ic_a = beta * ib_a
ie_a = (beta + 1.0) * ib_a
ve_v = ie_a * re_ohm
vb_v = ve_v + vbe_v
vc_v = vcc_v - ic_a * rc_ohm
vce_v = vc_v - ve_v
```

- [ ] **Step 5: Return the common dictionary**

Every new calculator returns exactly:

```python
{
    "mode": "Divider" | "Fixed" | "Emitter",
    "vb_v": ...,
    "ve_v": ...,
    "vc_v": ...,
    "vce_v": ...,
    "ib_a": ...,
    "ic_a": ...,
    "ie_a": ...,
    "region": region,
    "warnings": warnings,
}
```

- [ ] **Step 6: Run the existing engineering tests**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`

Expected: all 11 existing engineering tests pass.

---

## Task 2: Add Mode Dispatch and Unit Conversion in Flask

**Files:**
- Modify: `app.py`

**Interfaces:**
- Consumes: the new dataclasses and calculators from Task 1.
- Produces: `GET /?mode=divider|fixed|emitter` and `POST /calculate` with a `mode` field; template context keys `values`, `errors`, `result`, `normalized`, `submitted_unit`, `mode`, `mode_label`.

- [ ] **Step 1: Add mode constants and defaults**

Add `MODE_DIVIDER = "divider"`, `MODE_FIXED = "fixed"`, `MODE_EMITTER = "emitter"`, labels, mode-to-fields maps, and `DEFAULT_FORM` entries for `mode` and `rb`. Keep the existing divider defaults unchanged.

- [ ] **Step 2: Parse only mode-relevant fields**

Change `parse_form()` to accept the resolved mode. Preserve raw values for all fields, but only parse and report missing/non-numeric errors for the selected mode's required fields. Missing `mode` defaults to `divider`.

- [ ] **Step 3: Convert units once per selected mode**

Use the existing `RESISTOR_UNIT_MULTIPLIERS`. Convert:
- Divider: `r1`, `r2`, `rc`, `re`
- Fixed: `rb`, `rc`
- Emitter: `rb`, `rc`, `re`

- [ ] **Step 4: Dispatch to the matching calculator**

Use one `if/elif/else` on the resolved mode to construct the matching dataclass and call `calculate_divider_bias()`, `calculate_fixed_bias()`, or `calculate_emitter_bias()`. Catch `BiasValidationError` into the existing `errors` dictionary. Invalid mode produces `errors["mode"]` and re-renders without a result.

- [ ] **Step 5: Build mode-specific normalized resistance strings**

Keep `format_resistance()`. Build `normalized` with `r1`/`r2`/`rc`/`re`, `rb`/`rc`, or `rb`/`rc`/`re` as appropriate.

- [ ] **Step 6: Preserve GET and POST compatibility**

`GET /` without a mode still renders the Divider form and values. `POST /calculate` without a mode still behaves as Divider, so the existing HTTP tests remain valid. Return HTTP 400 when `errors` is non-empty, otherwise 200.

---

## Task 3: Update the Template and Presentation

**Files:**
- Modify: `templates/index.html`
- Modify: `static/style.css`

**Interfaces:**
- Consumes: `mode`, `mode_label`, `values`, `errors`, `result` (common dict), `normalized`, `submitted_unit`.
- Produces: mode navigation, mode-specific form fields, static schematics, common result table.

- [ ] **Step 1: Add server-rendered mode navigation**

Render three links to `url_for('index', mode=...)`: `Voltage Divider`, `Fixed Bias`, `Emitter Bias`. Add a hidden `mode` input in the form. Show `errors.get('mode')` near the navigation when present.

- [ ] **Step 2: Render mode-specific fields**

Always render `VCC`, `RC`, `beta`, `VBE`, and `resistor_unit`. Render `R1`/`R2` only for Divider, `RB` for Fixed/Emitter, and `RE` for Divider/Emitter.

- [ ] **Step 3: Keep divider results and schematic unchanged**

Keep the existing divider SVG markup, IDs, title text, and result formatting exactly. Render the divider schematic only in Divider mode. Add simple static SVGs for Fixed and Emitter modes using the existing schematic CSS classes.

- [ ] **Step 4: Render the common result dictionary**

Use `result.vb_v`, `result.ve_v`, `result.vc_v`, `result.vce_v`, `result.ib_a`, `result.ic_a`, `result.ie_a`, `result.region`, and `result.warnings`. Keep the existing `%.3f` formatting and mA/µA conversion in the template. Show the mode in the result heading.

- [ ] **Step 5: Render mode-specific normalized values**

Divider shows `R1`, `R2`, `RC`, `RE`; Fixed shows `RB`, `RC`; Emitter shows `RB`, `RC`, `RE`.

- [ ] **Step 6: Add minimal CSS**

Add styles for the mode navigation and active mode link. Do not put equations or calculations in CSS.

---

## Task 4: Documentation Without Unverified PASS Claims

**Files:**
- Modify: `README.md`
- Modify: `docs/validation.md`

- [ ] **Step 1: Update README scope and equations**

Document the three modes, the common inputs, canonical units, unit conversion boundary, warning criteria (`IB <= 0` or `VCE <= 0.2 V`), and the unchanged Divider compatibility. Keep Thai prose and English commands/equations.

- [ ] **Step 2: Create the A1–A5 browser evidence table**

Add a table with the A1–A5 checks and columns for observed browser result and status. Do not write PASS until the browser run has actually been performed. Preserve the existing divider hand calculation as reference.

- [ ] **Step 3: Fill evidence only after the browser check**

After the browser run, record the actual observed values and statuses. If a check was not performed, write `Not run` instead of PASS.

---

## Task 5: Verification

**Files:**
- Verify only; modify code only if a real defect is found.

- [ ] **Step 1: Run all existing tests**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: `Ran 24 tests` and `OK`.

- [ ] **Step 2: Start the Flask server**

Run in the background: `.\.venv\Scripts\python.exe -m flask --app app run --debug`

- [ ] **Step 3: Verify A1–A5 through the browser**

Confirm:
- A1: `GET /` returns the form; Divider default still gives `IC 1.230 mA` and `VCE 8.052 V`.
- A2: Changing inputs changes the backend result; no hard-coded result in HTML.
- A3: Divider, Fixed, and Emitter values match the independent formulas.
- A4: Zero/negative resistor, zero beta, and non-numeric input show errors with no result table.
- A5: `IB <= 0` and `VCE <= 0.2 V` show warnings, not input errors.

- [ ] **Step 4: Record real observations**

Update `docs/validation.md` with the observed browser values and statuses. Do not claim PASS for anything not observed.

- [ ] **Step 5: Review the working tree**

Run `git status --short` and `git diff --stat`. Do not commit or push.

---

## Self-Review

- **Spec coverage:** Tasks 1–3 cover the common dict, three equations, mode validation, unit conversion, mode UI, and warning criteria. Task 4 covers documentation and unverified-status handling. Task 5 covers regression, browser verification, and Git hygiene.
- **Step scan:** Each step names the file, interface, and checkable result. No commit steps because the user forbids commits.
- **Type consistency:** The dict keys in Task 1 match the template reads in Task 3. `FixedBiasInput` and `EmitterBiasInput` fields match the app dispatch in Task 2.
- **Review Focus:** Divider regression is pinned by the existing test and A1/A3; mode-specific fields, unit conversion, warning separation, and dict shape are covered by Tasks 1–5.
