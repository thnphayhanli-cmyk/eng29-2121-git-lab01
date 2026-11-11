# BJT Common-Emitter DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal multi-file Flask web app that computes the voltage-divider BJT common-emitter DC operating point, validates inputs, warns outside forward-active, and is verified by an independent calculation and automated tests.

**Architecture:** Server-rendered single-page Flask application. `dc_bias.py` is a pure Python engineering module that works in SI units (V, A, Ω); `app.py` owns HTTP parsing, kΩ→Ω conversion, validation-error presentation, and rendering; the Jinja template and CSS handle presentation only. Standard-library `unittest` covers engineering and HTTP behavior.

**Tech Stack:** Python 3.14 (via `py` on this machine), Flask 3.1.3, Jinja2, HTML/CSS, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-11-bjt-dc-bias-design.md`

## Global Constraints

- Scope is only the NPN common-emitter voltage-divider DC bias under the forward-active approximation. No AC, transient, Bode, signal generator, SPICE, load line, FET, circuit editor, database, auth, or extra bias templates.
- Canonical resistance unit is **Ω**. The form accepts `Ω` or `kΩ` through an explicit unit selector; convert once in `app.py` before calling the engineering module.
- Validation: missing/blank/non-numeric, non-finite numeric input, `VCC ≤ 0`, any resistor `≤ 0`, `β ≤ 0`. **No VBE range restriction.** No active-region requirement.
- Region: `VTH ≤ VBE` → Cutoff; otherwise `VCE < 0.3 V` → Saturation; otherwise Active. Cutoff takes precedence.
- Out-of-region equation output stays visible but must be labeled as invalid forward-active output, never as a validated operating point.
- Lab 01 files `electrical.py` and `test_electrical.py` must remain byte-for-byte untouched.
- Do not commit `.venv/`, `.env`, secrets, or credentials.
- Invalid form submissions return HTTP 400 while still rendering the page. Valid submissions return HTTP 200.
- Tests run from the repository root with `python -m unittest discover -s tests -v` (or `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` on Windows).
- README prose is Thai; commands and equations remain in English.
- Localhost only: `http://127.0.0.1:5000/`.

## Review Focus

These are the input classes most likely to bite a user. Each line is pinned to a test in the task that owns the code.

1. **Wrong resistor unit selected.** A user enters `100` with `kΩ` selected (or `100000` with `Ω`) and expects the correct operating point; the normalized Ω line must make the conversion auditable. Pinned by `test_post_kohm_values_matches_ohm_operating_point` and `test_post_invalid_unit_returns_400`.
2. **Blank or non-numeric field.** The page must re-render with a readable message, preserve other values, and never return a 500. Pinned by `test_post_missing_value_returns_400_with_error` and `test_post_non_numeric_returns_400_with_error`.
3. **Handout-legal but extreme VBE.** Negative VBE or VBE above VCC must not trigger a new validation error; the app must calculate or emit the cutoff warning instead of crashing. Pinned by `test_negative_vbe_is_not_rejected` and `test_vbe_above_vcc_is_not_rejected_but_warns`.
4. **Cutoff or saturation case.** Equation output may be negative or unphysical, but the page must show a clear warning and must not call it a valid operating point. Pinned by `test_cutoff_warning_when_vth_at_or_below_vbe`, `test_saturation_warning_when_vce_below_threshold`, `test_post_cutoff_case_shows_warning`, and `test_post_saturation_case_shows_warning`.
5. **Opening the template directly.** A user might double-click `templates/index.html` and expect the app; the README must state that Flask must serve it. Pinned by the README verification step and `test_get_index_returns_form` (the form is served by Flask at `/`).

---

## Task 1: Pure DC Bias Engineering Module

