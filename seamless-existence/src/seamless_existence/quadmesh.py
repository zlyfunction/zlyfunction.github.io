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

__all__ = ["QuadMesh", "MeshInvariant", "BoundaryInvariant"]


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


@dataclass(frozen=True)
class BoundaryInvariant:
    """What a mesh with boundary certifies.

    ``corner_angles`` is one sorted tuple per boundary component, in quarter turns;
    ``turnings`` is ``sum (2 - a)`` per component, which is what ``rho`` sees.
    """

    genus: int
    n_boundary: int
    orders: tuple[int, ...]
    corner_angles: tuple[tuple[int, ...], ...]
    rho_subgroup: int

    def turnings(self) -> tuple[int, ...]:
        return tuple(sum(2 - a for a in comp) for comp in self.corner_angles)

    def as_tuple(self):
        return (
            self.genus,
            self.n_boundary,
            self.orders,
            self.corner_angles,
            self.rho_subgroup,
        )

    def stripped(self) -> "BoundaryInvariant":
        """Forget interior marked points; boundary corners of angle pi/2 stay.

        A boundary vertex of angle ``pi`` (two quarter turns) is the boundary
        analogue of a marked point -- the boundary is straight there -- so those are
        dropped too.
        """
        return BoundaryInvariant(
            self.genus,
            self.n_boundary,
            tuple(m for m in self.orders if m != 0),
            tuple(tuple(a for a in comp if a != 2) for comp in self.corner_angles),
            self.rho_subgroup,
        )


