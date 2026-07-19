"""Scene 3: the letters G-O-O-G-L-E as soft voxel meshes, dropped into a pile.

Each letter is a pixel-font glyph extruded into voxels and tetrahedralized
(Kuhn subdivision), simulated as a squishy StableNeoHookean body in Google
brand colors, falling and squeezing against the ground and each other.

Run:  source env.sh && python scenes/google_pile.py   (from ipc_demo/gen)
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uipc
from uipc import Logger, Vector3
from uipc.core import Engine, World, Scene
from uipc.geometry import (
    tetmesh,
    ground,
    label_surface,
    label_triangle_orient,
    flip_inward_triangles,
)
from uipc.constitution import StableNeoHookean, ElasticModuli
from uipc.unit import kPa

from export import Recorder
from voxmesh import voxels_to_tetmesh, letter_voxels

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw")
os.makedirs(OUT, exist_ok=True)

FPS = 60.0
DT = 1.0 / FPS
FRAMES = 360  # 6 seconds: letters land one after another

Logger.set_level(Logger.Level.Warn)

engine = Engine("cuda", os.path.join(OUT, "google_pile_ws"))
world = World(engine)

config = Scene.default_config()
config["dt"] = DT
config["gravity"] = [[0.0], [-9.8], [0.0]]
config["contact"]["friction"]["enable"] = True
scene = Scene(config)

scene.contact_tabular().default_model(0.6, 1e9)

snh = StableNeoHookean()
squishy = ElasticModuli.youngs_poisson(70 * kPa, 0.48)

recorder = Recorder(FPS)


def rot_matrix(angle_deg, axis):
    axis = np.asarray(axis, dtype=np.float64)
    axis /= np.linalg.norm(axis)
    a = np.deg2rad(angle_deg)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * (K @ K)


VOX = 0.055  # voxel size in meters -> letters ~0.28m wide, 0.39m tall

GOOGLE = [
    ("G1", "G", "#4285F4"),
    ("O1", "O", "#EA4335"),
    ("O2", "O", "#FBBC05"),
    ("G2", "G", "#4285F4"),
    ("L1", "L", "#34A853"),
    ("E1", "E", "#EA4335"),
]

# tight slots so landed letters lean on their neighbors, thick (depth 4) so
# they stay upright, low staggered drops so they land in sequence readably
x_slots = np.linspace(-0.875, 0.875, 6)
for idx, (name, ch, color) in enumerate(GOOGLE):
    Vs, Ts, _ = voxels_to_tetmesh(letter_voxels(ch, depth=4), VOX)
    center = (Vs.max(0) + Vs.min(0)) / 2
    pos = np.array([x_slots[idx], 0.32 + 0.15 * idx, 0.0])
    Vs = (Vs - center) + pos

    mesh = tetmesh(Vs, Ts)
    label_surface(mesh)
    label_triangle_orient(mesh)
    mesh = flip_inward_triangles(mesh)
    snh.apply_to(mesh, squishy, mass_density=800.0)
    obj = scene.objects().create(name)
    slot, _ = obj.geometries().create(mesh)
    recorder.track(name, slot, "tri", color=color)
    print(f"  {name}: {len(Vs)} verts, {len(Ts)} tets, min_y={Vs[:,1].min():.3f}")

ground_obj = scene.objects().create("ground")
ground_obj.geometries().create(ground(0.0, Vector3.UnitY()))

world.init(scene)

for f in range(FRAMES):
    world.advance()
    world.retrieve()
    recorder.capture()
    if (f + 1) % 60 == 0:
        print(f"frame {f + 1}/{FRAMES}")

recorder.report()
recorder.save(os.path.join(OUT, "google_pile.npz"))
