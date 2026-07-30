# seamless-existence

Working repository for the open problem left by *Which Cross Fields can be
Quadrangulated?* (Shen, Zhu, Capouellez, Panozzo, Campen, Zorin, ACM TOG 41(4),
2022):

> For which holonomy signatures do seamless parametrizations with the
> corresponding topology exist?

Sufficient conditions are strong and combinatorial.  Necessary conditions are
essentially absent -- the only known obstruction is the torus with two cones of
angle `3 pi/2` and `5 pi/2`.  The bet of this repository is that the obstructions
are not new mathematics: they are already classified, in the language of flat
surfaces and `k`-differentials, and what is missing is the bridge.  That bridge is
now built and proved: **realizability is equivalent to non-emptiness of a stratum of
primitive `k`-differentials** (Theorem 10).

Start with [`docs/problem.md`](docs/problem.md) for the question and
[`docs/proofs.md`](docs/proofs.md) for the mathematics;
[`docs/dictionary.md`](docs/dictionary.md), [`docs/reduction.md`](docs/reduction.md)
and [`docs/genus1.md`](docs/genus1.md) are expositions of the proofs, and
[`results/verification.md`](results/verification.md) is the machine-checked part.

## The approach in five lines

A seamless parametrization is a flat cone metric with rotational holonomy in
`Z_4`, which is a meromorphic **4-differential** `q`: a cone of angle
`(m + 4) pi/2` is a zero or pole of order `m`.  Let `d` generate
`image(rho) <= Z_4`.  Then `q` is the `(4/d)`-th power of a primitive
`(4/d)`-differential with orders `m_i / d`, so the existence question becomes
**non-emptiness of a stratum** -- and that is classified: classically for `k = 1`,
by Masur-Smillie for `k = 2`, by Gendron-Tahar for `k = 4`.

## Findings so far

**Finding 1 -- the holonomy data almost never matters.**  Realizability depends on
the signature only through `(genus, multiset of cone angles, image(rho))`
(Reduction Lemma, `docs/reduction.md`).  So there are at most three cases per
cone-angle multiset instead of `4^{2g}`.  In particular, if any cone angle is an
odd multiple of `pi/2` then `image(rho) = Z_4` is forced and *all* choices of
rotations along homology loops are equivalent: point-pushing a cone of odd order
around a handle shifts the holonomy by an odd amount, so it can reach anything.
That is a first-principles explanation of the *shape* of the gcd condition of
Shen et al. 2022 -- their hypothesis is exactly the regime where the holonomy
cannot obstruct anything.  The conclusion is checked by brute force (BFS over all
`4^{2g}` holonomy vectors under point pushing and symplectic transvections) in
`tests/test_reduction.py` for `g = 1, 2`, and asserted for every case in the
survey, which covers `g <= 3`.

**Finding 2 -- there are more obstructions than the torus one, and they are
classical.**  Masur-Smillie's empty strata `Q(4)` and `Q(1,3)` translate into two
unrealizable holonomy signatures in genus 2:

| genus | cone angles | holonomy | reduced stratum |
|---|---|---|---|
| 2 | one cone of `6 pi` | `image(rho) = {0, pi}` | `Q(4)` -- empty |
| 2 | `3 pi` and `5 pi` | `image(rho) = {0, pi}` | `Q(1,3)` -- empty |

In graphics terms: a genus-2 surface carrying a cross field whose holonomy along
every homology loop is a multiple of `pi` (equivalently: the cross field splits
globally into two line fields) and with these singularities **cannot be
quadrangulated**.  Both are outside the gcd condition, so they contradict nothing;
they populate the gap.  Neither appears to have been noted in the graphics
literature, though that novelty claim is the one thing here I could not check
(`docs/VERIFY.md`, item 3).  Independent confirmation: an exhaustive enumeration
of all 1 889 667 gluings of up to four unit squares realizes 67 signatures, and
neither of these is among them, while every other surveyed signature of comparable
size is realized.  A dedicated search with a much larger budget -- up to six extra
regular vertices, 200 000 annealing steps, six restarts per size -- also fails on
all four unrealizable signatures (`results/negative_search.json`).

