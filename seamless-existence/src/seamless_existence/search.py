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
    "target_cost",
    "anneal",
    "search_target",
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
