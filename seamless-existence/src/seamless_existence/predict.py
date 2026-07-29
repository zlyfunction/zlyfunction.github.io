"""What the flat-surface literature already says about each reduced stratum.

After the reduction of ``docs/reduction.md``, a holonomy signature is realizable
iff a stratum of primitive ``k``-differentials is non-empty, with
``k = 4 / d`` and ``d`` the generator of ``image(rho)``:

===== ============================== ==========================================
``k`` object                         non-emptiness known from
===== ============================== ==========================================
1     abelian differential           classical (Masur-Smillie)
2     primitive quadratic diff.      Masur-Smillie 1993: four empty strata
4     primitive 4-differential       Gendron-Tahar (arXiv:2208.11654) -- the
                                     exceptional list still has to be read out
===== ============================== ==========================================

Genus 0 is settled independently and uniformly by Troyanov's theorem, and genus
1 is settled uniformly by an Abel-Jacobi argument (``docs/genus1.md``) which
reproduces Masur-Smillie's two genus-1 exceptions as a sanity check.

Every verdict carries the reason and the citation it rests on; anything this
module returns as ``UNKNOWN`` is a research target, not a gap in the code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .signature import Signature, subgroup_generator

__all__ = ["Verdict", "EXISTS", "EMPTY", "UNKNOWN", "predict", "classify_orders"]

EXISTS = "exists"
EMPTY = "empty"
UNKNOWN = "unknown"


@dataclass(frozen=True)
class Verdict:
    status: str
    reason: str
    source: str = ""

    def __str__(self) -> str:
        tail = f" [{self.source}]" if self.source else ""
        return f"{self.status}: {self.reason}{tail}"


# Masur-Smillie 1993: the only empty strata of primitive quadratic differentials
# with at worst simple poles.  Keys are (genus, sorted nonzero orders).
QUADRATIC_EMPTY = {
    (1, ()): "Q(empty) -- a quadratic differential with no zeros on a torus is a square",
    (1, (-1, 1)): "Q(1,-1) -- divisor c1 - c2 is never principal on an elliptic curve",
    (2, (1, 3)): "Q(1,3)",
    (2, (4,)): "Q(4)",
}

MASUR_SMILLIE = "Masur & Smillie 1993, Comment. Math. Helv. 68"
TROYANOV = "Troyanov 1986/1991 (flat metrics with prescribed conical singularities)"
GENDRON_TAHAR = "Gendron & Tahar, arXiv:2208.11654 (k-differentials with prescribed singularities)"
ABEL_JACOBI = "docs/genus1.md, Proposition A (Abel-Jacobi)"


def _nonzero(mu: Sequence[int]) -> tuple[int, ...]:
    return tuple(sorted(m for m in mu if m != 0))


def genus1_nonempty(k: int, mu: Sequence[int]) -> Verdict:
    """Proposition A: non-emptiness of a primitive ``k``-differential stratum on a torus.

    On an elliptic curve ``E`` the canonical bundle is trivial, so a
    ``k``-differential with divisor ``sum mu_i c_i`` exists iff that degree-zero
    divisor is principal, i.e. iff ``sum mu_i c_i = 0`` in the group law -- and
    we get to choose the (distinct) points.
    """
    nz = _nonzero(mu)
    if not nz:
        if k == 1:
            return Verdict(EXISTS, "flat torus with marked points", ABEL_JACOBI)
        return Verdict(
            EMPTY,
            f"a nowhere-zero {k}-differential on a torus is c*(dz)^{k}, "
            "hence a k-th power, hence not primitive",
            ABEL_JACOBI,
        )
    if len(nz) == 2 and abs(nz[0]) == 1:
        return Verdict(
            EMPTY,
            "divisor c1 - c2 with c1 != c2 is never principal on an elliptic curve "
            "(equivalently: no nonzero 1-torsion point)",
            ABEL_JACOBI,
        )
    if len(nz) == 2:
        m = abs(nz[0])
        return Verdict(
            EXISTS,
            f"choose c1 - c2 of exact order {m}: E has nonzero {m}-torsion, "
            "and exact order m obstructs every root, so the differential is primitive",
            ABEL_JACOBI,
        )
    return Verdict(
        EXISTS,
        "with >= 3 singularities the map (c_i) -> sum mu_i c_i is submersive, "
        "so distinct points with sum mu_i c_i = 0 exist",
        ABEL_JACOBI,
    )


def abelian_nonempty(genus: int, mu: Sequence[int]) -> Verdict:
    nz = _nonzero(mu)
    if any(m < 0 for m in nz):
        return Verdict(
            EMPTY, "an abelian differential arising here cannot have poles", MASUR_SMILLIE
        )
    if genus == 1:
        if nz:
            return Verdict(
                EMPTY,
                "an abelian differential on a torus is nowhere zero, so all orders "
                "must vanish",
                MASUR_SMILLIE,
            )
        return Verdict(EXISTS, "flat torus with marked points", MASUR_SMILLIE)
    return Verdict(
        EXISTS,
        f"every stratum H({list(nz)}) of abelian differentials is non-empty for g >= 2",
        MASUR_SMILLIE,
    )


def quadratic_nonempty(genus: int, mu: Sequence[int]) -> Verdict:
    nz = _nonzero(mu)
    if any(m < -1 for m in nz):
        return Verdict(
            EMPTY,
            "reduction produced a pole of order >= 2, which a finite-area cone "
            "cannot give",
            MASUR_SMILLIE,
        )
    key = (genus, nz)
    if key in QUADRATIC_EMPTY:
        return Verdict(EMPTY, QUADRATIC_EMPTY[key], MASUR_SMILLIE)
    if genus == 1:
        return genus1_nonempty(2, mu)
    return Verdict(
        EXISTS,
        f"Q({list(nz)}) is not one of the four exceptional empty strata",
        MASUR_SMILLIE,
    )


def quartic_nonempty(genus: int, mu: Sequence[int]) -> Verdict:
    if genus == 1:
        return genus1_nonempty(4, mu)
    return Verdict(
        UNKNOWN,
        "non-emptiness of this stratum of primitive 4-differentials has to be "
        "read off Gendron-Tahar's classification (milestone M1)",
        GENDRON_TAHAR,
    )


def predict(sig: Signature) -> Verdict:
    """Predicted realizability of a holonomy signature, with justification."""
    if sig.genus == 0:
        return Verdict(
            EXISTS,
            "on the sphere pi_1(M \\ C) is generated by the loops around the cones, "
            "so any Gauss-Bonnet-admissible set of angles that are multiples of "
            "pi/2 is realized by a flat cone metric whose holonomy is automatically "
            "in Z_4",
            TROYANOV,
        )
    k = sig.differential_order
    mu = sig.reduced_orders()
    if k == 1:
        return abelian_nonempty(sig.genus, mu)
    if k == 2:
        return quadratic_nonempty(sig.genus, mu)
    return quartic_nonempty(sig.genus, mu)


def admissible_rho_subgroups(orders: Sequence[int]) -> list[int]:
    """The generators ``d`` of subgroups ``image(rho)`` compatible with the orders.

    ``image(rho)`` must contain ``D = <m_i mod 4>``, i.e. ``d`` divides
    ``d_cone``.
    """
    d_cone = subgroup_generator(orders)
    return [d for d in (1, 2, 4) if d_cone % d == 0]


def classify_orders(genus: int, orders: Sequence[int]) -> list[tuple[Signature, Verdict]]:
    """One representative signature per orbit, with its predicted verdict."""
    out = []
    for d in admissible_rho_subgroups(orders):
        handle = [0] * (2 * genus)
        if d != subgroup_generator(orders):
            if genus == 0:
                continue  # no room for extra holonomy
            handle[0] = d
        sig = Signature(genus, tuple(orders), tuple(handle))
        if sig.rho_subgroup() != d:  # pragma: no cover - defensive
            raise AssertionError("failed to realize requested image(rho)")
        out.append((sig, predict(sig)))
    return out
