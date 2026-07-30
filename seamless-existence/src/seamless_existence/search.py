"""Search for square-tiled certificates of holonomy signatures.

Every closed quad mesh made of ``N`` unit squares realizes its own holonomy
signature (see ``quadmesh``), so finding one is a *proof of existence*.  The
converse direction is the standing conjecture that makes the search meaningful:

    (Density) If a stratum of 4-differentials is non-empty, it contains a
    square-tiled surface, because rational points are dense in period
    coordinates and the rotational holonomy is locally constant.

Under that conjecture, "no mesh with at most N squares" is evidence -- never a
proof -- of emptiness, and the interesting output of a search is the list of
orbit invariants that stay uncertified as ``N`` grows.

Two search regimes live here.  For closed meshes, annealing from a random gluing
works well.  For meshes with boundary it does *not*: it misses meshes that can be
written down by hand, such as ``QuadMesh.fan(5)``.  So the boundary experiments use
annealing only to certify and rely on exhaustive enumeration
(``enumerate_meshes_any``) for every negative statement.
"""

from __future__ import annotations

import random
from typing import Callable, Iterable, Iterator

from .quadmesh import MeshInvariant, QuadMesh

__all__ = [
    "perfect_matchings",
    "enumerate_meshes",
    "random_meshes",
    "collect_certificates",
    "min_faces",
    "min_faces_boundary",
    "partial_matchings",
    "enumerate_meshes_any",
    "anneal_boundary",
    "strip_start",
    "search_boundary_target",
    "boundary_target_cost",
    "target_cost",
    "anneal",
    "search_target",
    "allowed_valences",
    "exhaustive_target_search",
]


def perfect_matchings(n: int) -> Iterator[tuple[int, ...]]:
    """All fixed-point-free involutions of ``range(n)`` (``n`` even)."""
    if n % 2:
        raise ValueError("n must be even")
    alpha = [-1] * n

    def rec(k: int) -> Iterator[tuple[int, ...]]:
        while k < n and alpha[k] != -1:
            k += 1
        if k == n:
            yield tuple(alpha)
            return
        for j in range(k + 1, n):
            if alpha[j] == -1:
                alpha[k] = j
                alpha[j] = k
                yield from rec(k + 1)
                alpha[k] = -1
                alpha[j] = -1

    yield from rec(0)


def enumerate_meshes(n_faces: int) -> Iterator[QuadMesh]:
    """All connected closed quad meshes with ``n_faces`` squares (with repeats)."""
    for alpha in perfect_matchings(4 * n_faces):
        mesh = QuadMesh(n_faces, alpha, validate=False)
        if mesh.is_connected():
            yield mesh


def random_meshes(
    n_faces: int, samples: int, rng: random.Random | None = None
) -> Iterator[QuadMesh]:
    """Random connected closed quad meshes with ``n_faces`` squares."""
    rng = rng or random.Random(0)
    darts = list(range(4 * n_faces))
    for _ in range(samples):
        rng.shuffle(darts)
        alpha = [0] * (4 * n_faces)
        for i in range(0, len(darts), 2):
            a, b = darts[i], darts[i + 1]
            alpha[a] = b
            alpha[b] = a
        mesh = QuadMesh(n_faces, alpha, validate=False)
        if mesh.is_connected():
            yield mesh


def collect_certificates(
    meshes: Iterable[QuadMesh],
    into: dict[tuple, dict] | None = None,
    check: bool = False,
    keep: Callable[[MeshInvariant], bool] | None = None,
    strip_marked: bool = True,
) -> dict[tuple, dict]:
    """Map orbit invariants to a smallest witnessing gluing.

    ``into`` lets several searches accumulate into one table.  With
    ``strip_marked`` the key ignores valence-4 vertices, which existence does not
    see.
    """
    table = {} if into is None else into
    for mesh in meshes:
        if check:
            mesh.check_consistency()
        inv = mesh.invariant()
        if keep is not None and not keep(inv):
            continue
        key = (inv.stripped() if strip_marked else inv).as_tuple()
        prior = table.get(key)
        if prior is None or mesh.n_faces < prior["n_faces"]:
            table[key] = {
                "n_faces": mesh.n_faces,
                "alpha": list(mesh.alpha),
                "valences": sorted(mesh.valences()),
            }
    return table


