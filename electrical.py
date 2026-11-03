import math


def analyze_dc(voltage_v, resistance_ohm):
    if not math.isfinite(voltage_v):
        raise ValueError("Voltage must be a finite number.")
    if not math.isfinite(resistance_ohm) or resistance_ohm <= 0:
        raise ValueError("Resistance must be a finite number greater than zero.")

    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {"current_a": current_a, "power_w": power_w}


def main():
    try:
        voltage_v = float(input("Voltage (V): "))
        resistance_ohm = float(input("Resistance (ohms): "))
        result = analyze_dc(voltage_v, resistance_ohm)
    except ValueError as error:
        print(f"Error: {error}")
        return 1

    print(f"Current: {result['current_a']:.3f} A")
    print(f"Power: {result['power_w']:.3f} W")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())