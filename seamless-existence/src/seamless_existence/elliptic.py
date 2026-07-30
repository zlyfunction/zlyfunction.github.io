"""Exact arithmetic on the rational points of an elliptic curve, as a group.

For the divisor questions of ``docs/proofs.md`` (Proposition A) an elliptic curve
only ever enters through its group law, and only torsion points are needed, so
``E`` can be replaced by ``(Q/Z)^2`` -- the rational points of ``C / Lambda`` in
real coordinates.  Everything below is exact ``Fraction`` arithmetic, which makes
the witnesses in ``experiments/verify_proofs.py`` machine-checkable rather than
merely plausible.

Any subgroup statement proved in ``(Q/Z)^2`` holds in ``E``, since
``(Q/Z)^2`` embeds in ``E`` as its torsion subgroup: it is used here only to
*exhibit* points, never to prove non-existence.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd
from typing import Iterable, Sequence

__all__ = ["Pt", "ZERO", "torsion_point", "divide", "combination", "exact_order",
           "divisors", "largest_common_divisor_of_k", "divisor_witness"]


class Pt(tuple):
    """A point of ``(Q/Z)^2``, stored as a pair of ``Fraction``s in ``[0, 1)``."""

    __slots__ = ()

    def __new__(cls, x, y):
        return super().__new__(cls, (Fraction(x) % 1, Fraction(y) % 1))

    def __add__(self, other):
        return Pt(self[0] + other[0], self[1] + other[1])

    def __neg__(self):
        return Pt(-self[0], -self[1])

    def __sub__(self, other):
        return self + (-other)

    def __rmul__(self, n: int):
        return Pt(self[0] * n, self[1] * n)

    __mul__ = __rmul__

    def is_zero(self) -> bool:
        return self[0] == 0 and self[1] == 0

    def __repr__(self) -> str:
        return f"({self[0]}, {self[1]})"


ZERO = Pt(0, 0)


def torsion_point(e: int) -> Pt:
    """A point of exact order ``e`` (``e >= 1``)."""
    if e < 1:
        raise ValueError("order must be >= 1")
    return Pt(Fraction(1, e), 0)


def exact_order(p: Pt) -> int:
    """The exact additive order of ``p``."""
    return (p[0].denominator * p[1].denominator) // gcd(
        p[0].denominator, p[1].denominator
    )


def divide(p: Pt, n: int) -> Pt:
    """One solution ``q`` of ``n q = p``; ``n != 0``.

    Multiplication by ``n`` is surjective on ``(Q/Z)^2``, so a solution always
    exists; the one returned divides both coordinates.
    """
    if n == 0:
        raise ValueError("cannot divide by zero")
    return Pt(p[0] / n, p[1] / n)


def combination(coeffs: Sequence[int], points: Sequence[Pt]) -> Pt:
    """``sum coeffs[i] * points[i]``."""
    total = ZERO
    for c, p in zip(coeffs, points):
        total = total + c * p
    return total


def divisors(k: int) -> list[int]:
    return [e for e in range(1, k + 1) if k % e == 0]


def largest_common_divisor_of_k(k: int, mu: Iterable[int]) -> int:
    """The largest ``e`` dividing ``k`` with ``e | mu_i`` for all ``i``.

    This is the ``e*`` of Proposition A: the only candidate root orders for
    ``q = eta^e`` are divisors of ``k`` that divide every order.
    """
    mu = tuple(mu)
    best = 1
    for e in divisors(k):
        if all(m % e == 0 for m in mu):
            best = e
    return best


def divisor_witness(
    k: int, mu: Sequence[int], seed: int = 0, tries: int = 400
) -> tuple[Pt, ...] | None:
    """Explicit distinct points realizing a primitive ``k``-differential on a torus.

    Returns points ``c_1, ..., c_n`` (distinct) with

    * ``sum mu_i c_i = 0``  -- so a ``k``-differential with divisor
      ``sum mu_i c_i`` exists on the elliptic curve, and
    * ``sum (mu_i / e) c_i != 0`` for every ``e > 1`` dividing ``k`` and all
      ``mu_i``  -- so that differential has no ``e``-th root, i.e. it is
      primitive,

    or ``None`` when Proposition A says no such configuration exists.

    The construction follows the proof: let ``e*`` be the largest divisor of ``k``
    dividing every order, set ``nu = mu / e*``, and aim for
    ``sum nu_i c_i = T`` with ``T`` of exact order ``e*``.  Then
    ``sum mu_i c_i = e* T = 0`` while ``sum (mu_i/e) c_i = (e*/e) T`` has exact
    order ``e``, hence is nonzero, for every relevant ``e``.
    """
    import random

    mu = tuple(mu)
    if sum(mu) != 0:
        raise ValueError("orders must sum to zero on a torus")
    nonzero = [i for i, m in enumerate(mu) if m != 0]
    n = len(mu)

    # no zeros or poles: the differential is c (dz)^k, primitive only for k = 1
    if not nonzero:
        if k != 1:
            return None
        rng = random.Random(seed)
        return tuple(Pt(Fraction(i + 1, n + 1), 0) for i in range(n))

    e_star = largest_common_divisor_of_k(k, [mu[i] for i in nonzero])
    nu = tuple(m // e_star for m in mu)
    target = ZERO if e_star == 1 else torsion_point(e_star)

    rng = random.Random(seed)

    def finish(points: list[Pt | None]) -> tuple[Pt, ...] | None:
        """Fill in the marked points (order 0) keeping everything distinct."""
        used = {p for p in points if p is not None}
        out: list[Pt] = []
        for i, p in enumerate(points):
            if p is not None:
                out.append(p)
                continue
            for d in range(2, 200):
                cand = Pt(Fraction(1, d), Fraction(1, d + 1))
                if cand not in used:
                    used.add(cand)
                    out.append(cand)
                    break
            else:  # pragma: no cover - 200 candidates always suffice here
                return None
        return tuple(out) if len(set(out)) == n else None

    if len(nonzero) == 2:
        i, j = nonzero
        v = nu[i]  # nu[j] == -v
        if e_star == 1:
            # need v (c_i - c_j) = 0 with c_i != c_j: a nonzero v-torsion point
            if abs(v) < 2:
                return None
            u = torsion_point(abs(v))
        else:
            u = divide(target, v)
            if u.is_zero():  # pragma: no cover - impossible since v*u = T != 0
                return None
        points: list[Pt | None] = [None] * n
        points[i] = u
        points[j] = ZERO
        return finish(points)

    # three or more singularities: solve for one point, choose the rest freely
    j = nonzero[0]
    for attempt in range(tries):
        chosen: dict[int, Pt] = {}
        for i in nonzero:
            if i == j:
                continue
            d = rng.randrange(2, 12 + attempt // 20)
            chosen[i] = Pt(Fraction(rng.randrange(d), d), Fraction(rng.randrange(d), d))
        rest = combination([nu[i] for i in chosen], [chosen[i] for i in chosen])
        chosen[j] = divide(target - rest, nu[j])
        if len(set(chosen.values())) != len(chosen):
            continue
        points = [None] * n
        for i, p in chosen.items():
            points[i] = p
        result = finish(points)
        if result is not None:
            return result
    return None  # pragma: no cover - the proof says this never happens


def check_witness(k: int, mu: Sequence[int], points: Sequence[Pt]) -> list[str]:
    """Verify a witness against the two defining conditions.  Empty list = valid."""
    problems = []
    if len(set(points)) != len(points):
        problems.append("points are not distinct")
    total = combination(mu, points)
    if not total.is_zero():
        problems.append(f"sum mu_i c_i = {total} != 0, divisor is not principal")
    for e in divisors(k):
        if e == 1 or any(m % e for m in mu):
            continue
        val = combination([m // e for m in mu], points)
        if val.is_zero():
            problems.append(f"differential has an {e}-th root: sum (mu_i/{e}) c_i = 0")
        elif exact_order(val) != e:
            problems.append(
                f"sum (mu_i/{e}) c_i has order {exact_order(val)}, expected {e}"
            )
    return problems
