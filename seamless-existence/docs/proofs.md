# Proofs

This is the authoritative document.  `docs/dictionary.md`, `docs/reduction.md` and
`docs/genus1.md` are expositions of what is proved here; where they disagree with
this file, this file wins.

What is proved: the dictionary (Lemmas 1-4), the Reduction Lemma (Theorem 8), the
Main Theorem reducing realizability to non-emptiness of a stratum (Theorem 10),
and complete answers in genus 0 (Proposition 11) and genus 1 (Proposition 12,
Corollary 13).  Section 7 lists exactly which external facts are used and what
remains open.

Machine-checked instances of Lemma 6, Theorem 8, Proposition 12 and Theorem 10
are in `results/verification.md`.

## Conventions

`M` is a closed oriented surface of genus `g`; `C = {c_1, ..., c_n} subset M` is a
set of distinct marked points.  A *holonomy signature* on `(M, C)` is a pair
`s = (m, rho)` where

* `m = (m_1, ..., m_n)` are integers `m_i > -4`, the *orders*, encoding the cone
  angles `theta_i = (m_i + 4) pi / 2`, subject to Gauss-Bonnet
  `sum_i m_i = 4 (2g - 2)`;
* `rho: H_1(M \ C; Z) -> Z_4` is a homomorphism with `rho(gamma_i) = m_i mod 4`,
  where `gamma_i` is the positively oriented loop around `c_i`.

`Z_4 = Z/4Z` is written additively and identified with the group `mu_4` of
quarter turns; `1 in Z_4` is the rotation by `pi/2`.  Subgroups of `Z_4` are
written `d Z_4` with `d in {1, 2, 4}` (`4 Z_4 = 0`).

`H_1(M \ C; Z) = Z^{2g} + (sum_i Z gamma_i) / (sum_i gamma_i)`, so `rho` exists
(Gauss-Bonnet gives `sum_i m_i = 0` in `Z_4`, which is the only relation among the
`gamma_i`) and the set

    A(m) = { rho : rho(gamma_i) = m_i for all i }

is a coset of `H^1(M; Z_4) = Z_4^{2g}` inside `H^1(M \ C; Z_4)`.  (The map
`H^1(M; Z_4) -> H^1(M \ C; Z_4)` is injective.)

A *seamless parametrization* of `(M, C)` is a locally injective atlas on `M \ C`
with values in `R^2` whose transition maps lie in `Z_4 |x R^2`, i.e. are of the
form `z |-> i^k z + t`, and whose cone angles at the `c_i` are multiples of
`pi/2`.  It is *realized on a mesh* if it is piecewise linear with respect to some
refinement of a given triangulation of `M` whose vertex set contains `C`.  A
signature is *realizable* if some seamless parametrization has it.

---

## 1. The dictionary

### Lemma 1 (seamless parametrization = flat `Z_4` cone metric)

*Seamless parametrizations of `(M, C)` are the same thing as flat cone metrics on
`M` with cone points contained in `C`, cone angles in `(pi/2) Z`, and rotational
holonomy contained in `Z_4`; the signature corresponds on both sides.*

**Proof.**  Given a seamless atlas, pull back the euclidean metric.  This is
well defined because the transitions `z |-> i^k z + t` are isometries, and gives a
flat metric on `M \ C` with a cone point of the prescribed angle at each `c_i`.
Parallel transport along a loop `gamma` is the rotation part of the composite
transition along `gamma`, that is `i^{k(gamma)}`; since the rotation part of a
composition is the product of the rotation parts and `mu_4` is abelian,
`gamma |-> k(gamma)` is a homomorphism `H_1(M \ C; Z) -> Z_4`, and it is the
rotational holonomy.

Conversely, let `mu` be such a metric.  Developing maps on simply connected
subsets of `M \ C` give an atlas whose transitions are orientation-preserving
euclidean isometries; the rotation part of the transition around any loop is the
rotational holonomy of that loop, which lies in `Z_4` by hypothesis, so on a good
cover all transitions can be chosen of the form `z |-> i^k z + t`.  Local
injectivity holds because developing maps are local isometries.  The cone angle at
`c_i` is a multiple of `pi/2` by hypothesis.  Note that the holonomy around
`gamma_i` is the rotation by `theta_i`, so `rho(gamma_i) = m_i mod 4` is forced,
consistently with the definition of a signature. `[]`

### Lemma 2 (realizability is topological)

