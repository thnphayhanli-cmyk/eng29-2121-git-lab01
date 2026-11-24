"""Run the Lab 04 CE reference circuit with ngspice, independent of Flask."""

import math
import re
import subprocess
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory


TRANSIENT_FREQUENCY_HZ = (1, 100_000)
TRANSIENT_CYCLES = 20
PLOT_CYCLES = 4
AC_START_HZ = 0.1
AC_STOP_HZ = 100_000_000
AC_POINTS_PER_DECADE = 40
MAX_RAW_POINTS = 40_000
MAX_RAW_BYTES = 8_000_000
MAX_LOG_BYTES = 16_000
_ONSEMI_2N3904 = "5608c109b8d68d57798557991cee506661d031916f589325fad5ed10d82ccbf7"


class SpiceError(Exception):
    def __init__(self, message: str, log: str = ""):
        super().__init__(message)
        self.log = log


class SpiceUnavailable(SpiceError):
    """An external prerequisite is missing or unusable."""


@dataclass(frozen=True)
class Circuit:
    vcc_v: float
    r1_ohm: float
    r2_ohm: float
    rc_ohm: float
    re_ohm: float
    rl_ohm: float
    cin_f: float
    cout_f: float


@dataclass(frozen=True)
class SineSource:
    amplitude_v: float
    frequency_hz: float


@dataclass(frozen=True)
class Model:
    name: str
    filename: str
    statement: str
    reference: str = ""


@dataclass(frozen=True)
class OperatingPoint:
    vb_v: float
    ve_v: float
    vc_v: float
    vce_v: float
    ic_a: float


@dataclass(frozen=True)
class ACPoint:
    frequency_hz: float
    gain: complex


@dataclass(frozen=True)
class TransientPoint:
    time_s: float
    vin_v: float
    vout_v: float


@dataclass(frozen=True)
class Simulation:
    data: OperatingPoint | tuple[ACPoint, ...] | tuple[TransientPoint, ...]
    model: Model
    version: str
    netlist: str
    log: str
    points: int


def load_model(filename: str, name: str) -> Model:
    """Select one self-contained .model statement from the configured file."""
    if not filename or not name:
        raise SpiceUnavailable("BJT model not configured. Set BJT_MODEL_FILE and BJT_MODEL_NAME.")
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", name):
        raise SpiceUnavailable("BJT_MODEL_NAME must be a single ngspice model identifier.")
    path = Path(filename).expanduser()
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")
    except (OSError, UnicodeError, ValueError) as error:
        raise SpiceUnavailable("Cannot read BJT_MODEL_FILE. Check its path and text encoding.") from error

    # Inline only the named declaration, not .include paths or unrelated directives.
    declaration = re.compile(r"^\s*\.model\s+(\S+)\s+NPN(?=\s|\(|$)", re.IGNORECASE)
    matches = []
    current = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("*"):
            continue
        if current is not None and line.startswith("+"):
            current.append(line)
            continue
        current = None
        match = declaration.match(line)
        if match and match[1].casefold() == name.casefold():
            current = [line]
            matches.append(current)
    if len(matches) != 1:
        raise SpiceUnavailable("BJT_MODEL_FILE must contain exactly one matching .model <name> NPN declaration.")
    reference = (
        "onsemi 2N3904 · substitute reference"
        if name.casefold() == "q2n3904" and sha256(raw).hexdigest() == _ONSEMI_2N3904
        else ""
    )
    return Model(name, path.name, "\n".join(matches[0]), reference)