# --------------------------------------------------------------------------
# targeted search
# --------------------------------------------------------------------------
#
# Blind random gluings are useless for low genus (a random matching of 4N darts
# is concentrated near the maximal genus), so realizing a *prescribed* signature
# calls for a targeted search: fix the number of squares that the signature
# forces, then anneal the gluing towards the target invariant.


def min_faces(genus: int, orders: Iterable[int]) -> int:
    """Squares needed by a quad mesh whose cones are exactly ``orders``.

    Every square has four corners and a vertex of valence ``v`` uses ``v`` of
    them, so ``4N = sum (m_i + 4)`` once every extra vertex is regular
    (valence 4).  Allowing ``t`` regular vertices gives ``N + t`` squares.
    """
    orders = tuple(orders)
    return 2 * genus - 2 + len(orders)


def _multiset_distance(a: Iterable[int], b: Iterable[int]) -> int:
    from collections import Counter

    ca, cb = Counter(a), Counter(b)
    return sum((ca - cb).values()) + sum((cb - ca).values())


def target_cost(mesh: QuadMesh, target: tuple[int, tuple[int, ...], int]) -> int:
    """Distance from a mesh's stripped invariant to the target invariant."""
    genus, orders, d = target
    inv = mesh.invariant().stripped()
    cost = 6 * abs(inv.genus - genus)
    cost += _multiset_distance(inv.orders, orders)
    cost += 0 if inv.rho_subgroup == d else 2
    return cost


def _swap(alpha: list[int], a: int, b: int) -> None:
    """Re-glue so that ``a`` pairs with ``b`` and their old partners pair up."""
    a2, b2 = alpha[a], alpha[b]
    alpha[a], alpha[b] = b, a
    alpha[a2], alpha[b2] = b2, a2


def anneal(
    target: tuple[int, tuple[int, ...], int],
    n_faces: int,
    iters: int = 20000,
    rng: random.Random | None = None,
    temperature: float = 1.2,
) -> QuadMesh | None:
    """Metropolis search for a mesh with ``n_faces`` squares realizing ``target``."""
    import math

    rng = rng or random.Random(0)
    n = 4 * n_faces
    if n < 4:
        return None
    # random start
    darts = list(range(n))
    rng.shuffle(darts)
    alpha = [0] * n
    for i in range(0, n, 2):
        alpha[darts[i]] = darts[i + 1]
        alpha[darts[i + 1]] = darts[i]

    mesh = QuadMesh(n_faces, alpha, validate=False)
    if not mesh.is_connected():
        cost = 10**6
    else:
        cost = target_cost(mesh, target)
    if cost == 0:
        return mesh

    for step in range(iters):
        t = temperature * (1.0 - step / iters) + 0.05
        a = rng.randrange(n)
        b = rng.randrange(n)
        if a == b or alpha[a] == b:
            continue
        _swap(alpha, a, b)
        cand = QuadMesh(n_faces, alpha, validate=False)
        new_cost = target_cost(cand, target) if cand.is_connected() else 10**6
        if new_cost == 0:
            return cand
        delta = new_cost - cost
        if delta <= 0 or rng.random() < math.exp(-delta / t):
            cost = new_cost
        else:
            _swap(alpha, a, b)  # the swap is its own inverse
    return None


def search_target(
    target: tuple[int, tuple[int, ...], int],
    extra_regular: int = 4,
    iters: int = 20000,
    restarts: int = 3,
    seed: int = 0,
) -> QuadMesh | None:
    """Try to realize ``target``, allowing up to ``extra_regular`` regular vertices."""
    genus, orders, _ = target
    base = min_faces(genus, orders)
    for t in range(extra_regular + 1):
        n_faces = base + t
        if n_faces < 1:
            continue
        for r in range(restarts):
            mesh = anneal(target, n_faces, iters=iters, rng=random.Random(seed + 1000 * t + r))
            if mesh is not None:
                return mesh
    return None


