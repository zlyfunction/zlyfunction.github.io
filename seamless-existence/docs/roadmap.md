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

## M3. Boundaries and feature curves -- mostly done

Done (`docs/proofs.md` §8, `results/boundary.md`):

* Gauss-Bonnet with boundary and the parity constraint it forces (Lemma 14).
* The space of signatures with fixed orders and turnings is again `Z_4^{2g}`
  (Lemma 15), and the Reduction Lemma holds verbatim with `D` enlarged by the
  boundary turnings (Theorem 16).  Sliding a boundary component along a loop is the
  boundary analogue of point pushing.
* Corollary 17: an odd turning -- one `pi/2` corner suffices -- collapses the
  holonomy entirely.  The guess recorded here originally was right, and this is the
  precise form of it.
* The doubling map (Lemma 18), verified on every boundary mesh of at most three
  squares, and the necessary condition it yields (Corollary 19), which turns out to
  fire on nothing in range.

Left open: the boundary analogue of Theorem 10.  Doubling reduces it to
non-emptiness of *real* strata -- `k`-differentials invariant under a prescribed
anti-holomorphic involution, with the boundary as the fixed locus.  That is a
well-posed question in flat geometry and is now the whole content of the
feature-curve case.  Everything computational points at the answer being
"non-empty always", which would make feature-aligned existence unconditional given
Gauss-Bonnet and the parity constraint.

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

## M6. Fixed mesh connectivity -- partly tooled up

Stated as unknown in the 2025 paper.  This is the genuinely combinatorial version
and is probably hard.  The tooling improved, though:

* `experiments/exhaustive.py` enumerates *every* gluing and stops at four squares.
* `search.exhaustive_target_search` decides *one* signature at a time and reaches
  five squares, because the target prunes hard: a closed vertex cycle whose length
  is not an allowed valence kills the branch.  This is what makes the negative
  evidence for the four unrealizable signatures rigorous rather than anecdotal, and
  it also finds certificates the annealer never does.

Next steps here: extend the pruning to meshes with boundary (currently only the
closed case), add a genus bound to prune mid-way, and -- for the complete
enumeration -- canonical-form-based orderly generation to reach seven or eight
squares.

## M7. Three dimensions

Frame-field meshability.  Largest payoff, largest risk, and the dictionary used
here has no direct analogue -- there is no `k`-differential story in 3D.  Listed
for completeness, not recommended as a next step.

## State of play

Proved and machine-checked, closed case: the dictionary, the Reduction Lemma, the
Main Theorem, genus 0 and genus 1 complete, and the relation to the
fixed-conformal-structure criterion (`docs/proofs.md` §1-§7, §9).

Proved, boundary case: Gauss-Bonnet with corners, the Reduction Lemma with the
turnings, the collapse from an odd turning, and the doubling map (§8).

Blocked in this environment: M1, because `arxiv.org` is refused by the egress proxy
(`403` to `CONNECT`), so Gendron-Tahar cannot be read here.

## Immediate next actions

1. M1: extract the Gendron-Tahar list for `k = 4`.  This is the *only* thing between
   Theorem 10 and a complete answer for every genus, and it needs nothing but the
   paper.  The 120 square-tiled certificates in `results/survey.json` are a ready
   test of whatever list comes out.
2. Verify the remaining items of `docs/VERIFY.md` -- all literature checks now --
   and give (S1)-(S6) of `docs/proofs.md` §7 proper citations.
3. M3's open end: non-emptiness of real strata (4-differentials invariant under an
   anti-holomorphic involution).  A literature search on real / Klein-surface strata
   is the first step; everything computational here says the answer is "always
   non-empty", which would make feature-aligned existence unconditional.
4. M2: the write-up.
5. Extend the pruned per-signature search to meshes with boundary, which is the one
   place where the unreliable annealer is still load-bearing.
