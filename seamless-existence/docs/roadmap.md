# Roadmap

Ordered so that each milestone is worth writing up on its own.

## M0. Done: the reduction and the low-genus cases

* Reduction Lemma, verified computationally for `g <= 3` (`docs/reduction.md`).
* Genus 0 complete via Troyanov; genus 1 complete via Abel-Jacobi, reproducing the
  unique known exception (`docs/genus1.md`).
* Square-tiled certification engine and a 188-orbit survey (`results/survey.md`).

Remaining work on M0: prove (D2) properly, tighten Proposition A for `n >= 3`,
and verify the literature statements in `docs/VERIFY.md`.

## M1. Read the `k = 4` exceptional list out of Gendron-Tahar

This is the highest-value single task in the project.  `predict.quartic_nonempty`
returns `unknown` for every genus `>= 2` signature with `image(rho) = Z_4`; the
answer exists in arXiv:2208.11654 and needs to be translated into

    is the stratum of primitive 4-differentials with orders (m_1, ..., m_n),
    m_i > -4, sum m_i = 4(2g - 2), on a genus-g surface non-empty?

Once that table is in `predict.py`, the Main Conjecture of `docs/reduction.md`
becomes a *complete, checkable* answer to the open problem for every genus, modulo
(D2).  The survey already provides square-tiled certificates for 120 such strata,
which gives a large independent test of whatever list is extracted: any stratum the
paper calls empty but the search realizes means the translation is wrong.

Caveat: the paper is 71 pages in French.  Budget accordingly.

## M2. Write up "necessary and sufficient conditions for realizable holonomy signatures"

Contents, in the order they should appear:

1. Dictionary (`docs/dictionary.md`), with (D2) proved.
2. Reduction Lemma, with the two-line consequence that the gcd condition of
   Shen et al. 2022 is exactly the single-orbit regime.
3. Theorem: realizable iff the reduced stratum is non-empty.
4. Explicit tables: genus 0 (always), genus 1 (three exceptions), genus 2 (the
   Masur-Smillie pair plus whatever M1 contributes), general `g`.
5. The exceptional signatures as counterexamples in graphics language, with
   pictures of the near-miss meshes.

The framing that makes this land for a graphics audience: *the sufficient
condition was combinatorial, the obstructions are conformal, and the obstructions
were already classified -- here is the bridge.*

## M3. Boundaries and feature curves

Shen et al.'s conclusion flags padding feasibility in the bounded / feature-curve
setting as needing new theory, and the 2025 feature-aligned paper gives only
sufficient conditions.  The differential side of the dictionary extends: surfaces
with boundary correspond to `k`-differentials on the double, and feature curves to
prescribed horizontal/vertical trajectory conditions, i.e. to strata with a
prescribed real structure.  Concrete first question: what does the Reduction Lemma
become when `M` has boundary and `H_1(M \ C)` is free?  (Guess: the point-pushing
argument gets stronger, not weaker, so the collapse is even more complete and
existence should be nearly unconditional -- which would explain why the 2025
sufficient conditions work as well as they do in practice.)

## M4. Quantization feasibility

Which seamless parametrizations admit a valid integer-grid map?  Square-tiled
surfaces are exactly the ones that already *are* integer-grid maps, so the engine
in `quadmesh.py` is directly relevant: the question "is this signature realizable
by a square-tiled surface with at most `N` squares" is the quantized version of
the existence question, and the gap between the two is the quantization gap.  The
theory here is the thinnest part of the quad-meshing pipeline.

## M5. Reconcile with the fixed-conformal-structure Abel-Jacobi condition

Chen-Zheng-Ke-Lei-Luo-Gu give a necessary and sufficient condition at fixed
conformal structure and fixed cone positions, and cannot handle odd topological
valence.  The condition in `docs/genus1.md` is the same divisor condition with
both quantifiers loosened.  Writing down the precise logical relationship -- and
in particular explaining the odd-valence restriction in terms of `image(rho)`, since
odd valence is exactly `D = Z_4` -- is a clean, self-contained paper-sized
question.

## M6. Fixed mesh connectivity

Stated as unknown in the 2025 paper.  This is the genuinely combinatorial version
and is probably hard; `experiments/exhaustive.py` is the only rigorous tool here
and it stops at four squares.  Improving it is a real project: canonical-form
based orderly generation of quadrangulations by genus and valence multiset would
push it to `N = 7` or `8` and turn the "not found" rows of the survey into
theorems for small meshes.

## M7. Three dimensions

Frame-field meshability.  Largest payoff, largest risk, and the dictionary used
here has no direct analogue -- there is no `k`-differential story in 3D.  Listed
for completeness, not recommended as a next step.

## Immediate next actions

1. Verify the items in `docs/VERIFY.md` -- one afternoon with the PDFs.
2. M1: extract the Gendron-Tahar list.
3. Improve the search so that low-genus, many-cone targets stop failing (the cube,
   which obviously exists, is not found by the current annealer at `N = 6`; see
   `README.md`, Limitations).
