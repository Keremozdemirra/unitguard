"""The dimension type and its algebra.

A dimension is an exponent vector over the seven SI base dimensions. That is
the whole idea, and it is worth stating plainly because it is what makes the
arithmetic exact: multiplying quantities adds exponent vectors, dividing
subtracts them, raising to a power scales them.

**Exponents are rational, not integer.** The square root of an area is a
length, and a model that takes the square root of a variance in tCO2e-squared
is doing something meaningful. Integer exponents would refuse it. Floats would
make ``(d ** 0.1) ** 10 == d`` fail, and dimension equality has to be exact --
"nearly the same dimension" is not a thing. ``fractions.Fraction`` gives both.
"""

from fractions import Fraction
from typing import Dict, Iterable, Mapping, Tuple

#: The seven SI base dimensions, in the conventional order. Symbols follow
#: ISO 80000-1: L length, M mass, T time, I electric current, Θ thermodynamic
#: temperature, N amount of substance, J luminous intensity.
BASE: Tuple[str, ...] = ("L", "M", "T", "I", "Th", "N", "J")

_NAMES = {
    "L": "length",
    "M": "mass",
    "T": "time",
    "I": "electric current",
    "Th": "thermodynamic temperature",
    "N": "amount of substance",
    "J": "luminous intensity",
}


class DimensionError(ValueError):
    """An operation is not defined on these dimensions."""


class Dimension:
    """An exponent vector over the SI base dimensions.

    Immutable and hashable, so dimensions can be dictionary keys and set
    members -- which is how the registry and the formula checker will use them.
    """

    __slots__ = ("_exponents", "_hash")

    def __init__(self, exponents: Mapping[str, object] = ()):
        cleaned: Dict[str, Fraction] = {}
        items = exponents.items() if hasattr(exponents, "items") else exponents
        for symbol, power in items:
            if symbol not in _NAMES:
                raise DimensionError(
                    "%r is not an SI base dimension. The seven are: %s"
                    % (symbol, ", ".join(BASE))
                )
            power = _as_fraction(power, symbol)
            if power:                      # a zero exponent is simply absent
                cleaned[symbol] = cleaned.get(symbol, Fraction(0)) + power
        # Re-drop anything that cancelled to zero during accumulation.
        cleaned = {k: v for k, v in cleaned.items() if v}
        object.__setattr__(self, "_exponents", cleaned)
        object.__setattr__(self, "_hash", hash(tuple(sorted(cleaned.items()))))

    # -- construction ----------------------------------------------------

    @classmethod
    def base(cls, symbol: str) -> "Dimension":
        return cls({symbol: 1})

    # -- introspection ---------------------------------------------------

    @property
    def exponents(self) -> Dict[str, Fraction]:
        """A copy of the non-zero exponents, keyed by base symbol."""
        return dict(self._exponents)

    def exponent(self, symbol: str) -> Fraction:
        if symbol not in _NAMES:
            raise DimensionError("%r is not an SI base dimension" % symbol)
        return self._exponents.get(symbol, Fraction(0))

    @property
    def is_dimensionless(self) -> bool:
        return not self._exponents

    # -- algebra ---------------------------------------------------------

    def __mul__(self, other: "Dimension") -> "Dimension":
        _require(other, "multiply")
        merged = dict(self._exponents)
        for symbol, power in other._exponents.items():
            merged[symbol] = merged.get(symbol, Fraction(0)) + power
        return Dimension(merged)

    def __truediv__(self, other: "Dimension") -> "Dimension":
        _require(other, "divide")
        return self * other ** -1

    def __pow__(self, power) -> "Dimension":
        power = _as_fraction(power, "exponent")
        return Dimension({s: p * power for s, p in self._exponents.items()})

    def root(self, n: int) -> "Dimension":
        """The n-th root. Raises if any exponent would stop being rational-exact.

        It never does -- Fraction is closed under division by a non-zero
        integer -- which is precisely the argument for using Fraction here.
        """
        n = int(n)
        if n == 0:
            raise DimensionError("the zeroth root is undefined")
        return self ** Fraction(1, n)

    # -- identity --------------------------------------------------------

    def __eq__(self, other) -> bool:
        if not isinstance(other, Dimension):
            return NotImplemented
        return self._exponents == other._exponents

    def __ne__(self, other) -> bool:
        result = self.__eq__(other)
        return result if result is NotImplemented else not result

    def __hash__(self) -> int:
        return self._hash

    def __setattr__(self, name, value):
        raise AttributeError("Dimension is immutable")

    # -- display ---------------------------------------------------------

    def __repr__(self) -> str:
        return "Dimension(%s)" % (str(self) or "1")

    def __str__(self) -> str:
        if not self._exponents:
            return "1"
        parts = []
        for symbol in BASE:
            power = self._exponents.get(symbol)
            if power is None:
                continue
            if power == 1:
                parts.append(symbol)
            else:
                parts.append("%s^%s" % (symbol, _format_power(power)))
        return "·".join(parts)

    def describe(self) -> str:
        """A sentence naming the base dimensions involved, for error messages."""
        if not self._exponents:
            return "dimensionless"
        return ", ".join(
            "%s^%s" % (_NAMES[s], _format_power(self._exponents[s]))
            for s in BASE if s in self._exponents
        )


