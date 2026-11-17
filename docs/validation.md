# Validation — Lab 03 BJT DC Bias Web App

## 1. Method and Environment (วิธีตรวจจริง)

- Flask was served at `http://127.0.0.1:5001/`. Port 5000 had a stale Lab 02 Flask process, so port 5001 was used for every case in this run.
- **Playwright MCP: NOT RUN** — there is no `opencode.json` / `opencode.jsonc` in the project root and no Playwright MCP server configured, so the Playwright MCP browser tools were unavailable. This is the fallback path allowed by handout section **05 / Connect the browser MCP**.
- The method actually used was **OpenCode Browser** (in-app Chromium). For each case: navigate → snapshot → select the mode → fill the fields → click **Calculate DC Bias** → read the newly rendered page. Values were read from the page's results table, not from source code or `curl`.
- No browser console errors were observed on the checked pages.
- Tolerance from handout section **06 / Browser acceptance**: compare with the **unrounded independent reference**; `|ΔIC| ≤ 0.01 mA` and `|ΔVCE| ≤ 0.02 V`. The UI shows two decimal places.
- The Lab 02 Divider result was recorded before the change (`IC 1.230 mA`, `VCE 8.052 V`) and is unchanged after it.

## 2. A1–A5 Acceptance Table (ตารางตามใบงานข้อ 06)

Common inputs for A1–A5: `VCC = 12 V`, `RC = 2.2 kΩ (2,200 Ω)`, `β = 100`, `VBE = 0.70 V`; resistor unit `Ω` unless stated otherwise. Expected values were calculated independently **before** the browser run; the calculations are in sections 3–6.

| Case | Mode and inputs | Expected before run (unrounded reference) | Observed in browser, with units | Method | Status |
|---|---|---|---|---|---|
| **A1** | Divider (unchanged Lab 02 case): `R1 = 100 kΩ`, `R2 = 22 kΩ`, `RE = 1 kΩ` | `IC 1.229858 mA`, `VCE 8.052155 V` | `IC 1.230 mA`, `VCE 8.052 V`, region `Active` — matches the pre-change Lab 02 result | OpenCode Browser | **PASS** |
| **A2** | Fixed: `RB = 1 MΩ`; **no `RE` field submitted** | `IC 1.130000 mA`, `VCE 9.514000 V` | `IC 1.130 mA`, `VCE 9.514 V`, region `Active`. Form fields were `mode, vcc, rb, rc, beta, vbe, resistor_unit` — no `re` field | OpenCode Browser | **PASS** |
| **A3** | Emitter: `RB = 1 MΩ`, `RE = 1 kΩ` | `IC 1.026340 mA`, `VCE 8.705450 V` | `IC 1.026 mA`, `VCE 8.705 V`, region `Active`. Form had `input[name="re"]` with value `1000`; audit line showed `RE = 1,000 Ω (1 kΩ)` | OpenCode Browser | **PASS** |
| **A4** | Emitter: same as A3 but only `RE` changed to `2 kΩ` | Prediction **before run**: `IC` decreases (reason in §2.1). Reference `IC 0.940100 mA`, `VCE 8.032779 V` | `IC 0.940 mA` (decreased from A3), `VCE 8.033 V`, region `Active`; audit line showed `RE = 2,000 Ω (2 kΩ)` | OpenCode Browser | **PASS** |
| **A5** | Fixed: `RB = 0` | Flask validation error naming `RB` and the mode; no result table; no stale result from a previous case | Alert `Please fix the following:` / `Fixed Bias: RB must be greater than zero.`; no results section, no results table, no old result text anywhere on the page. Flask-side HTTP 400 confirmed separately with the existing test client | OpenCode Browser (+ Flask test client for HTTP status) | **PASS** |

Tolerance check against the unrounded references: A1 `ΔIC 0.000142 mA`, `ΔVCE 0.000155 V`; A2 `0.000000 mA`, `0.000000 V`; A3 `0.000340 mA`, `0.000450 V`; A4 `0.000100 mA`, `0.000221 V` — all below `0.01 mA` / `0.02 V`. Deltas are rounding-only.

### 2.1 A4 — prediction recorded before the run

Prediction: **IC will decrease** when `RE` changes from `1 kΩ` to `2 kΩ`, while `VCC, RB, RC, β, VBE` stay the same.

Reason: for Emitter bias `IB = (VCC − VBE) / [RB + (β + 1)RE]`. The denominator rises from `1,000,000 + 101·1,000 = 1,101,000 Ω` to `1,000,000 + 101·2,000 = 1,202,000 Ω` while the numerator stays `11.3 V`, so `IB` falls from `10.263 µA` to `9.401 µA` and `IC = β·IB` falls. The observed `IC 0.940 mA` confirms the predicted direction.

