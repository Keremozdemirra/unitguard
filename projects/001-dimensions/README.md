# unitguard-dimensions

Adding kWh to MWh is a **unit** error. It is wrong by a factor of a thousand and
a conversion fixes it.

Adding kWh to tonnes is a **dimension** error. There is no factor to get right,
because the operation means nothing. No amount of care with conversion tables
will catch it, because conversion never enters the picture.

This module catches the second kind. It is the foundation the rest of
`unitguard` is built on.

No dependencies beyond the Python standard library.

## What a dimension is

A vector of exponents over the seven SI base dimensions. Energy is energy
whether written in kWh, joules or therms, and all three carry:

```
M · L^2 · T^-2
```

Multiplying quantities adds the vectors, dividing subtracts them, powers scale
them, and two quantities may be added only if their vectors are identical. That
turns dimensional analysis into arithmetic.

## Use

```python
from unitguard_dimensions import ENERGY, EMISSION_INTENSITY, MASS

ENERGY * EMISSION_INTENSITY == MASS    # True — the Scope 2 identity
ENERGY.as_dict()                       # {'M': 1, 'L': 2, 'T': -2}
str(ENERGY)                            # 'M·L^2·T^-2'
```

The worked example (`PYTHONPATH=. python3 examples/emission_calculation.py`)
walks through an inverted emission factor — tonnes per MWh entered as MWh per
tonne, an easy slip that yields a plausible-looking number:

```
energy           M·L^2·T^-2          (energy)
emission factor  L^-2·T^2            (emission intensity)
product          M                   (mass)

with the factor inverted, the product is M·L^4·T^-4

adding it to scope 1 raises:
  cannot add or subtract M and M·L^4·T^-4 in scope 1 + scope 2 total: they
  measure different things, and no conversion factor exists that would make
  this meaningful
```

The inversion is not caught at the multiplication — that operation is perfectly
legal, it just produces something that is not a mass. It is caught at the
addition, which is the first point where the mistake becomes detectable.

## Two decisions worth knowing about

**Exponents are exact rationals, never floats.** Square roots of dimensions
occur in real formulas: the standard deviation of an energy series has dimension
E^(1/2). Storing exponents as `float` would make equality unreliable in exactly
the situation this module exists to make reliable — `0.1 + 0.2 != 0.3` is a poor
basis for deciding whether two quantities may be added. Exponents are
`Fraction`, so `(ENERGY ** 2).root(2) == ENERGY` holds exactly, and a test pins
it.

`Dimension.of` accepts floats for convenience but refuses any that is not an
exact small rational, on the grounds that a caller computing exponents
numerically has already lost the guarantee.

**Errors name both dimensions and the context.** "Cannot add these" without
saying what they were is the least useful message a checker can produce, so
`check_addable` reports both sides and where it happened.

## Verified properties

Dimensions under multiplication form an abelian group, and the test suite
asserts the axioms directly — identity, inverse, associativity, commutativity —
across a sample of seven dimensions rather than trusting the implementation.
Alongside those: powers add under multiplication, roots invert powers exactly,
and `ENERGY * EMISSION_INTENSITY == MASS`, the identity every Scope 2
calculation rests on.

41 tests.

## Base dimensions

The seven SI base dimensions, as defined in the SI Brochure (BIPM, 9th edition,
2019): mass, length, time, electric current, thermodynamic temperature, amount
of substance and luminous intensity.

Currency is deliberately not among them. It is not an SI dimension, it is not
convertible at a fixed rate, and pretending otherwise would license arithmetic
that looks checked and is not. Cost per tonne is handled at the unit layer, not
here.

## What this is not

It knows nothing about units — no kWh, no tonnes, no parsing, no conversion.
That is the next layer. This module answers only whether two quantities measure
the same kind of thing.

## Licence

MIT.
