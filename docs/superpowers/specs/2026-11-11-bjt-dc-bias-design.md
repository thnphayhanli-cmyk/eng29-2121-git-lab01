# BJT Common-Emitter DC Bias Web App — Design

- **Course:** ENG29 2121, Lab 02
- **Date:** 2026-11-11
- **Status:** Approved design, ready for implementation planning
- **Source specification:** `C:\Users\b6827526\Downloads\Lab02_BJT_Simulator_Brainstorm_2-2569.html`

## 1. Intent and why

Lab 02 requires a real, multi-file Flask web application, not a single HTML file. The app must demonstrate the separation between a browser form, Flask routing, an independent Python engineering module, templates, static resources, and automated tests. The engineering task is the DC operating point of an NPN common-emitter amplifier using voltage-divider bias under the forward-active approximation.

The lab is short. The design therefore optimizes for a working localhost demonstration, clear engineering logic, tests that can be run from the README, and a GitHub commit completed today. It deliberately avoids features reserved for later labs.

## 2. Goals

1. A Flask app served at `http://127.0.0.1:5000/` with a real Python backend.
2. Inputs: `VCC` [V], `R1`, `R2`, `RC`, `RE` [Ω], `β` (unitless), `VBE` [V].
3. Outputs: `VB`, `VE`, `VC`, `VCE` [V], `IC` [mA], plus `IB` [µA] and `IE` [mA], all with units.
4. Validation exactly as required by the handout: missing/non-numeric values, `R ≤ 0`, `β ≤ 0`, `VCC ≤ 0`.
5. Region handling: warn when `VTH ≤ VBE` (cutoff) or when `VCE` is near saturation; never present an out-of-region result as a validated operating point.
6. An independent hand calculation that verifies the default operating point.
7. Automated engineering tests and Flask HTTP tests using the standard library `unittest`.
8. Documentation sufficient to clone, install, run, and test the repository.
9. A localhost demonstration and a GitHub commit/push today.

## 3. Non-goals

- AC small-signal analysis, gain, Bode plots, transient analysis, signal generators, or overlays.
- SPICE/ngspice integration or a full circuit editor.
- FETs or additional bias templates (fixed bias, emitter bias, etc.).
- DC load-line plotting.
- A database, authentication, user accounts, or deployment configuration.
- A JavaScript framework or a JSON API.
- An on-page independent-reference comparison table.
- A separate cutoff or saturation solver.
- Any modification, move, or deletion of Lab 01's `electrical.py` or `test_electrical.py`.

## 4. Anti-goals

- Hard-coded results in the HTML template.
- Opening `templates/index.html` directly via `file://` as a substitute for running Flask.
- Reporting cutoff/saturation equation output as if the forward-active model were valid.
- Adding validation restrictions or engineering features that the handout does not require, especially ones that could prevent the lab from finishing.
- Letting scope grow beyond the single voltage-divider DC bias slice.

## 5. Constraints

- The handout is the authority for scope, equations, inputs, outputs, validation, and acceptance tests.
- The lab must finish today; implementation must stay small.
- Python 3.14 is available through `py` on this machine. Flask is not installed globally; the project will use a gitignored `.venv` and `requirements.txt`.
- The Flask development server is for localhost only.
- `.venv/`, `.env`, secrets, and credentials must not be committed.
- Existing Lab 01 source and tests must remain byte-for-byte untouched.
- Tests must run with `python -m unittest discover -s tests -v` (or the `py` equivalent on Windows).

## 6. Approaches considered

### A. Server-rendered single page — chosen

`GET /` renders the form; `POST /calculate` parses and validates the form, calls the engineering module, and re-renders the same Jinja template with results or errors. No JavaScript.

- **Why chosen:** smallest implementation, direct match to the handout's architecture, easy to test with Flask's test client, no hidden client-side calculation, and no extra API surface.

### B. JSON API plus `fetch`

`POST /api/calculate` returns JSON and JavaScript updates the page.

- **Why rejected:** adds a client-side layer, asynchronous behavior, and additional tests without improving the lab's learning outcome. It also risks the UI appearing to calculate in the browser.

### C. Two-page form/results flow

A form page posts to a separate results page.

- **Why rejected:** requires an additional template and navigation state for no benefit; the single-page two-state flow is simpler and equally clear.

## 7. Design

### 7.1 Architecture and file responsibilities