**Files:**
- Create: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `BiasInput` frozen dataclass with fields `vcc_v`, `r1_ohm`, `r2_ohm`, `rc_ohm`, `re_ohm`, `beta`, `vbe_v` (all `float`).
  - `BiasResult` frozen dataclass with fields `vth_v`, `rth_ohm`, `ib_a`, `ic_a`, `ie_a`, `ve_v`, `vb_v`, `vc_v`, `vce_v` (`float`), `region` (`str`), `warnings` (`tuple[str, ...]`).
  - `BiasValidationError(ValueError)` with an `errors: dict[str, str]` attribute keyed by `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`.
  - `VCE_SATURATION_THRESHOLD_V = 0.3`.
  - `calculate_dc_bias(inputs: BiasInput) -> BiasResult`.
  - `validate_dc_bias_inputs(inputs: BiasInput) -> None` (raises `BiasValidationError`).

- [ ] **Step 1: Write the failing engineering tests**

Create `tests/test_dc_bias.py` with `unittest`. Use this shared fixture:

```python
def default_input(**overrides):
    values = dict(
        vcc_v=12.0,
        r1_ohm=100_000.0,
        r2_ohm=22_000.0,
        rc_ohm=2_200.0,
        re_ohm=1_000.0,
        beta=100.0,
        vbe_v=0.70,
    )
    values.update(overrides)
    return BiasInput(**values)
```

Include these test methods and assertions:

1. `test_default_operating_point_matches_hand_calculation` — compute the default result and assert:

```python
self.assertAlmostEqual(result.vth_v, 2.163934426, places=6)
self.assertAlmostEqual(result.rth_ohm, 18_032.786885, places=3)
self.assertAlmostEqual(result.ib_a, 12.298581463e-6, places=12)
self.assertAlmostEqual(result.ic_a, 1.229858146e-3, places=9)
self.assertAlmostEqual(result.ie_a, 1.242156728e-3, places=9)
self.assertAlmostEqual(result.ve_v, 1.242156728, places=6)
self.assertAlmostEqual(result.vb_v, 1.942156728, places=6)
self.assertAlmostEqual(result.vc_v, 9.294312078, places=6)
self.assertAlmostEqual(result.vce_v, 8.052155351, places=6)
self.assertEqual(result.region, "Active")
self.assertEqual(result.warnings, ())
```

2. `test_independent_ie_formula_matches_module` — calculate the expected values with this independently rearranged expression and compare:

```python
vth = inp.vcc_v * inp.r2_ohm / (inp.r1_ohm + inp.r2_ohm)
rth = inp.r1_ohm * inp.r2_ohm / (inp.r1_ohm + inp.r2_ohm)
ie = (vth - inp.vbe_v) / (rth / (inp.beta + 1) + inp.re_ohm)
ic = inp.beta / (inp.beta + 1) * ie
ib = ie / (inp.beta + 1)
```

Assert `result.ie_a`, `result.ic_a`, and `result.ib_a` match the independent values with `places=12`; assert `result.ve_v` and `result.vce_v` match with `places=9`.

3. `test_active_region_has_no_warning` — default input; `region == "Active"` and `warnings == ()`.
4. `test_cutoff_warning_when_vth_at_or_below_vbe` — `default_input(r2_ohm=5_000.0)`; `region == "Cutoff"`; exactly one warning; `"cutoff"` in `warnings[0].lower()`.
5. `test_saturation_warning_when_vce_below_threshold` — `default_input(rc_ohm=10_000.0)`; `result.vce_v < VCE_SATURATION_THRESHOLD_V`; `region == "Saturation"`; `"saturation"` in `warnings[0].lower()`.
6. `test_rejects_non_positive_vcc` — `default_input(vcc_v=0.0)` raises `BiasValidationError`; `"vcc"` in `error.errors`.
7. `test_rejects_non_positive_resistors` — use `subTest` over `r1_ohm`, `r2_ohm`, `rc_ohm`, `re_ohm` and values `0.0`, `-1.0`; each raises; the corresponding key (`r1`, `r2`, `rc`, `re`) is in `error.errors`.
8. `test_rejects_non_positive_beta` — `beta=0.0` and `beta=-5.0`; each raises; `"beta"` in `error.errors`.
9. `test_rejects_non_finite_values` — use `subTest` for `vcc_v=math.nan`, `r1_ohm=math.inf`, `beta=math.nan`, `vbe_v=math.inf`; each raises `BiasValidationError`.
10. `test_negative_vbe_is_not_rejected` — `default_input(vbe_v=-0.5)` returns a result and has `region == "Active"` (no new VBE restriction).
11. `test_vbe_above_vcc_is_not_rejected_but_warns` — `default_input(vbe_v=20.0)` returns a result with `region == "Cutoff"` and a warning; no `BiasValidationError`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `py -m unittest discover -s tests -p "test_dc_bias.py" -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'dc_bias'`.

