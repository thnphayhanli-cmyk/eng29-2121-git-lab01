# BJT Common-Emitter DC Bias Web App

**ENG29 2121 · Lab 02 · 2/2569**

เว็บแอปพลิเคชัน Flask สำหรับคำนวณจุดทำงาน DC (DC Operating Point) ของวงจรขยาย BJT แบบ Common-Emitter ที่ใช้ Voltage-Divider Bias ภายใต้สมมติฐาน Forward-Active Approximation (β คงที่ และ VBE คงที่)

## ขอบเขตของ Lab 02

- รับค่า `VCC`, `R1`, `R2`, `RC`, `RE`, `β`, `VBE`
- คำนวณ `VB`, `VE`, `VC`, `VCE`, `IC` พร้อมแสดง `IB` และ `IE` ด้วย Python Backend
- ตรวจสอบข้อมูลนำเข้าและแสดงข้อความ Error ที่อ่านได้
- แจ้ง Warning เมื่อผลอยู่นอก Forward-Active Region (Cutoff / Saturation)
- แสดงหน่วยกำกับทุกค่า และแปลง Ω/kΩ อย่างถูกต้อง
- ไม่มี AC, Transient, Bode Plot, SPICE, FET หรือ Circuit Editor ใน Lab นี้

## โครงสร้างไฟล์

```text
.
├── app.py                  # Flask routes, form parsing, unit conversion
├── dc_bias.py              # Pure engineering calculations (no Flask)
├── templates/
│   └── index.html          # Jinja form, results, warnings
├── static/
│   └── style.css           # Responsive presentation
├── tests/
│   ├── test_dc_bias.py     # Engineering math, validation, region tests
│   └── test_web.py         # Flask test-client HTTP tests
├── requirements.txt        # Flask dependency
├── README.md
├── AGENTS.md
├── docs/
│   ├── design-note.md
│   ├── validation.md
│   └── reflection.md
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

ผลที่คาดหวัง: `Ran 20 tests` และ `OK`

## ค่าเริ่มต้นสำหรับสาธิต

| พารามิเตอร์ | ค่า |
|---|---|
| VCC | 12 V |
| R1 | 100000 Ω (100 kΩ) |
| R2 | 22000 Ω (22 kΩ) |
| RC | 2200 Ω (2.2 kΩ) |
| RE | 1000 Ω (1 kΩ) |
| β | 100 |
| VBE | 0.70 V |

หน่วยมาตรฐานของความต้านทานในระบบคือ **โอห์ม (Ω)** ฟอร์มมีตัวเลือกหน่วย `Ω` หรือ `kΩ` สำหรับความสะดวก โดยจะแปลงเป็น Ω ก่อนคำนวณทุกครั้ง และแสดงค่าที่แปลงแล้วในผลลัพธ์

## แบบจำลองทางวิศวกรรม

ใช้สมการ Forward-Active Approximation ตามโจทย์ Lab 02:

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

ผลลัพธ์ที่แสดง:

- `VB`, `VE`, `VC`, `VCE` หน่วย V
- `IC`, `IE` หน่วย mA
- `IB` หน่วย µA

## การตรวจสอบและ Warning

- ข้อมูลที่ขาดหายหรือไม่ใช่ตัวเลขจะแสดง Error และไม่ทำให้หน้าเว็บล้ม
- `VCC ≤ 0`, ความต้านทานใด ๆ `≤ 0`, หรือ `β ≤ 0` จะแสดง Error
- ไม่มีการเพิ่มข้อจำกัดช่วงของ `VBE` นอกเหนือจากที่โจทย์กำหนด
- ถ้า `VTH ≤ VBE` จะแสดง Warning ว่าเข้าสู่ Cutoff
- ถ้า `VCE < 0.3 V` จะแสดง Warning ว่าเข้าสู่ Saturation หรือใกล้ Saturation
- ผลที่อยู่นอก Active Region ยังแสดงค่าจากสมการ Forward-Active ได้ แต่จะถูกกำกับชัดเจนว่า **ไม่ใช่ Operating Point ที่ตรวจสอบแล้ว**

รายละเอียดการคำนวณอ้างอิงแบบมือและตารางเปรียบเทียบอยู่ใน [`docs/validation.md`](docs/validation.md)

## ข้อจำกัด

- เป็นการวิเคราะห์ DC Bias เท่านั้น
- β และ VBE ถูกถือว่าคงที่
- ไม่ได้จำลอง SPICE, Thermal Effect, Early Effect, AC Gain, Transient หรือ Frequency Response
- ค่า `VCE(sat) ≈ 0.3 V` เป็นเกณฑ์ Warning แบบตำรา ไม่ใช่แบบจำลอง Saturation ที่แม่นยำ

## Lab 01

ไฟล์ `electrical.py` และ `test_electrical.py` จาก Lab 01 ยังคงอยู่ใน Repository ตามเดิมและไม่ถูกแก้ไข โปรเจกต์ Lab 02 อยู่ในไฟล์และโฟลเดอร์ใหม่ตามโครงสร้างด้านบน

## เอกสารเพิ่มเติม

- [`docs/design-note.md`](docs/design-note.md) — สรุปการออกแบบ
- [`docs/validation.md`](docs/validation.md) — การคำนวณอ้างอิงและผลตรวจสอบ
- [`docs/reflection.md`](docs/reflection.md) — Reflection ของ Lab
- [`docs/superpowers/specs/2026-11-11-bjt-dc-bias-design.md`](docs/superpowers/specs/2026-11-11-bjt-dc-bias-design.md) — Design Document
- [`docs/superpowers/plans/2026-11-11-bjt-dc-bias.md`](docs/superpowers/plans/2026-11-11-bjt-dc-bias.md) — Implementation Plan