Note on reading A4: the first immediate read after clicking was still the previous page state, so the page was re-read after navigation completed; that final state showed `RE = 2,000 Ω (2 kΩ)` with the new values. The evidence below uses the post-navigation page state.

### 2.2 Evidence copied from the browser pages

A4 — heading, audit line and result rows:

```text
Emitter DC Operating Point
Resistances used: RB = 1,000,000 Ω (1,000 kΩ), RC = 2,200 Ω (2.2 kΩ), RE = 2,000 Ω (2 kΩ)
VCE | 8.033 | V
IC  | 0.940 | mA
```

A5 — error alert text:

```text
Please fix the following:
Fixed Bias: RB must be greater than zero.
```

For A5 the page reported `active mode: Fixed Bias`, `rbValue: "0"`, `hasResult: false`, `hasResultsTable: false`, and no occurrence of `DC Operating Point` in the page text. The message is the Flask validation error rendered in the form alert (the mode prefix is added by the template); Flask itself returns HTTP 400 for this input.

## 3. Independent Hand Calculation — Divider (unchanged)

Default example:

```text
VCC = 12 V
R1  = 100000 Ω
R2  = 22000 Ω
RC  = 2200 Ω
RE  = 1000 Ω
β   = 100
VBE = 0.70 V
```

### Step 1 — Thevenin equivalent of the base divider

```text
VTH = VCC · R2 / (R1 + R2)
    = 12 · 22000 / (100000 + 22000)
    = 264000 / 122000
    = 2.163934426 V

RTH = R1 · R2 / (R1 + R2)
    = 100000 · 22000 / 122000
    = 2,200,000,000 / 122,000
    = 18032.786885 Ω
```

### Step 2 — Base current

```text
IB = (VTH − VBE) / (RTH + (β + 1) · RE)
   = (2.163934426 − 0.70) / (18032.786885 + 101 · 1000)
   = 1.463934426 / 119032.786885
   = 0.000012298581 A
   = 12.298581 µA
```

### Step 3 — Collector and emitter currents

```text
IC = β · IB
   = 100 · 0.000012298581
   = 0.001229858146 A
   = 1.229858 mA

IE = (β + 1) · IB
   = 101 · 0.000012298581
   = 0.001242156728 A
   = 1.242157 mA
```

### Step 4 — Node voltages

```text
VE = IE · RE
   = 0.001242156728 · 1000
   = 1.242156728 V

VB = VE + VBE
   = 1.242156728 + 0.70
   = 1.942156728 V

VC = VCC − IC · RC
   = 12 − 0.001229858146 · 2200
   = 12 − 2.705687922
   = 9.294312078 V

VCE = VC − VE
    = 9.294312078 − 1.242156728
    = 8.052155350 V
```

## 4. Independent Hand Calculation — Fixed Bias

Default example:

```text
VCC = 12 V
RB  = 1000000 Ω
RC  = 2200 Ω
β   = 100
VBE = 0.70 V
```

```text
IB = (VCC − VBE) / RB
   = (12 − 0.70) / 1000000
   = 0.0000113 A
   = 11.300 µA

IC = β · IB
   = 100 · 0.0000113
   = 0.00113 A
   = 1.130 mA

IE = (β + 1) · IB
   = 101 · 0.0000113
   = 0.0011413 A
   = 1.141 mA

VE = 0 V
VB = VBE = 0.700 V

VC = VCC − IC · RC
   = 12 − 0.00113 · 2200
   = 12 − 2.486
   = 9.514 V

VCE = VC − VE
    = 9.514 V
```

Browser result: `VB 0.700 V`, `VE 0.000 V`, `VC 9.514 V`, `VCE 9.514 V`, `IC 1.130 mA`, `IB 11.300 µA`, `IE 1.141 mA`, region `Active`.

## 5. Independent Hand Calculation — Emitter Bias

Default example:

```text
VCC = 12 V
RB  = 1000000 Ω
RC  = 2200 Ω
RE  = 1000 Ω
β   = 100
VBE = 0.70 V
```

