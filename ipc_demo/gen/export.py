"""Headless per-frame recorder for libuipc simulations.

Tracks geometry slots of interest, captures vertex positions every frame,
and saves everything (topology once + per-frame positions) into a compressed
.npz that bake.py later converts into the web playback format.
"""

import numpy as np

import uipc
import uipc.builtin as builtin


class Recorder:
    """Collects per-frame vertex positions for a set of geometry slots."""

    def __init__(self, fps: float):
        self.fps = fps
        self.entries = []  # list of dicts: name, slot, kind, indices, frames

    def track(self, name: str, geo_slot, kind: str, static: bool = False):
        """Register a geometry slot to record.

        kind: "tri" (tet/shell mesh rendered as surface triangles)
              or "rod" (line mesh rendered as fat lines).
        static: object never moves — record frame 0 only.
        """
        assert kind in ("tri", "rod")
        self.entries.append(
            {"name": name, "slot": geo_slot, "kind": kind, "static": static,
             "indices": None, "frames": []}
        )

    def _extract_topology(self, entry):
        geo = entry["slot"].geometry()
        if entry["kind"] == "tri":
            tris = np.array(uipc.view(geo.triangles().topo())).reshape(-1, 3)
            is_surf_slot = geo.triangles().find(builtin.is_surf)
            if is_surf_slot is not None:
                is_surf = np.array(uipc.view(is_surf_slot)).reshape(-1)
                tris = tris[is_surf == 1]
            entry["indices"] = tris.astype(np.int32)
        else:
            edges = np.array(uipc.view(geo.edges().topo())).reshape(-1, 2)
            entry["indices"] = edges.astype(np.int32)

    def capture(self):
        """Call after world.advance() + world.retrieve() each frame."""
        for entry in self.entries:
            if entry["indices"] is None:
                self._extract_topology(entry)
            if entry["static"] and entry["frames"]:
                continue
            geo = entry["slot"].geometry()
            pos = np.array(uipc.view(geo.positions()), dtype=np.float32).reshape(-1, 3)
            entry["frames"].append(pos)

    def save(self, path: str):
        data = {"fps": np.float32(self.fps), "count": np.int32(len(self.entries))}
        for i, entry in enumerate(self.entries):
            frames = np.stack(entry["frames"])  # (F, N, 3)
            assert np.isfinite(frames).all(), f"NaN/Inf in '{entry['name']}'"
            data[f"obj{i}_name"] = np.str_(entry["name"])
            data[f"obj{i}_kind"] = np.str_(entry["kind"])
            data[f"obj{i}_static"] = np.bool_(entry["static"])
            data[f"obj{i}_indices"] = entry["indices"]
            data[f"obj{i}_frames"] = frames
        np.savez_compressed(path, **data)
        total = sum(e["frames"][0].shape[0] for e in self.entries)
        nf = len(self.entries[0]["frames"])
        print(f"saved {path}: {len(self.entries)} objects, {total} verts, {nf} frames")

    def report(self):
        """Print simple end-of-run sanity stats (motion should settle)."""
        for entry in self.entries:
            frames = np.stack(entry["frames"])
            tail_motion = np.abs(frames[-1] - frames[-2]).max() * self.fps if len(frames) > 1 else 0.0
            print(
                f"  {entry['name']:20s} kind={entry['kind']} verts={frames.shape[1]:5d} "
                f"y_range=[{frames[..., 1].min():+.3f}, {frames[..., 1].max():+.3f}] "
                f"final_speed~{tail_motion:.4f} m/s"
            )