# --------------------------------------------------------------------------
# meshes with boundary (feature-aligned signatures)
# --------------------------------------------------------------------------


def partial_matchings(n: int) -> Iterator[tuple[int, ...]]:
    """All involutions of ``range(n)``, fixed points allowed.

    A fixed point is an unglued side, i.e. a boundary edge, so this enumerates
    meshes with boundary as well as closed ones.
    """
    alpha = list(range(n))

    def rec(k: int) -> Iterator[tuple[int, ...]]:
        while k < n and alpha[k] != k:
            k += 1
        if k == n:
            yield tuple(alpha)
            return
        yield from rec(k + 1)  # leave k on the boundary
        for j in range(k + 1, n):
            if alpha[j] == j:
                alpha[k] = j
                alpha[j] = k
                yield from rec(k + 1)
                alpha[k] = k
                alpha[j] = j

    yield from rec(0)


def enumerate_meshes_any(n_faces: int) -> Iterator[QuadMesh]:
    """All connected quad meshes with ``n_faces`` squares, closed or with boundary."""
    for alpha in partial_matchings(4 * n_faces):
        mesh = QuadMesh(n_faces, alpha, validate=False)
        if mesh.is_connected():
            yield mesh


def min_faces_boundary(orders: Iterable[int], corner_angles: Iterable[int]) -> int:
    """Squares forced by interior orders plus boundary corner angles.

    Every square has four corners; an interior vertex of valence ``v`` uses ``v`` of
    them and a boundary vertex of angle ``a pi/2`` uses ``a``.
    """
    total = sum(m + 4 for m in orders) + sum(corner_angles)
    if total % 4:
        raise ValueError("corner count is not a multiple of four")
    return total // 4


def _reglue(alpha: list[int], a: int, b: int) -> None:
    """Re-glue side ``a`` to side ``b``, freeing whatever they were glued to."""
    a2, b2 = alpha[a], alpha[b]
    alpha[a] = b
    alpha[b] = a
    if a2 != a and b2 != b:
        alpha[a2] = b2
        alpha[b2] = a2
    elif a2 != a:
        alpha[a2] = a2
    elif b2 != b:
        alpha[b2] = b2


def boundary_target_cost(mesh: QuadMesh, target) -> int:
    """Distance from a mesh's stripped boundary invariant to the target."""
    inv = mesh.boundary_invariant().stripped()
    cost = 6 * abs(inv.genus - target.genus)
    cost += 4 * abs(inv.n_boundary - target.n_boundary)
    cost += _multiset_distance(inv.orders, target.orders)
    flat_a = [a for comp in inv.corner_angles for a in comp]
    flat_b = [a for comp in target.corner_angles for a in comp]
    cost += _multiset_distance(flat_a, flat_b)
    cost += _multiset_distance(inv.corner_angles, target.corner_angles)
    cost += 0 if inv.rho_subgroup == target.rho_subgroup else 2
    return cost


def strip_start(n_faces: int) -> list[int]:
    """A 1-by-``n`` strip of squares: a disk, already of the right topology.

    Annealing towards a low-genus target from a random gluing is hopeless, because
    random gluings sit near the maximal genus.  Starting from a strip -- which is
    already a disk with four right-angle corners and straight sides -- only leaves
    the corner structure to fix.
    """
    alpha = list(range(4 * n_faces))
    for i in range(n_faces - 1):
        a, b = 4 * i + 0, 4 * (i + 1) + 2
        alpha[a] = b
        alpha[b] = a
    return alpha


