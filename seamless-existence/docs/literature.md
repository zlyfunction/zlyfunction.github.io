# Annotated reading list

Ordered by what to extract, not by date.  Items marked **[fetch]** could not be
opened from the sandbox this repository was built in (outbound HTTPS was blocked
for arxiv.org, springer.com and cims.nyu.edu), so the statements attributed to
them here are from memory and secondary sources and must be checked; see
`docs/VERIFY.md`.

## The problem statement

* **[fetch]** H. Shen, L. Zhu, R. Capouellez, D. Panozzo, M. Campen, D. Zorin,
  *Which Cross Fields can be Quadrangulated?  Global Parameterization from
  Prescribed Holonomy Signatures*, ACM TOG 41(4), Art. 59, 2022.
  doi:10.1145/3528223.3530187.
  **Extract:** the exact definition of holonomy signature; the exact statement of
  the sufficient condition (the gcd hypothesis) and of the exceptional case; the
  exact wording of the open problem in the conclusion; what is said about
  boundaries and feature curves.
* **[fetch]** R. Capouellez, D. Zorin, *Seamless Parametrization in Penner
  Coordinates*, ACM TOG 43(4), 2024. arXiv:2407.21342.
  **Extract:** the restatement of the open problem in the introduction.
* **[fetch]** R. Capouellez, S. Singh, M. Heistermann, D. Bommes, D. Zorin,
  *Feature-Aligned Parametrization in Penner Coordinates*, SIGGRAPH 2025.
  doi:10.1145/3731216.
  **Extract:** the precise scope of what is still unknown at fixed connectivity;
  the sufficient conditions given for feasibility with feature curves.
* M. Campen, H. Shen, J. Zhou, D. Zorin, *Seamless Parametrization with Arbitrary
  Cones for Arbitrary Genus*, ACM TOG 2019 -- the earlier existence result that
  ignores holonomy along homology loops.

## The one known obstruction, and the machine that produced it

* **[fetch]** I. Izmestiev, R. B. Kusner, G. Rote, B. Springborn, J. M. Sullivan,
  *There is no triangulation of the torus with vertex degrees 5, 6, ..., 6, 7 and
  related results: geometric proofs for combinatorial theorems*, Geom. Dedicata
  166 (2013) 15-29. arXiv:1207.3605.
  **Extract:** the theorem on the holonomy group of a euclidean cone metric on
  the torus with two cone points, and the second proof via the induced conformal
  structure and the residue theorem.  The Abel-Jacobi argument of
  `docs/genus1.md` should be compared with that second proof; they are very
  likely the same argument, and the write-up must say so.

## Non-emptiness of strata: the machinery to borrow

* H. Masur, J. Smillie, *Quadratic differentials with prescribed singularities
  and pseudo-Anosov diffeomorphisms*, Comment. Math. Helv. 68 (1993) 289-307.
  **Used here:** exactly four strata of primitive quadratic differentials with at
  worst simple poles are empty -- `Q(empty)` and `Q(1,-1)` in genus 1, `Q(1,3)`
  and `Q(4)` in genus 2.  This is the source of the two apparently-new genus-2
  obstructions in `README.md`.
* **[fetch]** Q. Gendron, G. Tahar, *k-differentials with prescribed
  singularities*, arXiv:2208.11654 (in French, 71 pp.).
  **Extract:** the list of exceptional (empty) strata of primitive
  `k`-differentials for `k >= 3`, including the meromorphic case with poles of
  order `< k`.  For `k = 4` and poles of order `1, 2, 3` this is precisely the
  missing input for `predict.quartic_nonempty`, i.e. for genus `>= 2` with a
  genuine 4-differential.  **This is milestone M1 and the single highest-value
  item on this list.**
* Q. Gendron, G. Tahar, *Abelian differentials with prescribed singularities*,
  arXiv:2103.03165, and *Quadratic differentials with prescribed singularities*,
  arXiv:2111.12653 -- the `k = 1, 2` cases in the same framework, useful for
  calibrating how the `k = 4` statements are phrased.
* E. Lanneau, *Connected components of the strata of the moduli spaces of
  quadratic differentials*, Ann. Sci. ENS 41 (2008); M. Kontsevich, A. Zorich,
  *Connected components of the moduli spaces of Abelian differentials with
  prescribed singularities*, Invent. Math. 153 (2003).
  **Why:** the invariants that distinguish connected components (spin parity,
  hyperelliptic) are the natural candidates for refined invariants of holonomy
  signatures should the Reduction Lemma turn out to be too coarse for a finer
  question than existence -- e.g. connectivity of the space of parametrizations
  with a fixed signature.
* D. Chen, Q. Gendron, and the more recent literature on connected components of
  strata of `k`-differentials.

## Period conditions: the degenerate end

* T. Le Fils, *Periods of abelian differentials with prescribed singularities*,
  and independently Bainbridge, Johnson, Judge, Park.
  **Used here only for orientation:** these give necessary and sufficient
  conditions for a representation `H_1 -> C` to be the period/holonomy character
  of a translation surface with prescribed cone angles.  Note that the known
  torus obstruction is *not* of this type -- it lives at `image(rho) = Z_4`, the
  least degenerate case -- so period conditions are not the whole story
  (`docs/reduction.md`, last section).

## Fixed conformal structure, fixed positions

* Chen, Zheng, Ke, Lei, Luo, Gu -- necessary and sufficient (Abel-Jacobi)
  condition for a singularity configuration to satisfy the holonomy requirement,
  at *fixed* conformal structure and *fixed* cone positions; does not handle
  singularities of odd topological valence.
  **Why it matters here:** it is the same divisor condition that appears in
  `docs/genus1.md`, quantified differently.  Making the relationship between the
  two settings precise is milestone M5.

## Prescribing flat metrics

* M. Troyanov, *Les surfaces euclidiennes à singularités coniques* (1986) and
  *Prescribing curvature on compact surfaces with conical singularities*,
  Trans. AMS 324 (1991).
  **Used here:** existence of a flat cone metric with prescribed angles at
  prescribed points on any closed surface, which settles genus 0 outright
  (`docs/genus1.md`, Proposition 0).

## Downstream (not needed for this problem, listed for the roadmap)

* H.-C. Lyon, M. Campen, L. Kobbelt and the quantized global parametrization
  line -- which seamless parametrizations admit a valid integer-grid map.
* H. Liu, D. Bommes and the frame-field meshability line -- the 3D analogue.