*(a) The set of realizable signatures is invariant under the mapping class group
`MCG(M, C)` of homeomorphisms preserving `C` setwise.*

*(b) A signature `s = (m, rho)` is realizable iff there exists a flat cone metric
on `M` with cone angles `(m_i + 4) pi/2` at `n` distinct points whose signature
lies in the `MCG(M, C)`-orbit of `s`.*

**Proof.**  (a) If `phi in MCG(M, C)` and an atlas `{U_a, f_a}` realizes `s`, then
`{phi^{-1}(U_a), f_a . phi}` is again a seamless atlas, its transitions are
unchanged, and its signature is `phi^* s = (m . sigma, rho . phi_*)` for the
induced permutation `sigma` of `C`.  Any mapping class may be represented by a PL
homeomorphism, so the pushed-forward atlas is again PL on a refinement of a
triangulation.

(b) Necessity is Lemma 1.  For sufficiency, let `mu` be a flat cone metric with
cone points `p_1, ..., p_n` of angles `theta_{sigma(i)}` and signature `s'` in the
orbit of `s`.  Pick a homeomorphism `psi` of `M` with `psi(c_i) = p_{sigma(i)}`;
then `psi^* mu` is a flat cone metric whose cone set is exactly `C`, and whose
signature is again in the orbit of `s`.  By part (a) it suffices to realize any
signature in that orbit, so assume the signature is `s` itself.  Lemma 1 produces a
seamless atlas.

It remains to see that the atlas is PL with respect to a refinement of the given
triangulation `T`.  A flat cone metric admits a geodesic triangulation `T''` whose
vertex set contains the cone points (for instance a Delaunay triangulation of the
flat cone surface, §7 (S1)); the developing charts are affine on each triangle of
`T''`, so the atlas is PL with respect to `T''`.  Two triangulations of a surface
admit a common refinement (§7 (S2)); refining `T` by a common refinement of `T`
and `T''` keeps the atlas PL and does not move `C`. `[]`

Two consequences worth stating explicitly, because they are what make the rest of
the paper possible: the *conformal structure is free* (nothing above fixes it),
and the *cone positions are free* (only the combinatorics of `C` matters).  This is
the precise sense in which the question here differs from the fixed-conformal-
structure Abel-Jacobi criterion of Chen-Zheng-Ke-Lei-Luo-Gu.

### Lemma 3 (flat `Z_4` cone metric = meromorphic 4-differential)

*Flat cone metrics on `M` with cone angles in `(pi/2)Z` and rotational holonomy in
`Z_4` are the same thing as pairs `(X, q)` where `X` is a Riemann surface
homeomorphic to `M` and `q` is a meromorphic section of `K_X^4` with
`div(q) = sum_i m_i c_i`, `m_i > -4`.  The metric is `|q|^{1/2}`, the cone angle at
`c_i` is `(m_i + 4) pi/2`, and the rotational holonomy is the monodromy of the
local 4th roots of `q`.*

**Proof.**  Let `mu` be such a metric with developing charts `z_a` and transitions
`z_b = i^k z_a + t`.  Then `(dz_b)^4 = i^{4k} (dz_a)^4 = (dz_a)^4`, so the local
4-differentials `(dz_a)^4` agree on overlaps and define a nowhere-zero holomorphic
section `q` of `K^4` on `M \ C`, with `|q|^{1/2} = mu`.  Near a cone point of angle
`(m + 4) pi/2`, the metric is isometric to the standard cone, which in a
holomorphic coordinate `w` centred at the cone is developed by
`z = (4/(m+4)) w^{(m+4)/4}`; hence

    q = (dz)^4 = w^m (dw)^4 ,

so `q` extends meromorphically across `c_i` with order exactly `m_i`.  The
condition `m_i > -4` is exactly positivity of the cone angle (equivalently finite
area).  Since `deg K_X^4 = 4(2g - 2)`, the degree of `div(q)` reproduces
Gauss-Bonnet.

Conversely, given `(X, q)`, the metric `|q|^{1/2}` is flat away from `div(q)`,
with a cone point of angle `2 pi (m_i + 4)/4` at each `c_i`; a local primitive
`z = int q^{1/4}` is a developing chart, and two choices differ by
`z |-> i^k z + t`, so the rotational holonomy is the monodromy of `q^{1/4}` and
lies in `mu_4 = Z_4`. `[]`

### Lemma 4 (primitivity is measured by `image(rho)`)

