# The Reduction Lemma

The holonomy signature looks like a lot of data: `n` cone angles plus `4^{2g}`
choices of rotations along a homology basis.  This file argues that almost all of
that data is irrelevant, which is what makes a complete answer plausible.

## Setup

Fix a closed oriented genus-`g` surface `M` and `n` marked points `C`.  A
holonomy signature is a homomorphism

    rho : H_1(M \ C; Z) -> Z_4

whose value on the loop `gamma_i` around `c_i` is `m_i mod 4`, where
`theta_i = (m_i + 4) pi/2` is the prescribed cone angle.  Gauss-Bonnet says
`sum_i m_i = 4(2g - 2)`, which is exactly the relation `sum_i gamma_i = 0`, so
such a `rho` exists and the remaining freedom is

    H^1(M; Z_4) = Z_4^{2g},

recorded by `(rho(a_1), rho(b_1), ..., rho(a_g), rho(b_g))`.

Realizability is invariant under the mapping class group `MCG(M, C)`: a
homeomorphism carrying one signature to another carries a parametrization to a
parametrization.  So the question only depends on the orbit.

## The lemma

> **Reduction Lemma.**  Let `D = <m_1, ..., m_n> <= Z_4` be the subgroup generated
> by the cone rotations, and let `g >= 1`.  Then two signatures with the same
> genus and the same *multiset* of orders lie in the same `MCG(M, C)`-orbit iff
> they have the same `image(rho)`.  Consequently the number of orbits is the
> number of subgroups of `Z_4` containing `D`: one if `D = Z_4`, two if
> `D = 2 Z_4`, three if `D = 0`.

**The proof is in `docs/proofs.md`, Theorem 8** (with Lemmas 5, 6 and 7 as
ingredients).  What follows is the idea; two families of mapping classes do the
work.

**Point pushing.**  Pushing the cone `c_p` once around a loop `alpha` changes
`rho` by `m_p * <alpha, .>`.  As `alpha` ranges over `H_1(M; Z_4)` and the
intersection form is unimodular, these moves translate the handle part of `rho`
by an arbitrary element of `D^{2g}`.

**Dehn twists.**  They act on `H_1(M; Z_4)` by symplectic transvections
`T_c(x) = x + <x, c> c`, and `Sp(2g, Z) -> Sp(2g, Z_4)` is surjective, so the full
`Sp(2g, Z_4)` acts.

Modulo the translations, the handle part lives in `(Z_4 / D)^{2g}`, and
`Sp`-orbits there are classified by the *content* of the vector, i.e. by the
subgroup it generates -- equivalently by `image(rho) = D + <handle values>`.
That is the lemma.

One point that needs care, and that the proof in `docs/proofs.md` handles: the
action of `MCG(M, C)` on the set of signatures with fixed orders is *affine*, not
linear, so "the `Sp` action" only makes sense relative to a base point.  Lemma 7
constructs one: put all the cones inside an embedded disk, take `rho_0` to vanish
on a symplectic basis chosen outside that disk, and use only mapping classes
supported in the complement of the disk.  Those fix `rho_0` and still realize all
of `Sp(2g, Z_4)`.

`mcg.verify_reduction_lemma` checks the conclusion by brute force (BFS over all
`4^{2g}` handle vectors under both families of moves).  It has been verified for
`g = 1, 2, 3` and all `D`: the invariant is constant on orbits and separates
them, with orbit counts `1`, `2`, `3` exactly as predicted.

## Two consequences

**(a) An odd cone angle kills the holonomy data.**  If some cone angle is an odd
multiple of `pi/2` -- in particular if there is a cone of angle `3 pi/2` or
`5 pi/2` -- then `D = Z_4`, there is a single orbit, and realizability depends on
the cone angles alone.  This is a first-principles explanation of the *shape* of
the sufficient condition of Shen et al. 2022: their gcd hypothesis is exactly the
regime in which the rotations along homology loops cannot obstruct anything,
because point pushing can move them anywhere.  (What their theorem then proves --
that the resulting single orbit really is realizable, constructively, on a given
mesh -- is not reproved here.)

**(b) At most three cases per cone-angle multiset.**  The whole classification
problem is: for each `(g, multiset of orders, d)` with `d | D`, is the signature
realizable?  Combined with `docs/dictionary.md` this is exactly the question of
whether a stratum of primitive `k`-differentials (`k = 4/d`) with orders `m_i/d`
is non-empty.

## Main Theorem

> A holonomy signature `(g, m, rho)` is realizable by a seamless parametrization
> iff the stratum of primitive `(4/d)`-differentials with orders `m_i / d` is
> non-empty, where `d` generates `image(rho)`.

This is Theorem 10 of `docs/proofs.md`.  The forward direction is the dictionary;
the converse combines the dictionary with (D2) and with the Reduction Lemma, which
is what lets a differential with the *right image of rho* stand in for one with the
prescribed `rho`.  `results/survey.md` checks it against an independent
square-tiled search on 188 orbits: 178 certified, 4 predicted-empty and not found,
0 contradictions.

## Where the obstructions actually live

It is worth being clear about something the reduction makes visible.  One might
guess that obstructions appear only in the degenerate corner where `rho`
degenerates (`d = 2` or `d = 4`) and the surface becomes a half-translation or
translation surface, since that is where the period conditions of Le Fils and
Bainbridge-Johnson-Judge-Park bite.  The known torus exception refutes that
guess: cones of angle `3 pi/2` and `5 pi/2` give `D = Z_4`, i.e. `d = 1`, the
*least* degenerate case.  Its obstruction is not a period condition but an
Abel-Jacobi condition -- see `docs/genus1.md` -- and it survives for every
conformal structure and every choice of cone positions.

So there are (at least) two independent sources of necessary conditions:

1. **Divisor / Abel-Jacobi obstructions**, which is what kills the torus case and
   what Gendron-Tahar's exceptional lists encode in higher genus;
2. **Degeneration obstructions**, which is what kills `Q(1,3)` and `Q(4)` in
   genus 2 and which only apply when `d > 1`.

Both are already classified in the flat-surface literature.  The claim of this
repository is that they are the *only* two, and that the reduction above is the
bridge.