**Finding 3 -- genus 0 and genus 1 are completely settled, with proofs.**  Genus 0: every
Gauss-Bonnet-admissible signature is realizable (Troyanov; on the sphere the
holonomy is determined by the angles).  Genus 1: an Abel-Jacobi argument gives a
complete list of exceptions, and it recovers the known one in a line -- a
`k`-differential with divisor `c_1 - c_2` needs `c_1 - c_2` to be a nonzero
1-torsion point of an elliptic curve, and there are none (`docs/proofs.md`
Propositions 11-12, Corollary 13).  The same criterion independently reproduces
both of Masur-Smillie's genus-1 empty strata, which is a good sign that the
dictionary is right.  On the torus the answer is a complete list: unrealizable
exactly for (i) no cones with nontrivial holonomy, (ii) two cones of angle
`3 pi/2` and `5 pi/2`, (iii) two cones of angle `pi` and `3 pi` with holonomy
everywhere a multiple of `pi`.

**Finding 4 -- the Main Theorem survives a 188-orbit test.**  For every genus
`<= 3`, at most 4 cones and orders bounded by 8, the survey compares theory
against construction (`results/survey.md`):

| outcome | count |
|---|---|
| certified by an explicit square-tiled surface | 178 |
| predicted empty, and not found | 4 |
| predicted non-empty, search failed (search weakness, all genus 3, `N >= 8`) | 6 |
| **contradictions** | **0** |
| predicted unknown *and* not found (i.e. genuinely open cells) | 0 |

The four empty ones are exactly the four classical exceptions.  Notably all 120
surveyed genus-`>= 2` strata of primitive 4-differentials got certificates, so in
this range the answer to the open problem is: **realizable unless the reduced
stratum is one of the four classical empty ones.**

[`results/answers.md`](results/answers.md) states this per genus in graphics
language -- cone angles as multiples of `pi`, holonomy described in cross-field
terms -- so it can be checked against an implementation directly.

**Finding 5 -- the proofs are machine-checked where that is possible.**
[`results/verification.md`](results/verification.md) checks, with no appeal to any
failed search:

* **Lemma 6** (`Sp(2g, Z_4)` is transitive on each content class) for
  `g = 1, ..., 5`, by growing the orbit of `d e_1` under genuine transvections
  until it is the whole class -- `1 047 552` vectors at `g = 5`;
* **Theorem 8** (the Reduction Lemma) for `g = 1, 2, 3` and all three cone
  subgroups `D`, with the predicted orbit counts `1 / 2 / 3`;
* **Corollary 9** (an odd cone angle collapses the holonomy) case by case;
* **Proposition 12** (genus 1) by constructing the divisor witnesses explicitly in
  `(Q/Z)^2` with exact `Fraction` arithmetic and verifying both defining
  conditions, for every admissible `(k, mu)` in a range -- the criterion says
  "non-empty" exactly when a witness gets built;
* **Proposition 20** (at fixed conformal structure the holonomy is *computed*, not
  chosen) on every genus-1 witness, by evaluating the Abel-Jacobi set
  `E = {e | 4 : e divides every order and sum (m_i/e) c_i = 0}` exactly and checking
  `max E` against the intended `image(rho)`;
* **Theorem 10 and Lemma 3** against all `1 889 667` gluings of at most four unit
  squares: each satisfies Gauss-Bonnet and has holonomy equal to the valence mod 4
  at every vertex, and none realizes a signature the theorem calls empty;
* **Theorem 10 negatively**: for each of the four unrealizable signatures, a pruned
  exhaustive search over *all* gluings of a given size finds nothing, which is a
  proof at that size (`results/exhaustive_target.md`).  This is the only rigorous
  negative evidence in the repository; the annealing searches are not evidence of
  absence.  The same search finds certificates the annealer never does -- the cube
  turns up in 399 nodes.

