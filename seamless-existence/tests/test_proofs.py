"""Tests attached to specific statements of ``docs/proofs.md``.

Each test names the statement it checks.  The heavy versions of these checks live
in ``experiments/verify_proofs.py``; these are the fast ones that run on every
commit.
"""

import unittest

from seamless_existence.mcg import (
    content,
    handle_orbits,
    sp_generators,
    symplectic_product,
    transvection,
    verify_reduction_lemma,
    verify_sp_transitivity,
)
from seamless_existence.predict import EMPTY, classify_orders, predict
from seamless_existence.signature import Signature


class TestLemma6(unittest.TestCase):
    """Sp(2g, Z_4) is transitive on each content class."""

    def test_transitive_genus_1_and_2_full_generator_set(self):
        for genus in (1, 2):
            rep = verify_sp_transitivity(genus, count=None, powers=(1,))
            self.assertTrue(rep["transitive"], rep)
            # content classes of Z_4^{2g}: sizes 4^{2g} - 2^{2g}, 2^{2g} - 1, 1
            n = 2 * genus
            sizes = {d: info["class_size"] for d, info in rep["classes"].items()}
            self.assertEqual(sizes[1], 4**n - 2**n)
            self.assertEqual(sizes[2], 2**n - 1)
            self.assertEqual(sizes[4], 1)

    def test_content_is_invariant_under_transvections(self):
        from itertools import product

        for genus in (1, 2):
            gens = sp_generators(genus, powers=(1, 2, 3))
            for v in product(range(4), repeat=2 * genus):
                for c, p in gens:
                    self.assertEqual(content(transvection(v, c, p)), content(v))

    def test_transvection_powers_are_powers(self):
        """T_c^power really is the power of the transvection."""
        from itertools import product

        for c in product(range(4), repeat=4):
            for x in product(range(4), repeat=4):
                once = transvection(x, c)
                self.assertEqual(transvection(once, c), transvection(x, c, 2))
                self.assertEqual(
                    transvection(transvection(once, c), c), transvection(x, c, 3)
                )

    def test_transvections_are_symplectic(self):
        from itertools import product

        for c in product(range(4), repeat=2):
            for p in (1, 2, 3):
                for x in product(range(4), repeat=2):
                    for y in product(range(4), repeat=2):
                        self.assertEqual(
                            symplectic_product(
                                transvection(x, c, p), transvection(y, c, p)
                            ),
                            symplectic_product(x, y),
                        )


class TestTheorem8(unittest.TestCase):
    """image(rho) is a complete invariant of the MCG orbit."""

    # orders realizing each possible cone subgroup D, per genus
    CASES = {
        1: {1: (-1, 1), 2: (-2, 2), 4: (0, 0)},
        2: {1: (1, 7), 2: (2, 6), 4: (4, 4)},
    }
    EXPECTED_ORBITS = {1: 1, 2: 2, 4: 3}

    def test_orbit_counts_and_invariant(self):
        for genus, by_d in self.CASES.items():
            for d_cone, orders in by_d.items():
                chk = verify_reduction_lemma(genus, orders)
                self.assertTrue(chk["constant"], chk)
                self.assertTrue(chk["separating"], chk)
                self.assertEqual(chk["n_orbits"], self.EXPECTED_ORBITS[d_cone], chk)
                self.assertEqual(sum(chk["orbit_sizes"]), 4 ** (2 * genus), chk)

    def test_invariants_are_exactly_the_subgroups_containing_D(self):
        for genus, by_d in self.CASES.items():
            for d_cone, orders in by_d.items():
                chk = verify_reduction_lemma(genus, orders)
                seen = sorted(v[0] for v in chk["invariants"])
                expected = sorted(d for d in (1, 2, 4) if d_cone % d == 0)
                self.assertEqual(seen, expected)


class TestCorollary9(unittest.TestCase):
    def test_odd_order_gives_one_orbit(self):
        for genus, orders in [(1, (-1, 1)), (1, (-3, 3)), (2, (1, 7)), (2, (3, 5))]:
            self.assertTrue(any(m % 2 for m in orders))
            orbits = handle_orbits(genus, orders)
            self.assertEqual(len(orbits), 1)
            self.assertEqual(len(orbits[0]), 4 ** (2 * genus))

    def test_even_orders_do_not(self):
        for genus, orders in [(1, (-2, 2)), (2, (2, 6)), (2, (4, 4))]:
            self.assertFalse(any(m % 2 for m in orders))
            self.assertGreater(len(handle_orbits(genus, orders)), 1)


class TestCorollary13(unittest.TestCase):
    """The complete list of unrealizable signatures on the torus."""

    def test_the_three_exceptional_families(self):
        # (1) no cones, nontrivial holonomy
        for handle in [(1, 0), (2, 0), (0, 3)]:
            sig = Signature(1, (), handle)
            self.assertEqual(predict(sig).status, EMPTY, str(sig))
        self.assertNotEqual(predict(Signature(1, (), (0, 0))).status, EMPTY)

        # (2) two cones of angle 3pi/2 and 5pi/2 -- every rho, since D = Z_4
        for handle in [(0, 0), (1, 0), (2, 3)]:
            sig = Signature(1, (-1, 1), handle)
            self.assertEqual(sig.rho_subgroup(), 1)
            self.assertEqual(predict(sig).status, EMPTY, str(sig))

        # (3) two cones of angle pi and 3pi, but only with even holonomy
        self.assertEqual(predict(Signature(1, (-2, 2), (0, 0))).status, EMPTY)
        self.assertEqual(predict(Signature(1, (-2, 2), (2, 0))).status, EMPTY)
        self.assertNotEqual(predict(Signature(1, (-2, 2), (1, 0))).status, EMPTY)

    def test_nothing_else_in_a_sweep_is_empty(self):
        """Every other genus-1 signature with at most 3 cones is realizable."""
        exceptional = {((), 1), ((), 2), ((-1, 1), 1), ((-2, 2), 2)}
        for a in range(-3, 7):
            for b in range(-3, 7):
                for orders in [(a, -a), (a, b, -a - b)]:
                    if any(m <= -4 for m in orders) or any(m == 0 for m in orders):
                        continue
                    for sig, verdict in classify_orders(1, orders):
                        key = (tuple(sorted(orders)), sig.rho_subgroup())
                        if verdict.status == EMPTY:
                            self.assertIn(key, exceptional, str(sig))


if __name__ == "__main__":
    unittest.main()
