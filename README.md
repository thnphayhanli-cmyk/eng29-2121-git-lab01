# BJT Common-Emitter Amplifier Simulator

**ENG29 2121 · Lab 02–04 · 2/2569**

เว็บแอปพลิเคชัน Flask สำหรับคำนวณจุดทำงาน DC (DC Operating Point) ของวงจรขยาย BJT แบบ Common-Emitter ภายใต้สมมติฐาน Forward-Active Approximation (β คงที่ และ VBE คงที่) รองรับ 3 รูปแบบไบอัสจากแหล่งจ่ายเดียว

## ขอบเขตของ Lab

- **Voltage Divider Bias** — คงสมการและผลลัพธ์เดิมของ Lab 02 ไว้ทั้งหมด
- **Fixed Bias** — ใช้ `RB` จาก VCC ไป base, `RC` จาก VCC ไป collector และ emitter ต่อ ground
- **Emitter Bias** — ใช้ `RB` จาก VCC ไป base, `RC` จาก VCC ไป collector และ `RE` จาก emitter ไป ground
- แสดงแผนภาพ Static ของแต่ละโหมด
- คำนวณ `VB`, `VE`, `VC`, `VCE`, `IC`, `IB`, `IE` ด้วย Python Backend
- ตรวจสอบข้อมูลนำเข้าและแสดงข้อความ Error ที่อ่านได้
- แจ้ง Warning เมื่อ `IB ≤ 0` หรือ `VCE ≤ 0.2 V` ตามเกณฑ์ Lab 03
- แสดงหน่วยกำกับทุกค่า และแปลง Ω/kΩ อย่างถูกต้อง
- **Lab 04:** เพิ่มหน้า CE Simulation สำหรับวงจร Voltage-Divider อ้างอิงเพียงวงจรเดียว ใช้ ngspice รัน `.op`, `.ac` และ `.tran` โดยแยกผลจาก Analytical Bias ทั้งสามโหมด
- ไม่รองรับ FET, Circuit Editor หรือการจำลอง AC/Transient ในโหมด Fixed Bias และ Emitter Bias

## โครงสร้างไฟล์

```text
.
├── app.py                  # Flask routes, form parsing, mode dispatch, unit conversion
├── dc_bias.py              # Pure engineering calculations (no Flask)
├── spice_engine.py         # CE netlist, ngspice process, and ASCII raw parser
├── spice_plots.py          # Measurements and SVG plot coordinates
├── templates/
│   ├── index.html          # Lab 03 analytical calculator
│   ├── simulate.html       # Lab 04 form, results, and plots
│   ├── bias_schematic.html # Lab 03 SVG schematic
│   ├── ce_reference.html   # Lab 04 SVG schematic
│   ├── instrument_header.html
│   └── bench_components.html
├── static/
│   ├── style.css           # Responsive presentation
│   ├── simulation.js      # Analysis controls, units, and running status
│   └── bench.svg          # Workspace favicon
├── tests/
│   ├── test_dc_bias.py     # Existing engineering tests
│   ├── test_spice_engine.py # Netlist, configuration, real ngspice transport
│   └── test_web.py         # Flask test-client tests
├── requirements.txt        # Flask dependency
├── README.md
├── AGENTS.md
├── docs/
│   ├── design-note.md      # เอกสารเดิมของ Lab 02 (historical)
│   ├── validation.md       # ตาราง A1–A5 ของ Lab 03
│   ├── reflection.md       # เอกสารเดิมของ Lab 02 (historical)
│   └── superpowers/
│       ├── plans/
│       └── specs/
├── electrical.py           # Lab 01 — retained, untouched
└── test_electrical.py      # Lab 01 — retained, untouched
```

## สิ่งที่ต้องมี

- Python 3.10 ขึ้นไป (ทดสอบด้วย Python 3.14)
- Git
- ไม่ต้องใช้ Node.js, ฐานข้อมูล หรือบริการภายนอก

## วิธีติดตั้งและรัน

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

หาก PowerShell ไม่อนุญาตให้ activate ให้รันคำสั่งนี้ในหน้าต่างปัจจุบันก่อน:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

หรือเรียก Python ใน virtual environment โดยตรง:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app run --debug
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

เปิดเบราว์เซอร์ที่:

```text
http://127.0.0.1:5000/
```

