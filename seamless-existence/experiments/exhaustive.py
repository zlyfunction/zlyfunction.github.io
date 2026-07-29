"""Exhaustive enumeration of small square-tiled quarter-translation surfaces.

Unlike the annealing search this is a *proof* within its range: after enumerating
every gluing of ``N <= max_faces`` squares, any signature whose minimal face
count is at most ``max_faces`` and which does not appear is proved to have no
square-tiled realization that small.

``N = 4`` means 2 027 025 gluings and takes about a minute; ``N = 5`` is 324
times bigger and is out of reach for this brute force.

Usage::

    PYTHONPATH=src python3 experiments/exhaustive.py [--max-faces 4]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from seamless_existence.predict import EMPTY, classify_orders, predict  # noqa: E402
from seamless_existence.search import collect_certificates, enumerate_meshes  # noqa: E402
from seamless_existence.signature import SUBGROUP_NAMES  # noqa: E402


def verify_against_theory(table: dict) -> list[str]:
    """Every realized signature must be one the theory does not call empty.

    This is the strongest consistency check available: the meshes and the quoted
    literature are completely independent of each other.
    """
    problems = []
    for genus, orders, d in table:
        nonzero = tuple(m for m in orders if m != 0)
        match = [s for s, _ in classify_orders(genus, nonzero) if s.rho_subgroup() == d]
        if not match:
            problems.append(f"no orbit with image(rho)=<{d}> for g={genus} m={list(orders)}")
            continue
        verdict = predict(match[0])
        if verdict.status == EMPTY:
            problems.append(f"realized but predicted empty: {match[0]} -- {verdict}")
    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-faces", type=int, default=4)
    ap.add_argument("--check", action="store_true", help="assert consistency on every mesh")
    ap.add_argument("--out", default=str(ROOT / "results"))
    args = ap.parse_args()

    table: dict[tuple, dict] = {}
    counts = {}
    for n in range(1, args.max_faces + 1):
        t0 = time.time()
        seen = 0
        for mesh in enumerate_meshes(n):
            seen += 1
            collect_certificates([mesh], into=table, check=args.check)
        counts[n] = seen
        print(f"N={n}: {seen} connected gluings, {len(table)} invariants so far, "
              f"{time.time() - t0:.1f}s")

    problems = verify_against_theory(table)
    if problems:
        print("THEORY MISMATCH:")
        for p in problems:
            print("  " + p)
    else:
        print(f"all {len(table)} realized signatures are consistent with predict.py")

    rows = []
    for (genus, orders, d), cert in sorted(table.items()):
        rows.append(
            {
                "genus": genus,
                "orders": list(orders),
                "angles_in_quarter_turns": [m + 4 for m in orders],
                "rho_subgroup": SUBGROUP_NAMES[d],
                "certificate_faces": cert["n_faces"],
                "certificate_alpha": cert["alpha"],
            }
        )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "max_faces": args.max_faces,
        "connected_gluings": counts,
        "n_invariants": len(rows),
        "theory_mismatches": problems,
        "realized": rows,
    }
    (out / "exhaustive.json").write_text(json.dumps(payload, indent=1))
    print(f"{len(rows)} distinct signatures realized; wrote {out / 'exhaustive.json'}")


if __name__ == "__main__":
    main()