class QuadMesh:
    """A quad mesh given by a gluing involution on ``4 * n_faces`` darts.

    A fixed point ``alpha[d] == d`` means side ``d`` is *unglued*: the mesh then has
    boundary, and that side is a boundary edge.  With no fixed points the mesh is
    closed and every method below behaves as it did before boundary support was
    added.

    For a mesh with boundary the flat structure is a seamless parametrization with
    *aligned* boundary: every boundary edge is a side of a unit square, hence maps to
    an axis-parallel segment.  That is exactly the feature-curve condition of
    ``docs/proofs.md`` §8, so a quad mesh with boundary certifies a
    *feature-aligned* signature.
    """

    __slots__ = ("n_faces", "alpha")

    def __init__(self, n_faces: int, alpha: Sequence[int], validate: bool = True):
        if validate:
            if len(alpha) != 4 * n_faces:
                raise ValueError("alpha must have length 4 * n_faces")
            for d, e in enumerate(alpha):
                if alpha[e] != d:
                    raise ValueError("alpha must be an involution")
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
            for e in (self.sigma(d), self.alpha[d]):  # alpha[d] == d is harmless
                if e not in seen:
                    seen.add(e)
                    stack.append(e)
        return len(seen) == 4 * self.n_faces

    def is_boundary_dart(self, d: int) -> bool:
        return self.alpha[d] == d

    def has_boundary(self) -> bool:
        return any(self.alpha[d] == d for d in range(4 * self.n_faces))

    def n_edges(self) -> int:
        """Interior edges count once for two darts, boundary edges once for one."""
        n_bd = sum(1 for d in range(4 * self.n_faces) if self.is_boundary_dart(d))
        return (4 * self.n_faces - n_bd) // 2 + n_bd

    def vertex_orbits(self) -> list[list[int]]:
        """The vertices, as the sets of darts whose tail they are.

        Around an interior vertex the map ``nu`` cycles through all incident
        corners.  Around a boundary vertex it walks a *chain* instead, starting at
        the dart that is itself a boundary dart and ending at the dart whose
        predecessor in its face is a boundary dart.  Either way the class has one
        element per incident corner, so its size is the valence (interior) or the
        corner angle in quarter turns (boundary).
        """
        n = 4 * self.n_faces
        seen = [False] * n
        orbits = []
        # boundary chains first, started from the boundary darts
        for d0 in range(n):
            if seen[d0] or not self.is_boundary_dart(d0):
                continue
            orbit = []
            d = d0
            while True:
                seen[d] = True
                orbit.append(d)
                prev = self.sigma_inv(d)
                if self.is_boundary_dart(prev):
                    break
                d = self.alpha[prev]
                if seen[d]:  # pragma: no cover - defensive
                    break
            orbits.append(orbit)
        # then the interior cycles
        for d0 in range(n):
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

    def is_boundary_vertex(self, orbit: Sequence[int]) -> bool:
        return any(self.is_boundary_dart(d) for d in orbit)

    def valences(self) -> list[int]:
        """Valences of all vertices; for a boundary vertex, the number of corners."""
        return [len(o) for o in self.vertex_orbits()]

    def euler_characteristic(self) -> int:
        return len(self.vertex_orbits()) - self.n_edges() + self.n_faces

    def n_boundary_components(self) -> int:
        return len(self.boundary_cycles())

    def genus(self) -> int:
        chi = self.euler_characteristic()
        b = self.n_boundary_components()
        if (2 - chi - b) % 2:
            raise AssertionError(f"non-integral genus: chi = {chi}, b = {b}")
        return (2 - chi - b) // 2

    def orders(self) -> tuple[int, ...]:
        """Interior cone orders ``m_i = valence - 4`` (order 0 = regular, included)."""
        return tuple(
            len(o) - 4 for o in self.vertex_orbits() if not self.is_boundary_vertex(o)
        )

    def corner_angles(self) -> tuple[int, ...]:
        """Boundary corner angles in quarter turns, one per boundary vertex."""
        return tuple(
            len(o) for o in self.vertex_orbits() if self.is_boundary_vertex(o)
        )

    def next_boundary_dart(self, d: int) -> int:
        """The next boundary dart along the boundary, starting from boundary dart ``d``."""
        if not self.is_boundary_dart(d):
            raise ValueError("not a boundary dart")
        x = self.sigma(d)
        while not self.is_boundary_dart(x):
            x = self.sigma(self.alpha[x])
        return x

    def boundary_cycles(self) -> list[list[int]]:
        """The boundary components, each as the cyclic list of its boundary darts."""
        n = 4 * self.n_faces
        seen = set()
        cycles = []
        for d0 in range(n):
            if not self.is_boundary_dart(d0) or d0 in seen:
                continue
            cycle = []
            d = d0
            while d not in seen:
                seen.add(d)
                cycle.append(d)
                d = self.next_boundary_dart(d)
            cycles.append(cycle)
        return cycles

    def turning(self) -> int:
        """Total boundary turning in quarter turns, ``sum (2 - a)`` over corners."""
        return sum(2 - a for a in self.corner_angles())

    def boundary_holonomy(self, cycle: Sequence[int]) -> int:
        """Rotational holonomy along a boundary component, in quarter turns.

        Walking the component with the surface on the left and accumulating the
        chart transitions crossed while rotating around each vertex; negated for the
        same reason as in ``vertex_holonomy``.  It must equal the turning mod 4.
        """
        total = 0
        for d in cycle:
            x = self.sigma(d)
            while not self.is_boundary_dart(x):
                total += self.rotation(x)
                x = self.sigma(self.alpha[x])
        return (-total) % 4

    def boundary_turning(self, cycle: Sequence[int]) -> int:
        """Turning along one boundary component, in quarter turns.

        Each boundary dart of the cycle ends at one boundary vertex, so summing
        ``2 - a`` over the corners met walking the cycle gives its turning.
        """
        total = 0
        for d in cycle:
            # the vertex at the head of d is the tail of the next boundary dart
            head = self.next_boundary_dart(d)
            orbit = next(o for o in self.vertex_orbits() if head in o)
            total += 2 - len(orbit)
        return total

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
                if self.is_boundary_dart(d):
                    continue
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
            if d >= e:
                continue  # visit each interior edge once, skip boundary darts
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

    def boundary_invariant(self) -> BoundaryInvariant:
        cycles = self.boundary_cycles()
        per_component = []
        for c in cycles:
            angles = []
            for d in c:
                head = self.next_boundary_dart(d)
                orbit = next(o for o in self.vertex_orbits() if head in o)
                angles.append(len(orbit))
            per_component.append(tuple(sorted(angles)))
        return BoundaryInvariant(
            genus=self.genus(),
            n_boundary=len(cycles),
            orders=tuple(sorted(self.orders())),
            corner_angles=tuple(sorted(per_component)),
            rho_subgroup=self.rho_subgroup(),
        )

    def check_consistency(self) -> None:
        """Verify Gauss-Bonnet and the holonomy conditions, with or without boundary.

        * Gauss-Bonnet: ``sum_interior (4 - v) + sum_corners (2 - a) = 4 chi``.
        * every interior vertex: holonomy equals its valence mod 4.
        * every boundary component: holonomy equals its turning mod 4.
        """
        chi = self.euler_characteristic()
        interior = sum(4 - (m + 4) for m in self.orders())
        if interior + self.turning() != 4 * chi:
            raise AssertionError(
                f"Gauss-Bonnet violated: {interior} + {self.turning()} != {4 * chi}"
            )
        for orbit in self.vertex_orbits():
            if self.is_boundary_vertex(orbit):
                continue
            if self.vertex_holonomy(orbit) != len(orbit) % 4:
                raise AssertionError(
                    "vertex holonomy != valence mod 4 for orbit " + repr(orbit)
                )
        for cycle in self.boundary_cycles():
            if self.boundary_holonomy(cycle) != self.boundary_turning(cycle) % 4:
                raise AssertionError(
                    "boundary holonomy != turning mod 4 for cycle " + repr(cycle)
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
    def fan(cls, k: int) -> "QuadMesh":
        """``k`` squares in a cycle around a common apex, outer sides free.

        A disk with one interior cone of angle ``k pi/2`` -- order ``k - 4`` -- and
        ``k`` boundary corners of angle ``pi/2`` alternating with ``k`` straight
        ones.  An explicit infinite family of feature-aligned certificates, and the
        smallest one with odd boundary turning (``k = 3``: turning 3).
        """
        if k < 1:
            raise ValueError("k must be >= 1")
        alpha = list(range(4 * k))
        for i in range(k):
            j = (i + 1) % k
            alpha[4 * i + 3] = 4 * j
            alpha[4 * j] = 4 * i + 3
        return cls(k, alpha)

    @classmethod
    def strip(cls, n: int) -> "QuadMesh":
        """A 1-by-``n`` strip of squares: a disk with four right-angle corners."""
        alpha = list(range(4 * n))
        for i in range(n - 1):
            a, b = 4 * i, 4 * (i + 1) + 2
            alpha[a] = b
            alpha[b] = a
        return cls(n, alpha)

    def double(self) -> "QuadMesh":
        """The double of a mesh with boundary: a closed mesh with twice the faces.

        The mirror copy of face ``f`` is face ``n_faces + f`` with its sides
        relabelled by ``s |-> (-s) mod 4``, so that the mirror is traversed in the
        opposite direction and the double is orientable.  Interior edges are glued to
        the mirror of their partner; each boundary edge is glued to its own mirror,
        which is exactly reflecting across the boundary.

        On invariants (``docs/proofs.md`` §8, Lemma 14):

        * genus becomes ``2g + b - 1``;
        * an interior cone of order ``m`` becomes two cones of order ``m``;
        * a boundary corner of angle ``a pi/2`` becomes one cone of angle ``a pi``,
          i.e. of order ``2a - 4``;
        * ``image(rho)`` *grows* by the loops around those new cones:
          ``image(rho~) = image(rho) + <2a mod 4 : corners>``.  In particular a
          single corner of odd angle -- the generic feature corner, ``pi/2`` or
          ``3 pi/2`` -- puts ``2 Z_4`` inside it, so the double of a mesh with such a
          corner is never a translation surface.
        """
        n = self.n_faces
        if not self.has_boundary():
            raise ValueError("only a mesh with boundary can be doubled")

        def mirror(d: int) -> int:
            return 4 * (n + self.face(d)) + ((-self.side(d)) % 4)

        alpha = [0] * (8 * n)
        for d in range(4 * n):
            e = self.alpha[d]
            if e == d:  # boundary edge: glue to its own mirror
                alpha[d] = mirror(d)
                alpha[mirror(d)] = d
            else:
                alpha[d] = e
                alpha[mirror(d)] = mirror(e)
        return QuadMesh(2 * n, alpha)

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