def build_netlist(circuit: Circuit, model: Model, analysis: str, source: SineSource | None = None) -> str:
    """Generate a fixed circuit; only validated numeric inputs enter component lines."""
    c = circuit
    if not all(math.isfinite(value) and value > 0 for value in vars(c).values()):
        raise SpiceError("Circuit values must be positive finite numbers.")

    excitation = "DC 0 AC 1"
    if analysis == "dc":
        directive = ".op"
        vectors = "v(e) v(c) i(vsense)"
        # OP has no independent scale. Choose VB rather than relying on node order.
        scale = "setscale v(b)\n"
    elif analysis == "ac":
        directive = f".ac dec {AC_POINTS_PER_DECADE} {AC_START_HZ:.16g} {AC_STOP_HZ:.16g}"
        vectors = "v(in) v(out)"
        scale = ""
    elif analysis == "tran":
        low_hz, high_hz = TRANSIENT_FREQUENCY_HZ
        if (source is None or not low_hz <= source.frequency_hz <= high_hz
                or not math.isfinite(source.amplitude_v) or source.amplitude_v <= 0):
            raise SpiceError("Transient simulation requires a valid sine source.")
        period_s = 1 / source.frequency_hz
        step_s = period_s / 100
        excitation = f"SIN(0 {source.amplitude_v:.16g} {source.frequency_hz:.16g})"
        directive = f".tran {step_s:.16g} {TRANSIENT_CYCLES * period_s:.16g} 0 {step_s:.16g}"
        vectors = "v(in) v(out)"
        scale = ""
    else:
        raise SpiceError("Unknown simulation analysis.")

    return (
        "Lab 04 CE voltage-divider reference\n"
        f"VCC vcc 0 {c.vcc_v:.16g}\n"
        f"R1 vcc b {c.r1_ohm:.16g}\n"
        f"R2 b 0 {c.r2_ohm:.16g}\n"
        f"RC vcc c {c.rc_ohm:.16g}\n"
        f"RE e 0 {c.re_ohm:.16g}\n"
        f"RL out 0 {c.rl_ohm:.16g}\n"
        f"VIN in 0 {excitation}\n"
        f"CIN in b {c.cin_f:.16g}\n"
        f"COUT c out {c.cout_f:.16g}\n"
        "* Positive i(VSENSE) flows from RC into the collector of Q1.\n"
        "VSENSE c qc 0\n"
        f"Q1 qc b e {model.name}\n"
        f"{model.statement}\n"
        f"{directive}\n"
        ".control\nset filetype=ascii\nrun\n"
        f"{scale}write result.raw {vectors}\n"
        "quit\n.endc\n.end\n"
    )


_RAW_FORMAT = {
    "dc": ("operating point", "real", (
        ("v(b)", "voltage"), ("v(e)", "voltage"), ("v(c)", "voltage"), ("i(vsense)", "current"),
    )),
    "ac": ("ac analysis", "complex", (
        ("frequency", "frequency"), ("v(in)", "voltage"), ("v(out)", "voltage"),
    )),
    "tran": ("transient analysis", "real", (
        ("time", "time"), ("v(in)", "voltage"), ("v(out)", "voltage"),
    )),
}


def _number(token: str, complex_mode: bool) -> float | complex:
    if complex_mode:
        real, imag = map(float, token.split(","))
        if math.isfinite(real) and math.isfinite(imag):
            return complex(real, imag)
    else:
        value = float(token)
        if math.isfinite(value):
            return value
    raise ValueError("non-finite raw value")


def parse_raw(text: str, analysis: str) -> tuple[str, list[tuple]]:
    """Read one ngspice ASCII plot, checking headers, vector names and all samples."""
    plot_name, flags, vectors = _RAW_FORMAT[analysis]
    try:
        header_text, values_text = text.split("\nValues:\n", 1)
        headers_text, variables_text = header_text.split("\nVariables:\n", 1)
        headers = {}
        for line in headers_text.splitlines():
            key, sep, value = line.partition(":")
            if sep:
                headers[key.casefold()] = value.strip()
        if headers["plotname"].casefold() != plot_name or headers["flags"].casefold() != flags:
            raise ValueError("unexpected analysis or data type")
        if int(headers["no. variables"]) != len(vectors):
            raise ValueError("unexpected variable count")
        variables = [line.split() for line in variables_text.splitlines() if line.strip()]
        if (tuple((row[1].casefold(), row[2].casefold()) for row in variables) != vectors
                or [int(row[0]) for row in variables] != list(range(len(vectors)))):
            raise ValueError("unexpected variable names or units")
        count = int(headers["no. points"])
        if (analysis == "dc" and count != 1) or not 1 <= count <= MAX_RAW_POINTS:
            raise ValueError("unexpected point count")
        if analysis != "dc" and count < 2:
            raise ValueError("too few samples")
        tokens = iter(values_text.split())
        rows = []
        for i in range(count):
            if int(next(tokens)) != i:
                raise ValueError("out-of-order samples")
            rows.append(tuple(_number(next(tokens, ""), flags == "complex") for _ in vectors))
        if next(tokens, None) is not None:
            raise ValueError("trailing data")
        command = headers.get("command", "")
        version = re.match(r"ngspice-[\w.+-]+", command, re.IGNORECASE)
        return version[0] if version else "ngspice (version not reported)", rows
    except (ValueError, KeyError, IndexError, StopIteration) as error:
        raise SpiceError("ngspice output is incomplete or invalid.") from error


