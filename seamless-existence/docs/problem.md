# The problem

## As posed in the graphics literature

> For which holonomy signatures do seamless parametrizations with the
> corresponding topology exist?

This is the question left open by Shen, Zhu, Capouellez, Panozzo, Campen and
Zorin, *Which Cross Fields can be Quadrangulated? Global Parameterization from
Prescribed Holonomy Signatures*, ACM TOG 41(4), 2022, and restated verbatim in
the introduction of Capouellez and Zorin, *Seamless Parametrization in Penner
Coordinates*, ACM TOG 43(4), 2024.

The state of the art, as of this writing:

* **Sufficient conditions** exist and are strong.  Shen et al. 2022 prove
  realizability under a mild hypothesis on the cone angles -- a gcd-type
  condition, satisfied for instance whenever some cone has angle `3 pi/2` or
  `5 pi/2` -- with one exception: the torus with exactly two cones, of angles
  `3 pi/2` and `5 pi/2`.  Their construction is a rerouting argument: it is
  combinatorial and topological.
* **Necessary conditions** are essentially absent.  The only known obstruction is
  the torus exception above, which comes from Izmestiev, Kusner, Rote, Springborn
  and Sullivan, *There is no triangulation of the torus with vertex degrees
  5, 6, ..., 6, 7 and related results*, Geom. Dedicata 166 (2013), whose
  Corollary includes the non-existence of a `3,5`-quadrangulation of the torus.
* The 2025 feature-aligned sequel (Capouellez, Singh, Heistermann, Bommes,
  Zorin) states that for a given mesh connectivity, or for specific singularity
  configurations, existence is in general still unknown.

So the gap has not moved since 2022, and it is a gap of a specific shape: the
sufficient condition is combinatorial, while the one known obstruction is
conformal-algebraic.  This repository takes the position that the necessary
conditions should be sought in the language where the obstruction naturally
lives.

## Restated precisely

Fix a closed oriented surface `M` of genus `g`, an integer `n >= 0`, and

* cone angles `theta_i = (m_i + 4) pi / 2` with integers `m_i > -4`, satisfying
  Gauss-Bonnet `sum_i m_i = 4(2g - 2)`;
* a rotational holonomy homomorphism `rho: H_1(M \ C; Z) -> Z_4` with
  `rho(gamma_i) = m_i mod 4` on the loop around `c_i`.

**Question.** For which triples `(g, m, rho)` does there exist a seamless
parametrization of `M` -- equivalently (see `docs/dictionary.md`) a flat cone
metric with these cone angles and rotational holonomy `rho`?

Two remarks on what is *not* being asked.

* The cone *positions* are not fixed, and neither is the conformal structure.
  Existence is a question about a stratum being non-empty, not about a specific
  Riemann surface.  This is what separates the question from the Abel-Jacobi
  criterion of Chen-Zheng-Ke-Lei-Luo-Gu, which fixes both.  Relating the two
  settings precisely is itself a well-posed open problem (milestone M5).
* The mesh may be refined.  Existence at fixed connectivity is a different, and
  probably much harder, combinatorial question (milestone M6).

## What this repository contains

All proofs are in `docs/proofs.md`; the other documents are expositions.

1. A dictionary turning the question into non-emptiness of a stratum of
   `k`-differentials, including the topological equivalence that makes the
   question independent of the mesh and of the conformal structure (Lemmas 1-4).
2. A Reduction Lemma showing the answer depends on the holonomy only through
   `image(rho) <= Z_4`, leaving at most three cases per cone-angle multiset, and
   explaining why the known sufficient condition has the shape it has
   (Theorem 8, Corollary 9).
3. The Main Theorem: a signature is realizable iff a stratum of primitive
   `(4/d)`-differentials is non-empty (Theorem 10).
4. Complete answers in genus 0 and genus 1, the latter reproducing the unique
   known exception in one line (Propositions 11-12, Corollary 13).
5. A computational engine that certifies signatures by constructing square-tiled
   surfaces, a survey cross-checking theory against construction over 188 orbits
   (`results/survey.md`), and a machine-checked verification of the proofs
   (`results/verification.md`).
