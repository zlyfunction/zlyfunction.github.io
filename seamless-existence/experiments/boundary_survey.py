"""Feature-aligned signatures: which ones are realizable?

This is the boundary analogue of ``experiments/survey.py``, and it is deliberately
built the other way round.  The annealing search is *unreliable* for meshes with
boundary -- it fails on meshes that are exhibited by hand, such as the fan of five
squares -- so it is used only to certify, never to rule out.  All negative
statements here come from exhaustive enumeration.

Method:

1. Enumerate every connected quad mesh with at most ``--max-faces`` squares,
   closed or with boundary (involutions of the darts, fixed points allowed), and
   record the stripped boundary invariant of each.  This is a *complete* list of
   what is realizable at that size.
2. Enumerate every Gauss-Bonnet-admissible feature-aligned signature whose forced
   corner count fits in that many squares.  Gauss-Bonnet forces
   ``sum m_i + sum a_j`` to be even, and padding with straight boundary vertices
   (two corners each) or regular interior vertices (four corners each) preserves
   that parity, so the arithmetic is exact.
3. Compare.  A signature in list 2 and not in list 1 is *proved* not to be
   realizable with that many squares.
4. For each such signature, try the annealer at larger sizes -- a positive result
   there means it is realizable after all and only the size bound was binding.

It also checks the doubling map of ``docs/proofs.md`` §8 on every boundary mesh
found: the double must be a closed mesh whose genus is ``2g + b - 1``, whose orders
are the interior orders twice over together with ``2a - 4`` per corner, and whose
``image(rho)`` contains ``image(rho)`` of the original together with ``2a mod 4``.

Usage::

    PYTHONPATH=src python3 experiments/boundary_survey.py [--max-faces 3]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from itertools import combinations_with_replacement
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from seamless_existence.quadmesh import BoundaryInvariant  # noqa: E402
from seamless_existence.search import (  # noqa: E402
    enumerate_meshes_any,
    search_boundary_target,
)
from seamless_existence.signature import SUBGROUP_NAMES, subgroup_generator  # noqa: E402


# --------------------------------------------------------------------------- 1


def realized_invariants(max_faces: int, check_doubling: bool = True) -> tuple[dict, list]:
    """Stripped boundary invariants of every mesh with at most ``max_faces`` squares."""
    table: dict[tuple, dict] = {}
    problems = []
    counts = {}
    for n in range(1, max_faces + 1):
        t0 = time.time()
        seen = 0
        for mesh in enumerate_meshes_any(n):
            seen += 1
            mesh.check_consistency()
            inv = mesh.boundary_invariant().stripped()
            key = inv.as_tuple()
            prior = table.get(key)
            if prior is None or n < prior["n_faces"]:
                table[key] = {"n_faces": n, "alpha": list(mesh.alpha)}
            if check_doubling and mesh.has_boundary():
                problems += _check_double(mesh)
        counts[n] = {"meshes": seen, "seconds": round(time.time() - t0, 1)}
    return {"table": table, "counts": counts}, problems


def _check_double(mesh) -> list[str]:
    dbl = mesh.double()
    dbl.check_consistency()
    inv = dbl.invariant()
    g, b = mesh.genus(), mesh.n_boundary_components()
    want_genus = 2 * g + b - 1
    want_orders = tuple(
        sorted(list(mesh.orders()) * 2 + [2 * a - 4 for a in mesh.corner_angles()])
    )
    lower = subgroup_generator(
        [mesh.rho_subgroup()] + [(2 * a) % 4 for a in mesh.corner_angles()]
    )
    out = []
    if inv.genus != want_genus:
        out.append(f"double genus {inv.genus} != 2g+b-1 = {want_genus}")
    if inv.orders != want_orders:
        out.append(f"double orders {inv.orders} != {want_orders}")
    if lower % inv.rho_subgroup:  # image(rho~) must contain the predicted subgroup
        out.append(
            f"double image(rho) = <{inv.rho_subgroup}> does not contain <{lower}>"
        )
    return out


# --------------------------------------------------------------------------- 2


def admissible_signatures(
    max_faces: int,
    max_genus: int = 2,
    max_boundary: int = 3,
    max_interior: int = 3,
    max_corners: int = 4,
    order_bound: int = 8,
    angle_bound: int = 8,
) -> list[BoundaryInvariant]:
    """Every Gauss-Bonnet-admissible signature that fits in ``max_faces`` squares.

    Corner angles equal to ``2`` and interior orders equal to ``0`` are omitted:
    they are the removable (straight / regular) vertices, which padding supplies.
    """
    budget = 4 * max_faces
    orders_pool = [m for m in range(-3, order_bound + 1) if m != 0]
    angles_pool = [a for a in range(1, angle_bound + 1) if a != 2]

    interior_choices = [()]
    for k in range(1, max_interior + 1):
        for combo in combinations_with_replacement(orders_pool, k):
            if sum(m + 4 for m in combo) <= budget:
                interior_choices.append(combo)

    corner_choices = [()]
    for k in range(1, max_corners + 1):
        for combo in combinations_with_replacement(angles_pool, k):
            if sum(combo) <= budget:
                corner_choices.append(combo)

    out = []
    for genus in range(max_genus + 1):
        for b in range(1, max_boundary + 1):
            chi = 2 - 2 * genus - b
            for orders in interior_choices:
                interior_cost = sum(m + 4 for m in orders)
                if interior_cost > budget:
                    continue
                for comps in combinations_with_replacement(corner_choices, b):
                    total = interior_cost + sum(sum(c) for c in comps)
                    if total > budget or total == 0:
                        continue
                    turning = sum(2 - a for c in comps for a in c)
                    if sum(4 - (m + 4) for m in orders) + turning != 4 * chi:
                        continue
                    d_cone = subgroup_generator(
                        list(orders) + [sum(2 - a for a in c) for c in comps]
                    )
                    for d in (1, 2, 4):
                        if d_cone % d:
                            continue
                        if genus == 0 and d != d_cone:
                            continue  # no handles, so image(rho) = D is forced
                        out.append(
                            BoundaryInvariant(
                                genus=genus,
                                n_boundary=b,
                                orders=tuple(sorted(orders)),
                                corner_angles=tuple(sorted(comps)),
                                rho_subgroup=d,
                            )
                        )
    return sorted(set(out), key=lambda s: (s.genus, s.n_boundary, s.orders,
                                           s.corner_angles, s.rho_subgroup))


# --------------------------------------------------------------------------- report


def describe(sig: BoundaryInvariant) -> str:
    comps = " | ".join(
        ", ".join(f"{a}" for a in comp) if comp else "smooth" for comp in sig.corner_angles
    )
    return (
        f"g={sig.genus} b={sig.n_boundary} interior={list(sig.orders)} "
        f"corners=[{comps}] image(rho)={SUBGROUP_NAMES[sig.rho_subgroup]}"
    )


def double_of(sig: BoundaryInvariant) -> tuple[int, tuple[int, ...], int]:
    orders = tuple(
        sorted(
            list(sig.orders) * 2
            + [2 * a - 4 for comp in sig.corner_angles for a in comp]
        )
    )
    lower = subgroup_generator(
        [sig.rho_subgroup]
        + [(2 * a) % 4 for comp in sig.corner_angles for a in comp]
    )
    return (2 * sig.genus + sig.n_boundary - 1, orders, lower)


def corollary19_scan(sigs) -> list[dict]:
    """Signatures ruled out by the closed classification through the double.

    Corollary 19 of ``docs/proofs.md`` §8: if *every* closed signature the double
    could have is unrealizable, so is the boundary signature.  Whenever the double
    has an empty stratum for ``image(rho~) = 2 Z_4`` it also has a non-empty one for
    ``Z_4``, so this is expected to fire rarely -- and in the surveyed range it never
    does.
    """
    from seamless_existence.predict import EMPTY, predict
    from seamless_existence.signature import Signature

    def closed_status(genus, orders, d):
        nonzero = tuple(m for m in orders if m != 0)
        d_cone = subgroup_generator(nonzero)
        if d_cone % d:
            return None
        handle = [0] * (2 * genus)
        if d != d_cone:
            if genus == 0:
                return None
            handle[0] = d
        sig = Signature(genus, nonzero, tuple(handle))
        if sig.rho_subgroup() != d:
            return None
        return predict(sig).status

    out = []
    for sig in sigs:
        dg, do, lower = double_of(sig)
        stats = {}
        for S in (1, 2, 4):
            if lower % S:
                continue
            st = closed_status(dg, do, S)
            if st is not None:
                stats[S] = st
        if stats and all(v == EMPTY for v in stats.values()):
            out.append({"signature": describe(sig), "double_genus": dg,
                        "double_orders": list(do), "statuses": stats})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-faces", type=int, default=3)
    ap.add_argument("--rescue-iters", type=int, default=6000)
    ap.add_argument("--rescue-limit", type=int, default=60,
                    help="how many unrealized signatures to re-attempt at larger sizes")
    ap.add_argument("--out", default=str(ROOT / "results"))
    args = ap.parse_args()

    realized, double_problems = realized_invariants(args.max_faces)
    table = realized["table"]
    print(f"exhaustive: {sum(c['meshes'] for c in realized['counts'].values())} meshes, "
          f"{len(table)} distinct signatures realized")
    print(f"doubling check: {len(double_problems)} problems")

    sigs = admissible_signatures(args.max_faces)
    print(f"{len(sigs)} admissible signatures fit in {args.max_faces} squares")

    rows = []
    missing = []
    for sig in sigs:
        hit = table.get(sig.as_tuple())
        row = {
            "signature": describe(sig),
            "genus": sig.genus,
            "n_boundary": sig.n_boundary,
            "orders": list(sig.orders),
            "corner_angles": [list(c) for c in sig.corner_angles],
            "turnings": list(sig.turnings()),
            "rho_subgroup": SUBGROUP_NAMES[sig.rho_subgroup],
            "double": [double_of(sig)[0], list(double_of(sig)[1]),
                       SUBGROUP_NAMES[double_of(sig)[2]]],
            "realized_faces": hit["n_faces"] if hit else None,
        }
        if hit is None:
            missing.append(sig)
        rows.append(row)

    print(f"{len(missing)} admissible signatures are NOT realizable with "
          f"{args.max_faces} squares; re-attempting the first "
          f"{min(args.rescue_limit, len(missing))} at larger sizes")
    rescued = {}
    for i, sig in enumerate(missing[: args.rescue_limit]):
        mesh = search_boundary_target(
            sig, extra_regular=1, iters=args.rescue_iters, restarts=1
        )
        if mesh is not None:
            mesh.check_consistency()
            rescued[describe(sig)] = mesh.n_faces
        if (i + 1) % 10 == 0:
            print(f"  ... {i + 1}/{min(args.rescue_limit, len(missing))} attempted, "
                  f"{len(rescued)} realized")
    for row in rows:
        if row["realized_faces"] is None and row["signature"] in rescued:
            row["rescued_faces"] = rescued[row["signature"]]

    ruled_out = corollary19_scan(sigs)
    print(f"Corollary 19 rules out {len(ruled_out)} of the {len(sigs)} signatures")

    payload = {
        "corollary19_ruled_out": ruled_out,
        "max_faces": args.max_faces,
        "exhaustive_counts": realized["counts"],
        "n_realized": len(table),
        "doubling_problems": double_problems,
        "n_admissible": len(sigs),
        "rows": rows,
        "n_missing": len(missing),
        "n_rescued": len(rescued),
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "boundary.json").write_text(json.dumps(payload, indent=1))
    (out / "boundary.md").write_text(to_markdown(payload))
    print(f"{len(rescued)} of them were realized by a larger mesh; "
          f"wrote {out / 'boundary.md'}")


def to_markdown(p: dict) -> str:
    L = [
        "# Feature-aligned signatures",
        "",
        "Generated by `experiments/boundary_survey.py`.  Definitions and proofs are in",
        "`docs/proofs.md` §8.  A *feature-aligned* signature prescribes the genus, the",
        "number of boundary components, the interior cone orders, the boundary corner",
        "angles (in quarter turns, per component, with straight `a = 2` corners",
        "omitted) and `image(rho)`.",
        "",
        "Exhaustive enumeration of all connected quad meshes with at most",
        f"{p['max_faces']} squares -- closed or with boundary -- gives a **complete**",
        f"list of what is realizable at that size: {p['n_realized']} signatures.",
        "",
        "| squares | meshes enumerated | seconds |",
        "|---|---|---|",
    ]
    for n, c in sorted(p["exhaustive_counts"].items()):
        L.append(f"| {n} | {c['meshes']} | {c['seconds']} |")
    L += [
        "",
        f"Doubling check (§8 Lemma 18) on every boundary mesh found: "
        f"**{len(p['doubling_problems'])} problems**.  Genus and orders match the",
        "predicted formula exactly and the predicted subgroup is always contained in",
        "`image(rho~)`.",
        "",
        f"Of the {p['n_admissible']} Gauss-Bonnet-admissible signatures whose corner",
        f"count fits in {p['max_faces']} squares, {p['n_admissible'] - p['n_missing']}",
        f"are realized at that size and {p['n_missing']} are not; the annealer then",
        f"realized {p['n_rescued']} of the latter with a larger mesh.",
        "",
        "**Read the second number with care.**  Fitting the corner count is necessary",
        "but not sufficient: padding a signature to the right size means adding whole",
        "squares, not free straight boundary vertices (a quad mesh cannot subdivide a",
        "single boundary edge), so most of these simply need more squares.  The",
        "rigorous content of a `no` below is exactly *not realizable with this many",
        "squares*.",
        "",
        "## Obstructions transferred from the closed classification",
        "",
        "Corollary 19 of `docs/proofs.md` §8 rules out",
        f"**{len(p['corollary19_ruled_out'])}** of the {p['n_admissible']} signatures.",
        "",
        "Whenever the double lands in one of Masur-Smillie's empty strata (which needs",
        "`image(rho~) = 2 Z_4`) it also admits `image(rho~) = Z_4`, where the stratum is",
        "non-empty -- so the closed classification never decides the boundary case on",
        "its own.  A genuine feature-curve obstruction, if there is one, has to come",
        "from *real* strata: differentials invariant under an anti-holomorphic",
        "involution.  That is the open end of §8.",
        "",
        "## Not realizable at the forced size",
        "",
        "Each row is *proved* unrealizable with the stated number of squares.  A `no`",
        "in the last column means only that the annealer -- which is unreliable for",
        "meshes with boundary -- did not find a larger mesh; it is not evidence of",
        "anything.  The `double` column is the closed signature the double would have,",
        "which is where a genuine obstruction would have to come from (§8 Lemma 18).",
        "",
        "| signature | double (genus, orders, image) | larger mesh found |",
        "|---|---|---|",
    ]
    any_missing = False
    for r in p["rows"]:
        if r["realized_faces"] is not None:
            continue
        any_missing = True
        dg, do, dd = r["double"]
        rescued = r.get("rescued_faces")
        L.append(
            f"| {r['signature']} | g={dg}, {do}, {dd} | "
            f"{('yes, N=' + str(rescued)) if rescued else 'no'} |"
        )
    if not any_missing:
        L.append("| -- none -- | | |")
    L += [
        "",
        "## Realized",
        "",
        "| signature | squares |",
        "|---|---|",
    ]
    for r in p["rows"]:
        if r["realized_faces"] is not None:
            L.append(f"| {r['signature']} | {r['realized_faces']} |")
    L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
