"""A small Scope 2 inventory, and the three errors the type refuses to make.

Run from the project root:

    PYTHONPATH=.:../001-dimensions python3 examples/scope_two_inventory.py
"""

from fractions import Fraction

from unitguard_dimensions import DimensionError
from unitguard_quantity import (
    CELSIUS,
    GIGAJOULE,
    KELVIN,
    KILOWATT_HOUR,
    MEGAWATT_HOUR,
    TONNE,
    UnitError,
    derived,
    quantity as Q,
    ratio,
    total,
)

# Site meters report in whatever their vendor chose. Nobody normalises them
# before they reach the model, which is where the trouble starts.
metered = [
    Q(412_000, KILOWATT_HOUR),  # head office, from the electricity bill
    Q(1_250, MEGAWATT_HOUR),    # plant, from the half-hourly data
    Q(3_600, GIGAJOULE),        # district heat, from the site engineer
]

consumption = total(metered, unit=MEGAWATT_HOUR)
print("metered energy")
for reading in metered:
    print(f"  {reading:>20}  ->  {reading.to(MEGAWATT_HOUR)}")
print(f"  {'total':>20}  =   {consumption}\n")

# The grid factor is the user's own number, not one this library invented.
# Whoever supplies it owns its vintage and its source.
grid_factor = Q(Fraction(38, 100), derived("t/MWh", TONNE, MEGAWATT_HOUR))
emissions = consumption * grid_factor
print(f"grid factor          {grid_factor}")
print(f"scope 2 emissions    {emissions.to(TONNE)}")
print(f"                     dimension: {emissions.dimension}\n")

target = Q(400, TONNE)
print(f"against a {target} target: {float(ratio(emissions, target)) * 100:.1f}%\n")

print("three things this refuses to do")

# 1. Adding a mass to an energy. No factor exists that would fix it.
try:
    consumption + Q(10, TONNE)
except DimensionError as error:
    print(f"  1. {error}")

# 2. The inverted factor. MWh per tonne instead of tonnes per MWh multiplies
#    perfectly happily; the result is simply not a mass, and the attempt to add
#    it to anything that is fails.
inverted = Q(Fraction(100, 38), derived("MWh/t", MEGAWATT_HOUR, TONNE))
wrong = consumption * inverted
print(f"  2. inverted factor gives {wrong.dimension}, not a mass")
try:
    wrong + Q(0, TONNE)
except DimensionError as error:
    print(f"     {error}")

# 3. Averaging temperatures on the Celsius scale. The sum of two readings on an
#    affine scale has no defined value, so this raises rather than returning a
#    number that is wrong by 273.15 per reading.
try:
    total([Q(18, CELSIUS), Q(22, CELSIUS)])
except UnitError as error:
    print(f"  3. {error}")

swing = Q(22, CELSIUS) - Q(18, CELSIUS)
print(f"     the difference is well defined: {swing} = {swing.to(KELVIN)}")
