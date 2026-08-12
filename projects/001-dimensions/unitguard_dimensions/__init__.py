"""unitguard.dimensions: exact dimension algebra over the SI base dimensions."""

from .dimensions import (
    BASE_NAMES,
    BASE_SYMBOLS,
    DIMENSIONLESS,
    EMISSION_INTENSITY,
    ENERGY,
    ENERGY_INTENSITY,
    MASS,
    NAMED,
    POWER,
    Dimension,
    DimensionError,
    name_of,
    product,
)

__version__ = "0.1.0"

__all__ = [
    "BASE_NAMES",
    "BASE_SYMBOLS",
    "DIMENSIONLESS",
    "EMISSION_INTENSITY",
    "ENERGY",
    "ENERGY_INTENSITY",
    "MASS",
    "NAMED",
    "POWER",
    "Dimension",
    "DimensionError",
    "name_of",
    "product",
]