*Let `q` be as in Lemma 3 with rotational holonomy `rho`, and let `e | 4`.  Then
`q = eta^e` for a meromorphic section `eta` of `K^{4/e}` iff
`image(rho) subset e Z_4`.  Consequently, if `d` generates `image(rho)` then
`q = eta^d` for a **primitive** `(4/d)`-differential `eta` with
`div(eta) = sum_i (m_i/d) c_i`, and conversely `eta^d` has rotational holonomy with
image exactly `d Z_4`.*

Here a `k`-differential is *primitive* if it is not an `e`-th power for any
`e > 1` dividing `k`; every 1-differential (abelian differential) is primitive.

**Proof.**  Work locally: `q = f (dz)^4`.  A 4th root of `q` is `f^{1/4} dz`, and
by Lemma 3 the rotational holonomy `rho` is precisely the monodromy character of
the multivalued function `f^{1/4}`, valued in `mu_4`.  An `e`-th root of `q` is
`h (dz)^{4/e}` with `h^e = f`, i.e. `h = f^{1/e} = (f^{1/4})^{4/e}`.  The latter is
single valued iff `rho(gamma)^{4/e} = 1` in `mu_4` for every `gamma`, which in
additive notation reads `(4/e) rho(gamma) = 0` in `Z_4`, i.e.
`rho(gamma) in e Z_4`.  This proves the first claim, and it also forces `e | m_i`,
since `rho(gamma_i) = m_i mod 4` and `e | 4`.

Now let `d` generate `image(rho)`.  By the above there is `eta` with `eta^d = q`
and `div(eta) = div(q)/d`.  Its own holonomy `rho_eta: H_1 -> Z_{4/d}` satisfies
`rho = d . rho_eta` under `Z_{4/d} = d Z_4`, so `image(rho_eta)` is all of
`Z_{4/d}` (else `image(rho)` would be smaller), and by the first claim applied to
`eta` this says precisely that `eta` has no `e`-th root for `e > 1` dividing
`4/d`: `eta` is primitive.  The converse is the same computation read backwards. `[]`

---

## 2. The Reduction Lemma

Throughout this section `g >= 1` and the orders `m` are fixed.  Recall
`A(m)` is a coset of `Z_4^{2g}`.  Write

    D = < m_1 mod 4, ..., m_n mod 4 >  <=  Z_4,     d_D = generator of D,

so `D` is the part of `image(rho)` forced by the cone angles, and
`image(rho) supset D` for every `rho in A(m)`.

### Lemma 5 (point pushing)

*Let `p in C` and `alpha in H_1(M; Z)`, and let `P(alpha) in MCG(M, C)` be the
point-pushing map of `p` along a loop representing `alpha`.  Then*

    P(alpha)_* x = x + <x, alpha> gamma_p   for x in H_1(M \ C; Z),

*hence `P(alpha)^* rho = rho + m_p <., alpha>`.  As `p` and `alpha` vary these
moves generate exactly the translations of `A(m)` by `D . H^1(M; Z_4)`, and they
fix all puncture values.*

**Proof.**  It is enough to treat `alpha` represented by a *simple* closed curve
through `p`, and in fact enough to treat the `2g` curves of a symplectic basis: the
translations obtained will already span what is claimed.  For such an `alpha`,
`P(alpha)` is the composition `T_{alpha_L} T_{alpha_R}^{-1}` of Dehn twists along
the two boundary curves of an annulus neighbourhood of the curve, with `p` in the
annulus between them.  On `H_1(M \ C)` these are transvections, so

    P(alpha)_* x = x + <x, alpha_L> alpha_L - <x, alpha_R> alpha_R .

(The two twists commute and `<alpha_L, alpha_R> = 0`, since the curves are
disjoint.)  Both boundary curves are disjoint from `C` and homologous to `alpha` in
`M`, so their intersection numbers with `x` agree and equal `<x, alpha>`; and their
difference in `H_1(M \ C)` is `gamma_p`, because the annulus between them contains
exactly the puncture `p`.  Hence `P(alpha)_* x = x + <x, alpha> gamma_p`, and

    (P(alpha)^* rho)(x) = rho(x) + <x, alpha> rho(gamma_p) = rho(x) + m_p <x, alpha> .

