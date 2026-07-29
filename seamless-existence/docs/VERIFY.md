# Claims that still need checking

This repository was built in a sandbox whose outbound network access was
restricted to GitHub and package registries: `arxiv.org`, `link.springer.com` and
`cims.nyu.edu` all returned `403` at the egress proxy.  So none of the source PDFs
could be read.  Everything below is either quoted from memory, reconstructed from
search-result summaries, or derived here from scratch.  Nothing in the code
depends on an unverified literature claim without saying so.

Ordered by how much damage a mistake would do.

## 1. The topological equivalence (D2)

`docs/dictionary.md` (D2) asserts that realizability of a signature on some
refinement of a given mesh is the same as realizability by a flat cone metric on
the underlying topological surface with cones at *some* `n` distinct points.  The
proof sketch (pull back by a homeomorphism, then triangulate and refine) is
routine but it is the load-bearing wall of the whole reduction.  **Write it out
properly, and check it against how Shen et al. 2022 set up their own topological
existence statement.**

Risk if wrong: the reduction answers a slightly different question than the
graphics one, and the two apparently-new genus-2 obstructions would need
restating.

## 2. Density of square-tiled surfaces in strata of 4-differentials (D3)

Standard for abelian and quadratic differentials (rational points are dense in
period coordinates).  For `k = 4` with poles of order `1, 2, 3` it is the natural
analogue and is used here **only** to justify that searching for square-tiled
certificates is not futile.  No non-existence claim rests on it.

## 3. Are the two genus-2 obstructions actually new?

`README.md` Finding 2 claims that the signatures

* genus 2, one cone of angle `6 pi`, `image(rho) = 2 Z_4`  (`Q(4)`)
* genus 2, cones of angle `3 pi` and `5 pi`, `image(rho) = 2 Z_4`  (`Q(1,3)`)

are unrealizable and that this has not been noted in the graphics literature.
The mathematical content (Masur-Smillie) is certain modulo item 1; the *novelty*
claim is not, because Shen et al. 2022 and its sequels could not be read.  **Check
whether either paper lists exceptions beyond the torus case.**  If they do, the
finding downgrades from "new obstruction" to "independent rederivation", which is
still worth having, but the README must be corrected.

## 4. The exact statement of the Shen et al. gcd condition

`docs/reduction.md` consequence (a) claims that the gcd hypothesis is exactly the
regime `D = Z_4` in which the Reduction Lemma collapses all holonomy choices into
one orbit.  The *mechanism* is proved here; the claim that it coincides with their
hypothesis is inferred from secondary descriptions of the paper ("it suffices that
some cone has angle `3 pi/2` or `5 pi/2`; the actual condition is weaker").
**Read Theorem/Proposition statements and confirm, then quote them verbatim in
`docs/reduction.md`.**

If their condition is genuinely weaker than `D = Z_4` -- for instance if it also
covers some `D = 2 Z_4` cases -- that is *information*, not a problem: it would
say which `d = 2` orbits their construction already realizes.

## 5. Masur-Smillie's exceptional list, verbatim

Used in `predict.QUADRATIC_EMPTY`.  Recalled here as `Q(empty)`, `Q(1,-1)` in
genus 1 and `Q(1,3)`, `Q(4)` in genus 2, for primitive quadratic differentials
with at worst simple poles.  Secondary sources agree, but the exact hypotheses
(primitivity, poles allowed or not, marked points) should be quoted.  Two
independent internal checks already passed:

* the search finds no square-tiled surface in any of the four strata, while
  finding one in all 178 other surveyed orbits;
* the genus-1 Abel-Jacobi criterion of `docs/genus1.md`, derived independently,
  reproduces both genus-1 exceptions.

## 6. Proposition A, the `n >= 3` case

`docs/genus1.md` proves the two-singularity case of Proposition A carefully; the
`n >= 3` case is a submersion-plus-general-position argument that is sketched, and
the primitivity step there is asserted rather than proved.  Worth doing properly
since genus 1 is otherwise a complete result.

## 7. Troyanov's theorem, exact hypotheses

Used for Proposition 0 (genus 0).  Check the `n >= 3` hypothesis and whether the
conclusion is stated for prescribed points (it is, as far as I recall).
