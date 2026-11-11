"""Pure engineering calculations for a BJT voltage-divider DC bias point.

This module knows nothing about Flask, HTTP, HTML, or form field names.
All resistances are in ohms, voltages in volts, and currents in amperes.
"""

from dataclasses import dataclass
import math


VCE_SATURATION_THRESHOLD_V = 0.3


class BiasValidationError(ValueError):
    """Raised when the supplied values are not valid engineering values."""

    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors.values()))


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


def calculate_dc_bias(inputs: BiasInput) -> BiasResult:
    """Calculate the forward-active DC operating point and region warning."""

    validate_dc_bias_inputs(inputs)

    vth_v = inputs.vcc_v * inputs.r2_ohm / (inputs.r1_ohm + inputs.r2_ohm)
    rth_ohm = inputs.r1_ohm * inputs.r2_ohm / (inputs.r1_ohm + inputs.r2_ohm)
    ib_a = (vth_v - inputs.vbe_v) / (
        rth_ohm + (inputs.beta + 1.0) * inputs.re_ohm
    )
    ic_a = inputs.beta * ib_a
    ie_a = (inputs.beta + 1.0) * ib_a
    ve_v = ie_a * inputs.re_ohm
    vb_v = ve_v + inputs.vbe_v
    vc_v = inputs.vcc_v - ic_a * inputs.rc_ohm
    vce_v = vc_v - ve_v

    if vth_v <= inputs.vbe_v:
        region = "Cutoff"
        warnings = (
            "VTH ≤ VBE: the base-emitter junction is not forward biased. "
            "The transistor is in cutoff, so the forward-active equations are not valid.",
        )
    elif vce_v < VCE_SATURATION_THRESHOLD_V:
        region = "Saturation"
        warnings = (
            f"VCE < {VCE_SATURATION_THRESHOLD_V} V: the transistor is in saturation "
            "or at the edge of saturation. The forward-active approximation is not valid.",
        )
    else:
        region = "Active"
        warnings = ()

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
