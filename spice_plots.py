"""Build SVG coordinates and display measurements from parsed ngspice samples."""

import cmath
import math

from spice_engine import PLOT_CYCLES, ACPoint, SpiceError, TransientPoint


# Common coordinate rectangle. HTML ticks use the same linear percentage mapping.
LEFT, RIGHT, TOP, BOTTOM = 64, 412, 18, 158


def _label(value: float) -> str:
    base, sep, exponent = f"{value:.3g}".partition("e")
    text = f"{base}e{int(exponent)}" if sep else base
    return text.replace("-", "−")


def _frequency_label(hz: float) -> str:
    if hz >= 1e6:
        return f"{hz / 1e6:g}M"
    if hz >= 1e3:
        return f"{hz / 1e3:g}k"
    return f"{hz:g}"


def _frequency_text(hz: float) -> str:
    label = _frequency_label(hz)
    return f"{label[:-1]} {label[-1]}Hz" if label[-1] in "kM" else f"{label} Hz"


def _divisions(low: float, high: float, preferred: float | None = None) -> list[float]:
    """Choose readable major ticks without rounding the underlying samples."""
    interval = (high - low) / 5
    if math.isfinite(interval) and interval > 0:
        decade = 10.0 ** math.floor(math.log10(interval))
        if decade:
            step = preferred or next((f * decade for f in (1, 2, 2.5, 5, 10) if f * decade >= interval), interval)
            start = math.floor(low / step)
            end = math.ceil(high / step)
            ticks = [i * step for i in range(start, end + 1)]
            if all(math.isfinite(v) for v in ticks):
                return ticks
    # Keep convex interpolation finite for an unusually wide numeric domain.
    return [((4 - i) / 4) * low + (i / 4) * high for i in range(5)]


def _chart(x, series, *, title, x_label, y_label, summary, log=False, phase_axis=False):
    x_values = [math.log10(v) for v in x] if log else x
    x_min, x_max = x_values[0], x_values[-1]
    ys = [y for _, _, values in series for y in values if y is not None]
    if any(not math.isfinite(y) for y in ys):
        raise SpiceError("ngspice plot values are outside the display range.")
    y_min, y_max = (min(ys), max(ys)) if ys else (-1.0, 1.0)
    if y_min == y_max:
        padding = abs(y_min) * .1 or 1.0
        y_min, y_max = y_min - padding, y_max + padding
    if not math.isfinite(y_min) or not math.isfinite(y_max):
        raise SpiceError("ngspice plot values are outside the display range.")
    y_values = _divisions(y_min, y_max, preferred=90 if phase_axis and 180 <= y_max - y_min <= 450 else None)
    y_min, y_max = y_values[0], y_values[-1]
    if not log:
        x_steps = _divisions(x_min, x_max)
        x_min, x_max = x_steps[0], x_steps[-1]
    # Normalize first to avoid overflow for large positive-to-negative swings.
    scale = max(abs(y_min), abs(y_max))
    y_low, y_high = y_min / scale, y_max / scale
    if not math.isfinite(scale) or y_low == y_high:
        raise SpiceError("ngspice plot values are outside the display range.")

    def x_pos(value):
        return LEFT + (RIGHT - LEFT) * ((value - x_min) / (x_max - x_min))

    def y_pos(value):
        return BOTTOM - (BOTTOM - TOP) * ((value / scale - y_low) / (y_high - y_low))

    x_ticks, minor_x = [], []

    def tick_x(value, label, compact_hide=False):
        pos = min(max(LEFT, x_pos(value)), RIGHT)
        return {"pos": pos, "pct": round(100 * (pos - LEFT) / (RIGHT - LEFT), 4),
                "label": label, "compact_hide": compact_hide}

    if log:
        first, last = round(x_min), round(x_max)
        for exponent in range(first, last + 1):
            x_ticks.append(tick_x(exponent, _frequency_label(10 ** exponent),
                                  (exponent - first) % 2 == 1 and exponent != last))
        minor_x = [x_pos(exp + math.log10(factor)) for exp in range(first, last) for factor in (2, 5)]
    else:
        x_ticks = [tick_x(v, _label(v)) for v in x_steps]
        minor_x = [x_pos(a + (b - a) * i / 5) for a, b in zip(x_steps, x_steps[1:]) for i in range(1, 5)]
    y_ticks = []
    for value in y_values:
        pos = y_pos(value)
        y_ticks.append({"pos": pos, "pct": round(100 * (pos - TOP) / (BOTTOM - TOP), 4),
                        "label": _label(value)})
    minor_y = []
    if not log:
        minor_y = [a["pos"] + (b["pos"] - a["pos"]) * i / 5
                   for a, b in zip(y_ticks, y_ticks[1:]) for i in range(1, 5)]

    plots = []
    for name, color, values in series:
        segments = []
        segment = []
        for x_value, y_value in zip(x_values, values):
            if y_value is None:
                if segment:
                    segments.append(" ".join(segment))
                    segment = []
            else:
                segment.append(f"{x_pos(x_value):.2f},{y_pos(y_value):.2f}")
        if segment:
            segments.append(" ".join(segment))
        plots.append({"name": name, "style": color, "segments": segments})
    return {
        "title": title, "x_label": x_label, "y_label": y_label, "summary": summary,
        "x_ticks": x_ticks, "y_ticks": y_ticks, "series": plots,
        "view_box": f"{LEFT} {TOP} {RIGHT - LEFT} {BOTTOM - TOP}",
        "major_grid": " ".join([f"M{t['pos']:.3f} {TOP}V{BOTTOM}" for t in x_ticks]
                               + [f"M{LEFT} {t['pos']:.3f}H{RIGHT}" for t in y_ticks]),
        "minor_grid": " ".join([f"M{v:.3f} {TOP}V{BOTTOM}" for v in minor_x]
                               + [f"M{LEFT} {v:.3f}H{RIGHT}" for v in minor_y]),
        "zero_line": f"M{LEFT} {y_pos(0):.3f}H{RIGHT}" if not log and y_min < 0 < y_max else "",
        "is_scope": not log,
    }