```text
.
├── app.py                  # Flask app, HTTP routes, form parsing, unit conversion, error handling
├── dc_bias.py              # Pure engineering calculations and validation; no Flask imports
├── templates/
│   └── index.html          # Jinja form, results, warnings; no physics equations
├── static/
│   └── style.css           # Responsive presentation only
├── tests/
│   ├── test_dc_bias.py     # Engineering math, validation, region classification
│   └── test_web.py         # Flask test-client HTTP and conversion tests
├── requirements.txt        # Flask dependency
├── README.md               # Install, run, test, model assumptions, limitations
├── AGENTS.md               # AI/code conventions for this repository
├── docs/
│   ├── design-note.md      # Short design summary and link to this document
│   ├── validation.md       # Independent hand calculation and validation evidence
│   ├── reflection.md       # Lab reflection draft
│   └── superpowers/specs/
│       └── 2026-11-11-bjt-dc-bias-design.md
└── electrical.py           # Lab 01 — untouched
    test_electrical.py      # Lab 01 — untouched
```

**Separation rules:**

- `dc_bias.py` knows only engineering values and equations. It must not import Flask, `request`, templates, or HTML concepts.
- `app.py` owns HTTP concerns: reading `request.form`, parsing strings, converting units, collecting form errors, choosing HTTP status, and rendering.
- `templates/index.html` displays values and messages. It must not contain the DC bias equations.
- `static/style.css` contains presentation only.
- Tests import the engineering module directly or use Flask's test client; they do not scrape a live server.

### 7.2 Data flow

```text
Browser form (GET /)
        ↓
POST /calculate
        ↓
app.py: read form, parse numbers, validate presence/numerics,
        convert resistor values to Ω, collect field errors
        ↓
dc_bias.calculate_dc_bias(BiasInput)  ← pure Python, SI units
        ↓
BiasResult (voltages, currents, region, warnings)
        ↓
Jinja renders index.html with results or errors
        ↓
Browser displays DC operating point and warnings
```

### 7.3 Units and inputs

**Canonical engineering unit:** ohms (Ω) for every resistance inside the application and in the engineering module.

**Form:**

| Field | Unit | Notes |
|---|---|---|
| `VCC` | V | Positive supply |
| `R1` | Ω or kΩ | Base-to-VCC resistor |
| `R2` | Ω or kΩ | Base-to-ground resistor |
| `RC` | Ω or kΩ | Collector resistor |
| `RE` | Ω or kΩ | Emitter resistor |
| `beta` | unitless | Forward current gain |
| `VBE` | V | Base-emitter forward voltage |
| `resistor_unit` | `ohm` or `kohm` | Applies to all four resistors |

- The resistor unit selector is explicit. `Ω` is the default and the engineering unit; `kΩ` is accepted for convenience and converted before calculation.
- Conversion: `Ω × 1`, `kΩ × 1000`. The conversion is applied once in `app.py` to `R1`, `R2`, `RC`, and `RE` before constructing `BiasInput`.
- The result view echoes the normalized resistances in Ω and their kΩ equivalents so the conversion is visible and auditable.
- Default demonstration values, prefilled on `GET /`:
  - `VCC = 12 V`
  - `R1 = 100000 Ω` (100 kΩ)
  - `R2 = 22000 Ω` (22 kΩ)
  - `RC = 2200 Ω` (2.2 kΩ)
  - `RE = 1000 Ω` (1 kΩ)
  - `β = 100`
  - `VBE = 0.70 V`
- The default unit is `Ω`, matching the canonical engineering unit. A user may switch to `kΩ` and enter `100`, `22`, `2.2`, `1`; the backend must produce the same operating point.
- Output formatting: voltages to 3 decimal places with `V`; `IC` and `IE` to 3 decimal places with `mA`; `IB` to 3 decimal places with `µA`. Units are always visible.

### 7.4 Engineering equations

The engineering module uses exactly the handout's forward-active voltage-divider equations:

```text
VTH = VCC · R2 / (R1 + R2)
RTH = R1 · R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β + 1) · RE)
IC  = β · IB
IE  = (β + 1) · IB
VE  = IE · RE
VB  = VE + VBE
VC  = VCC − IC · RC
VCE = VC − VE
```

- `VTH` and `RTH` are internal values; they may be included in the result object for documentation and tests but need not be displayed.
- All calculations use SI units: V, A, Ω. The UI converts A to mA/µA only for display.
- No numerical solver, iteration, or external library is used.

### 7.5 Validation

Validation is limited to the handout's requirements plus the minimum needed to parse a web form safely.

| Condition | Behavior |
|---|---|
| Any required field missing or blank | Field error; re-render form; HTTP 400 |
| Any field not parseable as a number | Field error; re-render form; HTTP 400 |
| `NaN` or infinite numeric value | Rejected as an invalid numeric input, under the handout's non-numeric/invalid-input requirement |
| `VCC ≤ 0` | Error on `VCC` |
| Any of `R1`, `R2`, `RC`, `RE ≤ 0` | Error on the offending resistor |
| `β ≤ 0` | Error on `β` |
| Resistor unit not `Ω` or `kΩ` | Form error; re-render; HTTP 400 (UI integrity, not an engineering restriction) |