> สำคัญ: ต้องเปิดผ่าน Flask Server ตามคำสั่งด้านบน ไม่ใช่ Double-click เปิด `templates/index.html` โดยตรง เพราะไฟล์ HTML เป็นเพียง Template ที่ Server นำมาแสดง ผลคำนวณทั้งหมดเกิดใน Python Backend

### ตั้งค่า ngspice และ BJT model สำหรับ Lab 04

ติดตั้งโปรแกรม ngspice จาก [ngspice Downloads](https://ngspice.sourceforge.io/download.html) หากเครื่องยังไม่มี ไม่ต้องติดตั้งผ่าน `pip` เครื่องที่ตรวจใช้ ngspice 47

เมื่อไม่มี Starter Kit หรือโมเดลจากผู้สอน งานนี้ใช้ **onsemi 2N3904 (`Q2n3904`) เป็นโมเดลอ้างอิงทดแทน ไม่ใช่โมเดลที่ผู้สอนรับรอง** ดาวน์โหลดไฟล์ [2n3904.lib](https://www.onsemi.com/download/models/lib/2n3904.lib) โดยตรงจากผู้ผลิต ระบบใช้พารามิเตอร์เดิมทั้งหมด หัวไฟล์ระบุว่าเป็นซอฟต์แวร์กรรมสิทธิ์ และยังไม่พบสิทธิ์แจกไฟล์ต่อ จึงไม่รวมไฟล์นี้หรือ Netlist ที่ฝังพารามิเตอร์ไว้ใน GitHub

ตั้งค่าตัวแปรใน Terminal **ก่อน** รัน Flask แล้วเปิด `http://127.0.0.1:5000/simulate`:

```powershell
$env:NGSPICE_BIN = 'C:\path\to\ngspice_con.exe'
$env:BJT_MODEL_FILE = Join-Path $env:TEMP '2n3904.lib'
Invoke-WebRequest 'https://www.onsemi.com/download/models/lib/2n3904.lib' -OutFile $env:BJT_MODEL_FILE
Get-FileHash $env:BJT_MODEL_FILE -Algorithm SHA256
$env:BJT_MODEL_NAME = 'Q2n3904'
& $env:NGSPICE_BIN --version
.\.venv\Scripts\python.exe -m flask --app app run
```

SHA-256 ของไฟล์ที่ใช้ตรวจ: `5608c109b8d68d57798557991cee506661d031916f589325fad5ed10d82ccbf7` ดูหลักฐานและผลอ้างอิงใน [validation](docs/validation.md#10-lab-04--ce-simulation)

ตัวอย่าง macOS/Linux หลังเปิดใช้งาน `.venv` และติดตั้ง ngspice ใน `PATH` (การตรวจรันจริงในเอกสารนี้ใช้ Windows):

```bash
export BJT_MODEL_FILE="${TMPDIR:-/tmp}/2n3904.lib"
curl -fL 'https://www.onsemi.com/download/models/lib/2n3904.lib' -o "$BJT_MODEL_FILE"
export BJT_MODEL_NAME=Q2n3904
ngspice --version
python -m flask --app app run
```

หาก `ngspice` หรือ `ngspice_con` อยู่ใน `PATH` ไม่ต้องตั้ง `NGSPICE_BIN` สามารถเปลี่ยนไฟล์และชื่อโมเดลผ่านสองตัวแปรได้ ชื่อต้องตรงกับคำประกาศ `.model <name> NPN` ในไฟล์ รองรับบรรทัดต่อด้วย `+` แต่ไม่โหลด `.include`, `.lib` หรือ `.subckt` เพิ่มเติม หากตั้งค่าไม่ถูกต้อง หน้า Lab 04 จะแจ้งข้อผิดพลาดโดยไม่แทนผลด้วยค่าอื่น ส่วน Lab 03 ยังใช้งานได้ตามเดิม

- ค่าเริ่มต้นจากใบงาน Lab 04 ใน Moodle (`Lab04_BJT_Amplifier_Simulator_2-2569.html`): 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, RL 10 kΩ, Cin/Cout 10 µF และสัญญาณ 10 mV peak ที่ 1 kHz สำหรับ Transient ไฟล์ใบงานเป็นสำเนาเฉพาะเครื่องและไม่ต้องใช้รันแอป
- AC กวาด `0.1 Hz–100 MHz` บนแกนความถี่ลอการิทึม ใช้ `Vout / Vin` โดยวัด Vin ก่อน Cin และวัด Vout ที่ RL ไม่ประมาณจุดตัด −3 dB
- Transient รับ `1–100,000 Hz` รัน 20 คาบด้วยขนาดขั้นเวลาสูงสุด `period / 100` และแสดงตัวอย่างจริงในช่วงสี่คาบท้าย
- ตรวจซ้ำเฉพาะเครื่องโดยคัดลอก **Netlist used for this run** เป็น `circuit.cir` ในโฟลเดอร์ว่าง แล้วเรียก `& $env:NGSPICE_BIN -n -b -o run.log circuit.cir` (หรือ `ngspice -n -b -o run.log circuit.cir` เมื่อใช้ `PATH`) โปรแกรมจะเขียน `result.raw` เป็น ASCII และ `run.log` อย่าเผยแพร่ Netlist ที่ฝังโมเดล งานผ่านเว็บใช้โฟลเดอร์ชั่วคราวแยกแต่ละรอบและกำหนด timeout 10 วินาที

### การอ่านผลบนหน้าเว็บ

- Lab 03 และ Lab 04 ใช้หน้าควบคุมร่วมรูปแบบเดียวกัน แต่แยกผล Analytical ออกจากผล ngspice ชัดเจน เมื่อแก้ค่าอินพุต ผลเดิมจะขึ้นป้าย **Previous run** ตัวเลือก Ω/kΩ ใช้กับตัวต้านทานทุกตัวและไม่แปลงตัวเลขที่กรอกไว้
- DC แสดง `VCE` และ `IC` เป็นค่าหลัก พร้อมค่าที่โหนดและตารางเทียบกับสมมติฐาน Lab 03 ส่วน AC แยกกราฟ magnitude และ phase ที่ใช้แกนความถี่เดียวกัน และ Transient แยก Vin แบบเส้นประกับ Vout แบบเส้นทึบ
- ภาพจาก Chrome: [DC หลังปรับ](docs/captures/lab04-after-desktop-dc.png), [Bode ก่อน](docs/captures/lab04-before-desktop-ac.png) / [หลัง](docs/captures/lab04-after-desktop-ac.png), [Transient บนมือถือก่อน](docs/captures/lab04-before-mobile-tran.png) / [หลัง](docs/captures/lab04-after-mobile-tran.png) รายละเอียดการตรวจรับอยู่ใน [validation](docs/validation.md#10-lab-04--ce-simulation)

**บันทึก Lab 04**

- AI ช่วยเชื่อม Flask กับ ngspice, เขียนตัวอ่านผล และเพิ่มหน้าแสดงผลพร้อมการทดสอบ
- ตรวจผลวงจร BJT ด้วย ngspice และเทียบกับการรัน Netlist อ้างอิงแยกต่างหาก รวมถึงทดสอบการทำงานเดิม
- นักศึกษาควรตรวจที่มาของโมเดลทดแทนและทวนกราฟ/หน่วยด้วยตนเองก่อนส่งงาน

## วิธีรัน Tests

จากโฟลเดอร์โปรเจกต์:

```bash
python -m unittest discover -s tests -v
```

บน Windows หากไม่ได้ activate virtual environment:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

ผลตรวจสุดท้ายผ่าน 35 รายการ รวม 34 รายการก่อนตรวจและกรณีป้องกันผลคำนวณเกินช่วงตัวเลข ไม่ต้องใช้โมเดล onsemi สำหรับชุดทดสอบนี้ แต่ต้องตั้ง `NGSPICE_BIN` หรือมี ngspice ใน `PATH` เพื่อไม่ให้ข้ามการทดสอบกับโปรแกรมจริง การทดสอบ Passive ไม่ใช่การยืนยันผลของวงจร BJT; ดู [ผลตรวจจริง](docs/validation.md#11-final-engineering-and-submission-audit)

## ค่าเริ่มต้นสำหรับสาธิต

| โหมด | ค่าเริ่มต้น |
|---|---|
| Voltage Divider | VCC 12 V, R1 100000 Ω, R2 22000 Ω, RC 2200 Ω, RE 1000 Ω, β 100, VBE 0.70 V |
| Fixed Bias | VCC 12 V, RB 1000000 Ω, RC 2200 Ω, β 100, VBE 0.70 V |
| Emitter Bias | VCC 12 V, RB 1000000 Ω, RC 2200 Ω, RE 1000 Ω, β 100, VBE 0.70 V |

หน่วยมาตรฐานของความต้านทานในระบบคือ **โอห์ม (Ω)** ฟอร์มมีตัวเลือกหน่วย `Ω` หรือ `kΩ` โดยจะแปลงเป็น Ω ก่อนคำนวณทุกครั้ง และแสดงค่าที่แปลงแล้วในผลลัพธ์

## แบบจำลองทางวิศวกรรม

### Voltage Divider Bias — คงเดิม

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

ผลลัพธ์ที่แสดง:

- `VB`, `VE`, `VC`, `VCE` หน่วย V
- `IC`, `IE` หน่วย mA
- `IB` หน่วย µA

## การตรวจสอบและ Warning

- ข้อมูลที่ขาดหายหรือไม่ใช่ตัวเลขจะแสดง Error และไม่ทำให้หน้าเว็บล้ม
- `VCC ≤ 0`, ความต้านทานใด ๆ ที่โหมดนั้นใช้ `≤ 0`, หรือ `β ≤ 0` จะแสดง Error
- ไม่มีการเพิ่มข้อจำกัดช่วงของ `VBE` นอกเหนือจากที่โจทย์กำหนด
- ถ้า `IB ≤ 0` จะแสดง Warning ว่า Forward-Active Approximation อาจใช้ไม่ได้ (Cutoff)
- ถ้า `VCE ≤ 0.2 V` จะแสดง Warning ว่า Forward-Active Approximation อาจใช้ไม่ได้ (Saturation)
- Warning ไม่ใช่ Input Error: ยังแสดงผลจากสมการและตอบ HTTP 200
- ผลที่อยู่นอก Active Region ยังแสดงค่าจากสมการ Forward-Active ได้ แต่จะถูกกำกับชัดเจนว่า **ไม่ใช่ Operating Point ที่ตรวจสอบแล้ว**

รายละเอียดการคำนวณอ้างอิงและตาราง A1–A5 อยู่ใน [`docs/validation.md`](docs/validation.md)

## สิ่งที่ AI ช่วยสร้าง และสิ่งที่นักศึกษาตรวจสอบ

ตามหัวข้อ **07 / Deliverables & grading** ของใบงาน Lab 03:

**AI ช่วยสร้าง**
- ฟังก์ชัน `calculate_fixed_bias()` และ `calculate_emitter_bias()` ใน `dc_bias.py` พร้อม dataclass `FixedBiasInput`, `EmitterBiasInput` และผลลัพธ์ dict ที่ใช้ชื่อคีย์/หน่วยร่วมกัน
- ปรับ `app.py`: แยกกรณีไม่ส่ง `mode` (default Divider เพื่อรองรับ Lab 02) กับส่ง `mode` ที่ไม่รู้จัก (HTTP 400, ไม่ fallback เป็น Divider), ตรวจเฉพาะฟิลด์ของโหมดนั้น, แปลง Ω/kΩ และเติมชื่อโหมดในข้อความ error
- ปรับ `templates/index.html`: เลือกโหมดแล้วโหลดฟอร์มใหม่, ซ่อนช่องที่ไม่ใช้, ไม่แสดงผลรอบก่อนตอน error และแสดงชื่อโหมดในผล/error
- รัน OpenCode Browser เก็บผล A1–A5 และช่วยเขียน `docs/validation.md`

**นักศึกษาตรวจสอบ**
- ทวนสมการ `IB`, `IC`, `IE` และ `VCE` ของทั้งสามโหมดกับที่เรียน Engineering Electronics ว่าตรงใบงาน และสมการ Divider เดิมไม่ถูกเปลี่ยน
- ตรวจหน่วย V/A/Ω, การแปลง kΩ → Ω ที่ขอบระบบครั้งเดียว และชื่อคีย์ dict ที่แต่ละฟังก์ชันคืน
- คำนวณค่าคาดหมายอิสระก่อนรัน (ไม่นำค่าจากโปรแกรมที่กำลังตรวจ) แล้วเทียบกับผลบนหน้าเว็บตาม tolerance `IC ±0.01 mA`, `VCE ±0.02 V`
- ทวนหลักฐานจาก Browser เองอย่างน้อยหนึ่งกรณี และยืนยันว่า A5 เป็นการตรวจใน Flask ไม่ใช่แค่การบล็อกที่ฟอร์ม
- รัน tests เดิม 24 ตัว และตรวจ `git diff` / `git diff --staged` ก่อน Commit

## ตำแหน่ง mode dispatch และการแปลงหน่วย

ตามหัวข้อ **07 / Deliverables & grading** ที่ต้องระบุว่าโค้ดเลือกฟังก์ชันและแปลงหน่วยอยู่ตรงไหน:

- **เลือกโหมด:** `app.py::parse_mode()` อ่านค่าจากฟอร์ม — ไม่ส่งหรือว่าง → `divider` (รองรับ Lab 02), ค่าที่รู้จัก → โหมดนั้น, ค่าอื่น → error และไม่เลือก Divider ให้ เรียกใช้ใน `index()` และ `calculate()`
- **เรียกฟังก์ชันคำนวณ:** `app.py::calculate()` ในบล็อก `if mode == MODE_DIVIDER / elif mode == MODE_FIXED / else` เรียก `calculate_divider_bias()`, `calculate_fixed_bias()` และ `calculate_emitter_bias()` ตามลำดับ
- **ตรวจฟิลด์ตามโหมด:** `MODE_REQUIRED_FIELDS`, `MODE_RESISTOR_FIELDS` และ `parse_form()` ใน `app.py`
- **แปลงหน่วย:** `RESISTOR_UNIT_MULTIPLIERS = {"ohm": 1.0, "kohm": 1000.0}` ใน `app.py`; คูณ `factor` กับความต้านทานตอนสร้าง dataclass ใน `calculate()` **ครั้งเดียว** ก่อนส่งเข้า `dc_bias.py` ซึ่งเก็บหน่วย V, A, Ω เสมอ; `format_resistance()` / `_normalized_resistances()` แสดงค่า Ω และ kΩ เพื่อตรวจย้อนกลับ; `templates/index.html` แปลง A → mA/µA เฉพาะตอนแสดงผล
- **error ระบุโหมด:** `MODE_LABELS` ถูกส่งเป็น `mode_label` เข้า template แล้วเติมชื่อโหมดในข้อความ error

## ข้อจำกัดของ Analytical Bias (Lab 03)

- เป็นการวิเคราะห์ DC Bias เท่านั้น
- β และ VBE ถูกถือว่าคงที่
- ไม่ได้จำลอง SPICE, Thermal Effect, Early Effect, AC Gain, Transient หรือ Frequency Response; ใช้หน้า CE Simulation สำหรับ Lab 04 แยกต่างหาก
- ค่า `VCE ≤ 0.2 V` เป็นเกณฑ์ Warning ตาม Lab 03 ไม่ใช่แบบจำลอง Saturation ที่แม่นยำ
- ไม่มี Solver แยกสำหรับ Cutoff/Saturation และไม่ clamp กระแสเป็นศูนย์

## Lab 01

ไฟล์ `electrical.py` และ `test_electrical.py` จาก Lab 01 ยังคงอยู่ใน Repository ตามเดิมและไม่ถูกแก้ไข

## เอกสารเพิ่มเติม

- [`docs/design-note.md`](docs/design-note.md) — **เอกสารเดิมของ Lab 02 (historical)** เกณฑ์ region ในไฟล์นี้เป็นของ Lab 02 ไม่ใช่เกณฑ์ Lab 03
- [`docs/validation.md`](docs/validation.md) — หลักฐานการตรวจ Lab 03 และสถานะการตรวจรับ B1–B8 ของ Lab 04
- [`docs/reflection.md`](docs/reflection.md) — **Reflection เดิมของ Lab 02 (historical)** ไม่ได้อัปเดตเกณฑ์ Lab 03
- [`docs/superpowers/specs/2026-11-11-bjt-dc-bias-design.md`](docs/superpowers/specs/2026-11-11-bjt-dc-bias-design.md) — Design Document เดิม
- [`docs/superpowers/specs/2026-11-17-bias-modes-design.md`](docs/superpowers/specs/2026-11-17-bias-modes-design.md) — Design Document ของโหมดใหม่
- [`docs/superpowers/plans/2026-11-17-bias-modes.md`](docs/superpowers/plans/2026-11-17-bias-modes.md) — Implementation Plan ของโหมดใหม่