Puncture values are unchanged because `<gamma_i, alpha> = 0` (each `gamma_i` bounds
a disk in `M`).  Finally, `alpha |-> <., alpha>` is Poincaré duality, an
isomorphism `H_1(M; Z_4) -> H^1(M; Z_4)`, and `H_1(M; Z) -> H_1(M; Z_4)` is onto;
so already for `alpha` in a symplectic basis the functionals `m_p <., alpha>` span
`m_p H^1(M; Z_4)`.  Summing over `p` gives `D . H^1(M; Z_4)`, and no more, since
every such move is of this form. `[]`

### Lemma 6 (symplectic transitivity)

*Let `g >= 1`, `N >= 1`.  For `v in (Z/N)^{2g}` put
`content(v) = gcd(N, v_1, ..., v_{2g})`.  Then `Sp(2g, Z/N)` preserves `content`
and acts transitively on each level set.*

**Proof.**  Invariance is clear: `S` is invertible over `Z/N`, so the entries of
`Sv` and of `v` generate the same subgroup of `Z/N`.

For transitivity, let `content(v) = c` and write `N = c N'`, `v = c a` with
`a in (Z/N')^{2g}` and `gcd(N', a_1, ..., a_{2g}) = 1`.

*Step 1: lift `a` to a primitive integer vector.*  Choose any integer lift
`tilde a`.  For a prime `p` dividing all `tilde a_i`: `p` cannot divide `N'`,
because then `p` would divide `N'` and all `a_i`, contradicting
`gcd(N', a) = 1`.  So `N'` is invertible mod `p`, and replacing `tilde a_1` by
`tilde a_1 + N' k` for suitable `k` makes it not divisible by `p`.  There are
finitely many such primes (they all divide `tilde a_1`, or `tilde a_1 = 0` in
which case start by making it nonzero), so a single congruence condition on `k`
per prime and the Chinese Remainder Theorem give a lift with
`gcd(tilde a_1, ..., tilde a_{2g}) = 1`.

*Step 2: move a primitive vector to `e_1`.*  `Sp(2g, Z)` acts transitively on
primitive vectors of `Z^{2g}` (§7 (S3)).  So there is `tilde S in Sp(2g, Z)` with
`tilde S tilde a = e_1`, whence `tilde S (c tilde a) = c e_1`.

*Step 3: reduce.*  `Sp(2g, Z) -> Sp(2g, Z/N)` is surjective (§7 (S4)), so the
image `S` of `tilde S` lies in `Sp(2g, Z/N)` and `S v = c e_1` in `(Z/N)^{2g}`.
Since every `v` of content `c` maps to the same `c e_1`, the level set is one
orbit. `[]`

`verify_sp_transitivity` in `mcg.py` checks the conclusion for `N = 4` by closing
up `c e_1` under actual transvections `T_c^lambda(x) = x + lambda <x, c> c`, each of
which is the action of a power of a Dehn twist.  It succeeds for `g = 1, 2, 3` with
the complete set of transvections and for `g = 4` with a random subset of them
(`results/verification.md`); since a subgroup suffices to prove transitivity, these
are rigorous checks of Lemma 6 in those cases.

### Lemma 7 (a base point with a full symplectic stabilizer)

*There exist `rho_0 in A(m)` and a subgroup `H <= MCG(M, C)` fixing `C` pointwise
such that `H` fixes `rho_0` and the image of `H` in `Aut(H^1(M; Z_4))` is all of
`Sp(2g, Z_4)`.*

**Proof.**  Choose an embedded closed disk `D_0 subset M` containing `C` in its
interior, and let `Sigma = M \ int(D_0)`, a genus-`g` surface with one boundary
circle.  Choose a symplectic basis `a_1, b_1, ..., a_g, b_g` of `H_1(M; Z)`
represented by simple closed curves in the interior of `Sigma`.

Define `rho_0 in H^1(M \ C; Z_4)` by `rho_0(gamma_i) = m_i` and
`rho_0(a_j) = rho_0(b_j) = 0`.  This is well defined: the only relation among the
generators `a_j, b_j, gamma_i` of `H_1(M \ C; Z)` is `sum_i gamma_i = 0`, and
`sum_i m_i = 0` in `Z_4`.  So `rho_0 in A(m)`.

Note that `rho_0` vanishes on the image of `H_1(Sigma; Z) -> H_1(M \ C; Z)`: that
image is generated by the `a_j, b_j` and by `[partial Sigma] = sum_i gamma_i`, and
`rho_0` kills all of them.

