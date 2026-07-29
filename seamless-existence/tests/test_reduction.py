"""Tests of the Reduction Lemma and of the cross-checks between theory and search.

The interesting ones are ``test_known_empty_strata_are_not_realized`` and
``test_genus1_rule_reproduces_masur_smillie``: the search engine and the quoted
literature are independent, so agreeing on the four known empty strata is real
evidence that the dictionary in ``docs/dictionary.md`` is right.
"""

import unittest

from seamless_existence.mcg import handle_orbits, transvection, verify_reduction_lemma
from seamless_existence.predict import EMPTY, EXISTS, classify_orders, predict
from seamless_existence.search import search_target
from seamless_existence.signature import Signature

# (genus, orders, image(rho) generator) for the strata known to be empty
KNOWN_EMPTY = [
    (1, (-1, 1), 1),  # IKRSS 2013: no 3,5-quadrangulation of the torus
    (1, (-2, 2), 2),  # Masur-Smillie: Q(1,-1)
    (2, (8,), 2),  # Masur-Smillie: Q(4)
    (2, (2, 6), 2),  # Masur-Smillie: Q(1,3)
]

KNOWN_NONEMPTY = [
    (1, (-2, 2), 1),
    (1, (-3, 3), 1),
    (2, (8,), 1),
    (2, (8,), 4),
    (2, (2, 6), 1),
    (0, (-3, -3, -1, -1), 1),
]


def _signature(genus, orders, d):
    for sig, _ in classify_orders(genus, orders):
        if sig.rho_subgroup() == d:
            return sig
    raise AssertionError(f"no orbit with image(rho) = <{d}> for g={genus} m={orders}")


class TestReductionLemma(unittest.TestCase):
    def test_orbit_invariant_is_complete(self):
        for genus in (1, 2):
            for orders in [(-1, 1), (-2, 2), (0, 0), (4, -4), (8,), (2, 6), (1, 7)]:
                if sum(orders) != 4 * (2 * genus - 2):
                    continue
                chk = verify_reduction_lemma(genus, orders)
                self.assertTrue(chk["constant"], chk)
                self.assertTrue(chk["separating"], chk)

    def test_odd_cone_collapses_all_holonomy_choices(self):
        """A cone of angle an odd multiple of pi/2 makes rho irrelevant.

        This is the mechanism behind the gcd condition of Shen et al. 2022.
        """
        for genus in (1, 2):
            orders = (-1, 1) if genus == 1 else (1, 7)
            orbits = handle_orbits(genus, orders)
            self.assertEqual(len(orbits), 1)
            self.assertEqual(len(orbits[0]), 4 ** (2 * genus))

    def test_all_even_cones_leave_two_or_three_orbits(self):
        self.assertEqual(len(handle_orbits(1, (-2, 2))), 2)  # D = 2Z_4
        self.assertEqual(len(handle_orbits(1, (0, 0))), 3)  # D = 0
        self.assertEqual(len(handle_orbits(2, (4, 4))), 3)  # D = 0

    def test_transvection_preserves_symplectic_form(self):
        from itertools import product

        from seamless_existence.mcg import symplectic_product

        for c in product(range(4), repeat=2):
            for x in product(range(4), repeat=2):
                for y in product(range(4), repeat=2):
                    self.assertEqual(
                        symplectic_product(transvection(x, c), transvection(y, c)),
                        symplectic_product(x, y),
                    )


class TestTheoryAgainstSearch(unittest.TestCase):
    def test_known_empty_strata_are_predicted_empty(self):
        for genus, orders, d in KNOWN_EMPTY:
            sig = _signature(genus, orders, d)
            self.assertEqual(predict(sig).status, EMPTY, f"{sig}")

    def test_known_empty_strata_are_not_realized(self):
        for genus, orders, d in KNOWN_EMPTY:
            mesh = search_target((genus, tuple(sorted(orders)), d), extra_regular=2,
                                 iters=4000, restarts=2)
            self.assertIsNone(mesh, f"found a mesh for a known-empty stratum: {orders}")

    def test_known_nonempty_strata_are_certified(self):
        for genus, orders, d in KNOWN_NONEMPTY:
            sig = _signature(genus, orders, d)
            # the theory may legitimately say "unknown" (genus >= 2, k = 4); it
            # must never say "empty" for something the search realizes
            self.assertNotEqual(predict(sig).status, EMPTY, f"{sig}")
            mesh = search_target((genus, tuple(sorted(orders)), d), extra_regular=2,
                                 iters=4000, restarts=2)
            self.assertIsNotNone(mesh, f"no certificate for {sig}")
            mesh.check_consistency()

    def test_genus1_rule_reproduces_masur_smillie(self):
        """The Abel-Jacobi rule and Masur-Smillie's list must agree in genus 1."""
        from seamless_existence.predict import genus1_nonempty

        self.assertEqual(genus1_nonempty(2, ()).status, EMPTY)  # Q(empty)
        self.assertEqual(genus1_nonempty(2, (1, -1)).status, EMPTY)  # Q(1,-1)
        self.assertEqual(genus1_nonempty(2, (2, -2)).status, EXISTS)
        self.assertEqual(genus1_nonempty(1, ()).status, EXISTS)  # flat torus

    def test_no_realized_mesh_is_predicted_empty(self):
        """Every gluing of at most 3 squares must agree with the theory module.

        This is the strongest available check on the whole pipeline: 9603 meshes,
        each with an independently computed signature, none of which may land in a
        stratum that ``predict`` calls empty.
        """
        from seamless_existence.search import collect_certificates, enumerate_meshes

        table = {}
        for n in (1, 2, 3):
            collect_certificates(enumerate_meshes(n), into=table)
        for genus, orders, d in table:
            sig = _signature(genus, orders, d)
            self.assertNotEqual(
                predict(sig).status, EMPTY, f"realized but predicted empty: {sig}"
            )

    def test_genus0_is_always_realizable(self):
        sig = Signature(0, (-3, -3, -2), ())
        self.assertEqual(predict(sig).status, EXISTS)


if __name__ == "__main__":
    unittest.main()
