"""Decide one signature at a time, exhaustively.

Enumerating every gluing stops at four squares (``experiments/exhaustive.py``).
Deciding whether *one given* signature is realizable goes further, because the
target prunes the tree: gluing a side closes vertex cycles, and a cycle whose length
is not an allowed valence kills the branch at once.  The same pruning finds
certificates the annealer misses -- the cube, genus 0 with eight cones of angle
``3 pi/2``, turns up in 399 nodes.

A ``no`` from this search is a **proof** for that number of squares, provided the
run was exhausted (no node budget hit).  That is what upgrades the negative evidence
for the four unrealizable signatures from "the annealer did not find one" to
"there is none this small".

Usage::

    PYTHONPATH=src python3 experiments/exhaustive_target.py [--max-faces 5]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from seamless_existence.search import (  # noqa: E402
    exhaustive_target_search,
    min_faces,
)

# The signatures Theorem 10 says are unrealizable, with what makes them empty.
EMPTY_TARGETS = [
    ((1, (-1, 1), 1), "torus, cones 3pi/2 and 5pi/2 (no 3,5-quadrangulation)"),
    ((1, (-2, 2), 2), "torus, cones pi and 3pi, holonomy in {0, pi}: Q(1,-1)"),
    ((2, (8,), 2), "genus 2, one cone of 6pi, holonomy in {0, pi}: Q(4)"),
    ((2, (2, 6), 2), "genus 2, cones 3pi and 5pi, holonomy in {0, pi}: Q(1,3)"),
]

# Positive controls: these must be found, and one of them is the cube, which the
# annealer never finds.
CONTROL_TARGETS = [
    ((1, (-2, 2), 1), "torus, cones pi and 3pi, some odd holonomy"),
    ((2, (8,), 1), "genus 2, one cone of 6pi, primitive 4-differential"),
    ((2, (8,), 4), "genus 2, one cone of 6pi, translation surface"),
    ((2, (2, 6), 1), "genus 2, cones 3pi and 5pi, primitive 4-differential"),
    ((0, (-1,) * 8, 1), "the cube: genus 0, eight cones of 3pi/2"),
]


def run(target, max_faces: int, node_budget: int, time_budget: float) -> list[dict]:
    rows = []
    base = min_faces(target[0], target[1])
    spent = 0.0
    # a target whose minimum size already exceeds the cap is still tried at that
    # minimum -- the cube needs six squares and must not be skipped
    upper = max(max_faces, base)
    for n_faces in range(max(base, 1), upper + 1):
        if spent > time_budget:
            rows.append({"n_faces": n_faces, "skipped": "time budget"})
            break
        t0 = time.time()
        mesh, stats = exhaustive_target_search(target, n_faces, node_budget=node_budget)
        dt = time.time() - t0
        spent += dt
        rows.append(
            {
                "n_faces": n_faces,
                "found": None if mesh is None else list(mesh.alpha),
                "nodes": stats["nodes"],
                "exhausted": stats["exhausted"],
                "seconds": round(dt, 2),
            }
        )
        if mesh is not None:
            break
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-faces", type=int, default=5)
    ap.add_argument("--node-budget", type=int, default=0, help="0 = unlimited")
    ap.add_argument("--time-budget", type=float, default=1200.0,
                    help="soft per-target budget in seconds")
    ap.add_argument("--out", default=str(ROOT / "results"))
    args = ap.parse_args()

    out_rows = []
    for target, name in EMPTY_TARGETS + CONTROL_TARGETS:
        expected_empty = (target, name) in [(t, n) for t, n in EMPTY_TARGETS]
        rows = run(target, args.max_faces, args.node_budget, args.time_budget)
        found_at = next((r["n_faces"] for r in rows if r.get("found")), None)
        proved_up_to = max(
            (r["n_faces"] for r in rows if r.get("exhausted") and not r.get("found")),
            default=None,
        )
        status = "FOUND" if found_at else "no mesh"
        if expected_empty and found_at:
            status = "CONTRADICTION"
        if not expected_empty and not found_at:
            status = "MISSING CERTIFICATE"
        out_rows.append(
            {
                "target": [target[0], list(target[1]), target[2]],
                "name": name,
                "expected_empty": expected_empty,
                "min_faces": min_faces(target[0], target[1]),
                "found_at": found_at,
                "proved_empty_up_to": proved_up_to,
                "status": status,
                "rows": rows,
            }
        )
        print(f"{status:20s} {name} "
              f"(min {min_faces(target[0], target[1])} squares; "
              f"{'found at ' + str(found_at) if found_at else 'none up to ' + str(proved_up_to)})")

    payload = {"max_faces": args.max_faces, "targets": out_rows}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "exhaustive_target.json").write_text(json.dumps(payload, indent=1))
    (out / "exhaustive_target.md").write_text(to_markdown(payload))
    bad = [r for r in out_rows if r["status"] in ("CONTRADICTION", "MISSING CERTIFICATE")]
    print(f"{len(bad)} problems; wrote {out / 'exhaustive_target.md'}")
    sys.exit(1 if bad else 0)


def to_markdown(p: dict) -> str:
    L = [
        "# One signature at a time, exhaustively",
        "",
        "Generated by `experiments/exhaustive_target.py`.  For a fixed target the search",
        "tree can be pruned hard, so this reaches sizes that enumerating every gluing",
        "cannot.  A `no mesh` row with `exhausted = yes` is a **proof** that no quad mesh",
        "of that size realizes the signature.",
        "",
        "## The four unrealizable signatures",
        "",
        "| signature | minimum squares | no mesh up to | total nodes |",
        "|---|---|---|---|",
    ]
    for r in p["targets"]:
        if not r["expected_empty"]:
            continue
        nodes = sum(x.get("nodes", 0) for x in r["rows"])
        L.append(
            f"| {r['name']} | {r['min_faces']} | "
            f"{r['proved_empty_up_to'] if r['proved_empty_up_to'] else '-'} | {nodes} |"
        )
    L += [
        "",
        "Theorem 10 says these are unrealizable at *every* size; the table is an",
        "independent check at small sizes, and it is the only rigorous negative evidence",
        "in the repository -- the annealing searches are not evidence of absence.",
        "",
        "## Positive controls",
        "",
        "| signature | squares | nodes |",
        "|---|---|---|",
    ]
    for r in p["targets"]:
        if r["expected_empty"]:
            continue
        nodes = sum(x.get("nodes", 0) for x in r["rows"])
        L.append(f"| {r['name']} | {r['found_at']} | {nodes} |")
    L += [
        "",
        "The cube is the interesting control: the annealer of `search.py` never finds it",
        "(800 000 iterations are not enough), while the pruned exhaustive search settles",
        "it in a few hundred nodes.",
        "",
        "## Per-size detail",
        "",
        "| signature | squares | result | nodes | exhausted | seconds |",
        "|---|---|---|---|---|---|",
    ]
    for r in p["targets"]:
        for x in r["rows"]:
            if "skipped" in x:
                L.append(f"| {r['name']} | {x['n_faces']} | skipped ({x['skipped']}) | | | |")
                continue
            L.append(
                f"| {r['name']} | {x['n_faces']} | "
                f"{'found' if x['found'] else 'no mesh'} | {x['nodes']} | "
                f"{'yes' if x['exhausted'] else 'no'} | {x['seconds']} |"
            )
    L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