Let `H` be the image of `MCG(Sigma, partial Sigma) -> MCG(M, C)`, extending each
mapping class by the identity on `D_0`.  Every `phi in H` is the identity on a
neighbourhood of `C`, so `phi_* gamma_i = gamma_i`.  And for any 1-cycle `x`, the
class `phi_* x - x` lies in the image of `H_1(Sigma)`: `phi` is the identity
outside `Sigma` and on a neighbourhood of `partial Sigma`, so `x` and `phi_* x`
agree outside `Sigma` and their arcs inside `Sigma` have the same endpoints on
`partial Sigma`, whence their difference is a cycle contained in `Sigma`.  Hence

    (phi^* rho_0)(x) = rho_0(x) + rho_0(phi_* x - x) = rho_0(x) ,

so `H` fixes `rho_0`.  Finally `MCG(Sigma, partial Sigma) -> Sp(2g, Z)` is
surjective (§7 (S5)), and `Sp(2g, Z) -> Sp(2g, Z_4)` is surjective, so `H` realizes
all of `Sp(2g, Z_4)` on `H^1(M; Z_4)`. `[]`

With `rho_0` fixed, identify `A(m)` with `Z_4^{2g}` by `rho = rho_0 + v`.  Lemma 7
says the action of `H` in this coordinate is the *linear* action `v |-> S v`, and
Lemma 5 says point pushing acts by translations `v |-> v + w`, `w in D^{2g}`.
Under this identification

    image(rho_0 + v) = < D, v_1, ..., v_{2g} > = gcd(d_D, v_1, ..., v_{2g}) Z_4 .   (*)

### Theorem 8 (Reduction Lemma)

*Let `g >= 1` and fix the orders `m`.  Two signatures with orders `m` lie in the
same `MCG(M, C)`-orbit if and only if they have the same `image(rho)`.  Hence the
orbits with orders `m` are in bijection with the subgroups of `Z_4` containing
`D`: there are `1`, `2` or `3` of them according as `D = Z_4`, `D = 2 Z_4`,
`D = 0`.*

**Proof.**  If `rho' = rho . phi_*` for an automorphism `phi_*` of
`H_1(M \ C; Z)`, then `image(rho') = rho(phi_* H_1) = rho(H_1) = image(rho)`, so
the invariant is constant on orbits.

Conversely let `v, w in Z_4^{2g}` with `gcd(d_D, v) = gcd(d_D, w)` by `(*)`.
Reduce modulo `D`: since `d_D | 4`, `Z_4 / D = Z / d_D`, and the point-pushing
translations by `D^{2g}` act transitively on each fibre of
`Z_4^{2g} -> (Z / d_D)^{2g}`.  The reductions `bar v, bar w` have equal content in
`(Z/d_D)^{2g}`, namely `gcd(d_D, v) = gcd(d_D, w)`.  By Lemma 6 with `N = d_D`
there is `bar S in Sp(2g, Z/d_D)` with `bar S bar v = bar w`, and
`Sp(2g, Z_4) -> Sp(2g, Z/d_D)` is surjective, so some `S in Sp(2g, Z_4)` lifts it.
By Lemma 7, `S` is realized by some `phi in H`, and `phi^*` sends `v` into the
fibre of `bar w`; a point-pushing translation then finishes the job.  Both moves
lie in `MCG(M, C)`. `[]`

`verify_reduction_lemma` in `mcg.py` recomputes the orbits by brute force with
exactly these two families of moves, and confirms the statement for
`g = 1, 2, 3` and every `D`.

### Corollary 9 (why the gcd condition has the shape it has)

*If some cone angle is an odd multiple of `pi/2` -- in particular if some cone has
angle `3 pi/2` or `5 pi/2` -- then `D = Z_4`, all signatures with those cone
angles form a single `MCG`-orbit, and realizability does not depend on `rho` at
all.*

**Proof.**  `m_i` odd gives `D = Z_4` and `d_D = 1`, so `(Z/d_D)^{2g}` is trivial
and Theorem 8 leaves one orbit. `[]`

Mechanically: pushing a cone of odd order once around a handle shifts the
holonomy along the dual loop by an odd amount, so repeated pushes reach every
value.  The gcd hypothesis of Shen et al. 2022 is a hypothesis of exactly this
kind, which explains why their construction can ignore the rotations along
homology loops; see `docs/VERIFY.md` item 4 for the status of matching it to their
statement verbatim.

---

## 3. The Main Theorem

### Theorem 10

