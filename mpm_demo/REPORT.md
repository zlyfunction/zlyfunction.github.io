# Shattering Snow Letters with MPM — Technical Report

Reproducing the title shot of Disney's snow-paper video ([Stomakhin et al. 2013,
*A Material Point Method for Snow Simulation*](https://disneyanimation.com/publications/a-material-point-method-for-snow-simulation/)):
solid snow letters fall, hit a rigid floor, and burst into chunks and powder.
Simulated offline on GPU, baked to a static payload, replayed in the browser
with no solver on the client.

Everything below is reproducible from `gen/sim.py`, `gen/bake.py`, and
`gen/bake_surface.py`; the viewer is a single `index.html`.

---

## 1. Simulation

**Discretization.** MLS-MPM (Hu et al., SIGGRAPH 2018) with quadratic B-spline
weights, explicit time integration, single-grid contact against an analytic
floor. Grid `140` cells per world unit (`dx ≈ 7.1 mm`), `340k` particles,
`dt = 1e-5 s`, `1666` substeps per rendered frame, 90 frames at 60 fps
(1.5 s of sim time). About 7 minutes on an RTX 2070 via Taichi's CUDA backend.

**Constitutive model.** Stomakhin's snow model verbatim: fixed-corotated
elasticity on the elastic part of the deformation gradient, with the singular
values of `F` clamped into `[1 - θ_c, 1 + θ_s]` each substep; whatever the
clamp removes accumulates into the plastic state `J_p`, and the Lamé
parameters are scaled by `exp(ξ (1 - J_p))`.

Production parameters:

| parameter | value | role |
|---|---|---|
| `E`, `ν` | `3e6`, `0.2` | stiff enough to hold letter shape through the fall |
| `θ_c` (critical compression) | `0.020` | base crushes on impact |
| `θ_s` (critical stretch) | `0.0018` | **the fracture knob** — material pulled apart yields almost immediately |
| `ξ` (hardening) | `10` | compaction stiffens, tearing softens |
| `ρ` | `400 kg/m³` | packed snow |
| drop height / tilt | `0.55`, `10°` | 3.3 m/s impact, corner-first so letters bend rather than pancake |

Two deliberate deviations from the paper, both discussed in §3:

- **Hardening is clamped at both ends** (`harden_min`, `harden_max`). One
  exponent is being asked to do two opposite jobs, and they need very
  different magnitudes.
- **The strength floor fades back out for fully shredded material**
  (`powder_jp`, `powder_h`), so dust is cohesionless.

**Letter geometry.** Glyphs are rasterized from a real bold typeface (DejaVu
Sans Bold via PIL) at 320 px cap height, kept as one mask per letter so each
can be tinted independently, then extruded in Z. Particles are
rejection-sampled uniformly inside the glyph volume — pick a filled pixel,
then a uniform point within it — which is exact and much smoother than voxel
jitter. An earlier version used a hand-built 5×7 pixel font; after settling,
its 1-px gaps closed and GOOGLE read as "BOOBLE".

---

## 2. Rendering

The client never solves anything. Two representations are baked per frame.

**Surface.** Particles are splatted into a density grid (cell = 2.1× the
measured median inter-particle spacing), Gaussian-smoothed, and an isosurface
is extracted with marching cubes, decimated to 36k triangles, Taubin-smoothed,
and vertex-colored from the 6 nearest particles with inverse-cube distance
weighting. Frames whose particles have barely moved reference the previous
mesh instead of storing a duplicate.

**Spray.** An isosurface can only represent *coherent* snow. After the burst,
~30% of the mass is loose powder whose 8th-nearest neighbor sits ~5× the bulk
particle spacing away (vs ~2.5× inside chunks). No isolevel captures it
without bloating the dense surface past 500k raw triangles — so, as a fluid
pipeline handles whitewater, those particles are baked separately and drawn as
tiny instanced spheres.

**Shading.** `MeshPhysicalMaterial` with `sheen` (the velvety scatter of fresh
snow) plus light `clearcoat` (icy crust), a PMREM-baked environment on top of
sun and hemisphere lights, ACES filmic tone mapping, and an SSAO pass for
contact darkening in crevices.

Payload: `surface.bin.gz` 22.5 MB, `frames.bin.gz` 10.0 MB, `mesh.json` 0.6 MB.

---

## 3. Debugging log

This is the part worth reading. For a long stretch, the letters landed and
deformed like putty and **no constitutive parameter changed anything** — a
symptom shared by three independent causes.

The tool that broke the deadlock was a *fragmentation metric*: voxelize the
particles, label connected components, and report the mass fraction outside
the six largest. It read exactly `0.000` for every configuration, and sweeping
impact speed over 20× and stiffness over 14× never moved it. **A number that
refuses to budge across a parameter sweep is evidence the parameter is not in
the causal path at all** — which redirected the search from the material model
to the solver.

### 3.1 The ground boundary annihilated the impact energy

The paper's Coulomb condition includes a stick branch that zeroes the *entire*
velocity when `‖v_t‖ ≤ μ|v_n|`. Material falling straight down arrives with
`v_t = 0`, so **every** contacting grid node took that branch and froze solid.

Caught by instrumenting velocities: a letter arriving at 10.2 m/s had a maximum
particle speed of 1.24 m/s one frame later. An energy audit confirmed it —
squashing 50% dissipates ≈2.4 J/kg of plastic work against ≈50 J/kg of impact
energy, so ~95% was disappearing into the boundary rather than converting into
lateral flow.

Replaced with separating (slip) contact: cancel only the downward normal
velocity, apply tangential drag as a per-second decay rate. The rate matters —
a plain per-substep factor is applied ~1666 times per frame and annihilates
lateral motion just as thoroughly.

This is also why the bug never surfaced in an earlier snowball-on-a-slope
scene: material sliding down a ramp always carries tangential velocity, so it
never hits the degenerate branch.

### 3.2 The APIC velocity gradient was ~`inv_dx` too small

The canonical `mpm88` listing writes

```python
new_C += 4 * inv_dx * weight * g_v.outer_product(dpos)
```

because its `dpos` is in dimensionless grid units. This code multiplies `dpos`
by `dx`, so `C` needs `4 * inv_dx * inv_dx` to come out as a velocity gradient
(`1/T`) — the APIC `D⁻¹ = 4/dx²` for quadratic B-splines. Dimensional analysis
on the two conventions is what located it, and `p2g` already used
`inv_dx * inv_dx`, so the two halves of the transfer disagreed.

With one factor missing, `F` stayed at identity, the plastic clamp never
engaged, and stress was ≈0. Confirmed directly by printing `J_p`
(`--debug-plastic`):

| | median `J_p` | compacted (<0.95) | torn (>1.02) |
|---|---|---|---|
| before | `1.0000 ± 0.001` | 0.000 | 0.000 |
| after | `3.52` | — | 0.996 |

The material had simply never yielded. Every constitutive parameter was inert
because `exp(ξ(1 - J_p))` was identically 1.

### 3.3 Under-resolution masquerading as fracture

MLS-MPM needs roughly 4–8 particles per grid cell. Early sweeps ran at **0.58**,
where the material dilates into numerical dust that superficially resembles
shattering — one configuration reported 10,147 components with the largest
holding 0.5% of the mass, which looked like a spectacular fracture and was
actually the discretization falling apart. Every conclusion drawn from those
sweeps had to be discarded. `sim.py` now prints particles-per-cell and warns
below 3.5.

---

## 4. Getting the look right

With a correct solver, the remaining work was genuinely about parameters — but
the mapping from parameter to appearance was not obvious.

**Piling vs. splatting.** The first correct-physics result spread into a thin
sheet full of holes. Two causes: torn material retaining only 2% of its
strength behaves like slush, and low ground drag let chunks skate outward.
Raising the tensile softening floor to 0.25 makes crumbs behave like dry lumps
that support each other with an angle of repose; restoring high ground drag
stops them where they land. The rubble then keeps ~70% of the original letter
height instead of flattening.

**Powder must not levitate.** That same strength floor, applied to *fully*
shredded material, turned dilute dust clouds into a weak aerogel: grid-transmitted
stress held powder in mid-air and even trussed up arch fragments above it,
which reads immediately as broken gravity. The fix is to fade the floor back
out as `J_p` grows past a threshold — cracked crumbs keep strength and pile,
shredded powder loses cohesion and rains down. Hovering dust in the final
frame fell from **16.2% → 5.5%** of particles.

**Polygon shards.** Scattered debris rendered as flat floating plates. The
cause was triangle *size*, not triangle shape: marching cubes emitted ~275k
triangles and decimation cut 91% of them, leaving edges up to 60 mm on a
300 mm letter, so a small chunk survived as 2–3 triangles. Reconstructing more
coarsely brings the raw mesh near 100k, so the same budget cuts only 66% and
the longest edge stays around 25 mm.

**Surface shimmer.** The isolevel was being re-derived each frame from that
frame's own median density. That median drifts ~14% across the clip and jumps
up to 11% between consecutive frames, so the whole surface inflated and
deflated on every rebuild. Pinning it to one absolute density for the clip —
also the physically consistent choice, since the same snow density should
always produce the same surface — cut frame-to-frame surface volume change
from **0.39% mean / 0.99% max to 0.05% / 0.09%**. Taubin smoothing on the
decimated mesh removes the residual marching-cubes sampling noise without the
shrinkage a plain Laplacian would cause.

**Spray that reads as dust, not beads.** Grains at ~1× particle spacing overlap
into visible bead strings glued to the surface. Halving the radius, cutting
eligibility to 2.8%, and requiring grains to be 2.5+ cells clear of meshed snow
brought the count from 6318 to 1846 per frame and turned it into a light
dusting. Spray identity is also keyed to particle id rather than resampled per
frame — an independent random subset each keyframe made the powder strobe
(consecutive-keyframe identity overlap: ~0.1 → 0.97).

---

## 5. Reproducing

```bash
cd gen
python3 -m venv .venv && source env.sh && pip install -r requirements.txt

python3 sim.py --particles 340000 --seconds 1.5 --inv-dx 140 \
    --youngs 3e6 --theta-c 0.020 --theta-s 0.0018 --hardening-xi 10 \
    --harden-min 0.25 --powder-jp 1.3 --powder-h 0.01 \
    --density 400 --drop-height 0.55 --tilt 10 --friction 8 --dt 1e-5

python3 bake.py raw/google_drop.npz ../data/google_drop --max-particles 55000
python3 bake_surface.py raw/google_drop.npz ../data/google_drop
```

Then serve `mpm_demo/` over HTTP and open `index.html`.

Useful while iterating: `--letters 1` simulates only the leading G (~6× cheaper),
and `--debug-plastic` prints `J_p` statistics per frame — the fastest way to
tell whether the material is yielding at all.

---

## 6. Limitations

- Rounded letters (G/O/O/G) collapse into arched mounds rather than breaking
  into sharp-faceted blocks. Closed loops pancake more readily than the thin
  strokes of L and E, which do fracture crisply.
- Surface reconstruction rounds off small chunk facets. The reference renders
  keep sharper edges, which needs both a finer reconstruction grid and a
  higher simulation resolution — at a proportional cost in payload size.
- Shading is a PBR approximation. Snow's real appearance is dominated by
  microscopic subsurface scattering (the bluish tint of deep snow) and
  high-frequency specular glints from ice crystals; neither is modeled.
  A microfacet sparkle layer would be the cheapest meaningful upgrade, since
  it is a shader change requiring no re-simulation.
- Explicit time integration ties `dt` to the CFL limit. An implicit or
  semi-implicit integrator would allow much stiffer snow at the same cost.

---

## References

- Stomakhin, Schroeder, Chai, Teran, Selle. *A Material Point Method for Snow
  Simulation.* ACM TOG (SIGGRAPH 2013).
- Hu, Fang, Ge, Qu, Zhu, Pradhana, Jiang. *A Moving Least Squares Material
  Point Method with Displacement Discontinuity and Two-Way Rigid Body
  Coupling.* ACM TOG (SIGGRAPH 2018).
- Taubin. *A Signal Processing Approach to Fair Surface Design.* SIGGRAPH 1995.
