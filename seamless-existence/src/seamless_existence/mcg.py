"""Mapping-class-group action on holonomy signatures, and orbit computation.

Realizability of a holonomy signature is invariant under ``MCG(M, C)``: if a
homeomorphism carries one signature to another, a seamless parametrization for
one gives a seamless parametrization for the other by pullback.  So the
existence question only depends on the *orbit*.

This module computes the orbits by brute force for small genus, in order to
check the Reduction Lemma (``docs/proofs.md`` Theorem 8, exposition in
``docs/reduction.md``):

    Orbits of holonomy signatures with fixed genus ``g >= 1`` and fixed multiset
    of orders ``m`` are in bijection with the subgroups ``image(rho) <= Z_4``
    that contain ``D = <m_i mod 4>``.

Two families of mapping classes are used.

1. *Point pushing.*  Pushing the cone ``c_p`` once around a loop ``alpha``
   changes ``rho`` by ``m_p * <alpha, .>``.  Since the intersection form on
   ``H_1(M; Z_4)`` is unimodular, these moves translate the handle part of
   ``rho`` by an arbitrary element of ``D^{2g}``.

2. *Symplectic transvections.*  Dehn twists act on ``H_1(M; Z_4)`` by
   ``T_c(x) = x + <x, c> c``, and these generate the image of ``MCG(M)`` in
   ``Sp(2g, Z_4)`` (``Sp(2g, Z) -> Sp(2g, Z_4)`` is surjective).

That the action really is linear in a suitable coordinate -- and not merely affine
-- is ``docs/proofs.md`` Lemma 7, which supplies a base point fixed by a subgroup
realizing all of ``Sp(2g, Z_4)``.
"""

from __future__ import annotations

import random
from functools import lru_cache
from itertools import product
from typing import Iterable

from .signature import Signature, subgroup_generator

__all__ = [
    "symplectic_product",
    "transvection",
    "handle_orbits",
    "orbit_representatives",
    "verify_reduction_lemma",
    "content",
    "sp_generators",
    "verify_sp_transitivity",
]


def symplectic_product(x: tuple[int, ...], y: tuple[int, ...]) -> int:
    """Standard symplectic form on ``Z_4^{2g}`` in the basis ``a_1, b_1, ...``."""
    total = 0
    for i in range(0, len(x), 2):
        total += x[i] * y[i + 1] - x[i + 1] * y[i]
    return total % 4


def transvection(
    x: tuple[int, ...], c: tuple[int, ...], power: int = 1
) -> tuple[int, ...]:
    """``T_c^power (x) = x + power * <x, c> c`` over ``Z_4``.

    ``T_c`` is the action of the Dehn twist along a curve in the class ``c``, so
    every power of it is again the action of a mapping class.  Note that rescaling
    ``c`` does not produce these powers: replacing ``c`` by ``t c`` gives the power
    ``t^2``, and ``t^2 in {0, 1}`` mod 4.
    """
    s = power * symplectic_product(x, c)
    return tuple((xi + s * ci) % 4 for xi, ci in zip(x, c))


def content(v: tuple[int, ...]) -> int:
    """Generator of the subgroup of ``Z_4`` spanned by the entries of ``v``."""
    return subgroup_generator(v)


def sp_generators(
    genus: int, count: int | None = None, seed: int = 0, powers: tuple[int, ...] = (1,)
) -> list[tuple[tuple[int, ...], int]]:
    """Transvection data ``(c, power)`` used as generators of the ``Sp`` action.

    With ``count is None`` every nonzero ``c`` is used, which is the complete set
    of transvections and needs no justification.  With ``count`` given, a random
    subset of that size is used: any subgroup of the true action is enough to
    *prove* transitivity when the resulting orbits are already as large as
    claimed, which is how the higher-genus checks stay affordable.
    """
    all_c = [c for c in product(range(4), repeat=2 * genus) if any(c)]
    if count is not None and count < len(all_c):
        rng = random.Random(seed)
        all_c = rng.sample(all_c, count)
    return [(c, p) for c in all_c for p in powers]


def _push_shifts(genus: int, cone_generator: int) -> list[tuple[int, ...]]:
    """Generators of the point-pushing translation subgroup ``D^{2g}``."""
    if cone_generator == 4:  # D = 0, no pushing freedom
        return []
    shifts = []
    for i in range(2 * genus):
        shift = [0] * (2 * genus)
        shift[i] = cone_generator % 4
        shifts.append(tuple(shift))
    return shifts


