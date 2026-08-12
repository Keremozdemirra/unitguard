"""The mistakes this layer is meant to make impossible.

Run with: PYTHONPATH=. python3 examples/energy_intensity.py
"""

from dimensions import DIMENSIONLESS, ENERGY, INTENSITY, MASS, POWER, TIME, parse


def show(label, value):
    print("  %-46s %s" % (label, value))


print("Dimensions of the quantities an emissions model actually handles")
print("=" * 72)
show("energy (kWh, MWh, GJ, therm, BTU)", ENERGY)
show("power (kW, MW)", POWER)
show("mass (t, kt, tCO2e)", MASS)
show("emission intensity (tCO2e/MWh, kg/GJ)", INTENSITY)
print()

print("What must hold")
print("=" * 72)
show("intensity x energy is a mass", INTENSITY * ENERGY == MASS)
show("power x time is an energy", POWER * TIME == ENERGY)
show("energy / energy is dimensionless", (ENERGY / ENERGY) == DIMENSIONLESS)
show("energy is not a mass", ENERGY != MASS)
print()

print("Unit choice is invisible here; dimension is not")
print("=" * 72)
# kWh and GJ differ by a scale factor of 3.6e6 and by nothing else that
# matters at this layer. Catching kWh-plus-GJ is the registry's job. Catching
# kWh-plus-tCO2e is this one's, and it is the more expensive of the two.
show("parse('L^2·M·T^-2') is energy", parse("L^2·M·T^-2") == ENERGY)
show("parse('M/(L^2 M T^-2)') is intensity", parse("M/(L^2 M T^-2)") == INTENSITY)
print()

print("What is refused")
print("=" * 72)
for expression, why in (
    ("kWh", "a unit, not a dimension"),
    ("M/L/T", "chained division is ambiguous"),
    ("L^1/2", "a bare fractional exponent is ambiguous with division"),
):
    try:
        parse(expression)
    except Exception as exc:                      # noqa: BLE001 - demonstrating
        show("parse(%r)  -- %s" % (expression, why), type(exc).__name__)

try:
    ENERGY * 3
except Exception as exc:                          # noqa: BLE001 - demonstrating
    show("ENERGY * 3  -- scale the magnitude, not the dimension", type(exc).__name__)
