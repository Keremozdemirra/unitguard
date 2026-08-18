"""Units: a dimension, a scale to the SI coherent unit, and possibly an offset.

A *unit* is a named way of expressing a quantity of a given dimension. It is
fully described by three things:

- the dimension it measures,
- the factor that converts a magnitude in this unit to the SI coherent unit of
  that dimension (joule for energy, kilogram for mass, kelvin for temperature),
- an offset, added after scaling, which is zero for every unit except the
  affine temperature scales.

Scale factors are exact rationals. Every unit defined here is *definitional*
rather than measured -- 1 kWh is 3 600 000 J by the definition of the hour and
the watt, not by experiment -- so there is an exact rational for every one of
them, and storing 3.6e6 as a float would throw away exactness the module has
no reason to lose.

Sources, all definitional:

- The SI base and coherent derived units, and the decimal prefixes, are as
  defined in the SI Brochure, BIPM, 9th edition (2019), tables 1-5.
- The tonne (1 t = 1000 kg) and the hour (1 h = 3600 s) are non-SI units
  accepted for use with the SI: SI Brochure, 9th edition (2019), table 8.
  1 Wh = 3600 J follows.
- Degrees Celsius: t/degC = T/K - 273.15, SI Brochure, 9th edition (2019),
  section 2.3.1.
- Degrees Fahrenheit: T/K = (t/degF + 459.67) x 5/9. Not an SI unit; the
  relation is the standard definition of the scale and is exact.

This module deliberately holds a *small* vocabulary -- the energy, mass, power
and temperature units that emissions and energy models actually use. A general
registry with parsing, prefix composition and aliases is project 003. Growing
the table here instead would produce a registry with no parser and no way to
say a unit is unknown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from unitguard_dimensions import (
    DIMENSIONLESS,
    ENERGY,
    MASS,
    POWER,
    Dimension,
    DimensionError,
)

TEMPERATURE = Dimension.of(**{"Θ": 1})
TIME = Dimension.of(T=1)


class UnitError(ValueError):
    """Raised when an operation is meaningless for the units involved.

    Distinct from :class:`DimensionError`: a dimension error means the two
    quantities measure different things and nothing can rescue the operation.
    A unit error means the dimensions agree but the operation still has no
    defined answer -- multiplying two temperatures on the Celsius scale, for
    instance, where the answer depends on where the zero was put.
    """


@dataclass(frozen=True)
class Unit:
    """A unit of measurement.

    ``si_value = magnitude * scale + offset``.

    Frozen and hashable so units can key a lookup table, and so a quantity is
    itself hashable when its magnitude is.
    """

    symbol: str
    dimension: Dimension
    scale: Fraction
    offset: Fraction = field(default_factory=lambda: Fraction(0))

    def __post_init__(self) -> None:
        if not isinstance(self.scale, Fraction) or not isinstance(
            self.offset, Fraction
        ):
            raise UnitError(f"{self.symbol}: scale and offset must be Fractions")
        if self.scale <= 0:
            raise UnitError(
                f"{self.symbol}: scale must be positive, got {self.scale}. "
                "A negative scale would reverse ordering and silently break "
                "every comparison."
            )

    @property
    def is_affine(self) -> bool:
        """True for a scale whose zero is not the zero of the dimension."""
        return self.offset != 0

    def difference_unit(self) -> "Unit":
        """The unit in which a *difference* of two affine readings is expressed.

        30 degC minus 10 degC is not 20 degC: it is an interval of 20 kelvin.
        The difference has the same size as this unit but its zero is the zero
        of the dimension, so the offset drops away.
        """
        if not self.is_affine:
            return self
        return Unit("Δ" + self.symbol, self.dimension, self.scale)

    def __str__(self) -> str:
        return self.symbol


def _u(symbol: str, dimension: Dimension, scale: object, offset: object = 0) -> Unit:
    return Unit(symbol, dimension, Fraction(scale), Fraction(offset))


# -- dimensionless ----------------------------------------------------------

ONE = _u("1", DIMENSIONLESS, 1)
PERCENT = _u("%", DIMENSIONLESS, Fraction(1, 100))

# -- mass -------------------------------------------------------------------

KILOGRAM = _u("kg", MASS, 1)
GRAM = _u("g", MASS, Fraction(1, 1000))
TONNE = _u("t", MASS, 1000)
KILOTONNE = _u("kt", MASS, 1_000_000)
MEGATONNE = _u("Mt", MASS, 1_000_000_000)

# -- energy -----------------------------------------------------------------

JOULE = _u("J", ENERGY, 1)
KILOJOULE = _u("kJ", ENERGY, 1_000)
MEGAJOULE = _u("MJ", ENERGY, 1_000_000)
GIGAJOULE = _u("GJ", ENERGY, 1_000_000_000)
TERAJOULE = _u("TJ", ENERGY, 1_000_000_000_000)

WATT_HOUR = _u("Wh", ENERGY, 3_600)
KILOWATT_HOUR = _u("kWh", ENERGY, 3_600_000)
MEGAWATT_HOUR = _u("MWh", ENERGY, 3_600_000_000)
GIGAWATT_HOUR = _u("GWh", ENERGY, 3_600_000_000_000)
TERAWATT_HOUR = _u("TWh", ENERGY, 3_600_000_000_000_000)

# -- power ------------------------------------------------------------------

WATT = _u("W", POWER, 1)
KILOWATT = _u("kW", POWER, 1_000)
MEGAWATT = _u("MW", POWER, 1_000_000)
GIGAWATT = _u("GW", POWER, 1_000_000_000)

# -- time -------------------------------------------------------------------

SECOND = _u("s", TIME, 1)
HOUR = _u("h", TIME, 3_600)
#: A 365-day year. Named for what it is: "year" alone is ambiguous between
#: 365, 365.25 and the calendar, and the ambiguity has to be in the symbol
#: rather than in a footnote nobody reads.
YEAR_365 = _u("yr365", TIME, 365 * 24 * 3_600)

# -- temperature ------------------------------------------------------------

KELVIN = _u("K", TEMPERATURE, 1)
#: t/degC = T/K - 273.15, so T/K = t/degC + 273.15.
CELSIUS = _u("°C", TEMPERATURE, 1, Fraction(27315, 100))
#: T/K = (t/degF + 459.67) x 5/9.
FAHRENHEIT = _u(
    "°F", TEMPERATURE, Fraction(5, 9), Fraction(45967, 100) * Fraction(5, 9)
)

#: Every unit this project knows about, by symbol. Project 003 replaces this
#: with a registry that can parse and compose; until then a flat table is
#: honest about how little is here.
UNITS = {
    u.symbol: u
    for u in (
        ONE,
        PERCENT,
        KILOGRAM,
        GRAM,
        TONNE,
        KILOTONNE,
        MEGATONNE,
        JOULE,
        KILOJOULE,
        MEGAJOULE,
        GIGAJOULE,
        TERAJOULE,
        WATT_HOUR,
        KILOWATT_HOUR,
        MEGAWATT_HOUR,
        GIGAWATT_HOUR,
        TERAWATT_HOUR,
        WATT,
        KILOWATT,
        MEGAWATT,
        GIGAWATT,
        SECOND,
        HOUR,
        YEAR_365,
        KELVIN,
        CELSIUS,
        FAHRENHEIT,
    )
}


def unit(symbol: str) -> Unit:
    """Look a unit up by exact symbol.

    No prefix composition, no aliases, no case folding: an unknown symbol is
    an error rather than a guess. Guessing is what backlog item 005 exists to
    refuse, and it would be odd to start by doing it here.
    """
    try:
        return UNITS[symbol]
    except KeyError:
        raise UnitError(
            "unknown unit " + repr(symbol) + ". This project carries a fixed "
            "table of " + str(len(UNITS)) + " units; parsing and prefix "
            "composition are the registry's job."
        ) from None


def derived(symbol: str, numerator: Unit, denominator: Unit) -> Unit:
    """Compose a ratio unit, such as t/MWh, from two units.

    Refused for affine units: 20 degC per second has no defined meaning,
    because the numerator's zero is arbitrary and the ratio would depend on it.
    """
    for part in (numerator, denominator):
        if part.is_affine:
            raise UnitError(
                "cannot build a derived unit from " + part.symbol + ": it is an "
                "affine scale, so a ratio involving it depends on where its "
                "zero was put. Convert to the absolute scale first."
            )
    return Unit(
        symbol,
        numerator.dimension / denominator.dimension,
        numerator.scale / denominator.scale,
    )


__all__ = [
    "CELSIUS",
    "DimensionError",
    "FAHRENHEIT",
    "GIGAJOULE",
    "GIGAWATT",
    "GIGAWATT_HOUR",
    "GRAM",
    "HOUR",
    "JOULE",
    "KELVIN",
    "KILOGRAM",
    "KILOJOULE",
    "KILOTONNE",
    "KILOWATT",
    "KILOWATT_HOUR",
    "MEGAJOULE",
    "MEGATONNE",
    "MEGAWATT",
    "MEGAWATT_HOUR",
    "ONE",
    "PERCENT",
    "SECOND",
    "TEMPERATURE",
    "TERAJOULE",
    "TERAWATT_HOUR",
    "TIME",
    "TONNE",
    "UNITS",
    "Unit",
    "UnitError",
    "WATT",
    "WATT_HOUR",
    "YEAR_365",
    "derived",
    "unit",
]
