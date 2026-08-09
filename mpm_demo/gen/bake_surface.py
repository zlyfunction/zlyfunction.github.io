"""Bake a continuous snow *surface* mesh + a loose-powder spray pass per frame.

This is the surface-reconstruction step the Disney snow paper's renders rely
on: particles are splatted into a density grid, the isosurface is extracted
with marching cubes, decimated, and vertex-colored from the nearest
particles. The viewer then renders one smooth lit mesh per frame instead of
hundreds of thousands of individual grains.

An isosurface can only represent *coherent* snow, though. After the letters
burst, ~30% of the mass is loose powder -- individual grains whose 8th
nearest neighbor is ~5x the bulk particle spacing away. No isolevel keeps
them without also bloating the dense surface (lowering iso until the dust
appeared pushed marching cubes past 500k triangles). So, like a production
fluid pipeline's whitewater pass, particles the surface can't represent
(local density below the isolevel) are stored separately per frame and the
viewer renders them as tiny instanced grains on top of the mesh.

The snow also rests slightly *above* the collider plane (the sim's ground
boundary acts at GROUND_Y + 2 grid cells), so the resting carpet's own
bottom skin used to be meshed too. Particles near the measured resting
floor are mirrored across it before splatting -- doubling the carpet's
density so a thin layer stays above iso -- and triangles fully below the
floor are clipped afterwards, closing the carpet against the ground for
free instead of spending triangles on an invisible underside.

Input : gen/raw/<scene>.npz     (frames, colors from sim.py)
Output: ../data/<scene>/surface.json      per-frame counts + bounds
        ../data/<scene>/surface.bin.gz    per-frame quantized blocks

Binary layout per unique frame (sections padded to 2-byte alignment):
    positions   int16  v*3   quantized against clip-global bounds
    colors      uint8  v*3
    indices     uint16 t*3
    spray pos   int16  s*3
    spray col   uint8  s*3
    spray size  uint8  s*1   per-grain size jitter, keyed to particle id
Frames whose particles haven't moved (settled snow) are stored as a
reference to the previous frame's block instead of a duplicate.

Usage: python bake_surface.py raw/google_drop.npz ../data/google_drop
"""
import gzip
import json
import os
import sys

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage import measure
import fast_simplification

CELL_PER_SPACING = 2.1   # grid spacing as a multiple of the measured median
                         # nearest-neighbor particle spacing -- coarser than
                         # the particles so the splatted field is a connected
                         # solid, not a cloud of separate per-particle blobs
SIGMA = 1.5           # gaussian blur of the splat field, in cells
ISO_FRAC = 0.12       # isolevel as a fraction of interior (median) density.
                      # Lower than intuition suggests: after the burst the
                      # deposit settles into a 1-2-particle-thick carpet
                      # (~2.5 particles per bake cell over the footprint),
                      # and at 0.40 nearly a third of the spread snow sits
                      # below the isolevel and silently vanishes (see the
                      # disappearance analysis in REPORT.md). 0.12 keeps
                      # ~98% of the carpet meshed at every frame.
TARGET_TRIS = 36000   # decimation target per frame
MIN_COMPONENT = 120   # drop blobs smaller than this many cells (their
                      # particles land in the spray pass instead). At the
                      # coarser 2.1-spacing cell, 500 cells is a ~38mm chunk --
                      # an eighth of a letter -- so real debris was being
                      # classified as dust. 120 cells ~ 24mm: still well above
                      # the numerical-noise scale, small enough to keep
                      # genuine rubble.
# Those four are really one decision: how hard the decimator has to work.
# Triangle *size* is what produces flat-shard artifacts -- a debris chunk
# that survives decimation as only 2-3 triangles reads as a floating polygon
# plate, not snow. Keep the raw marching-cubes output within ~3x of the
# target budget and shards stay away.
REBUILD_P99 = 0.4     # rebuild the mesh only once the 99th-percentile particle
                      # displacement since the last built frame exceeds this
                      # fraction of a grid cell -- settled snow never goes
                      # perfectly still (a few grains keep creeping ~1mm/frame
                      # forever), and rebuilding for that is invisible churn
