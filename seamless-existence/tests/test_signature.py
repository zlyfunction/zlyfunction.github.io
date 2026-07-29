import unittest

from seamless_existence.signature import Signature, subgroup_generator


class TestSignature(unittest.TestCase):
    def test_gauss_bonnet_enforced(self):
        Signature(1, (-1, 1), (0, 0))  # sum 0 = 4*(2*1-2)
        with self.assertRaises(ValueError):
            Signature(1, (-1, 2), (0, 0))
        with self.assertRaises(ValueError):
            Signature(2, (7,), (0, 0, 0, 0))  # needs sum 8

    def test_cone_angle_positive(self):
        with self.assertRaises(ValueError):
            Signature(0, (-4, -4), ())

    def test_angles_and_valences(self):
        sig = Signature(1, (-1, 1), (0, 0))
        self.assertEqual(sig.cone_angles_in_quarter_turns(), (3, 5))

    def test_subgroup_generator(self):
        self.assertEqual(subgroup_generator([]), 4)
        self.assertEqual(subgroup_generator([0, 0]), 4)
        self.assertEqual(subgroup_generator([2, 0]), 2)
        self.assertEqual(subgroup_generator([2, 3]), 1)
        self.assertEqual(subgroup_generator([4, 8]), 4)

    def test_reduction_to_differential(self):
        # 3pi/2 and 5pi/2 on a torus: a genuine 4-differential
        sig = Signature(1, (-1, 1), (0, 0))
        self.assertEqual(sig.rho_subgroup(), 1)
        self.assertEqual(sig.differential_order, 4)
        self.assertEqual(sig.reduced_orders(), (-1, 1))

        # pi and 3pi with trivial handle holonomy: a half-translation surface
        sig = Signature(1, (-2, 2), (0, 0))
        self.assertEqual(sig.differential_order, 2)
        self.assertEqual(sig.reduced_orders(), (-1, 1))

        # the same cones with an odd handle rotation: back to a 4-differential
        sig = Signature(1, (-2, 2), (1, 0))
        self.assertEqual(sig.differential_order, 4)
        self.assertEqual(sig.reduced_orders(), (-2, 2))

        # all angles multiples of 2pi and trivial holonomy: a translation surface
        sig = Signature(2, (8,), (0, 0, 0, 0))
        self.assertEqual(sig.differential_order, 1)
        self.assertEqual(sig.reduced_orders(), (2,))

    def test_puncture_rotations_sum_to_zero(self):
        for sig in [
            Signature(1, (-1, 1), (0, 0)),
            Signature(2, (1, 7), (0, 0, 0, 0)),
            Signature(0, (-3, -3, -2), ()),
        ]:
            self.assertEqual(sum(sig.puncture_rotations()) % 4, 0)

    def test_orbit_invariant_ignores_basis_choice(self):
        a = Signature(1, (-2, 2), (1, 0))
        b = Signature(1, (2, -2), (0, 3))
        self.assertEqual(a.orbit_invariant(), b.orbit_invariant())


if __name__ == "__main__":
    unittest.main()
