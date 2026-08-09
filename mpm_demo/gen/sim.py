"""3D MLS-MPM snow simulation: the word GOOGLE, cast in snow, dropped and shattered.

The shot this reproduces is the title card of Disney's snow-paper video
(Stomakhin et al. 2013, "A Material Point Method for Snow Simulation"):
solid snow letters fall, hit the ground, and burst apart -- the bases crush
and splay outward while the tops fracture off in chunks and a haze of powder
sprays out sideways.

Physics is the paper's constitutive model, transferred with MLS-MPM (Hu et
al. 2018):

  * fixed-corotated elasticity on the *elastic* part of the deformation
    gradient, with the singular values clamped into [1-theta_c, 1+theta_s];
    whatever gets clamped away is pushed into the plastic part Jp.
  * Lame parameters scaled by exp(xi * (1 - Jp)), so compacted snow gets
    stiffer and stretched/loosened snow gets softer.

Getting *brittle shattering* rather than a wet splat is entirely about where
you sit in that parameter space (paper Fig. 12):

  * theta_s small (default 4e-3) -- the material yields in tension almost
    immediately, so it cannot stretch to accommodate the impact and instead
    separates into discrete pieces. This is the single most important knob
    for fracture.
  * xi large (default 10) -- strong hardening makes the response brittle:
    once a region yields it stiffens sharply instead of flowing, so cracks
    localize into clean fracture surfaces rather than smearing out.
  * E large (default 4.5e5) -- stiff enough that the letters hold their
    shape through the fall and the impact stays sharp instead of cushioned.

Letter shapes are rasterized from a real bold typeface (PIL), not a pixel
font, and extruded in Z; particles are rejection-sampled uniformly inside
that volume. Each letter is tinted with a Google brand color plus frosty
white noise so it still reads as snow rather than paint.

Output: raw/google_drop.npz -- per-frame particle positions, per-particle
colors, and a flat ground quad, all consumed by bake.py / bake_surface.py.

Run: source env.sh && python sim.py [--quick]
"""
import argparse
import os
import time

