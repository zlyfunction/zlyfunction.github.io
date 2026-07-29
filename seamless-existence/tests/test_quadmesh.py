import unittest

from seamless_existence.quadmesh import QuadMesh
from seamless_existence.search import enumerate_meshes, min_faces


def cube() -> QuadMesh:
    """The cube: 6 squares, 8 vertices of valence 3, genus 0.

    Faces are listed as counterclockwise vertex loops seen from outside, with
    cube vertices labelled by the bits of (x, y, z).
    """
    return QuadMesh.from_faces(
        [
            (0, 2, 3, 1),  # z = 0
            (4, 5, 7, 6),  # z = 1
            (0, 1, 5, 4),  # y = 0
            (2, 6, 7, 3),  # y = 1
            (0, 4, 6, 2),  # x = 0
            (1, 3, 7, 5),  # x = 1
        ]
    )


class TestQuadMesh(unittest.TestCase):
    def test_one_square_torus(self):
        mesh = QuadMesh(1, [2, 3, 0, 1])
        self.assertEqual(mesh.genus(), 1)
        self.assertEqual(mesh.valences(), [4])
        self.assertEqual(mesh.rho_subgroup(), 4)  # trivial holonomy: translation surface
        mesh.check_consistency()

    def test_cube(self):
        mesh = cube()
        self.assertTrue(mesh.is_connected())
        self.assertEqual(mesh.genus(), 0)
        self.assertEqual(sorted(mesh.valences()), [3] * 8)
        self.assertEqual(sorted(mesh.orders()), [-1] * 8)
        self.assertEqual(sum(mesh.orders()), 4 * (2 * 0 - 2))
        self.assertEqual(mesh.rho_subgroup(), 1)  # cones of angle 3pi/2 force Z_4
        mesh.check_consistency()

    def test_min_faces_matches_certificates(self):
        for n in (1, 2, 3):
            for mesh in enumerate_meshes(n):
                orders = [m for m in mesh.orders() if m != 0]
                n_marked = len(mesh.orders()) - len(orders)
                self.assertEqual(min_faces(mesh.genus(), orders) + n_marked, n)

    def test_exhaustive_consistency(self):
        """Gauss-Bonnet and holonomy-vs-valence hold for every small gluing."""
        for n in (1, 2, 3):
            for mesh in enumerate_meshes(n):
                mesh.check_consistency()

    def test_canonical_form_is_isomorphism_invariant(self):
        mesh = QuadMesh(2, [4, 5, 6, 7, 0, 1, 2, 3])
        self.assertTrue(mesh.is_connected())
        # relabel the two faces
        perm = {0: 1, 1: 0}
        n = 8
        relabel = [4 * perm[d // 4] + d % 4 for d in range(n)]
        alpha2 = [0] * n
        for d in range(n):
            alpha2[relabel[d]] = relabel[mesh.alpha[d]]
        other = QuadMesh(2, alpha2)
        self.assertEqual(mesh.canonical_form(), other.canonical_form())

    def test_from_faces_rejects_bad_orientation(self):
        with self.assertRaises(ValueError):
            # both faces list the edge (0, 1) in the same direction
            QuadMesh.from_faces([(0, 1, 2, 3), (0, 1, 4, 5)])

    def test_rejects_bad_gluings(self):
        with self.assertRaises(ValueError):
            QuadMesh(1, [0, 1, 2, 3])  # fixed points
        with self.assertRaises(ValueError):
            QuadMesh(1, [1, 2, 3, 0])  # not an involution


if __name__ == "__main__":
    unittest.main()