*Let `s = (m, rho)` be a holonomy signature on `(M, C)`, `g = genus(M)`, and let
`d` generate `image(rho)`.  Then `s` is realizable if and only if the stratum of
primitive `(4/d)`-differentials with orders `(m_1/d, ..., m_n/d)` on a genus-`g`
surface is non-empty.*

**Proof.**  If `s` is realizable, Lemmas 1 and 3 give `(X, q)` with
`div(q) = sum m_i c_i` and rotational holonomy `rho`, and Lemma 4 extracts a
primitive `(4/d)`-differential `eta` with orders `m_i/d`.

Conversely, let `eta` be a primitive `(4/d)`-differential with orders `m_i/d` on
some genus-`g` Riemann surface `X`, at points `p_1, ..., p_n`.  Put `q = eta^d`.  By
Lemma 4 the rotational holonomy of `q` has image exactly `d Z_4`, and
`div(q) = sum_i m_i p_i`, so by Lemma 3 the metric `|q|^{1/2}` is a flat cone metric
on `X` with cone angles `(m_i + 4) pi/2` at the `p_i`.

Transport it to `M`: choose an orientation-preserving homeomorphism `X -> M`
carrying `p_i` to `c_{sigma(i)}` for a permutation `sigma` matching equal orders.
The result is a flat cone metric on `M` with cone set `C`, whose signature
`s' = (m . sigma, rho')` has the same multiset of orders as `s` and, since the
transport is by a homeomorphism, `image(rho') = d Z_4 = image(rho)`.

For `g >= 1`, Theorem 8 now puts `s'` in the `MCG(M, C)`-orbit of `s`.  For
`g = 0`, `H^1(M; Z_4) = 0`, so `A(m)` is a single point and `s'` equals `s` after
relabelling `C`, which is again a mapping class.  Either way Lemma 2 (b) says `s`
is realizable. `[]`

So the open problem is *equivalent* to a stratum non-emptiness question, for which
the literature supplies: `d = 4` (abelian differentials) classical, `d = 2`
(primitive quadratic differentials) Masur-Smillie, `d = 1` (primitive
4-differentials) Gendron-Tahar.  Section 7 records that these three inputs are
external to this document.

---

## 4. Genus 0

### Proposition 11

*Every Gauss-Bonnet-admissible holonomy signature on the sphere is realizable.*

**Proof.**  First, `n >= 3`: Gauss-Bonnet gives `sum m_i = -8` while `m_i > -4`
forces `sum m_i > -4n`, so `n > 2`.

Second, `rho` is determined by `m`: `H_1(S^2 \ C; Z)` is generated by the
`gamma_i`, on which `rho(gamma_i) = m_i mod 4` is prescribed.  In particular any
flat cone metric on `S^2` with cone angles in `(pi/2)Z` automatically has
rotational holonomy in `Z_4`, and its signature is the given one.

Third, such a metric exists: by Troyanov's theorem (§7 (S6)), for any `n >= 3`
distinct points on `S^2` and any angles `theta_i > 0` with
`sum_i (2 pi - theta_i) = 4 pi` there is a flat cone metric with cone angle
`theta_i` at the `i`-th point.  Lemma 2 (b) concludes. `[]`

Note this settles genus 0 without any stratum classification.  Via Theorem 10 it
also says, as a by-product, that every genus-0 stratum arising this way is
non-empty.

---

## 5. Genus 1

### Proposition 12 (Abel-Jacobi criterion on a torus)

*Let `k in {1, 2, 4}` and let `mu = (mu_1, ..., mu_n)` be integers `mu_i > -k` with
`sum_i mu_i = 0`.  Let `n_0` be the number of nonzero `mu_i`.  The stratum of
primitive `k`-differentials with orders `mu` on a genus-1 surface is non-empty if
and only if*

* *`n_0 = 0` and `k = 1`; or*
* *`n_0 = 2`, in which case the two nonzero orders are `(mu, -mu)` and the
  condition is `|mu| >= 2`; or*
* *`n_0 >= 3`, with no further condition.*

*(`n_0 = 1` cannot occur, since the orders sum to zero.)*

**Proof.**  On `E = C / Lambda` the canonical bundle is trivialized by `dz`, so
every meromorphic `k`-differential is `q = f (dz)^k` with `f` meromorphic and
`div(q) = div(f)`.  By Abel-Jacobi a degree-zero divisor `sum mu_i c_i` on `E` is
principal iff

    sum_i mu_i c_i = 0    in the group law of E .                       (AJ)