def _run_batch(executable: str, netlist: str, timeout_s: float) -> tuple[str, str]:
    program = which(executable or "ngspice") or (which("ngspice_con") if not executable else None)
    if not program:
        raise SpiceUnavailable("ngspice executable not found. Set NGSPICE_BIN or check PATH.")
    program = str(Path(program).resolve())
    with TemporaryDirectory(prefix="lab04-spice-") as workdir:
        directory = Path(workdir)
        circuit_file = directory / "circuit.cir"
        log_file = directory / "run.log"
        result_file = directory / "result.raw"
        circuit_file.write_text(netlist, encoding="utf-8")

        def read_log() -> str:
            try:
                with log_file.open("rb") as file:
                    data = file.read(MAX_LOG_BYTES + 1)
                suffix = "\n[log truncated]" if len(data) > MAX_LOG_BYTES else ""
                return data[:MAX_LOG_BYTES].decode("utf-8", errors="replace").strip() + suffix
            except OSError:
                return ""

        try:
            process = subprocess.run(
                [program, "-n", "-b", "-o", log_file.name, circuit_file.name],
                cwd=directory, timeout=timeout_s, capture_output=True, text=True, errors="replace",
            )
        except subprocess.TimeoutExpired as error:
            raise SpiceError("ngspice timed out. Check the circuit and try again.", read_log()) from error
        except OSError as error:
            raise SpiceUnavailable("ngspice could not be started. Check NGSPICE_BIN.") from error

        log = read_log() or (process.stderr or process.stdout)[:MAX_LOG_BYTES].strip()
        if process.returncode or re.search(r"(?im)^\s*(?:error\b|fatal\b|.*simulation\(s\) aborted)", log):
            raise SpiceError("ngspice failed to complete the analysis. See the run log.", log)
        try:
            with result_file.open("rb") as file:
                raw = file.read(MAX_RAW_BYTES + 1)
        except OSError as error:
            raise SpiceError("ngspice did not produce a result file. See the run log.", log) from error
        if not raw or len(raw) > MAX_RAW_BYTES:
            raise SpiceError("ngspice returned empty or oversized output. See the run log.", log)
        try:
            return log, raw.decode("utf-8").replace("\r\n", "\n")
        except UnicodeError as error:
            raise SpiceError("ngspice did not produce readable ASCII output.", log) from error


def _read_data(rows: list[tuple], analysis: str, source: SineSource | None):
    if analysis == "dc":
        vb_v, ve_v, vc_v, ic_a = rows[0]
        vce_v = vc_v - ve_v
        if not math.isfinite(vce_v):
            raise SpiceError("ngspice operating point is not finite.")
        return OperatingPoint(vb_v, ve_v, vc_v, vce_v, ic_a)

    if analysis == "ac":
        count = round(math.log10(AC_STOP_HZ / AC_START_HZ) * AC_POINTS_PER_DECADE) + 1
        if len(rows) != count:
            raise SpiceError("ngspice returned an incomplete frequency sweep.")
        points = []
        for index, (scale, vin, vout) in enumerate(rows):
            # ngspice stores frequency in the real component of the scale vector.
            frequency_hz = scale.real
            expected_hz = AC_START_HZ * 10 ** (index / AC_POINTS_PER_DECADE)
            if not math.isclose(frequency_hz, expected_hz, rel_tol=1e-6) or vin == 0:
                raise SpiceError("ngspice returned an invalid AC scale or input phasor.")
            gain = vout / vin
            if not math.isfinite(abs(gain)):
                raise SpiceError("ngspice returned a non-finite AC gain.")
            points.append(ACPoint(frequency_hz, gain))
        return tuple(points)

    points = tuple(TransientPoint(*row) for row in rows)
    stop_s = TRANSIENT_CYCLES / source.frequency_hz
    if (points[0].time_s != 0 or not math.isclose(points[-1].time_s, stop_s, rel_tol=1e-6)
            or any(b.time_s <= a.time_s for a, b in zip(points, points[1:]))):
        raise SpiceError("ngspice returned an incomplete or invalid time scale.")
    return points


def simulate(
    circuit: Circuit, analysis: str, source: SineSource | None, *,
    executable: str, model_file: str, model_name: str, timeout_s: float = 10,
) -> Simulation:
    model = load_model(model_file, model_name)
    netlist = build_netlist(circuit, model, analysis, source)
    log, raw = _run_batch(executable, netlist, timeout_s)
    try:
        version, rows = parse_raw(raw, analysis)
        data = _read_data(rows, analysis, source)
    except SpiceError as error:
        raise SpiceError(str(error), log) from error
    return Simulation(data, model, version, netlist, log, len(rows))