**Finding 7 -- the fixed-conformal-structure criterion, reconciled.**  At a fixed
Riemann surface and fixed cone positions the holonomy is not free at all: it is
computed by Abel-Jacobi, `image(rho) = d Z_4` with
`d = max {e | 4 : e divides every m_i and sum (m_i/e) p_i ~ (4/e) K}`
(`docs/proofs.md` Proposition 20).  So a signature is realizable iff *some* `(X, p)`
has `max E = d` (Corollary 21) -- the fixed-structure criterion of
Chen-Zheng-Ke-Lei-Luo-Gu is the pointwise condition, and the question here is
whether the locus it cuts out is non-empty.  This also explains their restriction to
even topological valence: an odd `m_i` forces `E = {1}` for every `(X, p)`, i.e. a
genuine primitive 4-differential and `image(rho) = Z_4` -- exactly the `D = Z_4`
regime where, for the topological question, the holonomy drops out entirely
(Corollary 22).  The hard case there is the easy case here.

**Finding 6 -- feature curves: the same reduction, and no obstruction in sight.**
Cutting along a feature network turns the problem into one on a surface with
boundary whose sides must develop to axis-parallel segments.  `docs/proofs.md` §8
carries the machinery over:

* Gauss-Bonnet becomes `sum (4 - v_i) + sum (2 - a_j) = 4 chi`, which forces
  `sum m_i + sum a_j` to be even (Lemma 14);
* the space of signatures with fixed orders and boundary turnings is again
  `Z_4^{2g}` (Lemma 15), and the **Reduction Lemma holds verbatim** with
  `D = <m_i, t_j>` enlarged by the turnings `t_j = sum (2 - a_j)` (Theorem 16) --
  sliding a boundary component along a loop plays the role of point pushing;
* hence a single boundary component of odd turning -- one `pi/2` corner is enough --
  forces `D = Z_4` and a single orbit, so **the holonomy along homology loops cannot
  obstruct anything** (Corollary 17).  Real feature networks are full of right-angle
  corners, which is a precise reason the feature-aligned literature's sufficient
  conditions work as well as they do in practice.

Doubling along the boundary (Lemma 18, verified on all 110 303 boundary meshes of at
most three squares) transports a feature-aligned signature to a closed one on a
surface of genus `2g + b - 1`.  It is the only route by which the closed
classification could produce a feature-curve obstruction, and it produces none: of
3058 admissible feature-aligned signatures in range, Corollary 19 rules out zero.
The reason is structural -- a double that could land in one of Masur-Smillie's empty
strata always also admits the `image(rho~) = Z_4` alternative, where the stratum is
non-empty.  Deciding the boundary case therefore needs *real* strata, differentials
invariant under an anti-holomorphic involution; that is the open end of §8.

## Main Theorem

> A holonomy signature `(g, m, rho)` is realizable by a seamless parametrization
> iff the stratum of primitive `(4/d)`-differentials with orders `m_i / d` is
> non-empty, where `d` generates `image(rho)`.

Proved as Theorem 10 of [`docs/proofs.md`](docs/proofs.md), from the dictionary
(Lemmas 1-4), the topological equivalence (Lemma 2) and the Reduction Lemma
(Theorem 8).  It uses six standard facts, listed as (S1)-(S6) in §7 there, and
nothing else.

So the open problem is now a bookkeeping exercise over an existing classification.
What is still missing is the bookkeeping input for `k = 4`: Gendron-Tahar's
exceptional list (milestone M1).  Writing the whole thing up with explicit tables
is milestone M2.

## Layout

