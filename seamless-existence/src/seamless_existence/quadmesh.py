"""Square-tiled quarter-translation surfaces = combinatorial quad meshes.

A closed quad mesh built from ``N`` unit squares *is* a seamless parametrization:
each square is a chart, transitions across edges are rotations by multiples of
pi/2 plus translations, and every vertex of valence ``v`` is a cone of angle
``v * pi/2``.  So every such mesh is an existence certificate for its own
holonomy signature.

Combinatorial model
-------------------
Darts are pairs ``(f, s)`` encoded as ``4 * f + s`` with ``s in {0, 1, 2, 3}``:
dart ``(f, s)`` is side ``s`` of face ``f``, traversed counterclockwise from
corner ``s`` to corner ``s + 1``.

* ``sigma(f, s) = (f, s + 1)`` is the face rotation.
* ``alpha`` is a fixed-point-free involution on darts (the gluing).
* Vertices are the orbits of ``nu = alpha . sigma^{-1}``; the orbit through a
  dart consists of all darts whose *tail* is that vertex, so ``|orbit| = valence``.

Orienting side ``s`` so that its outward normal points in direction ``s``, gluing
side ``s`` of ``f`` to side ``t`` of ``g`` means the outward normal of ``s`` is
identified with the *inward* normal of ``t``, i.e. the chart transition from
``f`` to ``g`` is the rotation

    r = (t - s + 2) mod 4,

which is antisymmetric under swapping ``(f, s)`` and ``(g, t)``, as it must be.

The rotational holonomy ``rho`` is read off the dual graph: the dual 1-skeleton
is a deformation retract of ``M`` minus the vertices, so cycles in the dual graph
generate ``H_1(M \\ C)``, and ``rho`` of a cycle is the sum of its transition
rotations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .signature import Signature, subgroup_generator

__all__ = ["QuadMesh", "MeshInvariant"]


@dataclass(frozen=True)
class MeshInvariant:
    """What a mesh certifies: genus, sorted cone orders, ``image(rho)``."""

    genus: int
    orders: tuple[int, ...]
    rho_subgroup: int

    def as_tuple(self) -> tuple[int, tuple[int, ...], int]:
        return (self.genus, self.orders, self.rho_subgroup)

    def stripped(self) -> "MeshInvariant":
        """Forget marked points (orders equal to 0).

        Existence does not see them: deleting a marked point leaves the flat
        structure untouched, and its loop has trivial holonomy, so ``image(rho)``
        is unchanged.
        """
        return MeshInvariant(
            self.genus,
            tuple(m for m in self.orders if m != 0),
            self.rho_subgroup,
        )


class QuadMesh:
    """A closed quad mesh given by a gluing involution on ``4 * n_faces`` darts."""

    __slots__ = ("n_faces", "alpha")

    def __init__(self, n_faces: int, alpha: Sequence[int], validate: bool = True):
        if validate:
            if len(alpha) != 4 * n_faces:
                raise ValueError("alpha must have length 4 * n_faces")
            for d, e in enumerate(alpha):
                if alpha[e] != d:
                    raise ValueError("alpha must be an involution")
                if e == d:
                    raise ValueError("alpha must be fixed-point free")
        self.n_faces = n_faces
        self.alpha = tuple(alpha)

    # ------------------------------------------------------------- primitives

    @staticmethod
    def face(d: int) -> int:
        return d >> 2

    @staticmethod
    def side(d: int) -> int:
        return d & 3

    @staticmethod
    def sigma(d: int) -> int:
        return (d & ~3) | ((d + 1) & 3)

    @staticmethod
    def sigma_inv(d: int) -> int:
        return (d & ~3) | ((d - 1) & 3)

    def nu(self, d: int) -> int:
        """Next dart around the tail vertex of ``d``."""
        return self.alpha[self.sigma_inv(d)]

    def rotation(self, d: int) -> int:
        """Chart transition from ``face(d)`` to ``face(alpha(d))``, in quarter turns."""
        e = self.alpha[d]
        return (self.side(e) - self.side(d) + 2) % 4

    # ------------------------------------------------------------- topology

    def is_connected(self) -> bool:
        seen = {0}
        stack = [0]
        while stack:
            d = stack.pop()
            for e in (self.sigma(d), self.alpha[d]):
                if e not in seen:
                    seen.add(e)
                    stack.append(e)
        return len(seen) == 4 * self.n_faces

    def vertex_orbits(self) -> list[list[int]]:
        seen = [False] * (4 * self.n_faces)
        orbits = []
        for d0 in range(4 * self.n_faces):
            if seen[d0]:
                continue
            orbit = []
            d = d0
            while not seen[d]:
                seen[d] = True
                orbit.append(d)
                d = self.nu(d)
            orbits.append(orbit)
        return orbits

    def valences(self) -> list[int]:
        return [len(o) for o in self.vertex_orbits()]

    def genus(self) -> int:
        v = len(self.vertex_orbits())
        e = 2 * self.n_faces
        f = self.n_faces
        chi = v - e + f
        if chi % 2:
            raise AssertionError(f"non-integral genus: chi = {chi}")
        return (2 - chi) // 2

    def orders(self) -> tuple[int, ...]:
        """Cone orders ``m_i = valence - 4`` (marked points of order 0 included)."""
        return tuple(v - 4 for v in self.valences())

    # ------------------------------------------------------------- holonomy

    def _chart_potentials(self) -> list[int]:
        """Rotation of each face's chart relative to a spanning tree of the dual."""
        r = [None] * self.n_faces
        r[0] = 0
        stack = [0]
        while stack:
            f = stack.pop()
            for s in range(4):
                d = 4 * f + s
                g = self.face(self.alpha[d])
                if r[g] is None:
                    r[g] = (r[f] + self.rotation(d)) % 4
                    stack.append(g)
        if any(x is None for x in r):
            raise ValueError("mesh is not connected")
        return r  # type: ignore[return-value]

    def rho_generators(self) -> list[int]:
        """Holonomy of a basis of cycles of the dual graph (spans ``image(rho)``)."""
        r = self._chart_potentials()
        out = []
        for d in range(4 * self.n_faces):
            e = self.alpha[d]
            if d > e:
                continue  # visit each edge once
            f, g = self.face(d), self.face(e)
            out.append((r[f] + self.rotation(d) - r[g]) % 4)
        return out

    def rho_subgroup(self) -> int:
        return subgroup_generator(self.rho_generators())

    def vertex_holonomy(self, orbit: Sequence[int]) -> int:
        """Holonomy of the dual loop around a vertex, in quarter turns.

        ``nu`` walks around a vertex in the clockwise direction, so the sum of the
        transitions along the orbit is negated to get the counterclockwise
        holonomy.  It must equal ``valence mod 4``: that is the statement that a
        cone of angle ``v * pi/2`` has rotational holonomy ``v * pi/2``.
        """
        total = 0
        for d in orbit:
            total += self.rotation(self.sigma_inv(d))
        return (-total) % 4

    # ------------------------------------------------------------- summary

    def invariant(self) -> MeshInvariant:
        return MeshInvariant(
            genus=self.genus(),
            orders=tuple(sorted(self.orders())),
            rho_subgroup=self.rho_subgroup(),
        )

    def check_consistency(self) -> None:
        """Verify Gauss-Bonnet and the per-vertex holonomy condition."""
        g = self.genus()
        if sum(self.orders()) != 4 * (2 * g - 2):
            raise AssertionError("Gauss-Bonnet violated")
        for orbit in self.vertex_orbits():
            if self.vertex_holonomy(orbit) != len(orbit) % 4:
                raise AssertionError(
                    "vertex holonomy != valence mod 4 for orbit " + repr(orbit)
                )

    def signature(self) -> Signature:
        """A signature with these orders and *some* handle rotations in the orbit.

        Only the orbit invariant is meaningful, so the handle rotations are
        chosen to realize the observed ``image(rho)`` in the simplest way.
        """
        g = self.genus()
        orders = self.orders()
        d_mesh = self.rho_subgroup()
        d_cone = subgroup_generator(orders)
        handle = [0] * (2 * g)
        if d_mesh != d_cone:
            if g == 0:
                raise AssertionError("genus 0 cannot carry extra holonomy")
            handle[0] = d_mesh
        return Signature(g, orders, tuple(handle))

    def canonical_form(self) -> tuple[int, ...]:
        """Isomorphism-invariant encoding, for deduplication of gluings."""
        best = None
        n = 4 * self.n_faces
        for seed in range(n):
            # relabel darts by BFS from `seed`, exploring sigma before alpha
            label = [-1] * n
            order = [seed]
            label[seed] = 0
            i = 0
            while i < len(order):
                d = order[i]
                i += 1
                for e in (self.sigma(d), self.alpha[d]):
                    if label[e] < 0:
                        label[e] = len(order)
                        order.append(e)
            if len(order) < n:
                continue  # disconnected
            code = tuple(label[self.sigma(d)] for d in order) + tuple(
                label[self.alpha[d]] for d in order
            )
            if best is None or code < best:
                best = code
        if best is None:
            raise ValueError("mesh is not connected")
        return best

    @classmethod
    def from_faces(cls, faces: Sequence[Sequence[int]]) -> "QuadMesh":
        """Build a mesh from quadrilaterals given as counterclockwise vertex loops.

        Each face is a 4-tuple of vertex labels listed counterclockwise as seen
        from outside; side ``s`` is the directed edge from ``v[s]`` to
        ``v[s + 1]``.  A consistently oriented closed surface has every directed
        edge appearing exactly once, so gluing is determined: side ``s`` of ``f``
        is glued to the side carrying the reversed edge.
        """
        directed: dict[tuple[int, int], int] = {}
        for f, verts in enumerate(faces):
            if len(verts) != 4:
                raise ValueError("every face must have four sides")
            for s in range(4):
                key = (verts[s], verts[(s + 1) % 4])
                if key in directed:
                    raise ValueError(f"directed edge {key} used twice: bad orientation")
                directed[key] = 4 * f + s
        alpha = [-1] * (4 * len(faces))
        for (a, b), d in directed.items():
            e = directed.get((b, a))
            if e is None:
                raise ValueError(f"edge {(a, b)} has no partner: surface is not closed")
            alpha[d] = e
        return cls(len(faces), alpha)
