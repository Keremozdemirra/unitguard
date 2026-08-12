# dimensions

The layer everything else in `unitguard` stands on.

A `Dimension` says what *kind* of quantity something is — energy, mass, mass
per energy — without saying anything about the units it happens to be written
in. kWh, MWh, GJ, therms and BTU are all the same dimension. kWh and tCO2e are
not, and no amount of arithmetic should be able to hide that.

The split matters because the two errors are not equally expensive. Adding kWh
to GJ is wrong by a factor of 3.6 million and someone usually notices. Adding
tonnes of carbon to megawatt-hours is wrong in a way that produces a plausible
number and no complaint. This layer catches the second kind absolutely; the
first kind is the registry's job.

No dependencies beyond the Python standard library.

## Install

```bash
git clone <this repo>
cd projects/001-dimensions
python3 -m unittest discover -s tests -t .   # 76 tests, no deps needed
```

## Use

```python
from dimensions import ENERGY, INTENSITY, MASS, POWER, TIME, Dimension, parse

INTENSITY * ENERGY == MASS      # True  -- tCO2e/MWh x MWh is tCO2e
POWER * TIME == ENERGY          # True
ENERGY == MASS                  # False
str(ENERGY)                     # 'L^2·M·T^-2'
ENERGY.describe()               # 'length^2, mass^1, time^-2'

parse("M/(L^2 M T^-2)") == INTENSITY    # True
Dimension({"M": 1, "L": 2, "T": -2}) == ENERGY   # True
```

Seven base dimensions, named per ISO 80000-1: `L` length, `M` mass, `T` time,
`I` electric current, `Th` thermodynamic temperature, `N` amount of substance,
`J` luminous intensity. `ENERGY`, `POWER` and `INTENSITY` are provided because
they are the three this repository exists to police; build anything else from
the base dimensions.

Run `PYTHONPATH=. python3 examples/energy_intensity.py` for a worked tour:

```
What must hold
========================================================================
  intensity x energy is a mass                   True
  power x time is an energy                      True
  energy / energy is dimensionless               True
  energy is not a mass                           True

What is refused
========================================================================
  parse('kWh')  -- a unit, not a dimension       DimensionError
  parse('M/L/T')  -- chained division is ambiguous DimensionError
  parse('L^1/2')  -- a bare fractional exponent is ambiguous with division DimensionError
  ENERGY * 3  -- scale the magnitude, not the dimension DimensionError
```

## Method

**A dimension is an exponent vector.** Multiplication adds the vectors,
division subtracts them, exponentiation scales them. Stating it that plainly is
worth doing, because it is what makes the arithmetic exact rather than
approximate.

**Exponents are rational, not integer and not float.** The square root of an
area is a length, and a model taking the square root of a variance in
tCO2e² is doing something meaningful — integer exponents would refuse it.
Floats would make `(d ** 0.1) ** 10 == d` come out false, and dimension
equality has to be exact, because "nearly the same dimension" is not a thing.
`fractions.Fraction` gives both, and the test suite pins `d.root(n) ** n == d`
for n = 2, 3, 5, 7 over forty randomly generated dimensions.

**The tests assert group laws.** Dimensions under multiplication form an
abelian group: `DIMENSIONLESS` is the identity, multiplication is associative
and commutative, and every dimension has an inverse. That is not decoration —
it is the reason dimensional analysis works at all, and every checker built on
top of this layer will silently rely on it. The laws are swept over sixty
random dimensions with exponents drawn from thirds and halves as well as
integers.

**Three things are refused rather than guessed.**

`parse("kWh")` raises. Mapping unit strings onto dimensions is the registry's
job, and a parser that quietly turns `kWh` into energy is one that will
eventually quietly turn something else into the wrong thing.

`ENERGY * 3` raises, with an error message saying to scale the magnitude
instead. Three kWh is not a different dimension from one kWh.

`parse("M/L/T")` raises. Chained division reads differently to different
people, and bracketing costs the caller two characters.

**A bug the round-trip test caught.** `str()` rendered a fractional exponent as
`Th^-3/2`, and `parse` read that slash as division — so `parse(str(d)) == d`
failed on any dimension with a non-integer exponent. Non-integer exponents are
now bracketed on output, `L^(1/2)`, and a bare `L^1/2` is refused as ambiguous.
The round-trip is swept over 200 random dimensions.

**What this is not.** It knows nothing about units, magnitudes, prefixes or
conversion factors — `Dimension` carries no number at all. It cannot tell kWh
from GJ, and it is not supposed to. It does not know that tCO2e and tCO2 are
different things, because they are dimensionally identical and that particular
trap needs the carbon-specific layer, not this one. And it will not catch a
formula that is dimensionally valid and still wrong.

## Licence

MIT.
