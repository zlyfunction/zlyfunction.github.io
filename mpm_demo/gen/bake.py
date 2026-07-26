"""Bake raw sim.py output into compact web playback assets.

Input : gen/raw/snowball_hill.npz   (from sim.py: frames, colors, ground_verts/tris)
Output: ../data/<scene>/mesh.json         topology + metadata + static ground + colors
        ../data/<scene>/frames.bin.gz     gzip'd Int16-quantized per-frame particle positions

Same delta-encoding trick as the IPC demo's bake.py (see ipc_demo/gen/bake.py):
frame 0 holds absolute quantized positions, every later frame holds the
(wrapping) int16 delta from the previous frame -- smooth motion makes deltas
tiny, so gzip compresses far better. The viewer integrates deltas back into
absolute positions once, right after decompression.
Dequantize: pos = min + (q / 32767) * (max - min), per-axis over the whole clip.

Usage: python bake.py raw/snowball_hill.npz ../data/snowball_hill [--subsample 1]
"""
import gzip
import json
import os
import sys

import numpy as np


def bake(npz_path: str, out_dir: str, subsample: int = 1, max_particles: int = None, max_frames: int = None):
    raw = np.load(npz_path)
    frames = raw["frames"][::subsample]          # (F, N, 3) float32
    colors = raw["colors"]                        # (N, 3) uint8
    ground_verts = raw["ground_verts"]             # (Gv, 3) float32
    ground_tris = raw["ground_tris"]               # (Gt, 3) int32
    fps = float(raw["fps"]) / subsample

    if max_frames:
        frames = frames[:max_frames]

    if max_particles and frames.shape[1] > max_particles:
        rng = np.random.default_rng(3)
        keep = rng.choice(frames.shape[1], size=max_particles, replace=False)
        keep.sort()
        frames = frames[:, keep, :]
        colors = colors[keep]

    num_frames, n_particles, _ = frames.shape

    # per-axis bounds over the whole clip (ball only -- ground is separate)
    mins = frames.min(axis=(0, 1)).astype(np.float64)
    maxs = frames.max(axis=(0, 1)).astype(np.float64)
    span = np.where(maxs - mins < 1e-9, 1.0, maxs - mins)

    def quantize(p):
        return np.round((p.astype(np.float64) - mins) / span * 32767.0).astype("<i2")

    gmins = ground_verts.min(axis=0).astype(np.float64)
    gmaxs = ground_verts.max(axis=0).astype(np.float64)
    gspan = np.where(gmaxs - gmins < 1e-9, 1.0, gmaxs - gmins)
    ground_q = np.round((ground_verts.astype(np.float64) - gmins) / gspan * 32767.0).astype("<i2")

    os.makedirs(out_dir, exist_ok=True)

    quantized = quantize(frames)  # (F, N, 3) int16
    chunks = []
    for f in range(num_frames):
        block = quantized[f] if f == 0 else (
            quantized[f].view(np.uint16) - quantized[f - 1].view(np.uint16)
        ).astype("<u2")
        chunks.append(block.astype("<i2", copy=False).tobytes() if f == 0 else block.tobytes())
    bin_path = os.path.join(out_dir, "frames.bin.gz")
    with open(bin_path, "wb") as fh:
        fh.write(gzip.compress(b"".join(chunks), 9))

    meta = {
        "fps": fps,
        "numFrames": num_frames,
        "numParticles": n_particles,
        "bounds": {"min": mins.tolist(), "max": maxs.tolist()},
        "colors": colors.reshape(-1).tolist(),
        "ground": {
            "bounds": {"min": gmins.tolist(), "max": gmaxs.tolist()},
            "positions": ground_q.reshape(-1).tolist(),
            "indices": ground_tris.reshape(-1).tolist(),
        },
    }
    json_path = os.path.join(out_dir, "mesh.json")
    with open(json_path, "w") as fh:
        json.dump(meta, fh, separators=(",", ":"))

    print(
        f"{out_dir}: {n_particles} particles, {num_frames} frames @ {fps:g}fps, "
        f"{len(ground_verts)} ground verts / {len(ground_tris)} tris, "
        f"frames.bin.gz={os.path.getsize(bin_path) / 1e6:.2f}MB mesh.json={os.path.getsize(json_path) / 1e3:.0f}KB"
    )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    sub = int(sys.argv[sys.argv.index("--subsample") + 1]) if "--subsample" in sys.argv else 1
    maxp = int(sys.argv[sys.argv.index("--max-particles") + 1]) if "--max-particles" in sys.argv else None
    maxf = int(sys.argv[sys.argv.index("--max-frames") + 1]) if "--max-frames" in sys.argv else None
    bake(sys.argv[1], sys.argv[2], sub, maxp, maxf)
