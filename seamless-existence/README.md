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
surfaces and `k`-differentials, and what is missing is the bridge.

Start with [`docs/problem.md`](docs/problem.md), then
[`docs/dictionary.md`](docs/dictionary.md) and
[`docs/reduction.md`](docs/reduction.md).

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

**Finding 3 -- genus 0 and genus 1 are completely settled.**  Genus 0: every
Gauss-Bonnet-admissible signature is realizable (Troyanov; on the sphere the
holonomy is determined by the angles).  Genus 1: an Abel-Jacobi argument gives a
complete list of exceptions, and it recovers the known one in a line -- a
`k`-differential with divisor `c_1 - c_2` needs `c_1 - c_2` to be a nonzero
1-torsion point of an elliptic curve, and there are none (`docs/genus1.md`).  The
same criterion independently reproduces both of Masur-Smillie's genus-1 empty
strata, which is a good sign that the dictionary is right.

**Finding 4 -- the Main Conjecture survives a 188-orbit test.**  For every genus
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

## Main Conjecture

> A holonomy signature `(g, m, rho)` is realizable by a seamless parametrization
> iff the stratum of primitive `(4/d)`-differentials with orders `m_i / d` is
> non-empty, where `d` generates `image(rho)`.

The forward direction is the dictionary.  The converse needs the topological
equivalence (D2) of `docs/dictionary.md`.  Turning the conjecture into a theorem
with explicit tables is milestone M2; the missing input is the `k = 4` exceptional
list of Gendron-Tahar (milestone M1).

## Layout

```
docs/problem.md      the open problem, stated precisely
docs/dictionary.md   seamless parametrization <-> flat Z_4 metric <-> 4-differential
docs/reduction.md    the Reduction Lemma and the Main Conjecture
docs/genus1.md       complete answers in genus 0 and 1
docs/literature.md   annotated reading list: what to extract from which paper
docs/roadmap.md      milestones M0-M7 and immediate next actions
docs/VERIFY.md       every claim that still needs checking against a source
src/seamless_existence/
  signature.py       holonomy signatures, reduction to k-differential data
  mcg.py             mapping class group action, orbit computation
  quadmesh.py        square-tiled quarter-translation surfaces
  search.py          exhaustive and targeted (annealing) search
  predict.py         what the literature says about each reduced stratum
experiments/         survey, exhaustive enumeration, negative search
results/             generated: survey.md, survey.json, exhaustive.json, ...
tests/               24 tests, no dependencies
```

Pure standard library, Python 3.11+.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests    # ~4 s
PYTHONPATH=src python3 experiments/survey.py            # ~10 min, writes results/
PYTHONPATH=src python3 experiments/exhaustive.py        # ~1 min, N <= 4
PYTHONPATH=src python3 experiments/negative_search.py   # long; hammers the four empty strata
```

## Limitations

* **(D2) is not proved.**  The identification of the graphics question with a
  question about strata is routine but load-bearing; see `docs/VERIFY.md` item 1.
* **No source PDF could be read.**  The sandbox this was built in had outbound
  HTTPS blocked for `arxiv.org`, `springer.com` and `cims.nyu.edu`.  Literature
  statements are from memory and secondary sources; every one of them is listed in
  `docs/VERIFY.md` with what to check.
* **A failed search proves nothing.**  Annealing is weak exactly where certificates
  are hardest: low genus with many cones.  The cube -- genus 0, eight cones of
  angle `3 pi/2`, six squares -- is *not* found by the annealer even with 800 000
  iterations, though it obviously exists (`tests/test_quadmesh.py` builds it by
  hand).  So "not found" rows are evidence only when the theory independently says
  the stratum is empty, or when `experiments/exhaustive.py` covers the size.
* Exhaustive enumeration stops at four squares (`N = 5` is 324 times larger).
  Orderly generation would push it to seven or eight; that is milestone M6.