**Explicitly not added:**

- No `VBE < VCC` restriction.
- No `VBE ≥ 0` restriction.
- No minimum/maximum resistor, beta, or voltage ranges beyond the handout.
- No requirement that the circuit be in the active region.

`VBE` is used exactly as supplied. An unphysical or too-large `VBE` will normally produce `VTH ≤ VBE`, which triggers the cutoff warning rather than a new validation rule. This keeps the app aligned with the handout's warning-based treatment of out-of-region operation.

On validation failure, entered values and the selected resistor unit are preserved, a summary and field-level messages are shown, no result table is rendered, and the response does not raise a traceback.

### 7.6 Region classification and warnings

The forward-active equations are always evaluated. The result is then classified:

```text
if VTH ≤ VBE:
    region = "Cutoff"
    warning = base-emitter junction is not forward biased; the transistor is off
elif VCE < 0.3 V:
    region = "Saturation"
    warning = VCE is at or below the saturation threshold; forward-active approximation is invalid
else:
    region = "Active"
    no warning
```

- `VCE_SATURATION_THRESHOLD_V = 0.3` is a documented textbook assumption, defined as a named constant.
- Cutoff takes precedence when both conditions could apply.
- Outside the active region, the app keeps the equation output visible but marks it clearly as the **forward-active equation output, not a validated operating point**. It does not claim the model is accurate, and it does not add a separate cutoff/saturation solver.
- The warning is a visible banner near the results, plus a short region badge. The result remains useful for teaching why the approximation fails.
- A negative `VCE` is therefore a saturation case and is warned about, not silently accepted.

### 7.7 Page behavior

**Initial `GET /`:**

- Header with the lab name and a one-line description.
- Input form with labels and unit hints, prefilled with the default values.
- Short model note: forward-active approximation, constant β, constant VBE, `VCE(sat)` threshold ≈ 0.3 V.
- No results table.

**Successful `POST /calculate`:**

- Same form, retaining submitted values and unit.
- Result section with:
  - Region badge (`Active`, `Cutoff`, or `Saturation`).
  - Table of `VB`, `VE`, `VC`, `VCE` in V; `IC`, `IE` in mA; `IB` in µA.
  - A small normalized-input line showing the four resistances in Ω and kΩ.
  - Warning banner when outside the active region.
- HTTP 200.

**Failed `POST /calculate`:**

- Same form, retaining submitted values and unit.
- Error summary and field-level error messages.
- No result section.
- HTTP 400.

The page is responsive and usable at narrow widths. No external fonts, scripts, images, or CDNs are required. Accessibility basics: `<label>` for every input, visible units, sufficient contrast, and warning text that is not conveyed by color alone.

### 7.8 Independent engineering verification

The independent check is deliberately outside the runtime calculation path:

1. `docs/validation.md` contains a step-by-step hand calculation for the default example, using the handout equations and showing intermediate values (`VTH`, `RTH`, `IB`, `IC`, `IE`, `VE`, `VB`, `VC`, `VCE`).
2. `tests/test_dc_bias.py` contains a test with hand-derived expected constants for the default example, not values produced by calling the implementation.
3. A second test computes the expected emitter current with an algebraically rearranged independent expression, for example:

   ```text
   IE = (VTH − VBE) / (RTH/(β + 1) + RE)
   ```

   and cross-checks `IC`, `IB`, `VE`, and `VCE`.
4. `docs/validation.md` includes a comparison table (hand value, app value, difference, pass/fail) and the validation/warning cases exercised.

The comparison is not shown as an extra table in the UI, per the approved scope.

### 7.9 Test strategy

Use the standard library `unittest`. No pytest dependency.

**`tests/test_dc_bias.py` (engineering):**

- Default operating point matches hand-calculated constants.
- Independently rearranged `IE` formula matches the module.
- Active region classification has no warning.
- Cutoff warning when `VTH ≤ VBE`.
- Saturation warning when `VCE < 0.3 V`.
- `VCC ≤ 0` raises the expected validation error.
- Each resistor `≤ 0` raises the expected validation error.
- `β ≤ 0` raises the expected validation error.
- Non-numeric/non-finite values are rejected.

**`tests/test_web.py` (HTTP):**

