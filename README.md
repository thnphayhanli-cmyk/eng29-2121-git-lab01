# BJT Common-Emitter DC Bias Web App

**ENG29 2121 · Lab 02 / Lab 03 · 2/2569**

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
- ไม่มี AC, Transient, Bode Plot, SPICE, FET หรือ Circuit Editor

## โครงสร้างไฟล์

```text
.
├── app.py                  # Flask routes, form parsing, mode dispatch, unit conversion
├── dc_bias.py              # Pure engineering calculations (no Flask)
├── templates/
│   └── index.html          # Jinja form, mode navigation, results, warnings
├── static/
│   └── style.css           # Responsive presentation
├── tests/
│   ├── test_dc_bias.py     # Existing engineering tests
│   └── test_web.py         # Existing Flask test-client tests
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

## วิธีรัน Tests

จากโฟลเดอร์โปรเจกต์:

```bash
python -m unittest discover -s tests -v
```

บน Windows หากไม่ได้ activate virtual environment:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

ผลที่คาดหวัง: `Ran 24 tests` และ `OK` (tests เดิมทั้งหมด ไม่มีการเพิ่ม unittest ใหม่)

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

## ข้อจำกัด

- เป็นการวิเคราะห์ DC Bias เท่านั้น
- β และ VBE ถูกถือว่าคงที่
- ไม่ได้จำลอง SPICE, Thermal Effect, Early Effect, AC Gain, Transient หรือ Frequency Response
- ค่า `VCE ≤ 0.2 V` เป็นเกณฑ์ Warning ตาม Lab 03 ไม่ใช่แบบจำลอง Saturation ที่แม่นยำ
- ไม่มี Solver แยกสำหรับ Cutoff/Saturation และไม่ clamp กระแสเป็นศูนย์

## Lab 01

ไฟล์ `electrical.py` และ `test_electrical.py` จาก Lab 01 ยังคงอยู่ใน Repository ตามเดิมและไม่ถูกแก้ไข

## เอกสารเพิ่มเติม

- [`docs/design-note.md`](docs/design-note.md) — **เอกสารเดิมของ Lab 02 (historical)** เกณฑ์ region ในไฟล์นี้เป็นของ Lab 02 ไม่ใช่เกณฑ์ Lab 03
- [`docs/validation.md`](docs/validation.md) — การคำนวณอ้างอิงและตารางตรวจสอบ A1–A5 ตามใบงาน Lab 03
- [`docs/reflection.md`](docs/reflection.md) — **Reflection เดิมของ Lab 02 (historical)** ไม่ได้อัปเดตเกณฑ์ Lab 03
- [`docs/superpowers/specs/2026-11-11-bjt-dc-bias-design.md`](docs/superpowers/specs/2026-11-11-bjt-dc-bias-design.md) — Design Document เดิม
- [`docs/superpowers/specs/2026-11-17-bias-modes-design.md`](docs/superpowers/specs/2026-11-17-bias-modes-design.md) — Design Document ของโหมดใหม่
- [`docs/superpowers/plans/2026-11-17-bias-modes.md`](docs/superpowers/plans/2026-11-17-bias-modes.md) — Implementation Plan ของโหมดใหม่