```
docs/problem.md      the open problem, stated precisely
docs/proofs.md       ALL PROOFS: the dictionary, the Reduction Lemma, the Main
                     Theorem, genus 0 and genus 1; §7 lists every external fact used
docs/dictionary.md   exposition: seamless <-> flat Z_4 metric <-> 4-differential
docs/reduction.md    exposition: the Reduction Lemma and what it means
docs/genus1.md       exposition: complete answers in genus 0 and 1
                     (§8 of docs/proofs.md covers boundary / feature curves)
docs/literature.md   annotated reading list: what to extract from which paper
docs/roadmap.md      milestones M0-M7 and immediate next actions
docs/VERIFY.md       claims still needing a source check, and what has been discharged
src/seamless_existence/
  signature.py       holonomy signatures, reduction to k-differential data
  mcg.py             MCG action, orbit computation, symplectic transitivity check
  quadmesh.py        square-tiled quarter-translation surfaces
  search.py          exhaustive and targeted (annealing) search
  predict.py         what the literature says about each reduced stratum
  elliptic.py        exact (Q/Z)^2 arithmetic and the genus-1 divisor witnesses
experiments/         verify_proofs, survey, exhaustive, exhaustive_target,
                     negative_search, boundary_survey, tables
results/             generated: verification.md, survey.md, answers.md,
                     exhaustive_target.md, boundary.md, ...
tests/               59 tests, no dependencies
```

Pure standard library, Python 3.11+.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests    # ~6 s
PYTHONPATH=src python3 experiments/verify_proofs.py     # ~3 min, checks docs/proofs.md
PYTHONPATH=src python3 experiments/verify_proofs.py --deep   # + genus 5, ~9 min
PYTHONPATH=src python3 experiments/survey.py            # ~10 min, writes results/
PYTHONPATH=src python3 experiments/exhaustive.py        # ~1 min, N <= 4
PYTHONPATH=src python3 experiments/exhaustive_target.py # ~7 min, one signature at a time
PYTHONPATH=src python3 experiments/negative_search.py   # long; hammers the four empty strata
PYTHONPATH=src python3 experiments/boundary_survey.py   # ~5 min, feature curves
```

## Limitations

* **Six standard facts are used as black boxes** -- (S1)-(S6) of `docs/proofs.md`
  §7: geodesic triangulations of flat cone surfaces, common refinements of
  triangulations, transitivity of `Sp(2g, Z)` on primitive vectors, surjectivity of
  `Sp(2g, Z) -> Sp(2g, Z/N)` and of `MCG(Sigma_{g,1}, partial) -> Sp(2g, Z)`, and
  Troyanov's theorem.  Nothing else is assumed on the geometric side.
* **No source PDF could be read.**  The sandbox this was built in had outbound
  HTTPS blocked for `arxiv.org`, `springer.com` and `cims.nyu.edu`.  Literature
  statements are from memory and secondary sources; every one of them is listed in
  `docs/VERIFY.md` with what to check.
* **A failed annealing search proves nothing**, and annealing is weak exactly where
  certificates are hardest: low genus with many cones.  The cube -- genus 0, eight
  cones of angle `3 pi/2`, six squares -- is *not* found by the annealer even with
  800 000 iterations, though it obviously exists; with boundary it misses the
  five-square fan (`QuadMesh.fan(5)`).  For closed meshes this is now fixed by the
  pruned per-target search of `experiments/exhaustive_target.py`, which settles the
  cube in 399 nodes and decides any single signature exhaustively up to five squares.
  For meshes with boundary the annealer is still all there is above three squares, so
  the boundary survey takes every negative statement from exhaustive enumeration
  instead.
* **Fitting the corner count is not the same as fitting in the mesh.**  A quad mesh
  cannot subdivide a single boundary edge, so padding a feature-aligned signature to
  a given size means adding whole squares.  The 412 signatures that the boundary
  survey reports as unrealizable with three squares are, for the most part, simply
  larger than three squares.
* Exhaustive enumeration stops at four squares (`N = 5` is 324 times larger).
  Orderly generation would push it to seven or eight; that is milestone M6.