By Lemma 4 (or directly: an `e`-th root is `h (dz)^{k/e}` with `h^e = f`, i.e.
`div(h) = div(f)/e`), `q` is primitive iff for every `e > 1` dividing `k` with
`e | mu_i` for all `i`,

    sum_i (mu_i / e) c_i != 0 .                                          (P_e)

**Necessity.**  If `n_0 = 0` then `f` has no zeros or poles, so `f` is constant and
`q = c (dz)^k = (c^{1/k} dz)^k` is a `k`-th power; for `k > 1` this contradicts
primitivity, and for `k = 1` it is the flat torus with marked points, which exists.

If `n_0 = 2` the nonzero orders are `(mu, -mu)` at distinct points `c_1 != c_2`,
and (AJ) reads `mu (c_1 - c_2) = 0` with `c_1 - c_2 != 0`, i.e. `E` has a nonzero
`mu`-torsion point.  For `|mu| = 1` there is none.

**Sufficiency.**  Let `e*` be the largest divisor of `k` dividing every `mu_i`, set
`nu = mu / e*`, and let `T in E` be a point of exact order `e*` (so `T = 0` when
`e* = 1`).  Since the divisors of `k in {1, 2, 4}` form a chain under divisibility,
every `e > 1` occurring in (P_e) divides `e*`.

*Claim: distinct points with `sum_i nu_i c_i = T` suffice.*  Indeed then
`sum_i mu_i c_i = e* T = 0`, so (AJ) holds and `q` exists; and for each relevant
`e`,

    sum_i (mu_i/e) c_i = (e*/e) sum_i nu_i c_i = (e*/e) T ,

which has exact order `e* / gcd(e*, e*/e) = e > 1`, hence is nonzero, so (P_e)
holds and `q` is primitive.

*Case `n_0 = 2`, `|mu| >= 2`.*  Here `nu = (nu, -nu)` with `nu != 0`, and we need
`nu (c_1 - c_2) = T`.  If `e* > 1`, multiplication by `nu` is surjective on `E`, so
pick `u` with `nu u = T`; then `u != 0` because `T != 0`.  If `e* = 1` then `T = 0`
and `|nu| = |mu| >= 2`, so take `u` a nonzero `|nu|`-torsion point, which exists
since `E[|nu|] = (Z/|nu|)^2`.  Set `c_1 = u`, `c_2 = 0`.

*Case `n_0 >= 3`.*  Let `Psi: E^{n_0} -> E`, `Psi(c) = sum_i nu_i c_i`, the sum
being over the nonzero indices.  Some `nu_i != 0`, and multiplication by `nu_i` is
surjective, so `Psi` is surjective; let `K = ker Psi` and let `K^0` be its identity
component, an abelian subvariety of dimension `n_0 - 1 >= 2`.  The fibre
`Psi^{-1}(T)` contains a coset `x_0 + K^0`, which is irreducible and positive
dimensional.

Fix `i != j` among the nonzero indices.  On `K^0` the function `c_i - c_j` is
non-constant:

* if `nu_i + nu_j != 0`, the one-parameter subgroup `t |-> (c_i, c_j) = (nu_j t, -nu_i t)`
  (all other coordinates `0`) lies in `K`, hence in `K^0`, and on it
  `c_i - c_j = (nu_i + nu_j) t`;
* if `nu_i + nu_j = 0`, choose a third nonzero index `l` (possible since
  `n_0 >= 3`) and use `t |-> (c_i, c_l) = (nu_l t, -nu_i t)`, on which
  `c_i - c_j = nu_l t`.

A non-constant morphism stays non-constant after the translation by `x_0`, so
`c_i - c_j` is non-constant on `x_0 + K^0`; in particular
`Delta_{ij} = {c_i = c_j}` meets `x_0 + K^0` in a proper closed subset.  As
`x_0 + K^0` is irreducible, the union of these finitely many proper closed subsets
is not everything, so some point of `Psi^{-1}(T)` has all coordinates distinct.

Finally the marked points (`mu_i = 0`) do not appear in `Psi` and may be placed at
any of the infinitely many remaining points of `E`. `[]`

`elliptic.py` implements this construction with exact `Q/Z` arithmetic, and
`experiments/verify_proofs.py` checks the two defining conditions (AJ) and (P_e) on
the constructed points for every admissible `(k, mu)` in a range; see
`results/verification.md`.

