"""Bake raw .npz recordings into compact web playback assets.

Input : gen/raw/<scene>.npz          (from export.Recorder)
Output: data/<scene>/mesh.json       topology + metadata (+ static object positions)
        data/<scene>/frames.bin.gz   gzip'd Int16-quantized per-frame positions

frames.bin layout (before gzip): frame-major, little-endian int16,
delta-encoded: frame 0 holds absolute quantized values, every later frame
holds the (wrapping) int16 difference from the previous frame — smooth motion
makes deltas tiny, so gzip compresses far better. The viewer integrates the
deltas back into absolute values once, right after decompression.
  For each kept frame: for each NON-static object (in mesh.json order): N*3 int16.
Dequantize: pos = min + (q / 32767) * (max - min), per-axis over the whole clip.
Static objects appear once in mesh.json as a quantized "positions" array.

Usage: python bake.py raw/soft_stack.npz ../data/soft_stack [--subsample 2]
"""

import gzip
import json
import os
import sys

import numpy as np


def bake(npz_path: str, out_dir: str, subsample: int = 2):
    raw = np.load(npz_path)
    count = int(raw["count"])
    fps = float(raw["fps"]) / subsample

    objects = []
    for i in range(count):
        static = bool(raw[f"obj{i}_static"]) if f"obj{i}_static" in raw else False
        frames = raw[f"obj{i}_frames"]
        objects.append(
            {
                "name": str(raw[f"obj{i}_name"]),
                "kind": str(raw[f"obj{i}_kind"]),
                "static": static,
                "indices": raw[f"obj{i}_indices"],
                "frames": frames if static else frames[::subsample],
                "color": str(raw[f"obj{i}_color"]) if f"obj{i}_color" in raw else None,
                "opacity": float(raw[f"obj{i}_opacity"]) if f"obj{i}_opacity" in raw else None,
                "groups": raw[f"obj{i}_groups"].tolist() if f"obj{i}_groups" in raw else None,
                "gcolors": raw[f"obj{i}_gcolors"].tolist() if f"obj{i}_gcolors" in raw else None,
            }
        )

    moving = [o for o in objects if not o["static"]]
    num_frames = moving[0]["frames"].shape[0]
    assert all(o["frames"].shape[0] == num_frames for o in moving)

    # Global per-axis bounds over the whole animation (all objects)
    mins = np.min([o["frames"].min(axis=(0, 1)) for o in objects], axis=0).astype(np.float64)
    maxs = np.max([o["frames"].max(axis=(0, 1)) for o in objects], axis=0).astype(np.float64)
    span = np.where(maxs - mins < 1e-9, 1.0, maxs - mins)

    def quantize(p):
        return np.round((p.astype(np.float64) - mins) / span * 32767.0).astype("<i2")

    os.makedirs(out_dir, exist_ok=True)

    # frames.bin: frame-major; delta-encode across frames for compressibility
    quantized = [quantize(o["frames"]) for o in moving]  # per object: (F, N, 3) int16
    chunks = []
    for f in range(num_frames):
        for q in quantized:
            block = q[f] if f == 0 else (q[f].view(np.uint16) - q[f - 1].view(np.uint16)).astype("<u2")
            chunks.append(block.astype("<i2", copy=False).tobytes() if f == 0 else block.tobytes())
    bin_path = os.path.join(out_dir, "frames.bin.gz")
    with open(bin_path, "wb") as fh:
        fh.write(gzip.compress(b"".join(chunks), 9))

    meta = {
        "fps": fps,
        "numFrames": num_frames,
        "bounds": {"min": mins.tolist(), "max": maxs.tolist()},
        "objects": [
            {
                "name": o["name"],
                "kind": o["kind"],
                "static": o["static"],
                "numVerts": int(o["frames"].shape[1]),
                "indices": o["indices"].reshape(-1).tolist(),
                **({"positions": quantize(o["frames"][0]).reshape(-1).tolist()} if o["static"] else {}),
                **({"color": o["color"]} if o["color"] else {}),
                **({"opacity": o["opacity"]} if o["opacity"] is not None else {}),
                **({"groups": o["groups"], "groupColors": o["gcolors"]} if o["groups"] else {}),
            }
            for o in objects
        ],
    }
    json_path = os.path.join(out_dir, "mesh.json")
    with open(json_path, "w") as fh:
        json.dump(meta, fh, separators=(",", ":"))

    total = sum(o["frames"].shape[1] for o in objects)
    print(
        f"{out_dir}: {len(objects)} objects ({len(moving)} moving), {total} verts, "
        f"{num_frames} frames @ {fps:g}fps, frames.bin.gz={os.path.getsize(bin_path) / 1e6:.2f}MB "
        f"mesh.json={os.path.getsize(json_path) / 1e3:.0f}KB"
    )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    sub = int(sys.argv[sys.argv.index("--subsample") + 1]) if "--subsample" in sys.argv else 2
    bake(sys.argv[1], sys.argv[2], sub)