- [ ] **Step 3: Implement `dc_bias.py`**

Implement the interfaces above. Use `math.isfinite` and raise `BiasValidationError` with field-keyed messages:

- `vcc`: `"VCC must be a finite number."` or `"VCC must be greater than zero."`
- `r1`/`r2`/`rc`/`re`: `"R1 must be a finite number."` or `"R1 must be greater than zero."` (same pattern for each label)
- `beta`: `"Beta must be a finite number."` or `"Beta must be greater than zero."`
- `vbe`: `"VBE must be a finite number."` only

Do not add a VBE range check. Compute with the handout equations in this order:

```python
vth_v = vcc_v * r2_ohm / (r1_ohm + r2_ohm)
rth_ohm = r1_ohm * r2_ohm / (r1_ohm + r2_ohm)
ib_a = (vth_v - vbe_v) / (rth_ohm + (beta + 1.0) * re_ohm)
ic_a = beta * ib_a
ie_a = (beta + 1.0) * ib_a
ve_v = ie_a * re_ohm
vb_v = ve_v + vbe_v
vc_v = vcc_v - ic_a * rc_ohm
vce_v = vc_v - ve_v
```

Classify in this order:

```python
if vth_v <= vbe_v:
    region = "Cutoff"
    warnings = (
        "VTH ≤ VBE: the base-emitter junction is not forward biased. "
        "The transistor is in cutoff, so the forward-active equations are not valid.",
    )
elif vce_v < VCE_SATURATION_THRESHOLD_V:
    region = "Saturation"
    warnings = (
        f"VCE < {VCE_SATURATION_THRESHOLD_V} V: the transistor is in saturation "
        "or at the edge of saturation. The forward-active approximation is not valid.",
    )
else:
    region = "Active"
    warnings = ()
```

`dc_bias.py` must not import Flask, templates, or HTTP concepts.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `py -m unittest discover -s tests -p "test_dc_bias.py" -v`

Expected: 11 tests pass (`OK`).

- [ ] **Step 5: Commit**

```bash
git add dc_bias.py tests/test_dc_bias.py
git commit -m "feat: add voltage-divider DC bias engineering module"
```

---

## Task 2: Flask Page, Unit Conversion, and HTTP Tests

**Files:**
- Create: `requirements.txt`
- Create: `app.py`
- Create: `templates/index.html`
- Create: `static/style.css`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `BiasInput`, `BiasValidationError`, `calculate_dc_bias` from Task 1.
- Produces:
  - Flask application object named `app`.
  - `GET /` → 200, renders `index.html` with the form.
  - `POST /calculate` → 200 on valid input, 400 on invalid input.
  - Form field names: `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`, `resistor_unit`.
  - `resistor_unit` values: `"ohm"` (default) and `"kohm"`.
  - Template context keys: `values`, `errors`, `result`, `normalized`, `submitted_unit`.

- [ ] **Step 1: Create the dependency file and virtual environment**

Create `requirements.txt`:

```text
Flask==3.1.3
```

Run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Expected: Flask 3.1.3 installs successfully. `.venv/` is already gitignored.

- [ ] **Step 2: Write the failing HTTP tests**

Create `tests/test_web.py` with `unittest`, importing `app` from `app`. In `setUp`, set `app.config.update(TESTING=True)` and create `self.client = app.test_client()`.

Use this valid form payload for the default case:

```python
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
```

Include these test methods and assertions:

