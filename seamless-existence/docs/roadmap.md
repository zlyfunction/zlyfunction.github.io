# Roadmap

Ordered so that each milestone is worth writing up on its own.

## M0. Done: the reduction, the Main Theorem, and the low-genus cases

* The dictionary and the topological equivalence (D2), proved: `docs/proofs.md`
  Lemmas 1-4.
* Reduction Lemma, proved (`docs/proofs.md` Theorem 8) and verified computationally
  for `g <= 3`; its symplectic ingredient verified for `g <= 5`.
* Main Theorem: realizable iff the reduced stratum is non-empty (`docs/proofs.md`
  Theorem 10).
* Genus 0 complete via Troyanov (Proposition 11); genus 1 complete via Abel-Jacobi
  (Proposition 12, Corollary 13), reproducing the unique known exception, with
  explicit machine-checked witnesses.
* Square-tiled certification engine and a 188-orbit survey (`results/survey.md`),
  plus `results/verification.md`.

Remaining work on M0: verify the literature statements in `docs/VERIFY.md` against
the sources, and give (S1)-(S6) proper citations.

## M1. Read the `k = 4` exceptional list out of Gendron-Tahar

This is the highest-value single task in the project.  `predict.quartic_nonempty`
returns `unknown` for every genus `>= 2` signature with `image(rho) = Z_4`; the
answer exists in arXiv:2208.11654 and needs to be translated into

    is the stratum of primitive 4-differentials with orders (m_1, ..., m_n),
    m_i > -4, sum m_i = 4(2g - 2), on a genus-g surface non-empty?

Once that table is in `predict.py`, the Main Theorem (`docs/proofs.md` Theorem 10)
becomes a *complete, checkable* answer to the open problem for every genus.  The survey already provides square-tiled certificates for 120 such strata,
which gives a large independent test of whatever list is extracted: any stratum the
paper calls empty but the search realizes means the translation is wrong.

Caveat: the paper is 71 pages in French.  Budget accordingly.

## M2. Write up "necessary and sufficient conditions for realizable holonomy signatures"

Contents, in the order they should appear:

1. Dictionary and the topological equivalence (`docs/proofs.md` Lemmas 1-4).
2. Reduction Lemma (Theorem 8), with the corollary that the gcd condition of
   Shen et al. 2022 is exactly the single-orbit regime.
3. Main Theorem (Theorem 10): realizable iff the reduced stratum is non-empty.
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
valence.  The condition in `docs/proofs.md` Proposition 12 is the same divisor
condition with both quantifiers loosened.  Writing down the precise logical relationship -- and
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

1. Verify the items in `docs/VERIFY.md` -- one afternoon with the PDFs.  Two of the
   original items have been discharged by writing the proofs; what is left is all
   literature checking.
2. M1: extract the Gendron-Tahar list.  This is now the *only* thing between
   Theorem 10 and a complete answer for every genus.
3. Give (S1)-(S6) of `docs/proofs.md` §7 proper citations.
4. Improve the search so that low-genus, many-cone targets stop failing (the cube,
   which obviously exists, is not found by the current annealer at `N = 6`; see
   `README.md`, Limitations).
