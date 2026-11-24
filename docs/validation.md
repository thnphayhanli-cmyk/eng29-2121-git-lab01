# Validation — BJT Common-Emitter Web App

The first nine sections are the historical Lab 03 evidence. [Lab 04 evidence](#10-lab-04--ce-simulation) is recorded separately below.

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

The Lab 03 run covered A1–A5 and four additional checks (E1–E4). The PASS entries in sections 2 and 7 are the observations from that run and do not validate Lab 04.

## 10. Lab 04 — CE Simulation

- **Reference:** ENG29 2121 Lab 04 handout from Moodle (`Lab04_BJT_Amplifier_Simulator_2-2569.html`, local course copy; not part of the submission tree).
- **Environment:** Flask at `http://127.0.0.1:5007/` for the final responsive retest (`:5005` for the baseline and `:5004` for the model-missing check), Python from `.venv`, ngspice 47 (`ngspice_con.exe`, verified by `--version`); log shows analysis at 27 °C.
- **Model:** no instructor starter or model was provided. The substitute reference is onsemi’s 2N3904 PSpice model, `.MODEL Q2n3904 npn`, generated August 7, 2001; it is **not instructor-approved**. The [manufacturer download](https://www.onsemi.com/download/models/lib/2n3904.lib) and [legacy onsemi download](https://www.onsemi.com/pub/Collateral/2N3904.LIB) both returned the same 977 bytes (SHA-256 `5608c109b8d68d57798557991cee506661d031916f589325fad5ed10d82ccbf7`). The file stays local; the generated deck keeps the complete `.MODEL` and continuation lines without changing parameters.
- **Browser:** Playwright MCP **NOT RUN** (no tool available in the session). OpenCode Browser (Chromium) was used for B1–B7. Installed Chrome via DevTools was used for the exact-width B8 screenshots and layout checks.

| Case | Method | Input | Expected / reference | Observed | Evidence | Status |
|---|---|---|---|---|---|---|
| B1 | OpenCode Browser, submitted each analytical form | Lab 03 A1/A2/A3 inputs (§2) | IC/VCE match §2 within 0.01 mA / 0.02 V | Divider 1.230 mA / 8.052 V; Fixed 1.130 mA / 9.514 V; Emitter 1.026 mA / 8.705 V; all Active | Values read from each new results table | **PASS** (fallback browser) |
| B2 | OpenCode Browser + independent `.op` | Handout baseline, DC | VB/VE/VC/VCE/IC match ngspice `.op`; model and run status visible | VB 1.96795 V, VE 1.33638 V, VC 9.08387 V, VCE 7.74748 V, IC 1.32552 mA; Q2n3904, ngspice-47, Success | [DC screenshot](captures/lab04-before-desktop-dc.jpg); run log: 1 row | **PASS** (fallback browser) |
| B3 | OpenCode Browser + independent `.op` | RE only: 1 → 2 kΩ | Collector current decreases, and operating-point values change | IC 1.32552 → 0.713542 mA; VCE 7.74748 → 8.99011 V. Displayed netlist uses `RE e 0 2000`. | Updated browser readout and independent DC check below | **PASS** (fallback browser) |
| B4 | OpenCode Browser + independent `.ac` | Handout baseline, AC | Bode gain in dB and phase in degrees from `Vout/Vin`, frequency in Hz | Two 361-sample curves; 1 kHz sample: 1.7371 V/V, 4.797 dB, −179.9°. | [AC screenshot](captures/lab04-before-desktop-ac.png); raw rows and SVG comparison below | **PASS** (fallback browser) |
| B5 | OpenCode Browser + independent `.tran` | 10 mV peak, 1 kHz | Vin/Vout versus time; inverted output near midband | Final four periods (~16–20 ms); measured 9.998 mV Vin and 17.37 mV Vout peak; output inverted, independently measured at −179.87° fundamental phase. | [10 mV transient screenshot](captures/lab04-before-desktop-tran.png); run log: 2,008 rows, 401 displayed samples per signal | **PASS** (fallback browser) |
| B6 | OpenCode Browser + independent `.tran` | 20 mV peak, 1 kHz; only amplitude changed | Input/output amplitudes increase, based on the new `.tran` data | Vin 20 mV peak, Vout 34.74 mV peak; Vout approximately doubled and remained inverted. The vertical scale changed to fit the new samples. | [10 mV](captures/lab04-before-desktop-tran.png) / [20 mV](captures/lab04-before-desktop-tran-20mv.jpg) browser captures and independent peak-to-peak check | **PASS** (fallback browser) |
| B7 | OpenCode Browser and Chrome DevTools; additional adapter/HTTP checks | RE = 0; missing model; real solver failure immediately after successful AC | Error with no retained Success, readouts, or plots | RE = 0: HTTP 400. Missing model: HTTP 503. Real ngspice failure: HTTP 502, Error, zero readouts and zero plots after a run with two plots. | [Solver failure capture](captures/lab04-audit-solver-failure.jpg), run log and §11 | **PASS** (fallback browser) |
| B8 | Chrome DevTools with real browser form submissions | 1280×900 / 390×844, DC → AC → Transient | Controls, schematic and plots readable at both widths | No horizontal overflow, clipped axes, tick collisions, or schematic label collisions. Run button, units, and numeric readouts fit at both widths. Source controls appeared only for Transient. | Before/after captures and browser checks below | **PASS** after refinement (fallback browser); baseline **FAIL** |

### Independent BJT cross-check

The independent deck used the handout circuit with the unchanged manufacturer file via `.include 2n3904.lib` and Q1 connected directly to the collector. It did not use the web adapter's voltage-sense source:

- DC: `op` and `print v(b) v(e) v(c) v(c)-v(e) @q1[ic]`. At RE = 1 kΩ, independent VB/VE/VC/VCE were 1.967953686 / 1.336383612 / 9.083865683 / 7.747482070 V, and IC was 1.325515590 mA. At 2 kΩ, VCE was 8.990107078 V and IC was 0.713541639 mA. The adapter also satisfied `VCE = VC − VE` and `IC = (VCC − VC) / RC` at DC; the displayed difference from Lab 03 is a model difference, not a rounding error.
- AC: `ac lin 1 1k 1k`; `Vout/Vin = −1.737101486 − j0.003921840` at 1 kHz, or 4.796525971 dB at −179.870644°. A separate full 361-row sweep was compared with both rendered polylines after mapping the raw values onto the SVG axes. The maximum difference was below 0.006 SVG viewBox units (rendering rounds to 0.01).
- Transient: `tran 10u 20m 0 10u`; `meas tran … pp v(in)` / `v(out)` over 16–20 ms. At 10 mV peak the independent peak-to-peak input/output were 19.9969/34.7361 mV; at 20 mV peak they were 39.9938/69.4721 mV. The fundamental phase was checked by time-weighted projection of the samples. The independent time-domain samples mapped onto both rendered traces within 0.006 SVG viewBox units at both amplitudes.
- After refinement, the independently generated raw samples were mapped onto the new axis domains and compared with the HTML `<polyline>` coordinates again. All 361 per AC trace and 401 per displayed transient trace still matched, within 0.006 viewBox units at both amplitudes. The new axes change the display scale, not the solver output.

### B8 before/after evidence

| Browser viewport / result | Before | After |
|---|---|---|
| Desktop DC | [Capture](captures/lab04-before-desktop-dc.jpg) | [Capture](captures/lab04-after-desktop-dc.png) |
| Desktop Bode | [Capture](captures/lab04-before-desktop-ac.png) | [Capture](captures/lab04-after-desktop-ac.png) |
| Desktop transient (10 mV) | [Capture](captures/lab04-before-desktop-tran.png) | [Capture](captures/lab04-after-desktop-tran.png) |
| Desktop transient (20 mV) | [Capture](captures/lab04-before-desktop-tran-20mv.jpg) | [Capture](captures/lab04-after-desktop-tran-20mv.png) |
| Phone Bode | [Capture](captures/lab04-before-mobile-ac.png) | [Capture](captures/lab04-after-mobile-ac.png) |
| Phone transient | [Capture](captures/lab04-before-mobile-tran.png) | [Capture](captures/lab04-after-mobile-tran.png) |
| Additional final views | — | [Phone DC](captures/lab04-after-mobile-dc.png), Lab 03 [desktop](captures/lab04-after-desktop-lab03.png) / [phone](captures/lab04-after-mobile-lab03.png) |

The baseline failed due to `RC`/`Cout` and `R2`/`Q1 NPN` collisions and approximately 10.4 px axis labels on phone. The final Chrome run found no intersecting SVG text boxes in the CE diagram or any of the three Lab 03 schematics, at either width. The on-screen plot ticks are about 12.2 CSS px at both widths. In the fallback in-app browser, `Tab` moved from RE to RL, `Enter` ran DC, and focus reached the result heading. Switching from kΩ to Ω kept `R1 = 100`, changed the suffix to Ω, announced that the number was not converted, and marked the existing result **Previous run**. In the Chrome invalid-RE check after a successful transient run, focus moved to RE and the response showed Error with no retained trace.

Supplemental checks: at 320 px, the `10M` and `100M` tick labels initially overlapped; hiding the penultimate label at that width preserved the grid and cleared the collision on retest. The 768 px Bode view had no overflow or tick collisions. Chrome touch emulation tapped the 44 px Run button at 390 px and successfully reached the DC result heading. Selected text/background contrast measurements ranged from 6.67:1 (input units) to 14.45:1 (result heading), including 9.46:1 for plot ticks. This was not a full screen-reader or physical-device audit.

### Final UI review

- **Impeccable UX critique:** 22/40 before refinement, 27/40 on the first redesign, and **30/40** on the final independent review. Clearer unit handling, mobile navigation, and plot descriptions improved the measured score; it did not reach 36/40. Lab 03 mode changes still load that circuit's defaults rather than retaining an unsaved draft. The charts expose a measured summary in Chrome's accessibility tree, not a point-by-point spoken trace.
- **Impeccable technical audit:** **18/20** (accessibility 3/4, performance 4/4, theming 3/4, responsiveness 4/4, implementation integrity 4/4). The final Ready route scored 100 accessibility and 100 best practices in the in-app Lighthouse audit. Responsive checks used actual form submissions in Chrome, including keyboard and simulated touch. The UI uses local assets and a fixed light bench/dark readout palette, not a user-selectable theme.
- **Detector scope:** the changed-file scan included the handout and could not resolve the Jinja stylesheet in source, causing false heading-hierarchy findings. Rendered checks did not reproduce those findings. The detector's “nested cards” warning refers to the deliberately grouped `<dl>` readouts; it is not a schematic, layout, or results defect. Its mobile wrapping and tick-clearance findings were addressed.

### Model-independent checks

With `NGSPICE_BIN` set, all 34 tests passed, including the original 24. The passive ngspice probe intentionally replaces Q1 with a resistor **only inside the test**. It exercised `.op` (1 row), `.ac` (361 rows) and `.tran` (2,008 rows in the 1 kHz check), verified DC probe orientation against a resistor-network calculation, rejected truncated raw output, and checked the transient time scale and measured input amplitude. A separate passive RC check compares parsed AC gain and phase with the RC transfer function. This is adapter evidence only and does not satisfy B2–B6.

Impeccable critique, refinement and technical audit were conducted against the working interface. The student’s own review and GitHub URL/commit SHA are pending.

## 11. Final engineering and submission audit

Fresh runs used Python 3.14.2, Flask 3.1.3 and ngspice 47 on Windows. OpenCode Browser and installed Chrome at 1280×900 and 390×844 checked the current app on `127.0.0.1:5008`. B1–B8 were re-exercised using those real browsers; Playwright MCP remained **NOT RUN**. The SVGs, generated netlists, and browser results were checked independently of the prior reports.

### Engineering checks

| Item | Fresh audit evidence |
|---|---|
| Schematics vs. equations | Lab 03 Divider: R1 from supply to base, R2 from base to ground, RE in the emitter path. Fixed: RB from supply to base, emitter directly grounded. Emitter: RB from supply to base with RE to ground. RC feeds the collector in all three. The Lab 04 drawing adds Cin from Vin to base, Cout from collector to Vout, and RL from Vout to ground, with no emitter bypass. The generated netlist inserts an ideal 0 V `VSENSE` in series with Q1's collector as a current probe; it is electrically equivalent to the drawn wire. Q1 is NPN, with the emitter arrow facing outward. |
| Canonical units | The live default Ω and kΩ submissions generated identical SI netlists and DC results. VCC = 12 V; R1/R2/RC/RE/RL = 100,000/22,000/2,200/1,000/10,000 Ω; Cin/Cout = 10 µF = 10⁻⁵ F. `SIN` receives source amplitude in V peak and frequency in Hz. Raw vector names and dimensions are checked; display converts A to mA/µA and s/V to ms/mV as labeled. Bode gain uses V/V and dB; phase is in degrees. |
| Lab 03 regression | Independent base-node KCL and collector/emitter branch calculations matched all seven live readouts in each mode to within 0.0005 in the displayed unit. VCE/IC: Divider 8.052 V / 1.230 mA; Fixed 9.514 V / 1.130 mA; Emitter 8.705 V / 1.026 mA. The fixed emitter was 0 V; positive IC and the Active warning criteria remained unchanged. |
| Lab 04 DC consistency | With RE = 1 kΩ, independent `.op` gave VB = 1.967953686 V, VE = 1.336383612 V, VC = 9.083865683 V, VCE = 7.747482070 V and IC = 1.325515590 mA. VBE ≈ 0.632 V, VC > VB, and Vout = 0 V at DC. Positive IC matches `(VCC − VC)/RC`; divider-derived IB ≈ 10.868 µA and `IB + IC − VE/RE` was below 2 pA in magnitude for both RE values. Changing only RE to 2 kΩ yielded 8.990107078 V / 0.713541639 mA. |
| AC gain and sweep | ngspice independently emitted 361 samples from 0.1 Hz to 100 MHz, spaced 0.025 decades apart. At 1 kHz, `Vout/Vin = −1.737101486 − j0.003921840` → 1.737105913 V/V, 4.796525971 dB and −179.870644°. Each live SVG trace was checked against the independent complex data; no point differed by more than 0.005 SVG viewBox units. |
| Transient amplitude and frequency | At 10 mV peak / 1 kHz: 9.99845 mV Vin and 17.36807 mV Vout; frequency measured from positive-going Vin zero crossings was 1,000 Hz and the complex projection of the fundamental gave −179.8707°. Changing amplitude to 20 mV gave 19.99690 / 34.73607 mV. Changing only frequency to 2 kHz moved the browser window from 16–20 to 8–10 ms and measured 2,000 Hz, 17.36816 mV Vout, and −179.9386°. All 401 displayed samples per transient trace matched the independent data within 0.005 SVG units in each of the three cases. |
| Rejected runs | B7 confirmed HTTP 400 after a zero-RE submission and HTTP 502 after replacing only a scratch copy of the model with a declaration referencing an undefined parameter. The latter followed a successful AC run in the same tab; the log contained `Undefined parameter` and the failed response showed no plots or numeric readouts. The genuine model was restored. Local HTTP checks confirmed 503 for a missing engine after success; actual adapter runs exercised timeout and missing-result-file branches. |
| Defects corrected | Extreme finite Lab 03 inputs previously produced `nan`/`inf` readouts or a misleading finite Cutoff after a denominator overflow. They now return a separate HTTP 422 calculation error with no region or numeric result. Lab 03 validation ranges and equations are unchanged. The SPICE parser previously accepted altered raw vector dimensions and a sweep with missing interior samples; the regression suite now rejects wrong dimensions, missing rows, and off-grid frequencies. |
| Reproduction and repository | Used the README PowerShell download against the manufacturer endpoint; the Windows clean-copy exercise used only the candidate Git tree, the existing verified Python environment, ngspice, and the external model. Flask loaded and returned HTTP 200 for all three analyses; `pip check` reported no broken requirements. All **35 tests passed** in the working tree and clean copy, including all 34 pre-audit tests. macOS/Linux instructions were not executed. An old personal path was removed from a historical design note in the current tree; no history was rewritten. A scan of the candidate files found no personal-path or credential literals, vendored model, virtual environment, or generated raw/deck/log output. |

### Independent reproduction (local only)

Save the following as `check.cir` in a scratch folder alongside a separately downloaded, checksum-verified `2n3904.lib`. Do not add the vendor file or an inlined run deck to Git. Use `.include` here so the solver reads the original manufacturer file, not the app's parser output.

```spice
Lab 04 independent reference (no collector sense source)
VS p 0 12
R1 p b 100k
R2 b 0 22k
RC p c 2.2k
RE e 0 1k
RL out 0 10k
CIN in b 10u
COUT c out 10u
VIN in 0 DC 0 AC 1 SIN(0 10m 1k)
Q1 c b e Q2n3904
.include 2n3904.lib
.end
```

Before `.end`, insert a `.control`/`.endc` block containing `set numdgt=16`, `set wr_singlescale`, one of the command sequences below, and `quit`. Run `ngspice -n -b -o check.log check.cir` (or the configured console executable).

- DC: `op`, then `print v(b) v(e) v(c) v(c)-v(e) @q1[ic] v(out)`. Repeat with only RE changed to 2 kΩ.
- AC: `ac dec 40 .1 100Meg`, `let gain = v(out)/v(in)`, then `wrdata ac.dat gain`.
- Transient: `tran 10u 20m 0 10u`, then `wrdata tran.dat v(in) v(out)`. Read half peak-to-peak over the last four periods and frequency from upward Vin zero crossings. For 2 kHz use `SIN(0 10m 2k)` with `tran 5u 10m 0 5u`.
- Solver-failure reproduction: configure the app to use a separate temporary copy of the model and keep that path through both submissions. Run AC successfully, then replace the copy's declaration with a same-name NPN declaration that refers to an undefined parameter. Rerun AC and restore the genuine copy afterward. Do not edit the manufacturer's download.

### Handout rubric (provisional, not an instructor grade)

| Criterion | Demonstrated | Evidence / limit |
|---|---:|---|
| Lab 03 continuity | 1/1 | All three real browser paths and all seven quantities compared. |
| ngspice integration | 3/3 | Genuine `.op` and preserved raw dimensions, DC KCL/KVL, model and run provenance, tested failure paths. Credit assumes acceptance of the disclosed substitute. |
| AC and transient | 2/2 | Independent complex and time-domain data match the actual plotted samples. |
| UI and Impeccable | 2/2 | Before/after evidence, actual desktop and phone runs, and recorded critique/audit scores. |
| Browser acceptance | 1/1 | B1–B8 executed in the fallback browsers; Playwright MCP was unavailable and is not claimed. |
| GitHub and reproducibility | 0/1 pending | Clean-copy execution and reproduction steps are present, but this audit did not create a Lab 04 commit or push one. Repo URL and Lab 04 SHA remain submission items. |
| **Subtotal** | **9/10 provisional** | Ready for review and selective staging after approval. The student still needs to verify the evidence personally and the instructor/TA must decide whether the substitute and browser fallback satisfy their grading requirements. |

Manufacturer permission limit: the onsemi download contains a Symmetry Design Systems proprietary-software notice with commercial use or resale restricted. Public download is not a redistribution grant. No redistribution permission was verified, so the library and any inlined decks remain local. The instructor handout is also local and excluded from the prospective submission tree.