1. `test_get_index_returns_form` — `GET /` is 200; body contains `name="vcc"`, `name="r1"`, `name="beta"`, `name="vbe"`, `name="resistor_unit"`, and `value="100000"`.
2. `test_post_valid_ohm_values_returns_results` — post `DEFAULT_PAYLOAD`; 200; body contains `"DC Operating Point"`, `"1.230"` (IC in mA), `"8.052"` (VCE in V), and `"Active"`.
3. `test_post_kohm_values_matches_ohm_operating_point` — post the same values with `r1="100"`, `r2="22"`, `rc="2.2"`, `re="1"`, `resistor_unit="kohm"`; 200; body contains `"1.230"`, `"8.052"`, and `"100,000 Ω (100 kΩ)"`.
4. `test_post_missing_value_returns_400_with_error` — copy `DEFAULT_PAYLOAD`, set `r1=""`; 400; body contains `"Enter a value."` and does **not** contain `"DC Operating Point"`.
5. `test_post_non_numeric_returns_400_with_error` — set `beta="abc"`; 400; body contains `"Enter a number."`.
6. `test_post_zero_resistor_returns_400_with_error` — set `r1="0"`; 400; body contains `"greater than zero"`.
7. `test_post_invalid_unit_returns_400` — set `resistor_unit="mohm"`; 400; body contains `"Choose Ω or kΩ."`.
8. `test_post_cutoff_case_shows_warning` — set `r2="5000"`; 200; body contains `"Cutoff"`, `"not valid"`.
9. `test_post_saturation_case_shows_warning` — set `rc="10000"`; 200; body contains `"Saturation"`, `"not valid"`.

- [ ] **Step 3: Run the tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_web.py" -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 4: Implement `app.py`**

Implementation requirements:

```python
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
```

- `parse_form(form) -> tuple[dict[str, str], dict[str, float], dict[str, str]]` returns raw string values (including `resistor_unit`), parsed floats, and field errors. Blank → `"Enter a value."`; unparseable → `"Enter a number."`
- `format_resistance(value_ohm: float) -> str` returns e.g. `"100,000 Ω (100 kΩ)"`.
- `GET /` renders `index.html` with `values=DEFAULT_FORM`, empty `errors`, `result=None`, `normalized=None`, `submitted_unit="ohm"`.
- `POST /calculate` parses the form, validates the unit (`"ohm"`/`"kohm"`; otherwise `errors["resistor_unit"] = "Choose Ω or kΩ."`), converts all four resistors by the selected multiplier, constructs `BiasInput`, calls `calculate_dc_bias`, and catches `BiasValidationError` into `errors`.
- On success, build `normalized = {"r1": format_resistance(...), "r2": ..., "rc": ..., "re": ...}`.
- Always re-render `index.html` with `values`, `errors`, `result`, `normalized`, `submitted_unit`; return status 400 when `errors` is non-empty, otherwise 200.
- Do not put physics equations in `app.py` beyond the unit conversion.

- [ ] **Step 5: Implement `templates/index.html`**

Required structure:

- HTML5 document, `lang="en"`, viewport meta, stylesheet via `url_for('static', filename='style.css')`.
- Header: `ENG29 2121 · Lab 02`, title `BJT Common-Emitter DC Bias`, one-line model note.
- Error summary when `errors`: a list of `errors.values()`.
- Form `method="post"` to `url_for('calculate')` with labeled inputs:
  - `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`
  - `resistor_unit` select with options `Ω` (`value="ohm"`) and `kΩ` (`value="kohm"`), selected from `submitted_unit`
  - Each input uses `value="{{ values.<field> }}"` and shows `{{ errors.<field> }}` when present.
  - Submit button: `Calculate DC Bias`.
- When `result` exists:
  - Region badge `{{ result.region }}` with class `badge-{{ result.region|lower }}`.
  - Warning block when `result.warnings`: each warning, plus `"The values below are the forward-active equation output, not a validated operating point."`
  - Results table with `VB`, `VE`, `VC`, `VCE` in V; `IC`, `IE` in mA; `IB` in µA, formatted with `"%.3f"|format(...)`.
  - Normalized inputs line using `normalized.r1`, `normalized.r2`, `normalized.rc`, `normalized.re`.
- No equations, no calculation logic, no external scripts/fonts/images.