- `GET /` returns 200 and contains the input fields and default values.
- Valid `POST /calculate` with Ω values returns 200 and the computed results.
- Valid `POST /calculate` with equivalent kΩ values returns the same operating point (conversion test).
- Missing/non-numeric input returns 400 with a readable error.
- A non-positive resistor returns 400 with a readable error.
- A cutoff or saturation case returns 200 with the warning text.

This comfortably exceeds the handout minimum of at least 3 engineering tests and at least 1 Flask test-client test.

### 7.10 Documentation

- **`README.md`:** project title, circuit/model summary, file layout, prerequisites, virtual-environment setup, install, run, test commands, default example, units/conversion, assumptions, limitations, Lab 01 note, and localhost URL.
- **`AGENTS.md`:** repository conventions: pure engineering module, named units, Flask only in `app.py`, `unittest`, no secrets, no out-of-scope features, run tests before commit.
- **`docs/design-note.md`:** concise summary of the architecture and a pointer to this design document.
- **`docs/validation.md`:** hand calculation, reference comparison table, validation cases, warning cases, and a test-log section.
- **`docs/reflection.md`:** a concise reflection draft covering what was built, what was learned about frontend/backend separation, model limitations, and possible next labs. It is written so the student can personalize it.
- **This design document:** retained as the design record.

README language: Thai prose with English commands and equations, matching the existing repository.

### 7.11 Existing Lab 01 work

- `electrical.py` and `test_electrical.py` remain exactly as they are.
- The new app lives at the repository root, matching the handout's layout.
- `README.md` is rewritten for Lab 02 and includes a short note that the Lab 01 files are retained.
- No Lab 01 file is moved, renamed, deleted, or edited.

### 7.12 Demonstration, tests, and Git

1. Create a gitignored `.venv` with `py -m venv .venv`.
2. Install dependencies with `py -m pip install -r requirements.txt`.
3. Run `py -m unittest discover -s tests -v` and record the output.
4. Start the app with `py -m flask --app app run --debug`.
5. Demonstrate:
   - Default values → active operating point with units.
   - `R1 = 0` → readable validation error.
   - A cutoff case (`VTH ≤ VBE`) → cutoff warning.
   - A saturation case (`VCE < 0.3 V`) → saturation warning.
   - kΩ input → same result as equivalent Ω input.
6. Review `git status` and `git diff --staged`.
7. Commit with a focused message, push to `origin/main`, and report the commit SHA.

## 8. Decisions and assumptions

| Decision | Choice | Reason |
|---|---|---|
| Rendering approach | Server-rendered single page, no JavaScript | Smallest, most testable, matches handout |
| Canonical resistance unit | Ω | Handout engineering unit |
| kΩ handling | Explicit unit selector; convert to Ω in `app.py` | Handout requires consistent kΩ→Ω conversion |
| Default unit | Ω | Canonical engineering unit |
| Default example values | Handout values, expressed in Ω | Reproducible demo |
| Saturation threshold | `VCE < 0.3 V` | Standard textbook approximation; documented |
| Extra VBE validation | None | Handout does not specify one; cutoff warning covers it |
| Out-of-region output | Show forward-active equation result, clearly marked invalid | Teaching value; no separate solver |
| Independent reference | Docs + tests only | Approved scope; no UI table |
| Test framework | `unittest` | Handout command; no extra dependency |
| HTTP status for invalid form | 400 | Correct request semantics; page still renders |
| Lab 01 files | Untouched | User requirement and history preservation |

## 9. What is left to the implementation plan

The implementation plan will define:

- The exact task order and file creation sequence.
- The precise public API of `dc_bias.py` (dataclasses, function signature, exception/error type).
- The exact form field names and template structure.
- The exact test cases and expected reference constants.
- The CSS layout details.
- The README, AGENTS.md, and documentation content.
- The verification and commit sequence.

## 10. Acceptance criteria mapping

| Handout check | Design response |
|---|---|
| A1 · `GET /` returns 200 with the input form | `GET /` renders `index.html` with prefilled form |
| A2 · `POST /calculate` computes in Python, not hard-coded HTML | `app.py` parses and calls `dc_bias.calculate_dc_bias()`; template only displays |
| A3 · DC values match an independent calculation | Hand calculation in `docs/validation.md`; hand-constant and independently rearranged tests |
| A4 · `R ≤ 0`, `β ≤ 0`, non-numeric input show clear errors without crashing | Validation table in §7.5; HTTP 400 re-render with field messages |
| A5 · Warn for cutoff/saturation; do not claim validity | Region classification in §7.6; warning banner and region badge |
| A6 · At least 3 engineering tests and 1 Flask test | Test strategy in §7.9; target ~15 tests total |
| A7 · Clone, install, run, and test from README | README and reproducible command sequence in §7.12 |
