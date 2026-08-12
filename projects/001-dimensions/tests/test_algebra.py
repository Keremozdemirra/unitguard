import unittest
from fractions import Fraction

from dimensions import (
    BASE, DIMENSIONLESS, ENERGY, INTENSITY, LENGTH, MASS, POWER, TIME,
    Dimension, DimensionError, parse,
)


def _rng(seed):
    import random
    return random.Random(seed)


def _random_dimension(rng):
    return Dimension({
        s: Fraction(rng.randint(-4, 4), rng.choice((1, 2, 3)))
        for s in rng.sample(list(BASE), rng.randint(0, len(BASE)))
    })


class GroupLaws(unittest.TestCase):
    """Dimensions under multiplication form an abelian group.

    That is not decoration -- it is the reason dimensional analysis works at
    all, and every one of these laws is something a checker downstream will
    silently rely on.
    """

    def setUp(self):
        self.rng = _rng(80122026)
        self.sample = [_random_dimension(self.rng) for _ in range(60)]

    def test_dimensionless_is_the_identity(self):
        for d in self.sample:
            self.assertEqual(d * DIMENSIONLESS, d)
            self.assertEqual(DIMENSIONLESS * d, d)

    def test_multiplication_is_associative(self):
        for _ in range(200):
            a, b, c = (self.rng.choice(self.sample) for _ in range(3))
            self.assertEqual((a * b) * c, a * (b * c))

    def test_multiplication_is_commutative(self):
        for _ in range(200):
            a, b = self.rng.choice(self.sample), self.rng.choice(self.sample)
            self.assertEqual(a * b, b * a)

    def test_every_dimension_has_an_inverse(self):
        for d in self.sample:
            self.assertEqual(d * (d ** -1), DIMENSIONLESS)
            self.assertEqual(d / d, DIMENSIONLESS)

    def test_division_is_multiplication_by_the_inverse(self):
        for _ in range(200):
            a, b = self.rng.choice(self.sample), self.rng.choice(self.sample)
            self.assertEqual(a / b, a * (b ** -1))


class PowerLaws(unittest.TestCase):
    def setUp(self):
        self.rng = _rng(11)
        self.sample = [_random_dimension(self.rng) for _ in range(40)]

    def test_exponents_add(self):
        for d in self.sample:
            for m in (-3, -1, 0, 1, 2, 5):
                for n in (-2, 0, 1, 4):
                    self.assertEqual(d ** m * d ** n, d ** (m + n))

    def test_exponents_multiply_when_nested(self):
        for d in self.sample:
            for m in (-2, 1, 3):
                for n in (-1, 2):
                    self.assertEqual((d ** m) ** n, d ** (m * n))

    def test_anything_to_the_zero_is_dimensionless(self):
        for d in self.sample:
            self.assertEqual(d ** 0, DIMENSIONLESS)

    def test_roots_are_exact_and_invert_powers(self):
        # The argument for Fraction over float, stated as a test: a half power
        # squared has to come back to exactly the same dimension, not nearly.
        for d in self.sample:
            for n in (2, 3, 5, 7):
                self.assertEqual(d.root(n) ** n, d)
                self.assertEqual((d ** Fraction(1, n)) ** n, d)

    def test_a_float_exponent_is_taken_at_face_value(self):
        self.assertEqual(ENERGY ** 0.5, ENERGY ** Fraction(1, 2))
        self.assertEqual((ENERGY ** 0.1) ** 10, ENERGY)

    def test_the_zeroth_root_is_refused(self):
        with self.assertRaises(DimensionError):
            ENERGY.root(0)

    def test_a_non_finite_exponent_is_refused(self):
        for bad in (float("nan"), float("inf")):
            with self.assertRaises(DimensionError):
                ENERGY ** bad


