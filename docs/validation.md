# Validation — Lab 02 DC Bias

## 1. Independent Hand Calculation

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

## 2. Reference Comparison

The “App value” column comes from `dc_bias.calculate_dc_bias()` with the default input.

| Quantity | Hand value | App value | Difference | Result |
|---|---:|---:|---:|---|
| VTH | 2.163934 V | 2.163934 V | 0.000000 V | Pass |
| RTH | 18032.786885 Ω | 18032.786885 Ω | 0.000000 Ω | Pass |
| IB | 12.298581 µA | 12.298581 µA | 0.000000 µA | Pass |
| IC | 1.229858 mA | 1.229858 mA | 0.000000 mA | Pass |
| IE | 1.242157 mA | 1.242157 mA | 0.000000 mA | Pass |
| VE | 1.242157 V | 1.242157 V | 0.000000 V | Pass |
| VB | 1.942157 V | 1.942157 V | 0.000000 V | Pass |
| VC | 9.294312 V | 9.294312 V | 0.000000 V | Pass |
| VCE | 8.052155 V | 8.052155 V | 0.000000 V | Pass |

The automated reference tests are:

- `test_default_operating_point_matches_hand_calculation`
- `test_independent_ie_formula_matches_module` — uses the algebraically rearranged form `IE = (VTH − VBE) / (RTH/(β+1) + RE)`.

## 3. Validation Cases

| Case | Input change | Expected result |
|---|---|---|
| Default active | None | HTTP 200; Active; values in the table above |
| Missing resistor | `R1 = ""` | HTTP 400; “Enter a value.” |
| Non-numeric beta | `β = "abc"` | HTTP 400; “Enter a number.” |
| Zero resistor | `R1 = 0` | HTTP 400; “R1 must be greater than zero.” |
| Zero beta | `β = 0` | HTTP 400; “Beta must be greater than zero.” |
| Zero VCC | `VCC = 0` | HTTP 400; “VCC must be greater than zero.” |
| Invalid unit | `resistor_unit = "mohm"` | HTTP 400; “Choose Ω or kΩ.” |
| kΩ equivalence | `R1=100`, `R2=22`, `RC=2.2`, `RE=1`, unit `kΩ` | Same operating point as the default Ω values |
| Cutoff | `R2 = 5000 Ω` | HTTP 200; Cutoff warning; `VTH ≤ VBE` |
| Saturation | `RC = 10000 Ω` | HTTP 200; Saturation warning; `VCE < 0.3 V` |
| Negative VBE | `VBE = −0.5 V` | No validation error; calculation proceeds |
| VBE above VCC | `VBE = 20 V` | No validation error; Cutoff warning |

The last two cases pin the approved decision not to add a VBE range restriction beyond the handout.

## 4. Test Log

Command:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Result:

```text
Ran 20 tests in 0.053s

OK
```

Breakdown:

- 11 engineering tests in `tests/test_dc_bias.py`
- 9 Flask HTTP tests in `tests/test_web.py`

## 5. Scope Note

This comparison is documentation and automated-test evidence only. It is intentionally not displayed as an extra reference table in the web UI, to keep the Lab 02 scope minimal.
