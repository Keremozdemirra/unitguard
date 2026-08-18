"""A magnitude with a unit, and arithmetic that refuses to be wrong.

The type in this module is deliberately strict in three places.

**Addition checks dimensions and converts units.** ``kwh(1) + mj(1)`` is fine
and gives 1 kWh + 1 MJ expressed in kWh. ``kwh(1) + t(1)`` raises, because
energy and mass measure different things and there is no factor that would
make the sum mean anything.

**Magnitudes are exact rationals.** A tool whose whole purpose is to be
trusted about numbers should not be the place where 0.1 + 0.2 != 0.3. Floats
handed in are read the way a person reads them -- ``0.1`` means one tenth, not
the binary double nearest to one tenth -- and every internal scale factor is
already an exact rational, so unit conversion is exact and round-trips.

**Affine scales are handled rather than pretended away.** Degrees Celsius and
Fahrenheit put their zero somewhere other than the zero of the dimension, and
that breaks the usual algebra:

- 20 degC + 20 degC has no defined answer, and is refused;
- 30 degC - 10 degC is 20 kelvin, an *interval*, not 20 degC;
- 20 degC + 5 K is 25 degC, because an interval may be added to a reading;
- 20 degC x 2 is refused, because the answer depends on where the zero is.

Silently treating degC as if it scaled from zero is a common and expensive
error in building-energy and process models, and it produces numbers that look
entirely plausible.
"""

from __future__ import annotations

import decimal
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Iterable, Union

from unitguard_dimensions import Dimension, DimensionError, name_of

from .units import ONE, Unit, UnitError

Magnitude = Union[int, float, Fraction, Decimal, str]


def _exact(value: Magnitude, *, what: str = "magnitude") -> Fraction:
    """Read a magnitude as an exact rational.

    A float is converted through its shortest decimal repr rather than its
    binary value: someone who writes ``0.1`` means one tenth. Taking
    ``Fraction(0.1)`` instead would carry 3602879701896397/36028797018963968
    through every subsequent operation, which is exact but exactly the wrong
    number, and it would make printed output unreadable for no benefit.
    """
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        # bool is an int subclass; accepting it silently would let a stray
        # comparison result become a magnitude of 1.
        raise UnitError(f"{what} must be a number, got {value!r}")
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, (float, Decimal, str)):
        try:
            return Fraction(str(value))
        except (ValueError, ZeroDivisionError):
            raise UnitError(f"{what} {value!r} is not a number") from None
    raise UnitError(f"{what} must be a number, got {value!r}")


def _terminating_decimal(value: Fraction) -> "Decimal | None":
    """The exact decimal for a rational, when one exists."""
    remainder = value.denominator
    for prime in (2, 5):
        while remainder % prime == 0:
            remainder //= prime
    if remainder != 1:
        return None
    with decimal.localcontext() as context:
        context.prec = 60
        return Decimal(value.numerator) / Decimal(value.denominator)


def format_magnitude(value: Fraction) -> str:
    """Render a rational: exactly where it terminates, approximately otherwise.

    The leading ``~`` on a repeating rational is load-bearing. Printing
    ``0.333333`` with no marker invites the reader to type it back in, which
    is how an exact number becomes an inexact one.
    """
    exact = _terminating_decimal(value)
    if exact is not None:
        text = format(exact.normalize(), "f")
        return "0" if text in ("-0", "0") else text
    return f"~{float(value):.10g}"