def anneal_boundary(
    target,
    n_faces: int,
    n_boundary_darts: int,
    iters: int = 20000,
    rng: random.Random | None = None,
    temperature: float = 1.5,
    start: str = "random",
) -> QuadMesh | None:
    """Metropolis search for a mesh with boundary realizing ``target``.

    ``start`` is ``"random"`` or ``"strip"``; the strip start is much better for
    genus-0 targets, the random one for higher genus.
    """
    import math

    rng = rng or random.Random(0)
    n = 4 * n_faces
    if n < 4 or n_boundary_darts > n or (n - n_boundary_darts) % 2:
        return None

    if start == "strip":
        alpha = strip_start(n_faces)
    else:
        darts = list(range(n))
        rng.shuffle(darts)
        alpha = list(range(n))
        free = darts[n_boundary_darts:]
        for i in range(0, len(free), 2):
            alpha[free[i]] = free[i + 1]
            alpha[free[i + 1]] = free[i]

    def score(a: list[int]) -> int:
        m = QuadMesh(n_faces, a, validate=False)
        if not m.is_connected():
            return 10**6
        try:
            return boundary_target_cost(m, target)
        except (AssertionError, ValueError, StopIteration):  # pragma: no cover
            return 10**6

    cost = score(alpha)
    if cost == 0:
        return QuadMesh(n_faces, alpha, validate=False)

    for step in range(iters):
        t = temperature * (1.0 - step / iters) + 0.05
        a = rng.randrange(n)
        b = rng.randrange(n)
        if a == b:
            continue
        backup = list(alpha)
        _reglue(alpha, a, b)
        new_cost = score(alpha)
        if new_cost == 0:
            return QuadMesh(n_faces, alpha, validate=False)
        delta = new_cost - cost
        if delta <= 0 or rng.random() < math.exp(-delta / t):
            cost = new_cost
        else:
            alpha = backup
    return None


