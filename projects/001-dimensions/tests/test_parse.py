"""Parsing a dimension string back into a Dimension."""

import random
import unittest
from fractions import Fraction

from unitguard_dimensions import (
    BASE_SYMBOLS, DIMENSIONLESS, EMISSION_INTENSITY, ENERGY, MASS, POWER,
    Dimension, DimensionError, parse,
)


def _random_dimension(rng):
    return Dimension.from_mapping({
        symbol: Fraction(rng.randint(-4, 4), rng.choice((1, 2, 3)))
        for symbol in rng.sample(list(BASE_SYMBOLS), rng.randint(0, len(BASE_SYMBOLS)))
    })


class RoundTrip(unittest.TestCase):
    """The property worth having: what __str__ writes, parse must read back.

    Without it a dimension cannot safely be put in a config file, a column
    header or a docstring, because the value that comes back is not reliably
    the value that went out.
    """

    def test_str_and_parse_are_inverse_over_random_dimensions(self):
        rng = random.Random(812)
        for _ in range(300):
            dimension = _random_dimension(rng)
            self.assertEqual(parse(str(dimension)), dimension, str(dimension))

    def test_the_named_dimensions_round_trip(self):
        for named in (ENERGY, POWER, MASS, EMISSION_INTENSITY, DIMENSIONLESS):
            self.assertEqual(parse(str(named)), named, str(named))

    def test_fractional_exponents_are_bracketed_and_read_back(self):
        half = Dimension.from_mapping({"L": Fraction(1, 2)})
        self.assertEqual(str(half), "L^(1/2)")
        self.assertEqual(parse("L^(1/2)"), half)


class AcceptedSpellings(unittest.TestCase):
    def test_multiplication_may_be_written_three_ways(self):
        for text in ("M·L^2·T^-2", "M L^2 T^-2", "M*L^2*T^-2", "L^2 M T^-2"):
            self.assertEqual(parse(text), ENERGY, text)

    def test_division_and_grouping(self):
        self.assertEqual(parse("M/(L^2 M T^-2)"), EMISSION_INTENSITY)
        self.assertEqual(parse("M L^2 T^-2 / T"), POWER)

    def test_one_is_dimensionless(self):
        self.assertEqual(parse("1"), DIMENSIONLESS)
        self.assertEqual(str(DIMENSIONLESS), "1")

    def test_symbols_are_case_insensitive(self):
        self.assertEqual(parse("m l^2 t^-2"), ENERGY)

    def test_theta_may_be_typed_as_th(self):
        # The Greek letter is correct and awkward to type. A parser that only
        # accepts the awkward form gets worked around rather than used.
        theta = Dimension.from_mapping({"Θ": 2})
        for text in ("Θ^2", "th^2", "TH^2", "theta^2"):
            self.assertEqual(parse(text), theta, text)


class Refusals(unittest.TestCase):
    def test_a_unit_string_is_refused_rather_than_guessed(self):
        # parse("kWh") must not quietly become energy. Units are the registry's
        # job, and guessing here is the exact failure this repository is about.
        for text in ("kWh", "tCO2e", "MWh/t", "joule"):
            with self.assertRaises(DimensionError, msg=text):
                parse(text)

    def test_the_error_names_the_offending_symbol_and_the_alternatives(self):
        with self.assertRaises(DimensionError) as ctx:
            parse("kWh")
        message = str(ctx.exception)
        self.assertIn("kWh", message)
        self.assertIn("not units", message)

    def test_chained_division_is_refused_as_ambiguous(self):
        with self.assertRaises(DimensionError) as ctx:
            parse("M/L/T")
        self.assertIn("more than one", str(ctx.exception))

    def test_a_bare_fractional_exponent_is_refused(self):
        # L^1/2 cannot be told apart from division without guessing.
        with self.assertRaises(DimensionError):
            parse("L^1/2")

    def test_an_unclosed_exponent_bracket_is_refused(self):
        with self.assertRaises(DimensionError) as ctx:
            parse("L^(1/2")
        self.assertIn("unclosed", str(ctx.exception))

    def test_empty_and_malformed_input(self):
        for text in ("", "   ", "M^", "M^x", "/L", None, 7):
            with self.assertRaises(DimensionError, msg=repr(text)):
                parse(text)


if __name__ == "__main__":
    unittest.main()
