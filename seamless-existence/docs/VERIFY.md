# Claims that still need checking

This repository was built in a sandbox whose outbound network access was
restricted to GitHub and package registries: `arxiv.org`, `link.springer.com` and
`cims.nyu.edu` all returned `403` at the egress proxy.  So none of the source PDFs
could be read.  What follows is what is left to check, ordered by how much damage a
mistake would do.

Two items from the first version of this file have since been **discharged** by
writing the proofs; they are recorded at the bottom.

## Open: literature checks

### 1. Are the two genus-2 obstructions actually new?

`README.md` Finding 2 claims that the signatures

* genus 2, one cone of angle `6 pi`, `image(rho) = 2 Z_4`  (`Q(4)`)
* genus 2, cones of angle `3 pi` and `5 pi`, `image(rho) = 2 Z_4`  (`Q(1,3)`)

are unrealizable and that this has not been noted in the graphics literature.  The
mathematics is Masur-Smillie plus Theorem 10 of `docs/proofs.md`; the *novelty*
claim is not checkable here, because Shen et al. 2022 and its sequels could not be
read.  **Check whether either paper lists exceptions beyond the torus case.**  If
they do, the finding downgrades from "new obstruction" to "independent
rederivation", which is still worth having, but the README must be corrected.

### 2. The exact statement of the Shen et al. gcd condition

`docs/proofs.md` Corollary 9 proves that when some cone angle is an odd multiple of
`pi/2` the holonomy along homology loops is irrelevant, because a single `MCG`-orbit
remains.  The claim that this coincides with their gcd hypothesis is inferred from
secondary descriptions ("it suffices that some cone has angle `3 pi/2` or `5 pi/2`;
the actual condition is weaker").  **Read the theorem statements and quote them
verbatim in `docs/reduction.md`.**

If their condition is genuinely weaker than `D = Z_4` -- for instance if it also
covers some `D = 2 Z_4` cases -- that is *information*, not a problem: it would say
which `d = 2` orbits their construction already realizes.

### 3. Masur-Smillie's exceptional list, verbatim

Used in `predict.QUADRATIC_EMPTY`: `Q(empty)` and `Q(1,-1)` in genus 1,
`Q(1,3)` and `Q(4)` in genus 2, for primitive quadratic differentials with at
worst simple poles.  Secondary sources agree, but the exact hypotheses
(primitivity, poles allowed or not, marked points) should be quoted.  Three
independent internal checks already passed:

* the search finds no square-tiled surface in any of the four strata, while
  finding one in all 178 other surveyed orbits;
* the genus-1 criterion of `docs/proofs.md` Proposition 12, derived independently
  of Masur-Smillie, reproduces both genus-1 exceptions;
* the explicit `(Q/Z)^2` witnesses exist for exactly the complementary cases
  (`results/verification.md`).

### 4. Gendron-Tahar's list for `k = 4`

Not a correction to make, a gap to fill: `predict.quartic_nonempty` returns
`unknown` for `g >= 2`, `d = 1`.  Extracting the exceptional list from
arXiv:2208.11654 is milestone M1 and would turn Theorem 10 into a complete,
computable answer.  The 120 square-tiled certificates already in
`results/survey.json` are an independent test of whatever list gets extracted.

### 5. Troyanov's theorem, exact hypotheses

Used for `docs/proofs.md` Proposition 11 (genus 0) as fact (S6).  Check the
`n >= 3` hypothesis and that the conclusion is for prescribed points.

### 6. The standard facts (S1)-(S5)

`docs/proofs.md` §7 uses: geodesic (Delaunay) triangulations of flat cone
surfaces; common refinements of triangulations of a surface; transitivity of
`Sp(2g, Z)` on primitive vectors; surjectivity of `Sp(2g, Z) -> Sp(2g, Z/N)`;
surjectivity of `MCG(Sigma_{g,1}, partial) -> Sp(2g, Z)`.  All standard, all worth
a citation each in a write-up.

## Open: mathematics

### 7. Density of square-tiled surfaces in strata of 4-differentials

(D3) of `docs/dictionary.md`.  Standard for abelian and quadratic differentials
(rational points are dense in period coordinates).  For `k = 4` with poles of order
`1, 2, 3` it is the natural analogue and is used here **only** to justify that
searching for square-tiled certificates is not futile.  No non-existence claim
rests on it.

## Discharged

### The topological equivalence (D2) -- proved

Now `docs/proofs.md` Lemma 2, including the invariance of realizability under
`MCG(M, C)` and the refinement argument.  It rests on the two standard PL facts
(S1) and (S2) above rather than on an unproved assertion.

### Proposition A for three or more singularities -- proved

Now `docs/proofs.md` Proposition 12.  The `n_0 >= 3` case is handled by
irreducibility of a coset of the identity component of
`ker(c |-> sum nu_i c_i)` together with explicit one-parameter subgroups on which
`c_i - c_j` is non-constant; primitivity is handled uniformly for all `n_0` by
aiming the sum at a point of exact order `e*` instead of at `0`.  The construction
is also run in exact arithmetic and checked case by case
(`results/verification.md`).
