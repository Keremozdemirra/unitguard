"""Dimension algebra over the SI base dimensions.

The layer everything else in unitguard stands on. A :class:`Dimension` says
what kind of quantity something is -- energy, mass, mass per energy -- without
saying anything about the units it happens to be written in. kWh and MWh and GJ
are the same dimension; kWh and tCO2e are not, and no amount of arithmetic
should be able to hide that.
"""

from .algebra import (
    BASE,
    DIMENSIONLESS,
    AMOUNT,
    CURRENT,
    DimensionError,
    Dimension,
    ENERGY,
    INTENSITY,
    LENGTH,
    LUMINOSITY,
    MASS,
    POWER,
    TEMPERATURE,
    TIME,
    parse,
)

__all__ = [
    "Dimension",
    "DimensionError",
    "BASE",
    "DIMENSIONLESS",
    "LENGTH",
    "MASS",
    "TIME",
    "CURRENT",
    "TEMPERATURE",
    "AMOUNT",
    "LUMINOSITY",
    "ENERGY",
    "POWER",
    "INTENSITY",
    "parse",
]

__version__ = "0.1.0"
