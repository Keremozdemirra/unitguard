"""Dimension algebra over the SI base dimensions.

A *dimension* is what a quantity measures, independent of the unit chosen to
express it. Energy is energy whether it is written in kWh, MWh, joules or
therms; all four share the dimension

    M · L^2 · T^-2

Representing that as a vector of integer exponents over the seven SI base
dimensions turns dimensional analysis into arithmetic. Multiplying quantities
adds the exponent vectors; dividing subtracts them; raising to a power scales
them. Two quantities may be added only if their vectors are identical.

That last rule is the whole point of this module. Adding kWh to MWh is a *unit*
error and is recoverable by conversion. Adding kWh to tonnes is a *dimension*
error and is not recoverable by anything — it is meaningless, and no amount of
care with conversion factors will catch it, because there is no factor to get
wrong. Dimensions catch the second class; units, built on top of this, catch
the first.

**Exponents are exact rationals, not floats.** Square roots of dimensions occur
in real formulas — the standard deviation of an energy series has dimension
E^(1/2) — so exponents are stored as `Fraction`. Using floats here would make
equality unreliable in exactly the situation the module exists to make
reliable: `0.1 + 0.2 != 0.3` is a poor foundation for deciding whether two
quantities may be added.

The seven base dimensions are those of the SI, as defined in the SI Brochure
(BIPM, 9th edition, 2019): mass, length, time, electric current, thermodynamic
temperature, amount of substance and luminous intensity.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Mapping

# Order is fixed and load-bearing: the exponent tuple is positional, and the
# symbols are the conventional SI ones so that printed dimensions are readable
# by anyone who has seen a physics textbook.
BASE_SYMBOLS = ("M", "L", "T", "I", "Θ", "N", "J")
BASE_NAMES = (
    "mass",
    "length",
    "time",
    "electric current",
    "thermodynamic temperature",
    "amount of substance",
    "luminous intensity",
)


class DimensionError(ValueError):
    """Raised when an operation is not dimensionally meaningful."""


Exponents = tuple[Fraction, ...]


def _coerce(value: object, *, symbol: str) -> Fraction:
    """Turn an exponent into an exact Fraction, refusing lossy input.

    Floats are accepted because writing ``0.5`` is natural, but only when they
    convert exactly to a small rational. A float that does not is a sign the
    caller is computing exponents numerically, which is precisely the practice
    this module exists to replace.
    """
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        exact = Fraction(value).limit_denominator(64)
        if float(exact) != value:
            raise DimensionError(
                f"exponent {value!r} for {symbol} is not an exact small rational; "
                "pass a Fraction if you really mean it"
            )
        return exact
    raise DimensionError(f"exponent for {symbol} must be a number, got {value!r}")


@dataclass(frozen=True)
class Dimension:
    """A vector of exponents over the SI base dimensions.

    Instances are immutable and hashable, so dimensions can be dictionary keys
    — which is how a unit registry looks up what a given dimension can be
    expressed in.
    """

    exponents: Exponents

    def __post_init__(self) -> None:
        if len(self.exponents) != len(BASE_SYMBOLS):
            raise DimensionError(
                f"expected {len(BASE_SYMBOLS)} exponents, got {len(self.exponents)}"
            )
        if not all(isinstance(e, Fraction) for e in self.exponents):
            raise DimensionError("exponents must be Fractions; use Dimension.of()")

    # -- construction -------------------------------------------------------

    @classmethod
    def of(cls, **kwargs: object) -> "Dimension":
        """Build from keyword exponents: ``Dimension.of(M=1, L=2, T=-2)``."""
        unknown = set(kwargs) - set(BASE_SYMBOLS)
        if unknown:
            raise DimensionError(
                f"unknown base dimension(s) {', '.join(sorted(unknown))}; "
                f"the seven are {', '.join(BASE_SYMBOLS)}"
            )
        return cls(
            tuple(
                _coerce(kwargs.get(symbol, 0), symbol=symbol) for symbol in BASE_SYMBOLS
            )
        )

    @classmethod
    def dimensionless(cls) -> "Dimension":
        return cls.of()

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> "Dimension":
        return cls.of(**dict(mapping))

    # -- algebra ------------------------------------------------------------

    def __mul__(self, other: "Dimension") -> "Dimension":
        return Dimension(tuple(a + b for a, b in zip(self.exponents, other.exponents)))

    def __truediv__(self, other: "Dimension") -> "Dimension":
        return Dimension(tuple(a - b for a, b in zip(self.exponents, other.exponents)))

    def __pow__(self, power: object) -> "Dimension":
        factor = _coerce(power, symbol="exponent")
        return Dimension(tuple(e * factor for e in self.exponents))

    def inverse(self) -> "Dimension":
        return Dimension(tuple(-e for e in self.exponents))

    def root(self, n: int) -> "Dimension":
        """The nth root. Exact because exponents are rational."""
        if n <= 0:
            raise DimensionError(f"root order must be positive, got {n}")
        return self ** Fraction(1, n)

    # -- interrogation ------------------------------------------------------

    @property
    def is_dimensionless(self) -> bool:
        return all(e == 0 for e in self.exponents)

    def as_dict(self) -> dict[str, Fraction]:
        """Non-zero exponents only, keyed by base symbol."""
        return {
            symbol: exponent
            for symbol, exponent in zip(BASE_SYMBOLS, self.exponents)
            if exponent != 0
        }

    def check_addable(self, other: "Dimension", *, context: str = "") -> None:
        """Raise unless the two may be added.

        The error names both dimensions, because "cannot add these" without
        saying what they were is the least useful message a checker can give.
        """
        if self != other:
            where = f" in {context}" if context else ""
            raise DimensionError(
                f"cannot add or subtract {self} and {other}{where}: "
                "they measure different things, and no conversion factor exists "
                "that would make this meaningful"
            )

    # -- display ------------------------------------------------------------

    def __str__(self) -> str:
        parts = self.as_dict()
        if not parts:
            return "1"
        rendered = []
        for symbol, exponent in parts.items():
            if exponent == 1:
                rendered.append(symbol)
            elif exponent.denominator == 1:
                rendered.append(f"{symbol}^{exponent.numerator}")
            else:
                rendered.append(f"{symbol}^({exponent})")
        return "·".join(rendered)

    def __repr__(self) -> str:
        return f"Dimension({self})"


# Named dimensions that come up constantly in energy and emissions work. They
# are derived from the base vectors rather than written out, so a change to the
# representation cannot leave them inconsistent.

DIMENSIONLESS = Dimension.dimensionless()
MASS = Dimension.of(M=1)
LENGTH = Dimension.of(L=1)
TIME = Dimension.of(T=1)
CURRENT = Dimension.of(I=1)
TEMPERATURE = Dimension.of(Θ=1)
SUBSTANCE = Dimension.of(N=1)
LUMINOSITY = Dimension.of(J=1)

AREA = LENGTH ** 2
VOLUME = LENGTH ** 3
VELOCITY = LENGTH / TIME
ACCELERATION = VELOCITY / TIME
FORCE = MASS * ACCELERATION
ENERGY = FORCE * LENGTH
POWER = ENERGY / TIME

#: tCO2e per unit of energy — the emission factor of a fuel or a grid.
EMISSION_INTENSITY = MASS / ENERGY
#: Energy per unit of mass produced — the energy intensity of a process.
ENERGY_INTENSITY = ENERGY / MASS

NAMED: dict[str, Dimension] = {
    "dimensionless": DIMENSIONLESS,
    "mass": MASS,
    "length": LENGTH,
    "time": TIME,
    "current": CURRENT,
    "temperature": TEMPERATURE,
    "substance": SUBSTANCE,
    "luminosity": LUMINOSITY,
    "area": AREA,
    "volume": VOLUME,
    "velocity": VELOCITY,
    "acceleration": ACCELERATION,
    "force": FORCE,
    "energy": ENERGY,
    "power": POWER,
    "emission intensity": EMISSION_INTENSITY,
    "energy intensity": ENERGY_INTENSITY,
}


def name_of(dimension: Dimension) -> str:
    """Best-known name for a dimension, or its symbolic form."""
    for name, candidate in NAMED.items():
        if candidate == dimension:
            return name
    return str(dimension)


def product(dimensions: Iterable[Dimension]) -> Dimension:
    """Product of a sequence. Empty product is dimensionless, as it should be."""
    result = DIMENSIONLESS
    for dimension in dimensions:
        result = result * dimension
    return result
