"""Pure engineering calculations for a BJT common-emitter DC bias point.

This module knows nothing about Flask, HTTP, HTML, or form field names.
All resistances are in ohms, voltages in volts, and currents in amperes.

The voltage-divider API (BiasInput/BiasResult/calculate_dc_bias) is kept
unchanged for compatibility. Fixed-bias and emitter-bias calculations use
their own frozen inputs and return the common result dictionary used by the
web page.
"""

from dataclasses import dataclass
import math


VCE_SATURATION_THRESHOLD_V = 0.2


class BiasValidationError(ValueError):
    """Raised when the supplied values are not valid engineering values."""

    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors.values()))


class BiasCalculationError(ArithmeticError):
    """The inputs passed validation, but the arithmetic left the numeric range."""


def _require_finite(*values: float) -> None:
    if not all(math.isfinite(value) for value in values):
        raise BiasCalculationError("Calculation exceeded the numeric range. Use less extreme values.")


@dataclass(frozen=True)
class BiasInput:
    vcc_v: float
    r1_ohm: float
    r2_ohm: float
    rc_ohm: float
    re_ohm: float
    beta: float
    vbe_v: float


@dataclass(frozen=True)
class BiasResult:
    vth_v: float
    rth_ohm: float
    ib_a: float
    ic_a: float
    ie_a: float
    ve_v: float
    vb_v: float
    vc_v: float
    vce_v: float
    region: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class FixedBiasInput:
    vcc_v: float
    rb_ohm: float
    rc_ohm: float
    beta: float
    vbe_v: float


@dataclass(frozen=True)
class EmitterBiasInput:
    vcc_v: float
    rb_ohm: float
    rc_ohm: float
    re_ohm: float
    beta: float
    vbe_v: float


def _validate_resistor(
    errors: dict[str, str],
    *,
    field: str,
    label: str,
    value: float,
) -> None:
    key = field.removesuffix("_ohm")
    if not math.isfinite(value):
        errors[key] = f"{label} must be a finite number."
    elif value <= 0:
        errors[key] = f"{label} must be greater than zero."


def _validate_common_inputs(
    errors: dict[str, str],
    *,
    vcc_v: float,
    beta: float,
    vbe_v: float,
) -> None:
    if not math.isfinite(vcc_v):
        errors["vcc"] = "VCC must be a finite number."
    elif vcc_v <= 0:
        errors["vcc"] = "VCC must be greater than zero."

    if not math.isfinite(beta):
        errors["beta"] = "Beta must be a finite number."
    elif beta <= 0:
        errors["beta"] = "Beta must be greater than zero."

    if not math.isfinite(vbe_v):
        errors["vbe"] = "VBE must be a finite number."


def _classify_operating_point(
    ib_a: float,
    vce_v: float,
) -> tuple[str, tuple[str, ...]]:
    """Classify the operating region using the Lab 03 warning criteria."""

    if ib_a <= 0:
        return (
            "Cutoff",
            (
                "IB ≤ 0 A: the base-emitter junction is not forward biased. "
                "The transistor is in cutoff, so the forward-active approximation "
                "is not valid.",
            ),
        )

    if vce_v <= VCE_SATURATION_THRESHOLD_V:
        return (
            "Saturation",
            (
                f"VCE ≤ {VCE_SATURATION_THRESHOLD_V} V: the transistor is in "
                "saturation or at the edge of saturation. The forward-active "
                "approximation is not valid.",
            ),
        )

    return "Active", ()


def _result_dict(
    *,
    mode: str,
    vb_v: float,
    ve_v: float,
    vc_v: float,
    vce_v: float,
    ib_a: float,
    ic_a: float,
    ie_a: float,
    region: str,
    warnings: tuple[str, ...],
) -> dict[str, object]:
    """Build the common result shape shared by every bias mode."""

    return {
        "mode": mode,
        "vb_v": vb_v,
        "ve_v": ve_v,
        "vc_v": vc_v,
        "vce_v": vce_v,
        "ib_a": ib_a,
        "ic_a": ic_a,
        "ie_a": ie_a,
        "region": region,
        "warnings": warnings,
    }


def validate_dc_bias_inputs(inputs: BiasInput) -> None:
    """Validate the handout's engineering constraints.

    The handout specifies VCC > 0, every resistance > 0, and beta > 0.
    It does not specify a range for VBE, so no VBE range check is added.
    Non-finite values are rejected as invalid numeric input.
    """

    errors: dict[str, str] = {}

    if not math.isfinite(inputs.vcc_v):
        errors["vcc"] = "VCC must be a finite number."
    elif inputs.vcc_v <= 0:
        errors["vcc"] = "VCC must be greater than zero."

    for field, label in (
        ("r1_ohm", "R1"),
        ("r2_ohm", "R2"),
        ("rc_ohm", "RC"),
        ("re_ohm", "RE"),
    ):
        value = getattr(inputs, field)
        key = field.removesuffix("_ohm")
        if not math.isfinite(value):
            errors[key] = f"{label} must be a finite number."
        elif value <= 0:
            errors[key] = f"{label} must be greater than zero."

    if not math.isfinite(inputs.beta):
        errors["beta"] = "Beta must be a finite number."
    elif inputs.beta <= 0:
        errors["beta"] = "Beta must be greater than zero."

    if not math.isfinite(inputs.vbe_v):
        errors["vbe"] = "VBE must be a finite number."

    if errors:
        raise BiasValidationError(errors)