- [ ] **Step 6: Implement `static/style.css`**

Create a responsive card layout with:

- System font stack, light background, readable contrast.
- Max-width container, cards, a form grid that collapses to one column at `max-width: 640px`.
- Styled inputs, select, and submit button.
- Error alert (red), warning alert (amber), result table, region badges for active/cutoff/saturation.
- Field-error text and a small normalized-inputs line.
- No external assets.

- [ ] **Step 7: Run all tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: 20 test methods pass (`OK`); Flask serves the page.

- [ ] **Step 8: Commit**

```bash
git add requirements.txt app.py templates/index.html static/style.css tests/test_web.py
git commit -m "feat: add Flask DC bias page and HTTP tests"
```

---

## Task 3: Documentation, Validation Evidence, and Reflection

**Files:**
- Modify: `README.md`
- Create: `AGENTS.md`
- Create: `docs/design-note.md`
- Create: `docs/validation.md`
- Create: `docs/reflection.md`
- Include: `docs/superpowers/specs/2026-11-11-bjt-dc-bias-design.md` and this plan in the commit.

**Interfaces:**
- Consumes: the finished app and test suite from Tasks 1–2.
- Produces: reproducible install/run/test instructions and the independent hand-calculation record.

- [ ] **Step 1: Rewrite `README.md` for Lab 02**

Use Thai prose with English commands. Include:

- Project title and one-paragraph description.
- Circuit and model: NPN common-emitter, voltage-divider bias, forward-active approximation, constant β and VBE.
- File layout matching the design.
- Prerequisites: Python 3.10+ (tested with 3.14), Git.
- Windows setup and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

- macOS/Linux setup and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

- Open `http://127.0.0.1:5000/`.
- Tests: `python -m unittest discover -s tests -v`.
- Units: resistances are canonical Ω; the form's unit selector accepts Ω or kΩ and converts before calculation; default values are `12 V`, `100000 Ω`, `22000 Ω`, `2200 Ω`, `1000 Ω`, `β=100`, `VBE=0.70 V`.
- Assumptions and limitations: forward-active only, constant β/VBE, `VCE(sat) ≈ 0.3 V` warning threshold, no AC/transient/SPICE/FET.
- A note that Lab 01 files `electrical.py` and `test_electrical.py` are retained and untouched.
- A short statement that `templates/index.html` must be served by Flask, not opened directly.

- [ ] **Step 2: Create `AGENTS.md`**

Include conventions:

- `dc_bias.py` is pure engineering; no Flask imports.
- SI units in names (`_v`, `_a`, `_ohm`); convert at the HTTP boundary.
- `app.py` owns routes, parsing, unit conversion, and error presentation.
- Use `unittest`; run tests before committing.
- Keep Lab 01 files untouched.
- Do not add out-of-scope features (AC, transient, SPICE, FET, extra bias types).
- Never commit `.venv/`, `.env`, or secrets.

- [ ] **Step 3: Create `docs/design-note.md`**

Short summary: intent, architecture, data flow, units, validation, warnings, and a link to `docs/superpowers/specs/2026-11-11-bjt-dc-bias-design.md`.

- [ ] **Step 4: Create `docs/validation.md`**

Include:

- The independent hand calculation for the default example, step by step, with these reference values:

| Quantity | Hand value |
|---|---|
| VTH | 2.163934 V |
| RTH | 18,032.787 Ω |
| IB | 12.298581 µA |
| IC | 1.229858 mA |
| IE | 1.242157 mA |
| VE | 1.242157 V |
| VB | 1.942157 V |
| VC | 9.294312 V |
| VCE | 8.052155 V |

- A comparison table with columns `Quantity`, `Hand value`, `App value`, `Difference`, `Result`. Fill `App value` from the test run or a one-off `python -c` call after implementation; the differences should be zero within floating-point rounding.
- Validation cases: default active, `R1=0` error, `β=0` error, non-numeric error, cutoff (`R2=5 kΩ`), saturation (`RC=10 kΩ`), kΩ/Ω equivalence.
- A test-log section with the exact command and the final pass count.
- A note that the comparison is documentation/test evidence only, not a UI feature.

