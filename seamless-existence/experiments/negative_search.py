"""Hammer the signatures we believe are unrealizable.

The four strata below are the only ones the theory predicts to be empty in the
surveyed range.  Two of them are the graphics community's known cases (the torus
with cones of angle 3pi/2 and 5pi/2, and its half-translation shadow); the other
two, in genus 2, come from Masur-Smillie's exceptional strata Q(1,3) and Q(4) and
appear not to have been noted as obstructions to seamless parametrization.

A failed search proves nothing, so this script is only about making the negative
evidence expensive to overturn.  Rigorous non-existence for small meshes comes
from ``experiments/exhaustive.py`` instead.

Usage::

    PYTHONPATH=src python3 experiments/negative_search.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from seamless_existence.search import min_faces, search_target  # noqa: E402

TARGETS = [
    {
        "target": (1, (-1, 1), 1),
        "name": "torus, cones 3pi/2 and 5pi/2 (no 3,5-quadrangulation)",
        "known": "Izmestiev-Kusner-Rote-Springborn-Sullivan 2013; Shen et al. 2022 exception",
    },
    {
        "target": (1, (-2, 2), 2),
        "name": "torus, cones pi and 3pi, holonomy in {0, pi}",
        "known": "Masur-Smillie 1993: Q(1,-1) is empty",
    },
    {
        "target": (2, (8,), 2),
        "name": "genus 2, one cone of angle 6pi, holonomy in {0, pi}",
        "known": "Masur-Smillie 1993: Q(4) is empty -- apparently new in the graphics setting",
    },
    {
        "target": (2, (2, 6), 2),
        "name": "genus 2, cones 3pi and 5pi, holonomy in {0, pi}",
        "known": "Masur-Smillie 1993: Q(1,3) is empty -- apparently new in the graphics setting",
    },
]


def main() -> None:
    out = []
    for entry in TARGETS:
        genus, orders, d = entry["target"]
        t0 = time.time()
        mesh = search_target(
            (genus, tuple(sorted(orders)), d),
            extra_regular=6,
            iters=200000,
            restarts=6,
        )
        record = dict(entry)
        record["target"] = [genus, list(orders), d]
        record["min_faces"] = min_faces(genus, orders)
        record["max_faces_searched"] = min_faces(genus, orders) + 6
        record["found"] = None if mesh is None else list(mesh.alpha)
        record["seconds"] = round(time.time() - t0, 1)
        out.append(record)
        status = "FOUND (theory is wrong or there is a bug)" if mesh else "not found"
        print(f"{entry['name']}: {status} [{record['seconds']}s]")

    path = ROOT / "results" / "negative_search.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"budget": {"iters": 200000, "restarts": 6,
                                           "extra_regular": 6}, "results": out}, indent=1))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