def _require(other, verb):
    if not isinstance(other, Dimension):
        raise DimensionError(
            "can only %s a Dimension by another Dimension, got %s. A dimension "
            "times a number is still that dimension -- scale the magnitude, not "
            "the dimension." % (verb, type(other).__name__)
        )


def _as_fraction(power, where) -> Fraction:
    if isinstance(power, Fraction):
        return power
    if isinstance(power, bool):
        raise DimensionError("%s: a boolean is not an exponent" % where)
    if isinstance(power, int):
        return Fraction(power)
    if isinstance(power, float):
        if power != power or power in (float("inf"), float("-inf")):
            raise DimensionError("%s: exponent must be finite, got %r" % (where, power))
        # limit_denominator keeps 0.5 as 1/2 rather than as the binary
        # approximation, which is what makes (d ** 0.5) ** 2 == d hold exactly.
        return Fraction(power).limit_denominator(1_000_000)
    if isinstance(power, str):
        try:
            return Fraction(power)
        except (ValueError, ZeroDivisionError):
            raise DimensionError("%s: %r is not a number" % (where, power))
    raise DimensionError("%s: exponent must be a number, got %s"
                         % (where, type(power).__name__))


def _format_power(power: Fraction) -> str:
    """Render an exponent so that ``parse(str(d)) == d`` holds.

    Non-integer exponents are bracketed. Without that, ``Th^-3/2`` comes back
    out of ``str`` and the parser reads the slash as division -- which is
    exactly what the round-trip test caught.
    """
    if power.denominator == 1:
        return str(power.numerator)
    return "(%s)" % power


DIMENSIONLESS = Dimension()
LENGTH = Dimension.base("L")
MASS = Dimension.base("M")
TIME = Dimension.base("T")
CURRENT = Dimension.base("I")
TEMPERATURE = Dimension.base("Th")
AMOUNT = Dimension.base("N")
LUMINOSITY = Dimension.base("J")

#: Energy: M·L²·T⁻². Named because it is the dimension this whole repository
#: exists to police -- kWh, MWh, GJ, therms and BTU are all this.
ENERGY = MASS * LENGTH ** 2 / TIME ** 2
POWER = ENERGY / TIME
#: Emission intensity: mass per energy. tCO2e/MWh and kg/GJ are both this.
INTENSITY = MASS / ENERGY


_SYMBOL_LOOKUP = {s.lower(): s for s in BASE}


def parse(text: str) -> Dimension:
    """Parse a dimension expression such as ``"L^2·M·T^-2"`` or ``"M/(L T^2)"``.

    Accepts ``*``, ``·`` or whitespace for multiplication, ``/`` for division,
    ``^`` for exponentiation, and brackets for grouping. A non-integer exponent
    must be bracketed -- ``L^(1/2)`` -- because ``L^1/2`` is genuinely ambiguous
    with division and guessing between the two is not this library's business.

    Deliberately narrow: this parses *dimensions*, not units. ``parse("kWh")``
    is an error, and should be -- mapping unit strings onto dimensions is the
    registry's job, and conflating the two is how a library ends up guessing.
    """
    if not isinstance(text, str) or not text.strip():
        raise DimensionError("nothing to parse")
    body = _protect_exponents(text.strip(), text)
    if body == "1":
        return DIMENSIONLESS

    parts = body.split("/")
    if len(parts) > 2:
        raise DimensionError(
            "%r has more than one '/'. Chained division reads differently to "
            "different people, so it is refused rather than guessed; bracket "
            "the denominator instead." % text
        )
    result = _parse_product(parts[0], text)
    if len(parts) == 2:
        result = result / _parse_product(parts[1], text)
    return result


#: Stands in for a '/' that belongs to a bracketed exponent rather than to
#: division, so the top-level split cannot mistake one for the other.
_SLASH = "\x00"


def _protect_exponents(body: str, original: str) -> str:
    """Hide slashes inside ``^( ... )`` from the division split."""
    out = []
    i = 0
    while i < len(body):
        if body[i] == "^" and i + 1 < len(body) and body[i + 1] == "(":
            close = body.find(")", i + 2)
            if close == -1:
                raise DimensionError("%r: unclosed bracket after '^'" % original)
            out.append("^" + body[i + 2:close].replace("/", _SLASH))
            i = close + 1
            continue
        out.append(body[i])
        i += 1
    return "".join(out)


def _parse_product(chunk: str, original: str) -> Dimension:
    chunk = chunk.replace("(", " ").replace(")", " ").replace("·", " ").replace("*", " ")
    tokens = chunk.split()
    if not tokens:
        raise DimensionError("%r: empty factor" % original)
    result = DIMENSIONLESS
    for token in tokens:
        symbol, sep, power = token.partition("^")
        key = _SYMBOL_LOOKUP.get(symbol.lower())
        if key is None:
            raise DimensionError(
                "%r: %r is not an SI base dimension symbol. Expected one of %s. "
                "This parses dimensions, not units."
                % (original, symbol.replace(_SLASH, "/"), ", ".join(BASE))
            )
        exponent = _as_fraction(power.replace(_SLASH, "/"), original) if sep else 1
        result = result * Dimension({key: exponent})
    return result