- [ ] **Step 5: Create `docs/reflection.md`**

Write a concise draft that answers the handout's reflection questions:

- Why opening `templates/index.html` directly is not the same as running Flask.
- How the form sends data to Python.
- Why changing equations in `dc_bias.py` does not require changing the HTML.
- Why results outside the forward-active region need warnings.
- What was learned about separating engineering logic, HTTP, templates, and tests.
- Limitations and possible next steps (without implementing them).

- [ ] **Step 6: Verify and commit**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: all tests pass.

Verify the README commands work from a clean shell (at minimum, the run and test commands).

```bash
git add README.md AGENTS.md docs/design-note.md docs/validation.md docs/reflection.md docs/superpowers/specs/2026-11-11-bjt-dc-bias-design.md docs/superpowers/plans/2026-11-11-bjt-dc-bias.md
git commit -m "docs: add Lab 02 README, validation evidence, and reflection"
```

---

## Task 4: End-to-End Verification, Localhost Demo, and GitHub

**Files:**
- Modify only if verification reveals a defect; do not add features.
- Update `docs/validation.md` test log with the final result if needed.

**Interfaces:**
- Consumes: the complete app, tests, and documentation.
- Produces: a running localhost demonstration, a clean commit, a pushed branch, and the commit SHA.

- [ ] **Step 1: Run the complete test suite**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Expected: 20 test methods pass; no failures or errors. Save the summary for the report.

- [ ] **Step 2: Confirm Lab 01 files are untouched**

Run:

```powershell
git diff -- electrical.py test_electrical.py
```

Expected: no output.

- [ ] **Step 3: Start the localhost server**

Run in the background:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --debug
```

Expected: Flask reports it is running on `http://127.0.0.1:5000/`.

- [ ] **Step 4: Demonstrate in the browser**

Before the first browser tool call, load the `browser` skill. Open `http://127.0.0.1:5000/` and verify:

1. The form appears with the default values.
2. Submitting the defaults shows an Active result with `VB 1.942 V`, `VE 1.242 V`, `VC 9.294 V`, `VCE 8.052 V`, `IC 1.230 mA`, `IB 12.299 µA`, `IE 1.242 mA`.
3. Entering `R1=0` shows a readable error and no result table.
4. Entering `R2=5000` with the `Ω` selector shows a Cutoff warning.
5. Entering `RC=10000` with the `Ω` selector shows a Saturation warning.
6. Switching to `kΩ` and entering `100`, `22`, `2.2`, `1` produces the same operating point as the default Ω values.
7. The browser console has no application errors.

If browser tools are unavailable, verify the same cases with `Invoke-WebRequest`/`curl` POSTs and state that the UI was not visually inspected.

- [ ] **Step 5: Stop the server and review the commit**

Stop the Flask process. Run:

```powershell
git status --short
git diff --staged
```

Expected: only intended app, test, and documentation files; no `.venv/`, `.env`, secrets, or Lab 01 modifications.

- [ ] **Step 6: Push and report**

```bash
git push origin main
git rev-parse --short HEAD
```

If a final commit is still needed for verification notes, commit it first with a focused message. Report the repository URL, the localhost URL, the test pass count, and the commit SHA.

---

## Self-Review Notes

- **Spec coverage:** A1 is Task 2 Step 1/5; A2 is Task 2 Steps 4–5; A3 is Task 1 tests and Task 3 validation; A4 is Task 1 validation and Task 2 HTTP tests; A5 is Task 1 region logic and Task 2 warning UI/tests; A6 is Task 1 (11 tests) plus Task 2 (9 tests); A7 is Task 3 README and Task 4 verification.
- **Scope guard:** no task adds AC, transient, SPICE, FET, extra bias templates, a database, auth, a JS framework, or an on-page reference table.
- **Type consistency:** the `BiasInput`/`BiasResult` fields, form field names, error keys, and template context keys are named identically across Tasks 1–3.
- **Review Focus mapping:** each of the five risk lines has at least one named test or, for the direct-template case, the Flask-served GET test plus a README instruction.
