"""Machine-check the statements proved in ``docs/proofs.md``.

Six checks, in the order they appear in the proofs:

1. **Lemma 6** (symplectic transitivity over ``Z_4``): close up ``d e_1`` under
   genuine transvections and require the orbit to be the whole content class.
2. **Theorem 8** (Reduction Lemma): recompute the orbits under point pushing and
   transvections; ``image(rho)`` must be constant on orbits and separate them, with
   orbit counts ``1 / 2 / 3`` according to ``D``.
3. **Corollary 9**: a single orbit whenever some order is odd.
4. **Proposition 12** (genus 1): construct the divisor witnesses exactly in
   ``(Q/Z)^2`` and verify the two defining conditions; cross-check the criterion
   against ``predict.py``.
5. **Theorem 10** against construction: no square-tiled surface may realize a
   signature the criterion calls empty.
6. **Lemma 3** consistency on every small gluing: Gauss-Bonnet and
   holonomy-equals-valence.

Usage::

    PYTHONPATH=src python3 experiments/verify_proofs.py [--quick] [--max-faces 4]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from seamless_existence.elliptic import (  # noqa: E402
    check_witness,
    divisor_witness,
    largest_common_divisor_of_k,
)
from seamless_existence.mcg import (  # noqa: E402
    handle_orbits,
    verify_reduction_lemma,
    verify_sp_transitivity,
)
from seamless_existence.predict import EMPTY, classify_orders, genus1_nonempty, predict  # noqa: E402
from seamless_existence.search import collect_certificates, enumerate_meshes  # noqa: E402
from seamless_existence.signature import subgroup_generator  # noqa: E402


# --------------------------------------------------------------------------- 1


def check_lemma6(quick: bool, deep: bool = False) -> dict:
    runs = []
    plan = [(1, None), (2, None), (3, None)] if not quick else [(1, None), (2, None)]
    if not quick:
        plan.append((4, 20))
    if deep:
        # genus 5: 1 048 576 vectors, so a bigger random generator set is needed
        # (12 transvection classes are not enough to generate a transitive action)
        plan.append((5, 64))
    for genus, count in plan:
        t0 = time.time()
        powers = (1,) if count is None else (1, 2, 3)
        rep = verify_sp_transitivity(genus, count=count, seed=1, powers=powers)
        rep["generator_set"] = (
            "complete" if count is None else f"random subset of {count}"
        )
        rep["seconds"] = round(time.time() - t0, 1)
        runs.append(rep)
    return {"name": "Lemma 6 (symplectic transitivity)", "runs": runs,
            "ok": all(r["transitive"] for r in runs)}


# --------------------------------------------------------------------------- 2


def _orders_for(genus: int, d_cone: int) -> tuple[int, ...] | None:
    """Some admissible orders whose cone subgroup is ``d_cone``."""
    target = 4 * (2 * genus - 2)
    for candidate in [
        (1, target - 1), (-1, target + 1), (3, target - 3),
        (2, target - 2), (-2, target + 2), (6, target - 6),
        (4, target - 4), (-8, target + 8), (8, target - 8), (0, target),
    ]:
        if any(m <= -4 for m in candidate):
            continue
        if subgroup_generator(candidate) == d_cone:
            return candidate
    return None


def check_theorem8(quick: bool) -> dict:
    rows = []
    ok = True
    genera = (1, 2) if quick else (1, 2, 3)
    expected_orbits = {1: 1, 2: 2, 4: 3}
    for genus in genera:
        for d_cone in (1, 2, 4):
            orders = _orders_for(genus, d_cone)
            if orders is None:
                continue
            t0 = time.time()
            chk = verify_reduction_lemma(genus, orders)
            good = (
                chk["constant"]
                and chk["separating"]
                and chk["n_orbits"] == expected_orbits[d_cone]
                and sum(chk["orbit_sizes"]) == 4 ** (2 * genus)
            )
            ok = ok and good
            rows.append(
                {
                    "genus": genus,
                    "cone_subgroup_generator": d_cone,
                    "orders": list(orders),
                    "n_orbits": chk["n_orbits"],
                    "expected_orbits": expected_orbits[d_cone],
                    "orbit_sizes": chk["orbit_sizes"],
                    "invariants": [v[0] for v in chk["invariants"]],
                    "constant": chk["constant"],
                    "separating": chk["separating"],
                    "ok": good,
                    "seconds": round(time.time() - t0, 1),
                }
            )
    return {"name": "Theorem 8 (Reduction Lemma)", "rows": rows, "ok": ok}


# --------------------------------------------------------------------------- 3


def check_corollary9(quick: bool) -> dict:
    rows = []
    ok = True
    cases = [(1, (-1, 1)), (1, (-3, 3)), (1, (-3, 1, 2)), (2, (1, 7)), (2, (3, 5)),
             (2, (-1, 9)), (2, (-3, 11))]
    if not quick:
        cases += [(3, (1, 15)), (3, (-3, 19))]
    for genus, orders in cases:
        if any(m <= -4 for m in orders) or sum(orders) != 4 * (2 * genus - 2):
            continue
        odd = any(m % 2 for m in orders)
        orbits = handle_orbits(genus, orders)
        single = len(orbits) == 1 and len(orbits[0]) == 4 ** (2 * genus)
        good = (not odd) or single
        ok = ok and good
        rows.append({"genus": genus, "orders": list(orders), "has_odd_order": odd,
                     "n_orbits": len(orbits), "single_full_orbit": single, "ok": good})
    return {"name": "Corollary 9 (odd cone collapses rho)", "rows": rows, "ok": ok}


# --------------------------------------------------------------------------- 4


def genus1_cases(n_max: int, bound: int) -> list[tuple[int, tuple[int, ...]]]:
    """All ``(k, mu)`` with ``mu_i > -k``, ``sum mu_i = 0``, ``n <= n_max``."""
    out = []
    for k in (1, 2, 4):
        values = [v for v in range(-k + 1, bound + 1)]
        seen = set()

        def rec(prefix: tuple[int, ...], start: int, remaining: int, slots: int) -> None:
            if slots == 0:
                if remaining == 0:
                    seen.add(prefix)
                return
            for i in range(start, len(values)):
                v = values[i]
                rest = remaining - v
                if rest > bound * (slots - 1) or rest < (-k + 1) * (slots - 1):
                    continue
                rec(prefix + (v,), i, rest, slots - 1)

        for n in range(0, n_max + 1):
            rec((), 0, 0, n)
        out += [(k, mu) for mu in sorted(seen, key=lambda t: (len(t), t))]
    return out


def check_proposition12(quick: bool) -> dict:
    n_max, bound = (3, 4) if quick else (4, 6)
    rows = []
    ok = True
    for k, mu in genus1_cases(n_max, bound):
        verdict = genus1_nonempty(k, mu)
        witness = divisor_witness(k, mu)
        problems: list[str] = []
        if verdict.status == EMPTY:
            if witness is not None:
                problems.append("criterion says empty but a witness was constructed")
        else:
            if witness is None:
                problems.append("criterion says non-empty but no witness was constructed")
            else:
                problems += check_witness(k, mu, witness)
        ok = ok and not problems
        nz = [m for m in mu if m != 0]
        rows.append(
            {
                "k": k,
                "mu": list(mu),
                "n_nonzero": len(nz),
                "e_star": largest_common_divisor_of_k(k, nz) if nz else None,
                "criterion": verdict.status,
                "witness": [[str(p[0]), str(p[1])] for p in witness]
                if witness is not None
                else None,
                "problems": problems,
            }
        )
    return {
        "name": "Proposition 12 (genus 1 Abel-Jacobi criterion)",
        "n_cases": len(rows),
        "rows": rows,
        "ok": ok,
    }


# --------------------------------------------------------------------------- 7


def check_proposition20(quick: bool) -> dict:
    """On a torus, ``max E(X, p, m)`` must equal the intended ``image(rho)``.

    Proposition 20 says the holonomy at fixed conformal structure and fixed positions
    is *computed* by Abel-Jacobi: ``image(rho) = d Z_4`` with
    ``d = max {e | 4 : e | all m_i, sum (m_i/e) p_i ~ (4/e) K}``.  On a torus ``K`` is
    trivial, so this is a finite computation in ``(Q/Z)^2``, and the witnesses of
    Proposition 12 are exactly the points where ``max E`` takes the intended value.
    """
    from seamless_existence.elliptic import combination

    n_max, bound = (3, 4) if quick else (4, 6)
    rows = []
    ok = True
    for k, mu in genus1_cases(n_max, bound):
        witness = divisor_witness(k, mu)
        if witness is None:
            continue
        d = 4 // k
        m = [d * x for x in mu]
        E = []
        for e in (1, 2, 4):
            if any(x % e for x in m):
                continue
            if combination([x // e for x in m], witness).is_zero():
                E.append(e)
        good = bool(E) and max(E) == d
        ok = ok and good
        rows.append({"k": k, "mu": list(mu), "orders": m, "E": E,
                     "max_E": max(E) if E else None, "expected_d": d, "ok": good})
    return {
        "name": "Proposition 20 (holonomy is computed at fixed X and positions)",
        "n_cases": len(rows),
        "rows": rows,
        "ok": ok,
    }


# --------------------------------------------------------------------------- 5, 6


def check_theorem10_and_lemma3(max_faces: int) -> dict:
    table: dict[tuple, dict] = {}
    gluings = {}
    for n in range(1, max_faces + 1):
        t0 = time.time()
        seen = 0
        for mesh in enumerate_meshes(n):
            seen += 1
            mesh.check_consistency()  # Lemma 3 consistency, on every gluing
            collect_certificates([mesh], into=table)
        gluings[n] = {"connected_gluings": seen, "seconds": round(time.time() - t0, 1)}

    problems = []
    for genus, orders, d in table:
        nonzero = tuple(m for m in orders if m != 0)
        match = [s for s, _ in classify_orders(genus, nonzero) if s.rho_subgroup() == d]
        if not match:
            problems.append(f"no orbit with image(rho)=<{d}> for g={genus} m={list(orders)}")
            continue
        if predict(match[0]).status == EMPTY:
            problems.append(f"realized but predicted empty: {match[0]}")
    return {
        "name": "Theorem 10 and Lemma 3 against exhaustive construction",
        "max_faces": max_faces,
        "gluings": gluings,
        "total_gluings": sum(v["connected_gluings"] for v in gluings.values()),
        "n_signatures_realized": len(table),
        "problems": problems,
        "ok": not problems,
    }


# --------------------------------------------------------------------------- report


def to_markdown(result: dict) -> str:
    L = [
        "# Verification of `docs/proofs.md`",
        "",
        "Generated by `experiments/verify_proofs.py`.  Every check below uses only",
        "operations that are genuine mapping class actions, exact rational arithmetic,",
        "or explicit constructions; no check treats a failed search as evidence.",
        "",
        f"**Overall: {'all checks passed' if result['ok'] else 'FAILURES PRESENT'}**",
        "",
    ]

    l6 = result["lemma6"]
    L += ["## 1. Lemma 6 -- symplectic transitivity over `Z_4`", "",
          "| genus | generators | content class | class size | orbit size | transitive |",
          "|---|---|---|---|---|---|"]
    for run in l6["runs"]:
        for d, info in sorted(run["classes"].items()):
            L.append(
                f"| {run['genus']} | {run['generator_set']} ({run['n_generators']}) | "
                f"`{d}Z_4` | {info['class_size']} | {info['orbit_size']} | "
                f"{'yes' if info['transitive'] else 'NO'} |"
            )
    L += ["", "Each orbit is grown from the canonical representative `d e_1` using only",
          "transvections, so equality with the content class *proves* transitivity for",
          "that genus.", ""]

    t8 = result["theorem8"]
    L += ["## 2. Theorem 8 -- the Reduction Lemma", "",
          "| genus | `D` | orders | orbits | expected | orbit sizes | `image(rho)` per orbit | ok |",
          "|---|---|---|---|---|---|---|---|"]
    for r in t8["rows"]:
        L.append(
            f"| {r['genus']} | `{r['cone_subgroup_generator']}Z_4` | {r['orders']} | "
            f"{r['n_orbits']} | {r['expected_orbits']} | {r['orbit_sizes']} | "
            f"{r['invariants']} | {'yes' if r['ok'] else 'NO'} |"
        )
    L += ["", "`constant` and `separating` hold in every row, i.e. `image(rho)` is a",
          "complete invariant of the orbit, and the orbit sizes sum to `4^{2g}`.", ""]

    c9 = result["corollary9"]
    L += ["## 3. Corollary 9 -- an odd cone angle collapses the holonomy", "",
          "| genus | orders | odd order present | orbits | single full orbit |",
          "|---|---|---|---|---|"]
    for r in c9["rows"]:
        L.append(
            f"| {r['genus']} | {r['orders']} | {'yes' if r['has_odd_order'] else 'no'} | "
            f"{r['n_orbits']} | {'yes' if r['single_full_orbit'] else 'no'} |"
        )
    L.append("")

    p12 = result["proposition12"]
    n_empty = sum(1 for r in p12["rows"] if r["criterion"] == EMPTY)
    L += ["## 4. Proposition 12 -- genus 1, exact witnesses", "",
          f"{p12['n_cases']} cases `(k, mu)` checked; {p12['n_cases'] - n_empty} witnesses",
          f"constructed and verified, {n_empty} cases the criterion calls empty (no witness",
          "constructed, as required).  A witness is a list of distinct points of `(Q/Z)^2`",
          "satisfying `sum mu_i c_i = 0` and `sum (mu_i/e) c_i != 0` for every `e > 1`",
          "dividing `k` and all `mu_i`.", "",
          "Empty cases found (these are the whole obstruction in genus 1):", ""]
    for r in p12["rows"]:
        if r["criterion"] == EMPTY:
            L.append(f"* `k={r['k']}`, `mu={r['mu']}`")
    L += ["", "Sample verified witnesses:", "",
          "| `k` | `mu` | `e*` | points |", "|---|---|---|---|"]
    shown = 0
    for r in p12["rows"]:
        if r["witness"] and r["n_nonzero"] and shown < 12:
            pts = ", ".join(f"({a}, {b})" for a, b in r["witness"])
            L.append(f"| {r['k']} | {r['mu']} | {r['e_star']} | {pts} |")
            shown += 1
    L.append("")

    p20 = result["proposition20"]
    L += ["## 4b. Proposition 20 -- the holonomy is computed, not chosen", "",
          f"For each of the {p20['n_cases']} genus-1 witnesses, the set",
          "`E = {e | 4 : e divides every order and sum (m_i/e) c_i = 0}` was computed",
          "exactly, and `max E` compared with the intended `image(rho)` generator.",
          "",
          "| `k` | orders `m` | `E` | `max E` | expected | ok |",
          "|---|---|---|---|---|---|"]
    for r in p20["rows"][:14]:
        L.append(
            f"| {r['k']} | {r['orders']} | {r['E']} | {r['max_E']} | "
            f"{r['expected_d']} | {'yes' if r['ok'] else 'NO'} |"
        )
    if len(p20["rows"]) > 14:
        L.append(f"| ... {len(p20['rows']) - 14} more rows | | | | | |")
    L.append("")

    t10 = result["theorem10"]
    L += ["## 5-6. Theorem 10 and Lemma 3 against exhaustive construction", "",
          f"All {t10['total_gluings']} connected gluings of at most {t10['max_faces']} unit",
          "squares were enumerated.  Each one passes the Lemma 3 consistency conditions",
          "(Gauss-Bonnet, and rotational holonomy around every vertex equal to its valence",
          f"mod 4).  They realize {t10['n_signatures_realized']} distinct signatures, and",
          "none of them is a signature the criterion of Theorem 10 calls empty.", "",
          "| squares | connected gluings | seconds |", "|---|---|---|"]
    for n, info in sorted(t10["gluings"].items()):
        L.append(f"| {n} | {info['connected_gluings']} | {info['seconds']} |")
    if t10["problems"]:
        L += ["", "**Problems:**", ""] + [f"* {p}" for p in t10["problems"]]
    L.append("")

    L += ["## Not verified here", "",
          "* The external facts (S1)-(S6) of `docs/proofs.md` §7.",
          "* Masur-Smillie's and Gendron-Tahar's stratum classifications, which enter",
          "  `predict.py` as quoted literature (`docs/VERIFY.md`).",
          "* (D3), density of square-tiled surfaces in strata of 4-differentials -- used",
          "  only to justify searching.",
          ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--deep", action="store_true", help="also verify Lemma 6 at genus 5 (~6 min)")
    ap.add_argument("--max-faces", type=int, default=4)
    ap.add_argument("--out", default=str(ROOT / "results"))
    args = ap.parse_args()

    result = {
        "lemma6": check_lemma6(args.quick, deep=args.deep),
        "theorem8": check_theorem8(args.quick),
        "corollary9": check_corollary9(args.quick),
        "proposition12": check_proposition12(args.quick),
        "proposition20": check_proposition20(args.quick),
        "theorem10": check_theorem10_and_lemma3(args.max_faces),
    }
    result["ok"] = all(v["ok"] for v in result.values() if isinstance(v, dict))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "verification.json").write_text(json.dumps(result, indent=1))
    (out / "verification.md").write_text(to_markdown(result))

    for key in ("lemma6", "theorem8", "corollary9", "proposition12",
                "proposition20", "theorem10"):
        print(f"{'PASS' if result[key]['ok'] else 'FAIL'}  {result[key]['name']}")
    print(f"wrote {out / 'verification.md'}")
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
