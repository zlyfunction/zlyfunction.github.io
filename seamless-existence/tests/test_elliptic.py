import unittest
from fractions import Fraction

from seamless_existence.elliptic import (
    ZERO,
    Pt,
    check_witness,
    combination,
    divide,
    divisor_witness,
    exact_order,
    largest_common_divisor_of_k,
    torsion_point,
)
from seamless_existence.predict import EMPTY, genus1_nonempty


class TestGroupArithmetic(unittest.TestCase):
    def test_reduction_mod_one(self):
        self.assertEqual(Pt(Fraction(5, 4), Fraction(-1, 3)), Pt(Fraction(1, 4), Fraction(2, 3)))

    def test_addition_and_negation(self):
        p = Pt(Fraction(1, 3), Fraction(1, 4))
        self.assertEqual(p + (-p), ZERO)
        self.assertEqual(3 * p, Pt(0, Fraction(3, 4)))

    def test_exact_order(self):
        self.assertEqual(exact_order(ZERO), 1)
        self.assertEqual(exact_order(torsion_point(4)), 4)
        self.assertEqual(exact_order(Pt(Fraction(1, 2), Fraction(1, 3))), 6)

    def test_torsion_point_has_exact_order(self):
        for e in range(1, 13):
            p = torsion_point(e)
            self.assertEqual(exact_order(p), e)
            self.assertTrue((e * p).is_zero())

    def test_divide_is_a_right_inverse(self):
        p = Pt(Fraction(3, 7), Fraction(2, 5))
        for n in (-4, -1, 1, 2, 3, 4, 6):
            self.assertEqual(n * divide(p, n), p)

    def test_combination(self):
        pts = [torsion_point(3), torsion_point(4)]
        self.assertEqual(combination([3, 4], pts), ZERO)


class TestPropositionA(unittest.TestCase):
    """The witnesses of docs/proofs.md Proposition 12, checked exactly."""

    KNOWN_EMPTY = [(4, (-1, 1)), (2, (-1, 1)), (2, ()), (4, ()), (4, (0, 0)), (2, (0, 0))]
    KNOWN_NONEMPTY = [
        (1, (0, 0)),
        (4, (-2, 2)),
        (2, (-2, 2)),
        (4, (-3, 3)),
        (4, (-3, 1, 2)),
        (4, (-2, -2, 4)),
        (4, (-1, -1, 2)),
        (2, (-1, -1, 2)),
        (4, (-3, -3, 6)),
        (4, (-2, 1, 1)),
        (4, (-1, -1, -1, 3)),
    ]

    def test_known_empty_have_no_witness(self):
        for k, mu in self.KNOWN_EMPTY:
            self.assertEqual(genus1_nonempty(k, mu).status, EMPTY, f"k={k} mu={mu}")
            self.assertIsNone(divisor_witness(k, mu), f"k={k} mu={mu}")

    def test_known_nonempty_have_verified_witnesses(self):
        for k, mu in self.KNOWN_NONEMPTY:
            self.assertNotEqual(genus1_nonempty(k, mu).status, EMPTY, f"k={k} mu={mu}")
            w = divisor_witness(k, mu)
            self.assertIsNotNone(w, f"no witness for k={k} mu={mu}")
            self.assertEqual(check_witness(k, mu, w), [], f"bad witness for k={k} mu={mu}")

    def test_criterion_and_construction_agree_on_a_range(self):
        """Sweep: the criterion is non-empty exactly when a witness is built.

        Note the sweep is smaller than it looks: ``sum mu_i = 0`` together with
        ``mu_i > -k`` bounds ``a + b`` by ``k - 1``.
        """
        cases = 0
        for k in (1, 2, 4):
            for a in range(-k + 1, 9):
                for b in range(-k + 1, 9):
                    mu = (a, b, -a - b)
                    if -a - b <= -k:
                        continue
                    cases += 1
                    empty = genus1_nonempty(k, mu).status == EMPTY
                    w = divisor_witness(k, mu)
                    self.assertEqual(empty, w is None, f"k={k} mu={mu}")
                    if w is not None:
                        self.assertEqual(check_witness(k, mu, w), [], f"k={k} mu={mu}")
        self.assertGreater(cases, 60)

    def test_e_star(self):
        self.assertEqual(largest_common_divisor_of_k(4, (2, -2)), 2)
        self.assertEqual(largest_common_divisor_of_k(4, (4, -4)), 4)
        self.assertEqual(largest_common_divisor_of_k(4, (3, -3)), 1)
        self.assertEqual(largest_common_divisor_of_k(2, (2, -2)), 2)

    def test_witness_of_the_pi_and_3pi_torus(self):
        """The pair that shows image(rho), not the cone angles, decides.

        Cone angles pi and 3pi on a torus: as a primitive 4-differential
        (mu = (-2, 2)) it exists, as a primitive quadratic differential
        (mu = (-1, 1)) it does not.
        """
        w = divisor_witness(4, (-2, 2))
        self.assertIsNotNone(w)
        self.assertEqual(check_witness(4, (-2, 2), w), [])
        self.assertEqual(exact_order(w[0] - w[1]), 2)  # a nonzero 2-torsion difference
        self.assertIsNone(divisor_witness(2, (-1, 1)))


if __name__ == "__main__":
    unittest.main()