def handle_orbits(genus: int, orders: Iterable[int]) -> list[set[tuple[int, ...]]]:
    """Orbits of the handle part of ``rho`` under point pushing and ``Sp(2g, Z_4)``.

    Returns a list of orbits, each a set of vectors in ``Z_4^{2g}``.  The orbits
    depend on the orders only through ``D = <m_i mod 4>``, so the computation is
    cached on ``(genus, generator of D)``.
    """
    return [set(o) for o in _orbits(genus, subgroup_generator(tuple(orders)))]


@lru_cache(maxsize=None)
def _orbits(genus: int, d_cone: int) -> tuple[frozenset[tuple[int, ...]], ...]:
    shifts = _push_shifts(genus, d_cone)
    twists = [c for c in product(range(4), repeat=2 * genus) if any(c)]

    universe = set(product(range(4), repeat=2 * genus))
    orbits: list[frozenset] = []
    while universe:
        start = min(universe)
        orbit = {start}
        frontier = [start]
        while frontier:
            v = frontier.pop()
            neighbours = [tuple((a + b) % 4 for a, b in zip(v, s)) for s in shifts]
            neighbours += [transvection(v, c) for c in twists]
            for w in neighbours:
                if w not in orbit:
                    orbit.add(w)
                    frontier.append(w)
        orbits.append(orbit)
        universe -= orbit
    return tuple(frozenset(o) for o in orbits)


def orbit_representatives(genus: int, orders: Iterable[int]) -> list[Signature]:
    """One signature per ``MCG``-orbit, for the given genus and orders."""
    orders = tuple(orders)
    reps = []
    for orbit in handle_orbits(genus, orders):
        reps.append(Signature(genus, orders, min(orbit)))
    return reps


def verify_reduction_lemma(genus: int, orders: Iterable[int]) -> dict:
    """Check that ``image(rho)`` is a complete invariant of the orbit.

    Returns a dict with the observed orbits, the value of ``image(rho)`` on each,
    and booleans ``constant`` (the invariant is constant on every orbit) and
    ``separating`` (distinct orbits get distinct invariants).
    """
    orders = tuple(orders)
    orbits = handle_orbits(genus, orders)
    labels = []
    constant = True
    for orbit in orbits:
        values = {subgroup_generator(orders + v) for v in orbit}
        if len(values) != 1:
            constant = False
        labels.append(sorted(values))
    flat = [tuple(lab) for lab in labels]
    separating = len(set(flat)) == len(flat)
    return {
        "genus": genus,
        "orders": orders,
        "n_orbits": len(orbits),
        "orbit_sizes": [len(o) for o in orbits],
        "invariants": labels,
        "constant": constant,
        "separating": separating,
    }


def verify_sp_transitivity(
    genus: int, count: int | None = None, seed: int = 0,
    powers: tuple[int, ...] = (1, 2, 3),
) -> dict:
    """Check that ``Sp(2g, Z_4)`` is transitive on each content class of ``Z_4^{2g}``.

    This is the ingredient of the Reduction Lemma that does the real work
    (``docs/proofs.md``, Lemma 6).  The check starts from the canonical
    representative ``d * e_1`` of each content class and closes it up under
    transvections; success means the orbit is the whole class, so transitivity
    holds for this genus -- using only genuine mapping class actions, hence
    rigorously.
    """
    gens = sp_generators(genus, count=count, seed=seed, powers=powers)
    universe = list(product(range(4), repeat=2 * genus))
    classes: dict[int, set[tuple[int, ...]]] = {}
    for v in universe:
        classes.setdefault(content(v), set()).add(v)

    report = {"genus": genus, "n_generators": len(gens), "classes": {}}
    ok = True
    for d, expected in sorted(classes.items()):
        canonical = tuple([d % 4] + [0] * (2 * genus - 1))
        if d == 4:  # the trivial class is the single vector 0
            canonical = tuple([0] * (2 * genus))
        orbit = {canonical}
        frontier = [canonical]
        while frontier:
            v = frontier.pop()
            for c, p in gens:
                w = transvection(v, c, p)
                if w not in orbit:
                    orbit.add(w)
                    frontier.append(w)
        transitive = orbit == expected
        ok = ok and transitive
        report["classes"][d] = {
            "class_size": len(expected),
            "orbit_size": len(orbit),
            "transitive": transitive,
        }
    report["transitive"] = ok
    return report
