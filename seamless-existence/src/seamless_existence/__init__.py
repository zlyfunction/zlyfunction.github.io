"""Existence of seamless parametrizations with prescribed holonomy signature.

Modules
-------
``signature``  holonomy signatures and their reduction to ``k``-differential data
``mcg``        mapping-class-group action, orbit computation, Reduction Lemma check
``quadmesh``   square-tiled quarter-translation surfaces (= combinatorial quad meshes)
``search``     exhaustive / randomized search for square-tiled certificates
``predict``    what the flat-surface literature says about each reduced stratum
``elliptic``   exact ``(Q/Z)^2`` arithmetic and the genus-1 divisor witnesses

All proofs are in ``docs/proofs.md``; ``experiments/verify_proofs.py`` machine-checks
the parts that can be checked.
"""

from .elliptic import Pt, check_witness, divisor_witness
from .mcg import (
    handle_orbits,
    orbit_representatives,
    verify_reduction_lemma,
    verify_sp_transitivity,
)
from .predict import EMPTY, EXISTS, UNKNOWN, Verdict, classify_orders, predict
from .quadmesh import MeshInvariant, QuadMesh
from .search import collect_certificates, enumerate_meshes, random_meshes
from .signature import Signature, subgroup_generator

__all__ = [
    "Signature",
    "subgroup_generator",
    "QuadMesh",
    "MeshInvariant",
    "handle_orbits",
    "orbit_representatives",
    "verify_reduction_lemma",
    "verify_sp_transitivity",
    "Pt",
    "divisor_witness",
    "check_witness",
    "predict",
    "classify_orders",
    "Verdict",
    "EXISTS",
    "EMPTY",
    "UNKNOWN",
    "enumerate_meshes",
    "random_meshes",
    "collect_certificates",
]