import numpy as np
import taichi as ti
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("--quick", action="store_true", help="low particle count / short clip, for iterating on physics params")
ap.add_argument("--particles", type=int, default=340000)
ap.add_argument("--seconds", type=float, default=2.4)
ap.add_argument("--fps", type=float, default=60.0)
ap.add_argument("--font", default="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
ap.add_argument("--cap-height", type=float, default=0.30, help="letter height, world units")
ap.add_argument("--thickness", type=float, default=0.085, help="letter depth in Z")
ap.add_argument("--drop-height", type=float, default=0.55, help="gap between letter bottoms and the ground")
ap.add_argument("--v0", type=float, default=0.0, help="extra initial downward speed, m/s")
ap.add_argument("--tilt", type=float, default=4.0, help="max random per-letter lean, degrees")
# --- snow constitutive parameters (see module docstring) ---
ap.add_argument("--youngs", type=float, default=4.5e5)
ap.add_argument("--density", type=float, default=400.0)
ap.add_argument("--poisson", type=float, default=0.2)
ap.add_argument("--theta-c", type=float, default=1.9e-2, help="critical compression")
ap.add_argument("--theta-s", type=float, default=4.0e-3, help="critical stretch -- lower shatters harder")
ap.add_argument("--hardening-xi", type=float, default=10.0)
ap.add_argument("--harden-max", type=float, default=20.0, help="cap on compressive stiffening")
ap.add_argument("--harden-min", type=float, default=0.02, help="floor on tensile softening")
ap.add_argument("--powder-jp", type=float, default=1.3,
                help="Jp beyond which torn material fades to cohesionless powder")
ap.add_argument("--powder-h", type=float, default=0.01, help="residual strength of fully torn powder")
ap.add_argument("--friction", type=float, default=6.0,
                help="ground tangential drag, as a decay rate in 1/s (see ground_slip)")
ap.add_argument("--dt", type=float, default=4e-5)
ap.add_argument("--inv-dx", type=float, default=200.0, help="grid cells per world unit")
ap.add_argument("--letters", type=int, default=0, help="sim only the first N letters (0 = whole word)")
ap.add_argument("--out", default=None)
ap.add_argument("--debug-plastic", action="store_true", help="print Jp (plastic state) stats per frame")
ap.add_argument("--dump-jp", default=None, help="also save per-frame Jp history to this .npz path")
args = ap.parse_args()

n_particles_target = args.particles
seconds = args.seconds
if args.quick:
    n_particles_target = min(n_particles_target, 40000)
    seconds = min(seconds, 1.2)

ti.init(arch=ti.cuda, default_fp=ti.f32)

# --------------------------------------------------------------- letters ---
WORD = [
    ("G", "#4285F4"),
    ("O", "#EA4335"),
    ("O", "#FBBC05"),
    ("G", "#4285F4"),
    ("L", "#34A853"),
    ("E", "#EA4335"),
]
if args.letters:   # e.g. --letters 1 sims just the leading G, ~6x cheaper,
    WORD = WORD[:args.letters]   # for sweeping physics before a full run
RASTER_PX = 320          # cap height in raster pixels -- fine enough that the
                         # curved sides of G/O sample as smooth curves

def rasterize_word(font_path, chars):
    """Rasterize the word once at high resolution, keeping a separate mask per
    letter so each can be tinted individually. Returns (masks, px_per_world),
    where masks are bool arrays over a shared canvas and row 0 is the top."""
    # size the font so that cap height (measured on "G") lands on RASTER_PX
    probe = ImageFont.truetype(font_path, RASTER_PX)
    top, bottom = probe.getbbox("G")[1], probe.getbbox("G")[3]
    font = ImageFont.truetype(font_path, int(round(RASTER_PX * RASTER_PX / (bottom - top))))

    advances = [font.getlength(c) for c in chars]
    # letters are laid out on the font's own advances (real typographic
    # spacing), then nudged apart so neighbouring letters never touch --
    # they must fall as six independent bodies, not one welded slab
    extra = 0.10 * RASTER_PX
    xs, cur = [], 0.0
    for a in advances:
        xs.append(cur)
        cur += a + extra
    W = int(cur + 2 * RASTER_PX)
    H = int(3 * RASTER_PX)
    baseline = int(2.2 * RASTER_PX)

    masks = []
    for c, x0 in zip(chars, xs):
        img = Image.new("L", (W, H), 0)
        ImageDraw.Draw(img).text((RASTER_PX * 0.5 + x0, baseline), c, fill=255, font=font, anchor="ls")
        masks.append(np.array(img) > 127)

    union = np.any(masks, axis=0)
    rows, cols = np.nonzero(union)
    r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
    masks = [m[r0:r1, c0:c1] for m in masks]
    # world scale: the union's height is the cap height (all-caps word)
    px_per_world = (r1 - r0) / args.cap_height
    return masks, px_per_world


masks, px_per_world = rasterize_word(args.font, [c for c, _ in WORD])
mask_h, mask_w = masks[0].shape
word_w = mask_w / px_per_world
word_h = mask_h / px_per_world
THICK = args.thickness

# --------------------------------------------------------------- domain ---
dx = 1.0 / args.inv_dx
inv_dx = 1.0 / dx
GROUND_Y = 0.05

Lx = word_w + 0.55
Ly = GROUND_Y + args.drop_height + word_h + 0.22
Lz = THICK + 0.42          # generous: powder sprays out along Z on impact
nx, ny, nz = int(Lx * inv_dx) + 4, int(Ly * inv_dx) + 4, int(Lz * inv_dx) + 4

dt = args.dt
frame_dt = 1.0 / args.fps
n_frames = max(1, int(seconds * args.fps))
substeps = max(1, int(frame_dt / dt))

# ------------------------------------------------------------- material ---
E, nu = args.youngs, args.poisson
mu_0 = E / (2.0 * (1.0 + nu))
lambda_0 = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
hardening_xi = args.hardening_xi
harden_max = args.harden_max
harden_min = args.harden_min
powder_jp = args.powder_jp
powder_h = args.powder_h
theta_c = args.theta_c
theta_s = args.theta_s
gravity = 9.8
friction_mu = args.friction
# Tangential retention per substep. Expressed as a decay *rate* (1/s) so the
# amount of drag a sliding chunk feels per second of contact is independent
# of dt / the substep count -- a plain per-substep factor would be applied
# thousands of times per frame and instantly kill all lateral flow.
ground_slip = float(np.exp(-friction_mu * args.dt))
p_rho = args.density

# Ratio of the material's yield stress (E * theta_c) to the stress the impact
# delivers (sqrt(rho * E) * v): how much of the body is expected to yield.
# Reported as a sanity check, but note it is NOT the knob that controls
# fragmentation -- sweeping it from 0.09 to 1.39 produced no fracture at all
# while the ground boundary was sticky (see grid_update). Fix the boundary
# first; this only decides how far the pieces deform once they can move.
_impact_v = float(np.sqrt(args.v0 ** 2 + 2.0 * gravity * args.drop_height))
_brittleness = theta_c * float(np.sqrt(E / p_rho)) / _impact_v

# --------------------------------------------------------- particle init ---
rng = np.random.default_rng(7)
x_left = (Lx - word_w) / 2.0
y_bottom = GROUND_Y + args.drop_height

# area (in world units^2) of each letter's footprint, used to split the
# particle budget so every letter gets the same particle *density*
areas = np.array([m.sum() for m in masks], dtype=np.float64) / (px_per_world ** 2)
total_vol = float(areas.sum()) * THICK
counts = np.maximum(1, np.round(n_particles_target * areas / areas.sum()).astype(int))

positions, colors = [], []
for (ch, hexcol), mask, want in zip(WORD, masks, counts):
    rows, cols = np.nonzero(mask)
    # rejection-sample uniformly inside the glyph: pick a filled pixel, then a
    # uniform point within it. Exact and much smoother than voxel jitter.
    pick = rng.integers(0, len(rows), size=want)
    jx = rng.random(want)
    jy = rng.random(want)
    px = (cols[pick] + jx) / px_per_world
    py = (mask_h - 1 - rows[pick] + jy) / px_per_world
    pz = rng.random(want) * THICK

    pts = np.stack([px, py, pz], axis=1)
    # small random lean about Z, applied around the letter's own base centre,
    # so the six letters land on corners at slightly different angles rather
    # than all pancaking flat at the same instant
    ang = np.deg2rad(rng.uniform(-args.tilt, args.tilt))
    cx, cy = pts[:, 0].mean(), 0.0
    ca, sa = np.cos(ang), np.sin(ang)
    ox, oy = pts[:, 0] - cx, pts[:, 1] - cy
    pts[:, 0] = cx + ca * ox - sa * oy
    pts[:, 1] = cy + sa * ox + ca * oy

    pts[:, 0] += x_left
    pts[:, 1] += y_bottom
    pts[:, 2] += (Lz - THICK) / 2.0

    r = int(hexcol[1:3], 16) / 255.0
    g = int(hexcol[3:5], 16) / 255.0
    b = int(hexcol[5:7], 16) / 255.0
    frost = rng.uniform(-0.04, 0.14, size=want)
    col = np.stack([
        np.clip(r + frost, 0, 1), np.clip(g + frost, 0, 1), np.clip(b + frost, 0, 1),
    ], axis=1)

    positions.append(pts)
    colors.append(col)

init_pos = np.concatenate(positions).astype(np.float32)
colors_u8 = (np.concatenate(colors) * 255).astype(np.uint8)
n_particles = init_pos.shape[0]

p_vol = total_vol / n_particles
p_mass = p_vol * p_rho

# MLS-MPM needs the material sampled at roughly 4-8 particles per grid cell.
# Below ~2 the material dilates and scatters into numerical dust that looks
# superficially like fracture but is just under-resolution, so this is
# printed loudly rather than buried.
_ppc = n_particles / (total_vol / dx ** 3)
print(f"n_particles={n_particles} p_mass={p_mass:.3e} p_vol={p_vol:.3e} "
      f"grid=({nx},{ny},{nz}) substeps/frame={substeps} n_frames={n_frames}")
print(f"particles per grid cell = {_ppc:.1f}" + ("" if _ppc >= 3.5 else "   <-- TOO LOW, expect numerical dust"))
print(f"word {word_w:.3f} x {word_h:.3f} x {THICK:.3f}, impact speed "
      f"~{_impact_v:.2f} m/s, brittleness ~{_brittleness:.2f} "
      f"(wave speed {np.sqrt(E / p_rho):.0f} m/s, CFL dt < {dx / np.sqrt(E / p_rho):.1e})")

# ------------------------------------------------------------ ti. fields ---
x = ti.Vector.field(3, ti.f32, n_particles)
v = ti.Vector.field(3, ti.f32, n_particles)
C = ti.Matrix.field(3, 3, ti.f32, n_particles)
F = ti.Matrix.field(3, 3, ti.f32, n_particles)
Jp = ti.field(ti.f32, n_particles)

grid_v = ti.Vector.field(3, ti.f32, (nx, ny, nz))
grid_m = ti.field(ti.f32, (nx, ny, nz))


@ti.kernel
def init_particles(pos: ti.types.ndarray(), v0: ti.f32):
    for p in range(n_particles):
        x[p] = ti.Vector([pos[p, 0], pos[p, 1], pos[p, 2]])
        v[p] = ti.Vector([0.0, -v0, 0.0])
        F[p] = ti.Matrix.identity(ti.f32, 3)
        C[p] = ti.Matrix.zero(ti.f32, 3, 3)
        Jp[p] = 1.0


@ti.kernel
def p2g():
    for i, j, k in grid_m:
        grid_v[i, j, k] = ti.Vector.zero(ti.f32, 3)
        grid_m[i, j, k] = 0.0
    for p in range(n_particles):
        base = (x[p] * inv_dx - 0.5).cast(int)
        fx = x[p] * inv_dx - base.cast(ti.f32)
        w = [0.5 * (1.5 - fx) ** 2, 0.75 - (fx - 1.0) ** 2, 0.5 * (fx - 0.5) ** 2]

        F[p] = (ti.Matrix.identity(ti.f32, 3) + dt * C[p]) @ F[p]
        # Hardening, clamped at both ends. The paper's raw exp(xi*(1-Jp)) uses
        # one exponent for two jobs, and they need opposite magnitudes here:
        # tensile softening has to be violent enough that torn material loses
        # essentially all strength (so cracks open and chunks separate), while
        # compressive hardening must stay bounded or the crushed base turns
        # into a superball -- at xi=10 a half-compacted particle stiffens by
        # e^5 ~ 148x and the letter simply bounces back intact. Clamping lets
        # xi be cranked up for the tensile side alone.
        h = ti.exp(hardening_xi * (1.0 - Jp[p]))
        h = min(max(h, harden_min), harden_max)
        # Fully torn material is cohesionless powder. The harden_min floor is
        # what lets crumb *lumps* stack into a pile, but applied to everything
        # it also turns sparse dust clouds into a weak aerogel: stray powder
        # hangs in mid-air on grid-transmitted stress instead of raining down,
        # and can even truss up arch fragments above it -- visibly wrong
        # gravity. So the floor fades out again as Jp grows past the point
        # where the material is shredded rather than merely cracked.
        t = min(max((Jp[p] - powder_jp) / 0.5, 0.0), 1.0)
        h = h * (1.0 - t) + powder_h * t
        mu, la = mu_0 * h, lambda_0 * h
        U, sig, V = ti.svd(F[p])
        J = 1.0
        for d in ti.static(range(3)):
            s = sig[d, d]
            s = min(max(s, 1.0 - theta_c), 1.0 + theta_s)
            Jp[p] *= sig[d, d] / s
            sig[d, d] = s
            J *= s
        F[p] = U @ sig @ V.transpose()

        stress = 2.0 * mu * (F[p] - U @ V.transpose()) @ F[p].transpose()
        stress += ti.Matrix.identity(ti.f32, 3) * la * J * (J - 1.0)
        stress = (-dt * p_vol * 4.0 * inv_dx * inv_dx) * stress
        affine = stress + p_mass * C[p]

        for di, dj, dk in ti.static(ti.ndrange(3, 3, 3)):
            offset = ti.Vector([di, dj, dk])
            dpos = (offset.cast(ti.f32) - fx) * dx
            weight = w[di][0] * w[dj][1] * w[dk][2]
            grid_v[base + offset] += weight * (p_mass * v[p] + affine @ dpos)
            grid_m[base + offset] += weight * p_mass


bound = 4


@ti.kernel
def grid_update():
    for i, j, k in grid_m:
        if grid_m[i, j, k] > 0:
            gv = grid_v[i, j, k] / grid_m[i, j, k]
            gv.y -= dt * gravity

            if i < bound and gv.x < 0: gv.x = 0.0
            if i > nx - bound and gv.x > 0: gv.x = 0.0
            if k < bound and gv.z < 0: gv.z = 0.0
            if k > nz - bound and gv.z > 0: gv.z = 0.0
            if j > ny - bound and gv.y > 0: gv.y = 0.0

            # Flat ground, *separating* (slip) contact: cancel only the
            # downward normal velocity, then damp the tangential flow.
            #
            # The paper's full Coulomb condition also has a stick branch that
            # zeroes the whole velocity when ||v_t|| <= mu*|v_n|. That is fine
            # for a body sliding along a slope, but it is catastrophic for a
            # vertical impact: material arrives falling straight down, so
            # v_t = 0 at the instant of contact and *every* contacting node
            # takes the stick branch and is frozen solid. The impact energy is
            # then annihilated by the boundary rather than converted into
            # lateral flow -- measured at 95% of it for a 10 m/s drop, which
            # is why the letters used to just deflate in place and no amount
            # of constitutive tuning could make them burst.
            wy = j * dx
            if wy < GROUND_Y + 2.0 * dx and gv.y < 0.0:
                gv.y = 0.0
                gv.x *= ground_slip
                gv.z *= ground_slip
            grid_v[i, j, k] = gv


@ti.kernel
def g2p():
    for p in range(n_particles):
        base = (x[p] * inv_dx - 0.5).cast(int)
        fx = x[p] * inv_dx - base.cast(ti.f32)
        w = [0.5 * (1.5 - fx) ** 2, 0.75 - (fx - 1.0) ** 2, 0.5 * (fx - 0.5) ** 2]
        new_v = ti.Vector.zero(ti.f32, 3)
        new_C = ti.Matrix.zero(ti.f32, 3, 3)
        for di, dj, dk in ti.static(ti.ndrange(3, 3, 3)):
            offset = ti.Vector([di, dj, dk])
            dpos = (offset.cast(ti.f32) - fx) * dx
            weight = w[di][0] * w[dj][1] * w[dk][2]
            g_v = grid_v[base + offset]
            new_v += weight * g_v
            # APIC/MLS reconstruction: C = B * D^-1 with D = (dx^2/4) I for the
            # quadratic B-spline, so the factor is 4*inv_dx^2 -- NOT 4*inv_dx.
            # The canonical mpm88 listing writes 4*inv_dx because its dpos is
            # left in dimensionless grid units; ours is multiplied by dx, so it
            # needs the second inv_dx to come out as a velocity gradient (1/T).
            # With only one, C was ~inv_dx times too small: F stayed at identity,
            # the plastic clamp never engaged (measured Jp == 1.0000 throughout),
            # stress was ~0, and every constitutive parameter was inert.
            new_C += 4.0 * inv_dx * inv_dx * weight * g_v.outer_product(dpos)
        v[p] = new_v
        C[p] = new_C
        x[p] += dt * new_v


def substep():
    p2g()
    grid_update()
    g2p()


# ---------------------------------------------------------- ground mesh ---
def build_ground_mesh(nxv=24, nzv=12):
    """A flat quad grid, visual only -- the collider itself is the analytic
    plane in grid_update()."""
    xs = np.linspace(0.0, Lx, nxv)
    zs = np.linspace(0.0, Lz, nzv)
    gx, gz = np.meshgrid(xs, zs, indexing="ij")
    gy = np.full_like(gx, GROUND_Y)
    verts = np.stack([gx, gy, gz], axis=-1).reshape(-1, 3).astype(np.float32)
    tris = []
    for i in range(nxv - 1):
        for k in range(nzv - 1):
            a = i * nzv + k
            b = a + 1
            c = (i + 1) * nzv + k
            d = c + 1
            tris.append((a, c, b))
            tris.append((b, c, d))
    return verts, np.array(tris, dtype=np.int32)


def main():
    init_particles(init_pos, args.v0)
    ground_verts, ground_tris = build_ground_mesh()

    frames = np.zeros((n_frames, n_particles, 3), dtype=np.float32)
    jp_frames = np.zeros((n_frames, n_particles), dtype=np.float32) if args.dump_jp else None
    t0 = time.time()
    for f in range(n_frames):
        for _ in range(substeps):
            substep()
        frames[f] = x.to_numpy()
        if jp_frames is not None:
            jp_frames[f] = Jp.to_numpy()
        if args.debug_plastic and (f % 4 == 0 or f == n_frames - 1):
            jp = Jp.to_numpy()
            print(f"  [Jp] f{f:3d} min={jp.min():.4f} max={jp.max():.4f} "
                  f"med={np.median(jp):.4f} compacted(<0.95)={np.mean(jp < 0.95):.3f} "
                  f"torn(>1.02)={np.mean(jp > 1.02):.3f}")
        if (f + 1) % 10 == 0 or f == n_frames - 1:
            el = time.time() - t0
            print(f"frame {f + 1}/{n_frames}  ({el:.1f}s elapsed, {el / (f + 1):.2f}s/frame)")

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
    os.makedirs(out_dir, exist_ok=True)
    out_path = args.out or os.path.join(out_dir, "google_drop.npz")
    np.savez_compressed(
        out_path,
        frames=frames,
        colors=colors_u8,
        ground_verts=ground_verts,
        ground_tris=ground_tris,
        fps=np.float32(args.fps),
        domain=np.array([Lx, Ly, Lz], dtype=np.float32),
    )
    print(f"saved {out_path}  ({os.path.getsize(out_path) / 1e6:.1f} MB)")
    if jp_frames is not None:
        np.savez_compressed(args.dump_jp, jp=jp_frames)
        print(f"saved {args.dump_jp}")


if __name__ == "__main__":
    main()