COLOR_K = 6           # nearest particles averaged per vertex color
SAT_BOOST = 1.75      # re-saturate vertex colors (the white sheen/env lighting
                      # in the viewer washes colors out; k-NN averaging also
                      # pulls them toward the frosty mean)
PAD = 6               # grid padding, cells
MIRROR_BAND = 12.0    # mirror particles within this many cells of the floor.
                      # The carpet's density foot is ~3 cells thick (Gaussian
                      # skirt), so particles up to ~12 cells above the floor
                      # are still part of the surface that benefits from the
                      # doubled below-floor density; 3 cells only mirrored the
                      # bottom skin and left the rest of the foot thin.
SPRAY_FRAC = 0.028    # fraction of particles *eligible* to render as spray.
                      # Chosen once per particle id, NOT per frame: an
                      # independent random subsample each frame hands every
                      # keyframe a different 10-15% of the powder, and the
                      # grains strobe wildly during playback. With a fixed
                      # eligible set a grain only appears/disappears when its
                      # own local density actually crosses the threshold.
SPRAY_VAL_FRAC = 0.85 # spray only below this fraction of iso -- particles
                      # hovering right AT the isolevel flip between mesh and
                      # spray on tiny density changes (more flicker); ones in
                      # the narrow dead band are skipped entirely, invisibly,
                      # since they sit at the fringe of the meshed surface
SPRAY_MAX = 5000      # hard cap on spray stored per frame
SPRAY_ISOLATION = 2.5 # only spray grains this many cells clear of meshed snow.
                      # Grains hugging the surface read as beads stuck to it
                      # rather than as airborne powder.
SPRAY_RADIUS = 0.5    # grain radius as a multiple of particle spacing. At
                      # ~1x, neighbouring grains overlap into visible clumps.


SMOOTH_ITERS = 3      # Taubin smoothing passes on the decimated mesh
CLUMP = 0.28          # baked clumpy micro-relief: fraction of a cell that the
                      # decimated surface is pushed in/out along its normal by
                      # a fixed 3D value-noise field. The Disney renders get
                      # their "fluffy clods" from real grain-scale geometry;
                      # at our 5mm cells that scale is far below the mesh, so
                      # the nearest achievable thing is to dither the surface
                      # with a fixed ~1-2cm noise. Fixed in space, not per
                      # frame, so settled snow shimmers no more than before.
CLUMP_FREQ = 3.0      # noise frequency, cycles per cell (above the 5mm mesh
                      # scale, so it reads as grain rather than as lumps)
_NOISE = None         # lazily built fixed permutation + value table


def _noise3(p):
    """Deterministic trilinear value noise, p in cell units, out in [-1,1].
    Fixed table -> the same world point always gets the same value, so the
    relief is stable frame to frame even as the mesh is rebuilt."""
    global _NOISE
    if _NOISE is None:
        rng = np.random.default_rng(11)
        _NOISE = rng.random((64, 64, 64))
    i = np.floor(p).astype(np.int64)
    f = p - i
    f = f * f * (3 - 2 * f)  # smoothstep
    i0 = i % 64
    i1 = (i + 1) % 64
    n = _NOISE
    c000 = n[i0[:, 0], i0[:, 1], i0[:, 2]]; c100 = n[i1[:, 0], i0[:, 1], i0[:, 2]]
    c010 = n[i0[:, 0], i1[:, 1], i0[:, 2]]; c110 = n[i1[:, 0], i1[:, 1], i0[:, 2]]
    c001 = n[i0[:, 0], i0[:, 1], i1[:, 2]]; c101 = n[i1[:, 0], i0[:, 1], i1[:, 2]]
    c011 = n[i0[:, 0], i1[:, 1], i1[:, 2]]; c111 = n[i1[:, 0], i1[:, 1], i1[:, 2]]
    x00 = c000 + f[:, 0] * (c100 - c000); x10 = c010 + f[:, 0] * (c110 - c010)
    x01 = c001 + f[:, 0] * (c101 - c001); x11 = c011 + f[:, 0] * (c111 - c011)
    y0 = x00 + f[:, 1] * (x10 - x00); y1 = x01 + f[:, 1] * (x11 - x01)
    return (y0 + f[:, 2] * (y1 - y0)) * 2 - 1