def validate_fixed_bias_inputs(inputs: FixedBiasInput) -> None:
    """Validate the values used by the fixed-bias circuit."""

    errors: dict[str, str] = {}
    _validate_common_inputs(
        errors,
        vcc_v=inputs.vcc_v,
        beta=inputs.beta,
        vbe_v=inputs.vbe_v,
    )
    _validate_resistor(
        errors,
        field="rb_ohm",
        label="RB",
        value=inputs.rb_ohm,
    )
    _validate_resistor(
        errors,
        field="rc_ohm",
        label="RC",
        value=inputs.rc_ohm,
    )

    if errors:
        raise BiasValidationError(errors)


def validate_emitter_bias_inputs(inputs: EmitterBiasInput) -> None:
    """Validate the values used by the single-supply emitter-bias circuit."""

    errors: dict[str, str] = {}
    _validate_common_inputs(
        errors,
        vcc_v=inputs.vcc_v,
        beta=inputs.beta,
        vbe_v=inputs.vbe_v,
    )
    for field, label, value in (
        ("rb_ohm", "RB", inputs.rb_ohm),
        ("rc_ohm", "RC", inputs.rc_ohm),
        ("re_ohm", "RE", inputs.re_ohm),
    ):
        _validate_resistor(errors, field=field, label=label, value=value)

    if errors:
        raise BiasValidationError(errors)


def calculate_dc_bias(inputs: BiasInput) -> BiasResult:
    """Calculate the forward-active DC operating point and region warning."""

    validate_dc_bias_inputs(inputs)

    divider_ohm = inputs.r1_ohm + inputs.r2_ohm
    _require_finite(divider_ohm)
    vth_v = inputs.vcc_v * inputs.r2_ohm / divider_ohm
    rth_ohm = inputs.r1_ohm * inputs.r2_ohm / divider_ohm
    total_ohm = rth_ohm + (inputs.beta + 1.0) * inputs.re_ohm
    _require_finite(vth_v, rth_ohm, total_ohm)
    ib_a = (vth_v - inputs.vbe_v) / total_ohm
    ic_a = inputs.beta * ib_a
    ie_a = (inputs.beta + 1.0) * ib_a
    ve_v = ie_a * inputs.re_ohm
    vb_v = ve_v + inputs.vbe_v
    vc_v = inputs.vcc_v - ic_a * inputs.rc_ohm
    vce_v = vc_v - ve_v

    _require_finite(ib_a, ic_a, ie_a, ve_v, vb_v, vc_v, vce_v)
    region, warnings = _classify_operating_point(ib_a, vce_v)

    return BiasResult(
        vth_v=vth_v,
        rth_ohm=rth_ohm,
        ib_a=ib_a,
        ic_a=ic_a,
        ie_a=ie_a,
        ve_v=ve_v,
        vb_v=vb_v,
        vc_v=vc_v,
        vce_v=vce_v,
        region=region,
        warnings=warnings,
    )


def calculate_divider_bias(inputs: BiasInput) -> dict[str, object]:
    """Return the existing divider result in the common dictionary shape."""

    result = calculate_dc_bias(inputs)
    return _result_dict(
        mode="Divider",
        vb_v=result.vb_v,
        ve_v=result.ve_v,
        vc_v=result.vc_v,
        vce_v=result.vce_v,
        ib_a=result.ib_a,
        ic_a=result.ic_a,
        ie_a=result.ie_a,
        region=result.region,
        warnings=result.warnings,
    )


def calculate_fixed_bias(inputs: FixedBiasInput) -> dict[str, object]:
    """Calculate the fixed-bias forward-active DC operating point."""

    validate_fixed_bias_inputs(inputs)

    ib_a = (inputs.vcc_v - inputs.vbe_v) / inputs.rb_ohm
    ic_a = inputs.beta * ib_a
    ie_a = (inputs.beta + 1.0) * ib_a
    ve_v = 0.0
    vb_v = ve_v + inputs.vbe_v
    vc_v = inputs.vcc_v - ic_a * inputs.rc_ohm
    vce_v = vc_v - ve_v
    _require_finite(ib_a, ic_a, ie_a, ve_v, vb_v, vc_v, vce_v)
    region, warnings = _classify_operating_point(ib_a, vce_v)

    return _result_dict(
        mode="Fixed",
        vb_v=vb_v,
        ve_v=ve_v,
        vc_v=vc_v,
        vce_v=vce_v,
        ib_a=ib_a,
        ic_a=ic_a,
        ie_a=ie_a,
        region=region,
        warnings=warnings,
    )


def calculate_emitter_bias(inputs: EmitterBiasInput) -> dict[str, object]:
    """Calculate the single-supply emitter-bias forward-active DC point."""

    validate_emitter_bias_inputs(inputs)

    total_ohm = inputs.rb_ohm + (inputs.beta + 1.0) * inputs.re_ohm
    _require_finite(total_ohm)
    ib_a = (inputs.vcc_v - inputs.vbe_v) / total_ohm
    ic_a = inputs.beta * ib_a
    ie_a = (inputs.beta + 1.0) * ib_a
    ve_v = ie_a * inputs.re_ohm
    vb_v = ve_v + inputs.vbe_v
    vc_v = inputs.vcc_v - ic_a * inputs.rc_ohm
    vce_v = vc_v - ve_v
    _require_finite(ib_a, ic_a, ie_a, ve_v, vb_v, vc_v, vce_v)
    region, warnings = _classify_operating_point(ib_a, vce_v)

    return _result_dict(
        mode="Emitter",
        vb_v=vb_v,
        ve_v=ve_v,
        vc_v=vc_v,
        vce_v=vce_v,
        ib_a=ib_a,
        ic_a=ic_a,
        ie_a=ie_a,
        region=region,
        warnings=warnings,
    )
