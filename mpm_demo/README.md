# MPM Snow Demo

The word GOOGLE cast in snow, dropped, and shattered on impact — the title
shot from Disney's snow-paper video, simulated with the **Material Point
Method** and played back in the browser. Physics from
[Stomakhin et al. 2013, *A Material Point Method for Snow Simulation*](https://disneyanimation.com/publications/a-material-point-method-for-snow-simulation/)
(Disney) — fixed-corotated elasticity with hardening plasticity — transferred
with **MLS-MPM** (Hu et al. 2018, SIGGRAPH). Everything is simulated offline
on GPU (taichi, CUDA backend) and baked into a compact, static, self-contained
web page: no server-side code, no WebGPU/WASM solver in the browser, just a
precomputed clip.

This directory is its own git repository, independent of the parent
portfolio site — it just happens to live inside it.

## Layout

```
mpm_demo/
  gen/
    sim.py               # the drop: six extruded snow letters, shattered on a rigid floor
    bake.py                # raw/*.npz -> data/<scene>/{mesh.json, frames.bin.gz}
    bake_surface.py          # raw/*.npz -> data/<scene>/{surface.json, surface.bin.gz}
    requirements.txt
    env.sh                     # sets up venv + WSL CUDA driver lib path
    raw/                        # (gitignored) simulation output .npz
    .venv/                      # (gitignored)
  data/google_drop/         # baked web assets (checked in)
  index.html                  # three.js playback page
```

## Regenerating

```bash
cd gen
python3 -m venv .venv && source env.sh && pip install -r requirements.txt

# ~7 min on an RTX 2070. Defaults are the calibrated shatter; see below.
python3 sim.py --particles 340000 --seconds 1.5 --inv-dx 140 \
    --youngs 3e6 --theta-c 0.020 --theta-s 0.0018 --hardening-xi 10 \
    --harden-min 0.25 --powder-jp 1.3 --powder-h 0.01 \
    --density 400 --drop-height 0.55 --tilt 10 \
    --friction 8 --dt 1e-5

python3 bake.py raw/google_drop.npz ../data/google_drop --max-particles 55000
python3 bake_surface.py raw/google_drop.npz ../data/google_drop
```

Useful while iterating: `--letters 1` sims only the leading G (~6x cheaper),
and `--debug-plastic` prints the plastic state `Jp` per frame, which is the
fastest way to tell whether the material is yielding at all.

Then serve the repo root (`python3 -m http.server` from `mpm_demo/`) and open
`index.html`.

## Rendering notes

Three render modes, toggled via the "render:" button (persisted in
`localStorage`): `surface` > `grains` > `points`.

- **`surface`** (default) is the same idea production MPM
  renderers use: don't draw the particles, draw the *fluid surface they
  imply*. `bake_surface.py` splats each frame's particles into a density
  grid (grid cell auto-sized to ~1.35x the measured inter-particle
  spacing — much coarser and the shape blurs, much finer and each particle
  becomes its own blob and the surface turns to shredded confetti),
  gaussian-smooths it, extracts the isosurface with marching cubes,
  drops tiny disconnected components (single escaped grains would render
  as floating specks), decimates to ~24k triangles, and colors vertices by
  inverse-cube-distance-weighted nearest particles (a flat k-NN mean
  smears adjacent letters' blue+red into a magenta seam; heavy distance
  weighting keeps the blend zone tight). Triangle *size*, not triangle
  shape, is what makes debris read as floating polygon shards: a scattered
  chunk that survives decimation as only 2-3 triangles looks like a flat
  plate. Reconstructing coarsely enough that the raw mesh is ~100k rather
  than ~275k triangles means the same budget cuts 66% instead of 91%, which
  keeps the longest edge near 25mm instead of 60mm on a 300mm letter. The
  low ground friction matters here too: debris that spreads into a
  continuous carpet reconstructs as one connected surface, so there are
  barely any isolated blobs left to shard in the first place.

  An isosurface can only represent *coherent* snow, though. After the
  burst, ~30% of the mass is loose powder — isolated grains whose 8th
  nearest neighbor sits ~5x the bulk spacing away — and no isolevel keeps
  them without bloating the dense surface past 500k raw triangles. Without
  handling this, the scattered snow simply vanished from surface mode. So,
  like a production fluid pipeline's whitewater pass, particles whose local
  density is below the isolevel are baked as a separate **spray** section
  per frame (capped, quantized like the mesh) and rendered as tiny
  instanced spheres on top of the surface. Keep this pass sparse: grains at
  ~1x the particle spacing overlap into visible bead strings stuck to the
  snow, so the radius is half that and only grains 2.5+ cells clear of
  meshed snow qualify — airborne dust, not beads on a surface.

  Two things stop the surface shimmering. The isolevel is a single absolute
  density for the whole clip, not a per-frame fraction of that frame's own
  median: the median drifts ~14% over the clip and jumps up to 11% between
  consecutive frames, so a per-frame threshold inflates and deflates the
  whole surface on every rebuild (measured frame-to-frame volume change:
  0.39% mean / 0.99% max per-frame vs **0.05% / 0.09%** fixed). A constant
  density threshold is also the physically consistent choice. On top of
  that, a few Taubin smoothing passes low-pass the decimated mesh, removing
  the particle sampling noise marching cubes bakes into it without the
  shrinkage plain Laplacian smoothing would cause. Two related floor details: the
  sim's ground boundary acts a couple of *sim* grid cells above the visual
  ground plane, so the bake measures the actual resting floor height from
  the settled particles, mirrors near-floor particles across it (so the
  thin carpet's density stays above iso), and clips away the mirrored
  underside that would otherwise waste triangles below the ground.

  Since settled snow never goes
  perfectly still (grains creep ~1mm/frame forever), a frame only gets a
  new mesh once the p99 particle displacement since the last built mesh
  exceeds a fraction of a grid cell — dedup that cuts the payload roughly
  in half. The viewer preallocates one indexed `BufferGeometry` at max
  vert/tri counts and swaps quantized frame blocks into it, recomputing
  normals only when the mesh actually changes. One continuous mesh also
  casts/receives real shadow-map shadows, which 25k point sprites can't.
- **`grains`** renders each particle as a real lit sphere
  (`THREE.InstancedMesh` of a low-poly icosahedron, random per-instance
  facet rotation so they glint like faceted ice crystals). Kept because
  it's scene-agnostic (works without baked surface data) and shows the
  actual particle structure.
- **`points`** is the original flat point-sprite renderer — cheapest,
  useful on low-end GPUs.

Shared look: `MeshPhysicalMaterial` with `sheen` (the soft, velvety
scatter of fresh snow — kept moderate on the surface material, since a
full white sheen layer washes the letter colors to pastel) plus a touch of
`clearcoat` (icy crust), a small PMREM-baked environment map on top of the
sun/hemisphere lights, ACES filmic tone mapping, and an SSAO postprocess
pass for contact shadowing in crevices.
- Gotcha hit along the way: setting `material.vertexColors = true` on the
  instanced-sphere material caused the whole thing to render pure black.
  That flag makes the shader also read the geometry's own per-vertex
  `color` attribute, which a plain `IcosahedronGeometry` doesn't have — the
  unbound attribute reads back as zero and multiplies the diffuse color to
  black. Per-instance tint should come from `InstancedMesh.setColorAt`
  alone (`instanceColor`), which three.js wires up automatically whenever
  `object.instanceColor` exists, independent of `material.vertexColors`.

## Physics notes

- The snow constitutive model is Stomakhin 2013's: fixed-corotated
  elasticity, singular values of the elastic deformation gradient clamped to
  `[1-theta_c, 1+theta_s]`, Lame parameters hardened by accumulated plastic
  compaction. What produces the *shatter* rather than a splat is the tensile
  side: `theta_s` is set very low (1.5e-3), so material pulled apart yields
  almost immediately and softens toward zero strength, letting cracks open
  and chunks separate, while the compressed bulk stays stiff enough to hold
  the letter shape on the way down. The hardening is clamped at both ends —
  the paper's raw `exp(xi*(1-Jp))` uses one exponent for two opposite jobs,
  and an unclamped compressive branch turns the crushed base into a
  superball that bounces back intact.
- The floor is a **rigid analytic collider** with *separating* (slip)
  contact: only the downward normal velocity is cancelled, and tangential
  drag is applied as a per-second decay rate.
- Whether the debris *piles up* or flattens into a splat is set by two
  knobs working together. `--harden-min` is the floor on tensile softening:
  at the raw model's 0.02, torn material keeps ~2% strength and flows like
  slush into a thin sheet full of holes; at 0.25 the crumbs behave like dry
  lumps that support each other, so the rubble keeps ~90% of the letter
  height. High ground drag (`--friction 8`) then stops the chunks where
  they land instead of letting them skate outward across the floor.
  The floor cannot apply to *fully* shredded material, though: give sparse
  dust 25% stiffness and it stops falling — grid-transmitted stress turns a
  dilute particle cloud into a weak aerogel that hangs in mid-air and even
  trusses up arch fragments above it, which reads as broken gravity. So the
  strength floor fades back out as `Jp` grows past `--powder-jp`: cracked
  crumbs keep their strength (piling), shredded powder becomes cohesionless
  and rains down onto the pile (hovering dust at the last frame: 16% of
  particles before, 5% after).
- Why not [`yuanming-hu/taichi_mpm`](https://github.com/yuanming-hu/taichi_mpm)
  (the repo the original paper's demos + course notes point to)? It's the
  old pre-2019 Taichi compiler stack, unmaintained and effectively
  unbuildable today. `sim.py` reimplements the published MLS-MPM/snow
  algorithm directly against the modern `taichi` Python package instead.

### Two bugs that made fracture impossible, and how they were found

Both presented identically — letters landing and deforming like putty, with
*no* constitutive parameter making any difference — so they are worth
recording. The decisive tool was a fragmentation metric (voxelize the
particles, label connected components, report the mass fraction outside the
six largest). It read exactly `0.000` for every config, meaning nothing ever
detached; sweeping impact speed over 20x and stiffness over 14x never moved
it. A number that refuses to budge across a parameter sweep is evidence the
parameter isn't in the causal path at all.

1. **The ground boundary annihilated the impact energy.** The paper's
   Coulomb condition has a stick branch that zeroes the *whole* velocity when
   `||v_t|| <= mu*|v_n|`. Material falling straight down arrives with
   `v_t = 0`, so every contacting node took that branch and froze solid.
   Caught by noticing that a letter arriving at 10.2 m/s had a maximum
   particle speed of 1.24 m/s one frame later; an energy audit showed
   squashing 50% dissipates ~2.4 J/kg of plastic work against ~50 J/kg of
   impact energy, so ~95% was going somewhere unphysical. (This is also why
   the effect never showed up in the old snowball-on-a-slope scene: material
   sliding down a ramp always has tangential velocity, so it never hit the
   degenerate branch.)
2. **The APIC velocity gradient was ~`inv_dx` times too small.** The
   canonical mpm88 listing writes `new_C += 4 * inv_dx * weight * ...`
   because its `dpos` is in dimensionless grid units; this code multiplies
   `dpos` by `dx`, so it needs `4 * inv_dx * inv_dx` for `C` to come out as a
   velocity gradient (1/T). With one factor missing, `F` stayed at identity,
   the plastic clamp never engaged, and stress was ~0. Confirmed directly by
   printing `Jp` (`--debug-plastic`): it sat at `1.0000 +/- 0.001` through an
   entire impact, with the compacted and torn fractions both `0.000`. After
   the fix, median `Jp` reached 3.5 and the torn fraction 0.996 on the same
   input. Dimensional analysis on the two `dpos` conventions is what located
   it; note `p2g` already used `inv_dx * inv_dx`, so the two halves of the
   transfer disagreed.

A third, milder trap: MLS-MPM needs roughly 4-8 particles per grid cell.
Early sweeps ran at 0.58, where the material dilates into numerical dust
that superficially resembles fracture. `sim.py` now prints particles-per-cell
and warns below 3.5.