def taubin_smooth(verts, faces, iters=SMOOTH_ITERS, lam=0.5, mu=-0.53):
    """Low-pass the mesh without the shrinkage a plain Laplacian causes.

    Marching cubes on a splatted particle field carries the particles' own
    sampling noise into the surface, which shimmers frame to frame even when
    the snow is barely moving. Taubin's alternating positive/negative pass
    removes that high-frequency component while preserving overall volume.
    """
    import scipy.sparse as sp
    n = len(verts)
    e = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    e = np.vstack([e, e[:, ::-1]])
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    deg = np.asarray(A.sum(1)).ravel()
    deg[deg == 0] = 1.0
    L = sp.diags(1.0 / deg) @ A
    v = verts.astype(np.float64)
    for _ in range(iters):
        v += lam * (L @ v - v)
        v += mu * (L @ v - v)
    return v.astype(np.float32)


def reconstruct(points, tree_colors_f32, cell, y_floor, iso):
    """-> (verts f32 (V,3), tris u32 (T,3), vcols u8 (V,3), spray_mask (N,))"""
    n_real = len(points)
    near = points[:, 1] < y_floor + MIRROR_BAND * cell
    mirrored = points[near].copy()
    mirrored[:, 1] = 2.0 * y_floor - mirrored[:, 1]
    allp = np.concatenate([points, mirrored])

    lo = allp.min(0) - PAD * cell
    idx = np.floor((allp - lo) / cell).astype(np.int64)
    shape = idx.max(0) + 1 + PAD
    field = np.zeros(shape, np.float32)
    np.add.at(field, (idx[:, 0], idx[:, 1], idx[:, 2]), 1.0)
    field = ndimage.gaussian_filter(field, SIGMA)

    # drop tiny isolated blobs; their particles fall through to the spray pass
    lbl, nlbl = ndimage.label(field > iso)
    if nlbl > 1:
        sizes = ndimage.sum_labels(np.ones_like(lbl), lbl, index=np.arange(1, nlbl + 1))
        small = np.isin(lbl, np.nonzero(sizes < MIN_COMPONENT)[0] + 1)
        field[small] = 0.0

    # loose powder: everything the surface will not represent (with a small
    # dead band below iso, see SPRAY_VAL_FRAC), and only where it is clear of
    # the meshed snow -- see SPRAY_ISOLATION
    ridx = idx[:n_real]
    val = field[ridx[:, 0], ridx[:, 1], ridx[:, 2]]
    spray_mask = val < iso * SPRAY_VAL_FRAC
    dense = val >= iso
    if dense.any() and spray_mask.any():
        dist, _ = cKDTree(points[dense]).query(points[spray_mask], k=1, workers=-1)
        keep = dist > SPRAY_ISOLATION * cell
        sel = np.nonzero(spray_mask)[0]
        spray_mask = np.zeros(n_real, bool)
        spray_mask[sel[keep]] = True

    verts, faces, _, _ = measure.marching_cubes(field, level=iso, spacing=(cell, cell, cell))
    verts = (verts + lo).astype(np.float32)

    # clip the mirrored underside: faces entirely below the resting floor are
    # hidden by the ground plane anyway
    below = verts[:, 1] < y_floor - 0.1 * cell
    keep = ~below[faces].all(axis=1)
    faces = faces[keep]
    used = np.unique(faces)
    remap = np.zeros(len(verts), np.int64)
    remap[used] = np.arange(len(used))
    verts, faces = verts[used], remap[faces]

    if len(faces) > TARGET_TRIS:
        reduction = 1.0 - TARGET_TRIS / len(faces)
        verts, faces = fast_simplification.simplify(verts, faces, reduction)
        verts = verts.astype(np.float32)
    faces = np.asarray(faces, np.uint32)
    if SMOOTH_ITERS and len(faces):
        verts = taubin_smooth(verts, faces.astype(np.int64))

    # bake the fluffy clods: push the decimated surface along its own normal
    # by the fixed noise field. Done *after* smoothing so the high-frequency
    # component survives (Taubin would otherwise iron exactly this out).
    if CLUMP and len(faces):
        v = verts.astype(np.float64)
        n = np.zeros_like(v)
        tris = v[faces.astype(np.int64)]
        fn = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        for c in range(3):
            np.add.at(n, faces[:, c].astype(np.int64), fn)
        ln = np.linalg.norm(n, axis=1)
        ln[ln == 0] = 1.0
        n /= ln[:, None]
        disp = CLUMP * cell * _noise3(verts * (CLUMP_FREQ / cell))
        verts = (v + n * disp[:, None]).astype(np.float32)

    tree = cKDTree(points)
    dist, nn = tree.query(verts, k=COLOR_K, workers=-1)
    # inverse-cube distance weighting: smooths noise among same-letter
    # neighbors but keeps the blend zone where two letters touch narrow,
    # instead of a flat mean smearing e.g. blue+red into a magenta seam
    w = 1.0 / (dist ** 3 + 1e-9)
    w /= w.sum(axis=1, keepdims=True)
    vcols = (tree_colors_f32[nn] * w[:, :, None]).sum(axis=1)
    gray = vcols.mean(axis=1, keepdims=True)
    vcols = gray + (vcols - gray) * SAT_BOOST
    vcols = np.clip(np.round(vcols), 0, 255).astype(np.uint8)
    return verts, faces, vcols, spray_mask


