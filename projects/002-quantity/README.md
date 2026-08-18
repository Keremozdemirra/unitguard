# unitguard-quantity

A magnitude with a unit attached, arithmetic that checks dimensions before it
adds, and conversions that are exact and reversible.

Built on [`unitguard-dimensions`](../001-dimensions), which answers *can these
be added at all*. This project answers the next question: *and by what factor*.

No dependencies beyond the Python standard library and the sibling dimensions
package.

## Use

```python
from fractions import Fraction
from unitguard_quantity import (
    MEGAWATT_HOUR, TONNE, KILOWATT_HOUR, derived, quantity as Q, total
)

total([Q(412_000, KILOWATT_HOUR), Q(1_250, MEGAWATT_HOUR)], unit=MEGAWATT_HOUR)
# Quantity(1662 MWh)

factor = Q(Fraction(38, 100), derived("t/MWh", TONNE, MEGAWATT_HOUR))
(Q(2662, MEGAWATT_HOUR) * factor).to(TONNE)
# Quantity(1011.56 t)
```

The worked example is `examples/scope_two_inventory.py`:

```
PYTHONPATH=.:../001-dimensions python3 examples/scope_two_inventory.py
```

It builds a three-meter Scope 2 inventory from readings in kWh, MWh and GJ, and
then walks into three errors on purpose. Real output:

```
metered energy
            412000 kWh  ->  412 MWh
              1250 MWh  ->  1250 MWh
               3600 GJ  ->  1000 MWh
                 total  =   2662 MWh

grid factor          0.38 t/MWh
scope 2 emissions    1011.56 t
                     dimension: M

against a 400 t target: 252.9%

three things this refuses to do
  1. cannot add 2662 MWh and 10 t: energy and mass measure different things, and no conversion factor exists that would make this meaningful
  2. inverted factor gives M·L^4·T^-4, not a mass
     cannot add ~7005.263158 MWh·(MWh/t) and 0 t: M·L^4·T^-4 and mass measure different things, and no conversion factor exists that would make this meaningful
  3. cannot total onto the affine scale °C: a sum of readings depends on where the zero was put
     the difference is well defined: 4 Δ°C = 4 K
```

Note where the second one is caught. Multiplying by an inverted emission factor
is a perfectly legal multiplication — it just does not produce a mass. The
mistake surfaces at the first addition, which is the earliest point at which it
is detectable at all.

## Three decisions worth knowing about

### Magnitudes are exact rationals

`Quantity(0.1, JOULE) + Quantity(0.2, JOULE) == Quantity(0.3, JOULE)` is true
here. A library whose entire purpose is to be trusted about numbers is a poor
place to inherit binary floating point.

A float handed in is read as the decimal it looks like: `0.1` means one tenth,
not the double nearest to one tenth. Every scale factor in the unit table is
already an exact rational — 1 kWh is 3 600 000 J by definition, not by
measurement — so conversion is exact and `q.to(a).to(b).to(a)` returns `q`
unchanged rather than approximately.

Where a magnitude does not terminate in decimal, printing marks it: `~0.3333333333`
rather than `0.3333333333`, so nobody types the rounded value back in.

### Equality is physical, not textual

`Quantity(1, KILOWATT_HOUR) == Quantity(3.6, MEGAJOULE)` is true, they hash
equal, and sorting a list of mixed units orders by the physical quantity. Two
spellings of the same quantity being unequal because somebody typed a different
unit would defeat the point.

### Affine scales are handled, not pretended away

Degrees Celsius and Fahrenheit put their zero somewhere other than the zero of
the dimension. That breaks the usual algebra, and treating them as ordinary
scaled units produces answers wrong by 273.15 per reading that still look
plausible.

| Expression | Result |
| --- | --- |
| `Q(20, CELSIUS) + Q(20, CELSIUS)` | raises — a sum of readings depends on where the zero is |
| `Q(30, CELSIUS) - Q(10, CELSIUS)` | `20 Δ°C`, an interval, equal to 20 K |
| `Q(20, CELSIUS) + Q(5, KELVIN)` | `25 °C` — an interval may shift a reading |
| `Q(300, KELVIN) - Q(20, CELSIUS)` | raises — a reading is not an interval |
| `Q(20, CELSIUS) * 2` | raises — doubling depends on the zero |
| `Q(68, FAHRENHEIT) - Q(32, FAHRENHEIT)` | `36 Δ°F`, exactly 20 K |

## What it is not for

- **It is not a unit registry.** The table here is 27 fixed symbols covering
  energy, mass, power, time and temperature. There is no parsing, no prefix
  composition, no aliases, and `unit("KWH")` raises rather than guessing.
  That is backlog item 003.
- **It does not know about CO2 versus CO2e, or carbon versus carbon dioxide.**
  Those are not unit conversions — they depend on which IPCC assessment report
  the warming potentials come from. Backlog item 004.
- **It carries no emission factors.** Every factor in the example above is the
  user's own number. A library that shipped factors would also have to ship
  their vintage, their geography and their supersession history, and that is a
  different project (`open-climate-data`).
- **It is not fast.** Exact rational arithmetic costs more than floats and the
  denominators grow. This is for model-scale work — inventories, bridges,
  reconciliations — not for arrays or tight loops. Call `float(q)` at the
  boundary where speed starts to matter.
- **Roots are refused.** `Q(4, JOULE) ** Fraction(1, 2)` raises. The square
  root of 3 600 000 is irrational, so an exact answer does not exist and an
  approximate one would break the promise the rest of the type makes.

## Sources

Every scale factor is definitional rather than measured:

- SI base and coherent derived units, and the decimal prefixes: SI Brochure,
  BIPM, 9th edition (2019), tables 1–5.
- The tonne (1 t = 1000 kg) and the hour (1 h = 3600 s) as non-SI units
  accepted for use with the SI: SI Brochure, 9th edition (2019), table 8.
  1 Wh = 3600 J follows from the hour and the watt.
- Degrees Celsius, *t*/°C = *T*/K − 273.15: SI Brochure, 9th edition (2019),
  section 2.3.1.
- Degrees Fahrenheit, *T*/K = (*t*/°F + 459.67) × 5/9. Not an SI unit; this is
  the standard definition of the scale and is exact. Checked in the tests
  against both anchor points, 32 °F = 0 °C and 212 °F = 100 °C.

## Tests

```
python3 -m unittest discover -s tests -t .
```

72 tests. They assert the abelian group laws for addition, associativity and
commutativity of multiplication, exact round-tripping of every conversion,
invariance of a sum under the unit it is performed in, the Scope 2 identity
(energy × emission factor = mass), and both Fahrenheit anchor points.