### Corollary 13 (complete answer on the torus)

*A holonomy signature on the torus is realizable if and only if it is **not** one
of*

1. *no cones, with `image(rho) != 0`;*
2. *exactly two cones, of angles `3 pi/2` and `5 pi/2`;*
3. *exactly two cones, of angles `pi` and `3 pi`, with `image(rho) = 2 Z_4`.*

**Proof.**  Apply Theorem 10 with `g = 1`, `k = 4/d`, `mu = m/d`, and read
Proposition 12.  The empty cases are:

* `n_0 = 0` and `k > 1`, i.e. no cones and `d != 4`, which is case 1;
* `n_0 = 2` and `|mu| = 1`, i.e. two cones with orders `(m, -m)` and `|m| = d`.
  Since `d in {1, 2, 4}` and `m > -4`, the possibilities are `|m| = d = 1`,
  giving cone angles `3 pi/2` and `5 pi/2` (and then `D = Z_4` forces `d = 1`, so
  the case is independent of `rho`) -- case 2 -- and `|m| = d = 2`, giving cone
  angles `pi` and `3 pi` with `image(rho) = 2 Z_4` -- case 3.  `|m| = d = 4` would
  need an order `-4`, which is excluded.

Everything else is realizable. `[]`

Case 2 is the exception of Shen et al. 2022 and the non-existence of a
`3,5`-quadrangulation of the torus of Izmestiev-Kusner-Rote-Springborn-Sullivan
2013.  Case 3 is Masur-Smillie's empty stratum `Q(1,-1)`.  Note the contrast
between cases 2 and 3 and the *realizable* signature "two cones of angles `pi` and
`3 pi` with some odd holonomy": the cone angles alone do not decide.

---

## 6. What is machine-checked

`experiments/verify_proofs.py` writes `results/verification.md`.  It checks:

| statement | how |
|---|---|
| Lemma 6 (`N = 4`) | close up `d e_1` under genuine transvections; orbit must be the whole content class.  Complete transvection set for `g <= 3`, random subset for `g = 4` |
| Theorem 8 | recompute orbits under point pushing + transvections; `image(rho)` must be constant on orbits and separate them; orbit counts `1/2/3` |
| Corollary 9 | orbit count is `1` whenever some order is odd |
| Proposition 12 | construct the points in `(Q/Z)^2` exactly and verify (AJ) and (P_e); also check the criterion against the independent square-tiled search |
| Theorem 10 | every square-tiled surface found must have a signature the criterion does not call empty; run over all 1 889 667 gluings of at most four squares |
| Lemma 3 consistency | for every gluing: Gauss-Bonnet, and holonomy around each vertex equal to its valence mod 4 |

A search failing to find a certificate is never used as evidence for emptiness in
any of the above.

## 7. External facts used, and what remains open

Standard facts, used as black boxes:

* **(S1)** A flat cone metric on a closed surface admits a geodesic triangulation
  whose vertices include the cone points (e.g. Delaunay).
* **(S2)** Two triangulations of a compact surface have a common refinement (PL
  topology in dimension 2).
* **(S3)** `Sp(2g, Z)` acts transitively on primitive vectors of `Z^{2g}`.
* **(S4)** `Sp(2g, Z) -> Sp(2g, Z/N)` is surjective.
* **(S5)** `MCG(Sigma_{g,1}, partial) -> Sp(2g, Z)` is surjective.
* **(S6)** Troyanov: flat cone metrics with prescribed angles at prescribed points
  exist on any closed surface when `n >= 3` and Gauss-Bonnet holds.

Literature inputs that this document does **not** prove and that could not be
verified against their sources in the environment where this repository was built
(see `docs/VERIFY.md`):

* Masur-Smillie's list of empty strata of primitive quadratic differentials, used
  by `predict.py` for `d = 2`.
* Gendron-Tahar's classification for primitive 4-differentials, still to be
  extracted (milestone M1); this is the only reason `predict.py` returns
  `unknown` for `g >= 2`, `d = 1`.

Genuinely open here:

* **(D3) Density.**  Whether a non-empty stratum of primitive 4-differentials with
  poles always contains a square-tiled surface.  Standard for `k = 1, 2`; used
  only to justify searching, never to conclude non-existence.
* **Fixed connectivity.**  Everything above allows refinement (Lemma 2).  Existence
  at fixed mesh connectivity is a different question (milestone M6).
* **Boundaries and feature curves** (milestone M3).