def pad2(b: bytes) -> bytes:
    return b + (b"\0" if len(b) & 1 else b"")


def bake(npz_path: str, out_dir: str):
    raw = np.load(npz_path)
    frames = raw["frames"]            # (F, N, 3) float32
    pcolors = raw["colors"].astype(np.float32)  # (N, 3)
    fps = float(raw["fps"])
    F = len(frames)

    spacing = float(np.median(cKDTree(frames[0]).query(frames[0][::17], k=2)[0][:, 1]))
    cell = CELL_PER_SPACING * spacing
    # resting height of the snow floor: the sim's ground boundary acts a
    # couple of *sim* grid cells above the visual ground plane, so measure it
    # from where the settled particles actually sit in the last frame
    y_floor = float(np.percentile(frames[-1][:, 1], 0.5))

    # One absolute isolevel for the whole clip. Deriving it per frame from
    # that frame's own median density (the obvious thing) makes the whole
    # surface breathe: the median drifts ~14% over the clip and jumps up to
    # 11% between consecutive frames, so the isosurface inflates and deflates
    # every rebuild and the snow visibly shimmers even when barely moving. A
    # constant density threshold is also the physically consistent choice --
    # the same snow density should always land on the same surface.
    interiors = []
    for f in range(0, F, max(1, F // 8)):
        pts = frames[f]
        lo = pts.min(0) - PAD * cell
        idx = np.floor((pts - lo) / cell).astype(np.int64)
        fld = np.zeros(idx.max(0) + 1 + PAD, np.float32)
        np.add.at(fld, (idx[:, 0], idx[:, 1], idx[:, 2]), 1.0)
        fld = ndimage.gaussian_filter(fld, SIGMA)
        interiors.append(float(np.median(fld[fld > fld.max() * 0.2])))
    iso = float(np.median(interiors)) * ISO_FRAC
    print(f"median particle spacing {spacing:.4f} -> grid cell {cell:.4f}, "
          f"snow floor y={y_floor:.4f}, fixed iso={iso:.4f} "
          f"(per-frame interior spread {min(interiors):.3f}..{max(interiors):.3f})")

    mins = frames.min(axis=(0, 1)).astype(np.float64) - 2 * cell
    maxs = frames.max(axis=(0, 1)).astype(np.float64) + 2 * cell
    span = np.where(maxs - mins < 1e-9, 1.0, maxs - mins)
    rng = np.random.default_rng(5)
    N = frames.shape[1]
    # stable spray identity: eligibility and size are functions of the
    # particle id, so the same physical grains render every frame
    spray_eligible = rng.random(N) < SPRAY_FRAC
    spray_size = rng.integers(0, 256, N).astype(np.uint8)

    def quant(p):
        return np.round((p - mins) / span * 32767.0).astype("<i2")

    blobs, entries, overlaps = [], [], []
    prev_pts, prev_spray = None, None
    max_v = max_t = max_s = 0
    for f in range(F):
        pts = frames[f]
        if prev_pts is not None:
            moved = np.percentile(np.abs(pts - prev_pts).max(axis=1), 99)
            if moved < REBUILD_P99 * cell:
                entries.append({"same": 1})
                continue
        prev_pts = pts
        verts, faces, vcols, spray_mask = reconstruct(pts, pcolors, cell, y_floor, iso)
        assert len(verts) < 65536, f"frame {f}: {len(verts)} verts overflow uint16 indices"

        spray_idx = np.nonzero(spray_mask & spray_eligible)[0][:SPRAY_MAX]
        spos = pts[spray_idx]
        scol = np.clip(pcolors[spray_idx], 0, 255).astype(np.uint8)
        ssize = spray_size[spray_idx]

        blob = (pad2(quant(verts).tobytes()) + pad2(vcols.tobytes())
                + pad2(faces.astype("<u2").tobytes())
                + pad2(quant(spos).tobytes()) + pad2(scol.tobytes())
                + pad2(ssize.tobytes()))
        blobs.append(blob)
        if entries and prev_spray is not None and len(spray_idx) and len(prev_spray):
            inter = len(np.intersect1d(spray_idx, prev_spray, assume_unique=True))
            overlaps.append(inter / max(len(spray_idx), len(prev_spray)))
        prev_spray = spray_idx
        entries.append({"v": len(verts), "t": len(faces), "s": len(spray_idx)})
        max_v, max_t, max_s = max(max_v, len(verts)), max(max_t, len(faces)), max(max_s, len(spray_idx))
        if f % 10 == 0:
            print(f"  frame {f}/{F}: {len(verts)} verts {len(faces)} tris {len(spray_idx)} spray")

    os.makedirs(out_dir, exist_ok=True)
    bin_path = os.path.join(out_dir, "surface.bin.gz")
    with open(bin_path, "wb") as fh:
        fh.write(gzip.compress(b"".join(blobs), 9))
    meta = {
        "fps": fps,
        "numFrames": F,
        "bounds": {"min": mins.tolist(), "max": maxs.tolist()},
        "maxVerts": max_v,
        "maxTris": max_t,
        "maxSpray": max_s,
        "sprayRadius": spacing * SPRAY_RADIUS,
        "frames": entries,
    }
    with open(os.path.join(out_dir, "surface.json"), "w") as fh:
        json.dump(meta, fh, separators=(",", ":"))
    uniq = sum(1 for e in entries if "v" in e)
    if overlaps:
        print(f"spray identity overlap between consecutive keyframes: "
              f"median {np.median(overlaps):.2f} min {min(overlaps):.2f} (1.0 = no flicker)")
    print(
        f"{out_dir}: {F} frames ({uniq} unique meshes), max {max_v} verts / {max_t} tris / "
        f"{max_s} spray, surface.bin.gz={os.path.getsize(bin_path) / 1e6:.2f}MB"
    )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    bake(sys.argv[1], sys.argv[2])