def search_boundary_target(
    target,
    extra_regular: int = 2,
    iters: int = 20000,
    restarts: int = 3,
    seed: int = 0,
) -> QuadMesh | None:
    """Try to realize a boundary signature, allowing a few extra regular vertices.

    "Regular" means an interior vertex of valence 4 (four extra corners) or a
    boundary vertex of angle ``pi`` (two extra corners); neither is visible to the
    signature.  Padding is needed even to make the corner count a multiple of four:
    a stripped signature with an odd number of boundary corners always needs at
    least one straight boundary vertex.
    """
    flat_corners = [a for comp in target.corner_angles for a in comp]
    total = sum(m + 4 for m in target.orders) + sum(flat_corners)
    n_bd_min = len(flat_corners)
    for extra in range(0, 4 * extra_regular + 4):
        if (total + extra) % 4:
            continue
        n_faces = (total + extra) // 4
        if n_faces < 1:
            continue
        for straight in range(0, extra // 2 + 1):
            if (extra - 2 * straight) % 4:
                continue
            n_bd = n_bd_min + straight
            if n_bd == 0 or n_bd > 4 * n_faces:
                continue
            for r in range(restarts):
                for start in ("strip", "random"):
                    mesh = anneal_boundary(
                        target,
                        n_faces,
                        n_bd,
                        iters=iters,
                        rng=random.Random(seed + 977 * extra + 31 * straight + r),
                        start=start,
                    )
                    if mesh is not None:
                        return mesh
    return None


# --------------------------------------------------------------------------
# exact search for one target
# --------------------------------------------------------------------------
#
# Enumerating *all* gluings stops at four squares.  Deciding whether *one* given
# signature is realizable at a given size goes much further, because the target
# prunes the tree hard: gluing a side closes vertex cycles, and a closed cycle whose
# length is not an allowed valence kills the branch immediately.


def allowed_valences(genus: int, orders: Iterable[int], n_faces: int) -> list[int] | None:
    """Multiset of vertex valences a mesh with this signature and size must have.

    The cones contribute ``m_i + 4`` each and every remaining vertex is regular, so
    the padding is forced: ``n_faces - min_faces`` vertices of valence 4.  Returns
    ``None`` when the size is impossible.
    """
    orders = tuple(orders)
    base = min_faces(genus, orders)
    padding = n_faces - base
    if padding < 0:
        return None
    return sorted([m + 4 for m in orders] + [4] * padding)


def _chains(alpha: list[int], n: int) -> tuple[list[int], list[int]]:
    """Lengths of the closed vertex cycles and of the open chains, for a partial gluing.

    ``alpha[d] == -1`` means "not glued yet".  Following ``nu(x) = alpha[sigma^{-1}(x)]``
    walks around a vertex; ``x`` has no predecessor exactly when ``alpha[x] == -1``, so
    the unglued sides are the heads of the open chains and everything not reached from
    a head lies on a closed cycle.
    """
    seen = [False] * n
    open_lens: list[int] = []
    for head in range(n):
        if alpha[head] != -1:
            continue
        x = head
        length = 0
        while True:
            seen[x] = True
            length += 1
            prev = (x & ~3) | ((x - 1) & 3)
            nxt = alpha[prev]
            if nxt == -1:
                break
            x = nxt
        open_lens.append(length)
    closed_lens: list[int] = []
    for start in range(n):
        if seen[start]:
            continue
        x = start
        length = 0
        while not seen[x]:
            seen[x] = True
            length += 1
            prev = (x & ~3) | ((x - 1) & 3)
            x = alpha[prev]
        closed_lens.append(length)
    return closed_lens, open_lens


def _feasible(alpha: list[int], n: int, allowed: list[int]) -> bool:
    """Necessary conditions for a partial gluing to extend to one realizing ``allowed``.

    * every closed cycle is an allowed valence, with multiplicity;
    * no open chain is longer than the largest valence still unused;
    * there are at least as many open chains as vertices still to be formed, since
      each of those vertices needs at least one.
    """
    from collections import Counter

    closed, open_lens = _chains(alpha, n)
    remaining = Counter(allowed)
    for v in closed:
        if remaining[v] == 0:
            return False
        remaining[v] -= 1
    slots = sorted(remaining.elements())
    if not slots:
        return not open_lens
    if open_lens and max(open_lens) > slots[-1]:
        return False
    return len(open_lens) >= len(slots)


def exhaustive_target_search(
    target: tuple[int, tuple[int, ...], int], n_faces: int, node_budget: int = 0
) -> tuple[QuadMesh | None, dict]:
    """Decide whether some closed mesh with ``n_faces`` squares realizes ``target``.

    Returns ``(mesh, stats)``; ``mesh`` is ``None`` when no such mesh exists, which
    -- unlike an annealing failure -- is a proof for that size, provided
    ``stats["exhausted"]`` is true.  ``node_budget`` of 0 means no limit.
    """
    genus, orders, d = target
    allowed = allowed_valences(genus, orders, n_faces)
    stats = {"nodes": 0, "exhausted": True, "n_faces": n_faces}
    if allowed is None:
        return None, stats

    n = 4 * n_faces
    alpha = [-1] * n
    result: list[QuadMesh] = []

    def rec() -> bool:
        """True means stop (found, or budget exhausted)."""
        stats["nodes"] += 1
        if node_budget and stats["nodes"] > node_budget:
            stats["exhausted"] = False
            return True
        try:
            d0 = next(x for x in range(n) if alpha[x] == -1)
        except StopIteration:
            mesh = QuadMesh(n_faces, alpha, validate=False)
            if mesh.is_connected() and mesh.invariant().stripped().as_tuple() == target:
                result.append(mesh)
                return True
            return False
        # symmetry reduction: at the very first step the partner of side 0 may be
        # taken in face 0 or, after permuting faces and rotating the new one, to be
        # side 0 of face 1.
        candidates = range(d0 + 1, min(5, n)) if d0 == 0 else range(d0 + 1, n)
        for e in candidates:
            if alpha[e] != -1:
                continue
            alpha[d0] = e
            alpha[e] = d0
            if _feasible(alpha, n, allowed):
                if rec():
                    return True
            alpha[d0] = -1
            alpha[e] = -1
        return False

    rec()
    return (result[0] if result else None), stats