def ac_display(points: tuple[ACPoint, ...]) -> dict:
    frequencies = [point.frequency_hz for point in points]
    gains_db = []
    phases_deg = []
    previous = None
    for point in points:
        magnitude = abs(point.gain)
        if magnitude == 0:
            gains_db.append(None)
            phases_deg.append(None)
            previous = None
            continue
        gains_db.append(20 * math.log10(magnitude))
        phase = math.degrees(cmath.phase(point.gain))
        if previous is not None:
            phase = previous + math.remainder(phase - previous, 360)
        phases_deg.append(phase)
        previous = phase
    # Report an actual solver sample nearest the handout's 1 kHz reference.
    sample = min(range(len(points)), key=lambda i: abs(math.log10(frequencies[i]) - 3))

    def endpoints(values, unit):
        readings = (
            f"{_label(v)} {unit}" if v is not None else "undefined"
            for v in (values[0], values[-1])
        )
        first, last = readings
        return (f"Sweep from {_frequency_text(frequencies[0])} to {_frequency_text(frequencies[-1])}. "
                f"At the first frequency: {first}. At the last frequency: {last}.")

    return {
        "charts": [
            _chart(frequencies, [("Magnitude", "gain", gains_db)], title="Magnitude",
                   x_label="Frequency (Hz, logarithmic)", y_label="dB",
                   summary=endpoints(gains_db, "dB"), log=True),
            _chart(frequencies, [("Phase", "phase", phases_deg)], title="Phase",
                   x_label="Frequency (Hz, logarithmic)", y_label="°",
                   summary=endpoints(phases_deg, "degrees"), log=True, phase_axis=True),
        ],
        "has_zero_gain": None in gains_db,
        "sample": (frequencies[sample], abs(points[sample].gain), gains_db[sample], phases_deg[sample]),
    }


def _correlation(points: tuple[TransientPoint, ...]) -> float | None:
    """Measure relative polarity over the shown time window, not a phase angle."""
    max_in = max(abs(p.vin_v) for p in points)
    max_out = max(abs(p.vout_v) for p in points)
    if not max_in or not max_out:
        return None
    duration = points[-1].time_s - points[0].time_s
    v_in, v_out, in_sq, out_sq, product = 0.0, 0.0, 0.0, 0.0, 0.0
    for a, b in zip(points, points[1:]):
        weight = (b.time_s - a.time_s) / (2 * duration)
        for p in (a, b):
            x, y = p.vin_v / max_in, p.vout_v / max_out
            v_in += weight * x
            v_out += weight * y
            in_sq += weight * x * x
            out_sq += weight * y * y
            product += weight * x * y
    variance_product = (in_sq - v_in * v_in) * (out_sq - v_out * v_out)
    if variance_product <= 0:
        return None
    return max(-1, min(1, (product - v_in * v_out) / math.sqrt(variance_product)))


def transient_display(points: tuple[TransientPoint, ...], frequency_hz: float) -> dict:
    start_s = points[-1].time_s - PLOT_CYCLES / frequency_hz
    visible = tuple(p for p in points if p.time_s >= start_s)
    if len(visible) < 2:
        raise SpiceError("ngspice returned too few samples in the waveform window.")
    times_ms = [p.time_s * 1e3 for p in visible]
    vin_mv = [p.vin_v * 1e3 for p in visible]
    vout_mv = [p.vout_v * 1e3 for p in visible]
    chart = _chart(
        times_ms, [("Vin", "input", vin_mv), ("Vout", "output", vout_mv)],
        title="Input and output", x_label="Time (ms)", y_label="Voltage (mV)",
        summary=(f"Vin and Vout from {_label(times_ms[0])} to {_label(times_ms[-1])} ms. "
                 "Measured amplitudes and relative polarity are listed above the plot."),
    )
    correlation = _correlation(visible)
    if correlation is None:
        phase_note = "Polarity could not be determined from these samples."
    elif correlation < -0.5:
        phase_note = "Vout is predominantly inverted relative to Vin in this window."
    elif correlation > 0.5:
        phase_note = "Vout is predominantly in phase with Vin in this window."
    else:
        phase_note = "The signals are not clearly in phase or inverted in this window."
    return {
        "charts": [chart], "phase_note": phase_note,
        "vin_amplitude_mv": max(vin_mv) / 2 - min(vin_mv) / 2,
        "vout_amplitude_mv": max(vout_mv) / 2 - min(vout_mv) / 2,
    }
