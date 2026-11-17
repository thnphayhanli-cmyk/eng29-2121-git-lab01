# BJT Bias Modes — Design

- **Course:** ENG29 2121, Lab 02 / Lab 03 warning criteria
- **Date:** 2026-11-17
- **Status:** Approved in conversation; implementation in progress
- **Scope:** Add Fixed Bias and single-supply Emitter Bias to the existing Flask DC bias app while preserving the existing Voltage Divider behaviour.

## 1. Intent

The existing app calculates only voltage-divider bias. The extension adds two additional common-emitter bias topologies:

1. **Voltage Divider Bias** — unchanged equations, defaults, result values, and tests.
2. **Fixed Bias** — `RB` from VCC to base, `RC` from VCC to collector, emitter grounded.
3. **Emitter Bias** — `RB` from VCC to base, `RC` from VCC to collector, `RE` from emitter to ground.

All modes are DC forward-active calculations using a single supply. No AC, transient, SPICE, FET, circuit editor, database, authentication, or JavaScript framework is added.

## 2. Goals

- Preserve the existing Divider result exactly, including A1 (`IC = 1.230 mA`, `VCE = 8.052 V`).
- Keep the existing `BiasInput`, `BiasResult`, `calculate_dc_bias()`, and all existing tests working unchanged.
- Put all new engineering equations in `dc_bias.py`.
- Return a common dictionary shape from every mode with matching keys and canonical units.
- Select the correct calculator and validation rules from the submitted mode.
- Use the Lab 03 warning criteria: `IB <= 0` or `VCE <= 0.2 V` produces a warning, never an input error.
- Verify through the browser after implementation. Do not create new `unittest` tests.
- Do not commit or push until the user explicitly authorises it.

## 3. Non-goals

- No new automated tests.
- No AC small-signal analysis, gain, load line, transient, or frequency response.
- No separate cutoff/saturation solver and no clamping of equation output.
- No VBE range validation.
- No change to Lab 01 files.

## 4. Common result contract

Every mode returns:

```python
{
    "mode": "Divider" | "Fixed" | "Emitter",
    "vb_v": float,
    "ve_v": float,
    "vc_v": float,
    "vce_v": float,
    "ib_a": float,
    "ic_a": float,
    "ie_a": float,
    "region": "Active" | "Cutoff" | "Saturation",
    "warnings": tuple[str, ...],
}
```

Canonical units are V, A, and Ω. The template converts A to mA/µA only for display.

## 5. Equations

### Divider — unchanged

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

### Fixed Bias

```text
IB  = (VCC − VBE) / RB
IC  = β · IB
IE  = (β + 1) · IB
VE  = 0
VB  = VBE
VC  = VCC − IC · RC
VCE = VC
```

### Emitter Bias

```text
IB  = (VCC − VBE) / (RB + (β + 1) · RE)
IC  = β · IB
IE  = (β + 1) · IB
VE  = IE · RE
VB  = VE + VBE
VC  = VCC − IC · RC
VCE = VC − VE
```

## 6. Validation and warnings

Common validation:

- Missing/blank or non-numeric fields.
- Non-finite numeric values.
- `VCC <= 0`.
- Every resistance used by the selected mode `<= 0`.
- `beta <= 0`.
- `VBE` finite only; no range restriction.

Mode-specific required fields:

| Mode | Required fields |
|---|---|
| Divider | `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe` |
| Fixed | `vcc`, `rb`, `rc`, `beta`, `vbe` |
| Emitter | `vcc`, `rb`, `rc`, `re`, `beta`, `vbe` |

Warning classification:

- `IB <= 0` → `Cutoff`; warning says the forward-active approximation is not valid.
- Otherwise `VCE <= 0.2 V` → `Saturation`; warning says the forward-active approximation is not valid.
- Otherwise → `Active`; no warning.

Warnings remain HTTP 200 and are visually separate from input errors (HTTP 400).

## 7. UI

- A server-rendered mode navigation with three links: Divider, Fixed, Emitter.
- The selected mode is carried in a hidden form field.
- Only fields required by the selected mode are rendered and required.
- The existing divider SVG remains unchanged for the divider mode; fixed and emitter modes get simple static SVGs.
- The result table keeps the existing V/mA/µA presentation.

## 8. Verification

- Run all 24 existing tests after implementation.
- Run the Flask app and verify A1–A5 in the browser.
- Record only observed browser results in `docs/validation.md`; no PASS claim before the browser check.
- Do not commit or push.

## 9. Decisions

| Decision | Choice | Reason |
|---|---|---|
| Divider compatibility | Keep old dataclasses and function untouched; add dict wrapper | Existing tests and A1 values must not change |
| New mode inputs | Separate frozen dataclasses | Avoid forcing unused divider fields |
| Result shape | Common dict | Same keys and units across modes |
| Mode selection | Server-rendered links + hidden field | No JavaScript framework needed |
| Warning threshold | `IB <= 0` or `VCE <= 0.2 V` | Lab 03 criteria |
| Out-of-region output | Show equation output with warning, no clamping | Matches existing behaviour |
| Tests | Existing tests only | User requirement |
| Git | No commit/push | User requirement |
