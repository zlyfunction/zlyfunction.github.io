# The dictionary

Everything in this repository rests on translating a graphics question into a
flat-geometry one.  This file fixes the translation; the proofs are Lemmas 1-4 of
`docs/proofs.md`.

## 1. Seamless parametrization = flat cone metric with `Z_4` holonomy

Let `M` be a closed oriented surface of genus `g` and `C = {c_1, ..., c_n}` a set
of marked points.  A *seamless parametrization* with cones at `C` is an atlas of
charts on `M \ C` into `R^2`, locally injective, whose transition maps lie in
`Z_4 |x R^2` (rotation by a multiple of `pi/2`, then a translation), such that
each `c_i` has a cone angle that is a multiple of `pi/2`.

Such an atlas *is* the developing atlas of a flat cone metric whose rotational
holonomy takes values in `Z_4`, and conversely.  So

> **(D1)** Seamless parametrizations of `M` with cones at `C` = flat cone metrics
> on `M` with cone angles in `(pi/2) Z` and rotational holonomy in `Z_4`.

This is the standard identification; nothing here is new.

## 2. What "existence" means

The graphics question is asked for an *input mesh*: given a triangulated surface
and a prescribed cone vertex set, does a seamless parametrization with a given
holonomy signature exist?  Shen et al. 2022 allow the mesh to be refined, which
makes the question purely topological:

> **(D2)** A signature is realizable on some refinement of a given mesh iff it is
> realizable by a flat cone metric on the underlying topological surface with the
> cones at *some* `n` distinct points.

This is **proved** as Lemma 2 of `docs/proofs.md`: pull the metric back by a
homeomorphism taking the prescribed cone vertices to the `p_i`, triangulate the
flat structure geodesically, and refine the input mesh by a common refinement.
The two standard PL inputs it uses (existence of a geodesic triangulation of a
flat cone surface, and existence of a common refinement of two triangulations of a
surface) are listed in `docs/proofs.md` §7 as (S1) and (S2).

The precise statement is slightly stronger than "realizable iff a metric exists":
realizability is invariant under `MCG(M, C)`, and a signature is realizable iff
some flat cone metric realizes a signature *in its orbit*.  That is the form
Theorem 10 uses.

An important consequence of (D2): the *conformal structure is free*.  That is the
difference between this question and the Abel-Jacobi condition of
Chen-Zheng-Ke-Lei-Luo-Gu, which fixes both the conformal structure and the cone
positions.  Here we ask whether *some* point of *some* Riemann surface works,
i.e. whether a stratum is non-empty.

## 3. Flat `Z_4`-cone metric = meromorphic 4-differential

A flat cone metric with holonomy in `Z_4` and cone angles in `(pi/2)Z` is the
same thing as a Riemann surface `X` with a meromorphic section `q` of `K_X^4`,
the metric being `|q|^{1/2}`.  Under this correspondence a zero or pole of order
`m` of `q` is a cone of angle

    theta = 2 pi (m + 4) / 4 = (m + 4) pi / 2,

so the graphics data and the differential-geometric data agree on the nose:

| seamless parametrization | 4-differential |
|---|---|
| cone angle `theta_i = (m_i + 4) pi/2` | zero/pole of order `m_i` |
| quad-mesh valence `v_i = m_i + 4` | order `m_i = v_i - 4` |
| finite cone angle `> 0` | `m_i > -4` |
| Gauss-Bonnet `sum (2pi - theta_i) = 2 pi chi` | `deg div(q) = 4 (2g - 2)` |
| rotational holonomy `rho: H_1(M \ C) -> Z_4` | monodromy of the local 4th roots of `q` |

The last row is the useful one.  Write `d` for the generator of `image(rho)` in
`{1, 2, 4}` (so `image(rho) = d Z_4`).  Then

* `d = 1`: `q` is a **primitive 4-differential**;
* `d = 2`: `image(rho) = {0, pi}`, the square root `sqrt(q)` exists globally, so
  `q = phi^2` for a **primitive quadratic differential** `phi` (a
  half-translation surface); in graphics terms the cross field splits globally
  into a pair of line fields;
* `d = 4`: `rho` is trivial, so `q = omega^4` for an **abelian differential**
  `omega` (a translation surface); all cone angles are multiples of `2 pi`.

In all three cases the reduced object is a primitive `k`-differential with
`k = 4 / d` and orders `mu_i = m_i / d`.  This is what `Signature.reduced_orders`
computes.

## 4. Why this is progress

Non-emptiness of strata of `k`-differentials with prescribed orders is a solved
or nearly solved problem:

* `k = 1`: classical -- every stratum of abelian differentials is non-empty for
  `g >= 2`; on a torus an abelian differential is nowhere zero.
* `k = 2`: Masur-Smillie 1993 -- exactly four empty strata, `Q(empty)` and
  `Q(1,-1)` in genus 1, `Q(1,3)` and `Q(4)` in genus 2.
* `k = 4`: Gendron-Tahar (arXiv:2208.11654) classify which strata of primitive
  `k`-differentials with prescribed zeros and poles are non-empty.

So the open graphics problem reduces to a bookkeeping exercise over an existing
classification.  That reduction is `docs/proofs.md` Theorem 10, and the only
missing entry in the table above is the explicit `k = 4` exceptional list
(milestone M1).

## 5. Square-tiled surfaces = quad meshes

A closed quad mesh built from unit squares is a flat `Z_4`-cone metric all of
whose cone points are mesh vertices, i.e. a square-tiled quarter-translation
surface, i.e. an integer-grid seamless parametrization.  So *every quad mesh is
an existence certificate for its own signature*.  The converse is the density
statement used to interpret failed searches:

> **(D3)** If a stratum is non-empty it contains a square-tiled surface, because
> rational points are dense in period coordinates and `image(rho)` is locally
> constant.

(D3) is standard for `k = 1, 2`; for `k = 4` with poles it is the natural
analogue and is treated here as a conjecture (`docs/VERIFY.md`, item 7).  It is
only ever used to justify *searching*, never to conclude non-existence.
