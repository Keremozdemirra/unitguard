"""Dimensional check of a routine emissions calculation.

    emissions [mass] = energy [energy] x emission factor [mass / energy]

The multiplication is checked by construction: if the factor were entered as
energy per unit mass — an easy inversion to make, and one that produces a
plausible-looking number — the result would carry the wrong dimension and the
addition at the end would raise.
"""

from unitguard_dimensions import EMISSION_INTENSITY, ENERGY, MASS, Dimension, name_of

grid_electricity = ENERGY
grid_factor = EMISSION_INTENSITY
scope2 = grid_electricity * grid_factor

print(f"energy           {ENERGY}          ({name_of(ENERGY)})")
print(f"emission factor  {EMISSION_INTENSITY}  ({name_of(EMISSION_INTENSITY)})")
print(f"product          {scope2}                ({name_of(scope2)})")
print()

# The inverted factor: energy per unit mass instead of mass per unit energy.
inverted = grid_electricity * EMISSION_INTENSITY.inverse()
print(f"with the factor inverted, the product is {inverted} ({name_of(inverted)})")

scope1 = MASS
try:
    scope1.check_addable(inverted, context="scope 1 + scope 2 total")
except Exception as exc:  # DimensionError
    print(f"\nadding it to scope 1 raises:\n  {exc}")