```text
IB = (VCC − VBE) / (RB + (β + 1) · RE)
   = (12 − 0.70) / (1000000 + 101 · 1000)
   = 11.3 / 1101000
   = 0.00001026339691 A
   = 10.263 µA

IC = β · IB
   = 100 · 0.00001026339691
   = 0.001026339691 A
   = 1.026 mA

IE = (β + 1) · IB
   = 101 · 0.00001026339691
   = 0.001036603088 A
   = 1.037 mA

VE = IE · RE
   = 0.001036603088 · 1000
   = 1.036603088 V

VB = VE + VBE
   = 1.036603088 + 0.70
   = 1.736603088 V

VC = VCC − IC · RC
   = 12 − 0.001026339691 · 2200
   = 12 − 2.257947320
   = 9.742052680 V

VCE = VC − VE
    = 9.742052680 − 1.036603088
    = 8.705449592 V
```

Browser result: `VB 1.737 V`, `VE 1.037 V`, `VC 9.742 V`, `VCE 8.705 V`, `IC 1.026 mA`, `IB 10.263 µA`, `IE 1.037 mA`, region `Active`.

## 6. Independent Hand Calculation — Emitter Bias with RE = 2 kΩ (A4 reference)

Only `RE` changes from section 5.

```text
VCC = 12 V
RB  = 1000000 Ω
RC  = 2200 Ω
RE  = 2000 Ω
β   = 100
VBE = 0.70 V

IB = (VCC − VBE) / [RB + (β + 1)·RE]
   = 11.3 / (1000000 + 101·2000)
   = 11.3 / 1202000
   = 0.000009400998 A
   = 9.401 µA

IC = β·IB          = 0.000940100 A = 0.940100 mA
IE = (β + 1)·IB    = 0.000949501 A = 0.950 mA

VE = IE·RE         = 0.000949501 · 2000 = 1.899002 V
VB = VE + VBE      = 2.599002 V
VC = VCC − IC·RC   = 12 − 2.068220 = 9.931780 V
VCE = VC − VE      = 8.032779 V
```

Browser result (A4, post-navigation page state): `VB 2.599 V`, `VE 1.899 V`, `VC 9.932 V`, `VCE 8.033 V`, `IC 0.940 mA`, `IB 9.401 µA`, `IE 0.950 mA`, region `Active`.

## 7. Additional Browser Checks (E1–E4)

These are checks kept from the previous round. They are deliberately **not** named A1–A5.

### E1 — Input errors (Divider)

| Input change | Browser alert | Result table |
|---|---|---|
| `R1 = 0` | `Voltage Divider: R1 must be greater than zero.` | none |
| `β = abc` | `Voltage Divider: Enter a number.` | none |
| `β = 0` | `Voltage Divider: Beta must be greater than zero.` | none |

Observed with OpenCode Browser. HTTP 400 for invalid input was also confirmed against the running Flask server / existing test client. The mode name in each message is the selected mode.

### E2 — Cutoff warning

Divider with `R2 = 5000 Ω`: badge `Cutoff`, table `IC -0.122 mA`, `VCE 12.390 V`; warning begins `IB ≤ 0 A: the base-emitter junction is not forward biased...` and states that the displayed values are forward-active equation output, not a validated operating point. No input error; HTTP 200. (OpenCode Browser)

### E3 — Saturation warning

Divider with `RC = 10000 Ω`: badge `Saturation`, table `IC 1.230 mA`, `VCE -1.541 V`; warning begins `VCE ≤ 0.2 V: the transistor is in saturation or at the edge of saturation...` with the same model-limitation note. No input error; HTTP 200. (OpenCode Browser)

Two earlier threshold rows from `POST /calculate` checks (not a browser run): `RC = 8544 Ω → VCE 0.250 V, Active`; `RC = 8600 Ω → VCE 0.181 V, Saturation`.

### E4 — Unit conversion (kΩ → Ω)

Fixed Bias form switched to `kΩ` with `RB = 1000`, `RC = 2.2`. The browser audit line showed:

```text
Resistances used: RB = 1,000,000 Ω (1,000 kΩ), RC = 2,200 Ω (2.2 kΩ)
```

The same values produced `IC 1.130 mA` and `VCE 9.514 V`, matching the Ω submission in A2. (OpenCode Browser)

## 8. Existing Test Log

Command:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Result:

```text
Ran 24 tests

OK
```

Breakdown:

- 11 engineering tests in `tests/test_dc_bias.py`
- 13 Flask HTTP tests in `tests/test_web.py`
- No new `unittest` tests were added.

## 9. Scope Note

This evidence covers the handout's A1–A5 browser acceptance cases plus four additional checks (E1–E4). It does not add AC, transient, SPICE, a load line, a separate cutoff/saturation solver, or new unittest / Playwright scripts. No result was fabricated: every PASS above is backed by the browser observations recorded in sections 2 and 7.
