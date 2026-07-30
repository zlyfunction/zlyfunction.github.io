"""Tests for the feature-curve (boundary) machinery of ``docs/proofs.md`` §8."""

import unittest
from math import gcd

from seamless_existence.quadmesh import BoundaryInvariant, QuadMesh
from seamless_existence.search import (
    enumerate_meshes_any,
    min_faces_boundary,
    search_boundary_target,
    strip_start,
)
from seamless_existence.signature import subgroup_generator


fan = QuadMesh.fan


class TestBoundaryBasics(unittest.TestCase):
    def test_unit_square(self):
        m = QuadMesh(1, [0, 1, 2, 3])
        self.assertTrue(m.has_boundary())
        self.assertEqual((m.genus(), m.n_boundary_components()), (0, 1))
        self.assertEqual(sorted(m.corner_angles()), [1, 1, 1, 1])
        self.assertEqual(m.turning(), 4)
        m.check_consistency()

    def test_cylinder(self):
        alpha = list(range(8))
        for a, b in ((0, 6), (2, 4)):
            alpha[a], alpha[b] = b, a
        m = QuadMesh(2, alpha)
        self.assertEqual((m.genus(), m.n_boundary_components()), (0, 2))
        self.assertEqual(m.turning(), 0)
        m.check_consistency()

    def test_fans(self):
        for k in (1, 2, 3, 5, 7):
            m = fan(k)
            m.check_consistency()
            self.assertEqual(m.genus(), 0)
            self.assertEqual(m.n_boundary_components(), 1)
            self.assertEqual(sorted(m.orders()), [k - 4])
            self.assertEqual(sorted(m.corner_angles()), sorted([1] * k + [2] * k)[: 2 * k])
            # Gauss-Bonnet with boundary, Lemma 14
            self.assertEqual(
                sum(4 - (o + 4) for o in m.orders()) + m.turning(),
                4 * m.euler_characteristic(),
            )

    def test_odd_turning_exists(self):
        """A single boundary component can have odd turning -- Corollary 17's trigger."""
        m = fan(3)
        self.assertEqual(m.turning() % 2, 1)
        d = subgroup_generator(list(m.orders()) + [m.turning()])
        self.assertEqual(d, 1)  # D = Z_4, so the holonomy cannot obstruct

    def test_gauss_bonnet_parity(self):
        """Lemma 14: sum m_i + sum a_j is even for every realizable signature."""
        for n in (1, 2):
            for m in enumerate_meshes_any(n):
                total = sum(m.orders()) + sum(m.corner_angles())
                self.assertEqual(total % 2, 0)

    def test_min_faces_boundary(self):
        for n in (1, 2):
            for m in enumerate_meshes_any(n):
                self.assertEqual(min_faces_boundary(m.orders(), m.corner_angles()), n)

    def test_strip_start_is_a_disk(self):
        for n in (1, 2, 3, 4):
            self.assertEqual(strip_start(n), list(QuadMesh.strip(n).alpha))
            m = QuadMesh(n, strip_start(n))
            self.assertTrue(m.is_connected())
            self.assertEqual((m.genus(), m.n_boundary_components()), (0, 1))
            m.check_consistency()

    def test_exhaustive_consistency_with_boundary(self):
        for n in (1, 2):
            for m in enumerate_meshes_any(n):
                m.check_consistency()


class TestDoubling(unittest.TestCase):
    """Lemma 18."""

    def predicted(self, m):
        g, b = m.genus(), m.n_boundary_components()
        orders = list(m.orders()) * 2 + [2 * a - 4 for a in m.corner_angles()]
        lower = subgroup_generator(
            [m.rho_subgroup()] + [(2 * a) % 4 for a in m.corner_angles()]
        )
        return 2 * g + b - 1, tuple(sorted(orders)), lower

    def test_doubled_square_is_the_pillowcase(self):
        d = QuadMesh(1, [0, 1, 2, 3]).double()
        d.check_consistency()
        self.assertEqual(d.genus(), 0)
        self.assertEqual(sorted(d.orders()), [-2, -2, -2, -2])
        self.assertEqual(d.rho_subgroup(), 2)  # a half-translation surface

    def test_genus_and_orders_and_inclusion(self):
        checked = 0
        for n in (1, 2):
            for m in enumerate_meshes_any(n):
                if not m.has_boundary():
                    continue
                d = m.double()
                d.check_consistency()
                inv = d.invariant()
                want_g, want_orders, lower = self.predicted(m)
                self.assertEqual(inv.genus, want_g)
                self.assertEqual(inv.orders, want_orders)
                # image(rho~) must contain the predicted subgroup
                self.assertEqual(gcd(lower, inv.rho_subgroup), inv.rho_subgroup)
                checked += 1
        self.assertGreater(checked, 400)

    def test_inclusion_can_be_strict(self):
        """The double can carry holonomy the boundary signature does not.

        Reflecting across boundary edges of different directions contributes a
        rotation by pi, so ``image(rho~)`` is only *contained in* by the predicted
        subgroup, not equal to it.
        """
        # smallest example, found by exhaustive search over three squares:
        # a genus-0 surface with three straight boundary circles and trivial rho
        m = QuadMesh(3, [0, 3, 4, 1, 2, 5, 8, 7, 6, 11, 10, 9])
        m.check_consistency()
        self.assertEqual((m.genus(), m.n_boundary_components()), (0, 3))
        self.assertEqual(m.rho_subgroup(), 4)  # trivial holonomy on M
        _, _, lower = self.predicted(m)
        self.assertEqual(lower, 4)
        self.assertEqual(m.double().rho_subgroup(), 2)  # but not on the double

    def test_closed_mesh_cannot_be_doubled(self):
        with self.assertRaises(ValueError):
            QuadMesh(1, [2, 3, 0, 1]).double()


class TestBoundarySearch(unittest.TestCase):
    def test_certifies_a_few_signatures(self):
        targets = [
            BoundaryInvariant(0, 1, (), ((1, 1, 1, 1),), 4),
            BoundaryInvariant(0, 2, (), ((), ()), 4),
            BoundaryInvariant(0, 1, (-3,), ((1,),), 1),
            BoundaryInvariant(0, 1, (-1,), ((1, 1, 1),), 1),
        ]
        for t in targets:
            mesh = search_boundary_target(t, extra_regular=1, iters=8000, restarts=2)
            self.assertIsNotNone(mesh, f"no certificate for {t}")
            mesh.check_consistency()
            self.assertEqual(mesh.boundary_invariant().stripped(), t)


if __name__ == "__main__":
    unittest.main()