@dataclass(frozen=True)
class Quantity:
    """A magnitude expressed in a unit."""

    value: Fraction
    unit: Unit

    def __post_init__(self) -> None:
        if not isinstance(self.value, Fraction):
            raise UnitError("magnitude must be a Fraction; use Quantity.of()")
        if not isinstance(self.unit, Unit):
            raise UnitError(f"expected a Unit, got {self.unit!r}")

    # -- construction -------------------------------------------------------

    @classmethod
    def of(cls, value: Magnitude, unit: Unit) -> "Quantity":
        return cls(_exact(value), unit)

    # -- interrogation ------------------------------------------------------

    @property
    def dimension(self) -> Dimension:
        return self.unit.dimension

    @property
    def si_value(self) -> Fraction:
        """The magnitude in the SI coherent unit of this dimension."""
        return self.value * self.unit.scale + self.unit.offset

    @property
    def is_affine(self) -> bool:
        return self.unit.is_affine

    def to(self, target: Unit) -> "Quantity":
        """Convert. Exact, and an exact inverse of converting back."""
        if not isinstance(target, Unit):
            raise UnitError(f"expected a Unit, got {target!r}")
        if target.dimension != self.unit.dimension:
            raise DimensionError(
                f"cannot express {self.unit} ({name_of(self.unit.dimension)}) "
                f"as {target} ({name_of(target.dimension)}): they measure "
                "different things"
            )
        return Quantity((self.si_value - target.offset) / target.scale, target)

    def __float__(self) -> float:
        return float(self.value)

    # -- additive arithmetic ------------------------------------------------

    def _require_same_dimension(self, other: "Quantity", operation: str) -> None:
        if self.unit.dimension != other.unit.dimension:
            raise DimensionError(
                f"cannot {operation} {self} and {other}: "
                f"{name_of(self.unit.dimension)} and "
                f"{name_of(other.unit.dimension)} measure different things, and "
                "no conversion factor exists that would make this meaningful"
            )

    def __add__(self, other: object) -> "Quantity":
        if not isinstance(other, Quantity):
            return NotImplemented
        self._require_same_dimension(other, "add")
        if self.is_affine and other.is_affine:
            raise UnitError(
                f"cannot add {self} and {other}: both are readings on an affine "
                "scale, and their sum depends on where the zero was put. Add an "
                f"interval instead, or convert both to "
                f"{name_of(self.unit.dimension)} on an absolute scale."
            )
        if other.is_affine:
            # An interval plus a reading is the reading shifted; report it on
            # the affine scale, which is the one the reader asked a question in.
            return other + self
        # ``other`` is an interval here: scale it, do not re-zero it.
        shifted = self.value + other.value * other.unit.scale / self.unit.scale
        return Quantity(shifted, self.unit)

    def __sub__(self, other: object) -> "Quantity":
        if not isinstance(other, Quantity):
            return NotImplemented
        self._require_same_dimension(other, "subtract")
        if self.is_affine and other.is_affine:
            difference_unit = self.unit.difference_unit()
            return Quantity(
                (self.si_value - other.si_value) / difference_unit.scale,
                difference_unit,
            )
        if other.is_affine:
            raise UnitError(
                f"cannot subtract {other} from {self}: an affine reading is not "
                "an interval, so taking it away from an interval has no meaning."
            )
        shifted = self.value - other.value * other.unit.scale / self.unit.scale
        return Quantity(shifted, self.unit)

    def __neg__(self) -> "Quantity":
        if self.is_affine:
            raise UnitError(
                f"cannot negate {self}: negating a reading on an affine scale "
                "reflects it about an arbitrary zero."
            )
        return Quantity(-self.value, self.unit)

    def __abs__(self) -> "Quantity":
        if self.is_affine:
            raise UnitError(f"cannot take the magnitude of the affine reading {self}")
        return Quantity(abs(self.value), self.unit)

    # -- multiplicative arithmetic ------------------------------------------

    def _require_absolute(self, operation: str) -> None:
        if self.is_affine:
            raise UnitError(
                f"cannot {operation} {self}: it is a reading on an affine "
                f"scale, so the result depends on where {self.unit}'s zero was "
                "put. Convert to an absolute scale first."
            )

    def __mul__(self, other: object) -> "Quantity":
        if isinstance(other, Quantity):
            self._require_absolute("multiply")
            other._require_absolute("multiply")
            return Quantity(
                self.value * other.value,
                Unit(
                    _compose_symbol(self.unit, other.unit, "·"),
                    self.unit.dimension * other.unit.dimension,
                    self.unit.scale * other.unit.scale,
                ),
            )
        if isinstance(other, (int, float, Fraction, Decimal)):
            self._require_absolute("scale")
            return Quantity(self.value * _exact(other, what="factor"), self.unit)
        return NotImplemented

    __rmul__ = __mul__

    def __truediv__(self, other: object) -> "Quantity":
        if isinstance(other, Quantity):
            self._require_absolute("divide")
            other._require_absolute("divide")
            if other.value == 0:
                raise ZeroDivisionError(f"division by the zero quantity {other}")
            return Quantity(
                self.value / other.value,
                Unit(
                    _compose_symbol(self.unit, other.unit, "/"),
                    self.unit.dimension / other.unit.dimension,
                    self.unit.scale / other.unit.scale,
                ),
            )
        if isinstance(other, (int, float, Fraction, Decimal)):
            self._require_absolute("scale")
            divisor = _exact(other, what="divisor")
            if divisor == 0:
                raise ZeroDivisionError("division by zero")
            return Quantity(self.value / divisor, self.unit)
        return NotImplemented

    def __pow__(self, power: object) -> "Quantity":
        """Integer powers only.

        A root would generally take the scale factor out of the rationals --
        the square root of 3 600 000 is irrational -- and the exactness this
        type promises would quietly become an approximation. Dimensions
        support rational exponents because exponents stay rational under a
        root; magnitudes and scale factors do not.
        """
        if not isinstance(power, int) or isinstance(power, bool):
            raise UnitError(
                f"exponent must be an integer, got {power!r}. Roots are out of "
                "scope: they leave the exact rationals this type is built on."
            )
        self._require_absolute("raise to a power")
        if power < 0 and self.value == 0:
            raise ZeroDivisionError("zero quantity raised to a negative power")
        symbol = "1" if power == 0 else f"({self.unit.symbol})^{power}"
        return Quantity(
            self.value**power,
            Unit(symbol, self.unit.dimension**power, self.unit.scale**power),
        )

    # -- comparison ---------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        """Equal when they are the same physical quantity.

        1 kWh equals 3.6 MJ. Comparing the stored magnitude instead would make
        equality depend on which unit somebody happened to type, which is the
        opposite of what this type is for.
        """
        if not isinstance(other, Quantity):
            return NotImplemented
        if self.unit.dimension != other.unit.dimension:
            return False
        return self.si_value == other.si_value

    def __hash__(self) -> int:
        return hash((self.unit.dimension, self.si_value))

    def _compare(self, other: object, operation: str) -> Fraction:
        if not isinstance(other, Quantity):
            raise UnitError(f"cannot compare a quantity with {other!r}")
        self._require_same_dimension(other, operation)
        return self.si_value - other.si_value

    def __lt__(self, other: object) -> bool:
        return self._compare(other, "order") < 0

    def __le__(self, other: object) -> bool:
        return self._compare(other, "order") <= 0

    def __gt__(self, other: object) -> bool:
        return self._compare(other, "order") > 0

    def __ge__(self, other: object) -> bool:
        return self._compare(other, "order") >= 0

    # -- display ------------------------------------------------------------

    def __str__(self) -> str:
        if self.unit is ONE or self.unit.symbol == "1":
            return format_magnitude(self.value)
        return f"{format_magnitude(self.value)} {self.unit}"

    def __format__(self, specification: str) -> str:
        """Format the rendered quantity, not the bare magnitude.

        ``f"{q:>20}"`` aligning a column of quantities is the common case, and
        a numeric format code would drop the unit, which is the one thing this
        type exists to keep attached.
        """
        return format(str(self), specification)

    def __repr__(self) -> str:
        return f"Quantity({self})"


def _compose_symbol(left: Unit, right: Unit, operator: str) -> str:
    """Bracket a composed symbol so ``t/MWh/yr`` cannot be misread."""
    left_symbol = f"({left.symbol})" if _needs_brackets(left.symbol) else left.symbol
    right_symbol = f"({right.symbol})" if _needs_brackets(right.symbol) else right.symbol
    return f"{left_symbol}{operator}{right_symbol}"


def _needs_brackets(symbol: str) -> bool:
    return any(character in symbol for character in "·/^") and not symbol.startswith("(")


def quantity(value: Magnitude, unit: Unit) -> Quantity:
    """Shorthand constructor."""
    return Quantity.of(value, unit)


def total(quantities: Iterable[Quantity], *, unit: "Unit | None" = None) -> Quantity:
    """Sum a sequence, converting to a single unit.

    Refuses an empty sequence rather than returning a dimensionless zero: a
    total of nothing has no dimension, and inventing one would let an empty
    inventory be added to a mass without complaint.
    """
    items = list(quantities)
    if not items and unit is None:
        raise UnitError(
            "cannot total an empty sequence without a unit: the result would "
            "have no dimension, and a dimensionless zero added to a mass is "
            "exactly the error this library exists to catch"
        )
    target = unit if unit is not None else items[0].unit
    if target.is_affine:
        raise UnitError(
            f"cannot total onto the affine scale {target}: a sum of readings "
            "depends on where the zero was put"
        )
    running = Quantity(Fraction(0), target)
    for item in items:
        running = running + item.to(target)
    return running


def ratio(numerator: Quantity, denominator: Quantity) -> Fraction:
    """The dimensionless ratio of two quantities of the same dimension.

    Returns a plain Fraction rather than a dimensionless Quantity, because the
    answer to "what fraction of the target is this" is a number, and wrapping
    it invites it to be multiplied back into something with a unit.
    """
    numerator._require_same_dimension(denominator, "take the ratio of")
    numerator._require_absolute("take the ratio of")
    denominator._require_absolute("take the ratio of")
    if denominator.si_value == 0:
        raise ZeroDivisionError(f"ratio against the zero quantity {denominator}")
    return numerator.si_value / denominator.si_value


__all__ = [
    "Magnitude",
    "Quantity",
    "format_magnitude",
    "quantity",
    "ratio",
    "total",
]