class EqualityIgnoresUnitsNotDimensions(unittest.TestCase):
    def test_energy_is_energy_however_it_was_built(self):
        # kWh, GJ and BTU differ only by a scale factor, and none of that
        # belongs here. All three are M L^2 T^-2.
        self.assertEqual(MASS * LENGTH ** 2 / TIME ** 2, ENERGY)
        self.assertEqual(POWER * TIME, ENERGY)
        self.assertEqual(ENERGY / TIME, POWER)

    def test_energy_is_not_mass(self):
        # The tCO2e-versus-MWh confusion, at the dimension level.
        self.assertNotEqual(ENERGY, MASS)
        self.assertNotEqual(INTENSITY, DIMENSIONLESS)

    def test_intensity_times_energy_is_mass(self):
        # tCO2e/MWh times MWh is tCO2e. If this ever fails the library is lying.
        self.assertEqual(INTENSITY * ENERGY, MASS)

    def test_zero_exponents_are_dropped_not_stored(self):
        built = Dimension({"L": 2, "M": 0, "T": 0})
        self.assertEqual(built, LENGTH ** 2)
        self.assertEqual(set(built.exponents), {"L"})

    def test_dimensions_are_hashable_and_usable_as_keys(self):
        table = {ENERGY: "energy", MASS: "mass"}
        self.assertEqual(table[POWER * TIME], "energy")
        self.assertEqual(len({ENERGY, MASS * LENGTH ** 2 / TIME ** 2}), 1)

    def test_equality_against_a_non_dimension_is_false_not_an_error(self):
        self.assertNotEqual(ENERGY, "M L^2 T^-2")
        self.assertNotEqual(ENERGY, 1)
        self.assertFalse(ENERGY == None)  # noqa: E711

    def test_dimensions_are_immutable(self):
        with self.assertRaises(AttributeError):
            ENERGY.foo = 1
        # And the exponents property must hand out a copy, not the internals.
        taken = ENERGY.exponents
        taken["L"] = Fraction(99)
        self.assertEqual(ENERGY.exponent("L"), 2)


class Refusals(unittest.TestCase):
    def test_an_unknown_base_symbol_is_refused(self):
        with self.assertRaises(DimensionError) as ctx:
            Dimension({"Q": 1})
        self.assertIn("not an SI base dimension", str(ctx.exception))

    def test_multiplying_by_a_number_is_refused_with_an_explanation(self):
        # Tempting, and always wrong: 3 kWh is not a different dimension.
        with self.assertRaises(DimensionError) as ctx:
            ENERGY * 3
        self.assertIn("scale the magnitude", str(ctx.exception))
        with self.assertRaises(DimensionError):
            ENERGY / 3

    def test_a_boolean_is_not_an_exponent(self):
        with self.assertRaises(DimensionError):
            Dimension({"L": True})


class Parsing(unittest.TestCase):
    def test_round_trip_through_str(self):
        rng = _rng(5)
        for _ in range(200):
            d = _random_dimension(rng)
            self.assertEqual(parse(str(d)), d)

    def test_an_unclosed_exponent_bracket_is_refused(self):
        with self.assertRaises(DimensionError):
            parse("L^(1/2")

    def test_the_documented_spellings_all_agree(self):
        for text in ("M·L^2·T^-2", "M L^2 T^-2", "M*L^2*T^-2", "L^2 M T^-2"):
            self.assertEqual(parse(text), ENERGY, text)

    def test_division_and_brackets(self):
        self.assertEqual(parse("M/(L T^2)"), MASS / (LENGTH * TIME ** 2))
        self.assertEqual(parse("M L^2 T^-2 / T"), POWER)

    def test_one_is_dimensionless(self):
        self.assertEqual(parse("1"), DIMENSIONLESS)
        self.assertEqual(str(DIMENSIONLESS), "1")

    def test_symbols_are_case_insensitive(self):
        self.assertEqual(parse("m l^2 t^-2"), ENERGY)

    def test_fractional_exponents_survive_the_round_trip(self):
        # Bracketed on output, because "L^1/2" is ambiguous with division --
        # the round-trip test caught str() and parse() disagreeing about it.
        d = LENGTH ** Fraction(1, 2)
        self.assertEqual(str(d), "L^(1/2)")
        self.assertEqual(parse("L^(1/2)"), d)
        with self.assertRaises(DimensionError):
            parse("L^1/2")

    def test_a_unit_string_is_refused_rather_than_guessed(self):
        # parse("kWh") must not quietly become energy. Units are the registry's
        # job; guessing here is exactly the failure this repository is about.
        for text in ("kWh", "tCO2e", "MWh/t"):
            with self.assertRaises(DimensionError, msg=text):
                parse(text)

    def test_ambiguous_double_division_is_refused(self):
        with self.assertRaises(DimensionError) as ctx:
            parse("M/L/T")
        self.assertIn("more than one", str(ctx.exception))

    def test_empty_and_malformed_input(self):
        for text in ("", "   ", "M^", "M^x", "/L"):
            with self.assertRaises(DimensionError, msg=repr(text)):
                parse(text)


class Display(unittest.TestCase):
    def test_str_orders_by_the_si_convention_not_by_insertion(self):
        built = Dimension({"T": -2, "M": 1, "L": 2})
        self.assertEqual(str(built), "L^2·M·T^-2")

    def test_describe_names_the_dimensions(self):
        self.assertIn("thermodynamic temperature", Dimension({"Th": 1}).describe())
        self.assertEqual(DIMENSIONLESS.describe(), "dimensionless")

    def test_repr_is_readable(self):
        self.assertEqual(repr(DIMENSIONLESS), "Dimension(1)")
        self.assertIn("L^2", repr(ENERGY))


if __name__ == "__main__":
    unittest.main()
