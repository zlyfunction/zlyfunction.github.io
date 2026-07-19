"""Scene 4: a jelly YouTube play button bouncing on a cloth trampoline.

The play button is a rounded-rect voxel tet mesh (soft StableNeoHookean, red,
with the white triangle painted as a second surface-color group). It drops
onto a square cloth trampoline (StrainLimitingBaraffWitkinShell) pinned at its
boundary, bounces and jiggles — showcasing IPC coupling between a volumetric
soft body and a codimensional shell.

Run:  source env.sh && python scenes/play_trampoline.py   (from ipc_demo/gen)
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uipc
from uipc import Logger, Vector3
import uipc.builtin as builtin
from uipc.core import Engine, World, Scene
from uipc.geometry import (
    tetmesh,
    trimesh,
    ground,
    label_surface,
    label_triangle_orient,
    flip_inward_triangles,
    mesh_partition,
)
from uipc.constitution import (
    StableNeoHookean,
    ElasticModuli,
    StrainLimitingBaraffWitkinShell,
    DiscreteShellBending,
    ElasticModuli2D,
)
from uipc.unit import kPa, MPa

from export import Recorder
from voxmesh import voxels_to_tetmesh, play_button_voxels

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw")
os.makedirs(OUT, exist_ok=True)

FPS = 60.0
DT = 1.0 / FPS
FRAMES = 360  # 6 seconds of bouncing

Logger.set_level(Logger.Level.Warn)

engine = Engine("cuda", os.path.join(OUT, "play_trampoline_ws"))
world = World(engine)

config = Scene.default_config()
config["dt"] = DT
config["gravity"] = [[0.0], [-9.8], [0.0]]
config["contact"]["friction"]["enable"] = True
config["contact"]["d_hat"] = 0.005
scene = Scene(config)

scene.contact_tabular().default_model(0.3, 1e9)

recorder = Recorder(FPS)

# ----------------------------------------------------------------------
# Jelly play button (voxel rounded rect + white triangle color group)
# ----------------------------------------------------------------------
VOX = 0.036
voxels, white_vox = play_button_voxels(w=15, h=11, depth=3, corner=2)
Vs, Ts, node_id = voxels_to_tetmesh(voxels, 1.0)  # integer coords first

# white front-face node set: the 4 nodes of each white voxel's front face
white_nodes = set()
for (i, j, k) in white_vox:
    for di in (0, 1):
        for dj in (0, 1):
            n = node_id.get((i + di, j + dj, k + 1))
            if n is not None:
                white_nodes.add(n)

center = (Vs.max(0) + Vs.min(0)) / 2
Vs = (Vs - center) * VOX
# tilt slightly and lift above the trampoline
a = np.deg2rad(-6)  # negative: back edge dips first so it lands play-icon-up
Rx = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
Vs = Vs @ Rx.T + np.array([0.0, 1.25, 0.0])

mesh = tetmesh(Vs, Ts)
label_surface(mesh)
label_triangle_orient(mesh)
mesh = flip_inward_triangles(mesh)

# split surface triangles into white (play icon) / red groups
tris = np.array(uipc.view(mesh.triangles().topo())).reshape(-1, 3)
is_surf = np.array(uipc.view(mesh.triangles().find(builtin.is_surf))).reshape(-1)
surf = tris[is_surf == 1]
white_mask = np.array([all(v in white_nodes for v in t) for t in surf])
groups = [surf[~white_mask], surf[white_mask]]

snh = StableNeoHookean()
snh.apply_to(mesh, ElasticModuli.youngs_poisson(25 * kPa, 0.47), mass_density=400.0)
btn_obj = scene.objects().create("play_button")
btn_slot, _ = btn_obj.geometries().create(mesh)
recorder.track("play_button", btn_slot, "tri",
               groups=groups, group_colors=["#FF0000", "#FFFFFF"])
print(f"  play_button: {len(Vs)} verts, {len(Ts)} tets, "
      f"{len(groups[0])} red + {len(groups[1])} white surface tris")

# ----------------------------------------------------------------------
# Cloth trampoline, boundary pinned
# ----------------------------------------------------------------------
N = 36
SIZE = 1.3
HEIGHT = 0.6
xs = np.linspace(-SIZE / 2, SIZE / 2, N + 1)
gx, gz = np.meshgrid(xs, xs, indexing="ij")
CVs = np.stack([gx.ravel(), np.full(gx.size, HEIGHT), gz.ravel()], axis=1)
CFs = []
for i in range(N):
    for j in range(N):
        a0 = i * (N + 1) + j
        b0 = a0 + 1
        c0 = a0 + (N + 1)
        d0 = c0 + 1
        if (i + j) % 2 == 0:
            CFs += [[a0, c0, b0], [b0, c0, d0]]
        else:
            CFs += [[a0, c0, d0], [a0, d0, b0]]
CFs = np.array(CFs, dtype=np.int32)

cloth = trimesh(CVs, CFs)
label_surface(cloth)
slbws = StrainLimitingBaraffWitkinShell()
dsb = DiscreteShellBending()
slbws.apply_to(cloth, moduli=ElasticModuli2D.youngs_poisson(150 * kPa, 0.49),
               mass_density=200.0, thickness=0.001)
dsb.apply_to(cloth, bending_stiffness=5.0)
mesh_partition(cloth)

is_fixed = cloth.vertices().find(builtin.is_fixed)
fixed_view = uipc.view(is_fixed).reshape(-1)
border = (np.abs(np.abs(CVs[:, 0]) - SIZE / 2) < 1e-6) | (np.abs(np.abs(CVs[:, 2]) - SIZE / 2) < 1e-6)
fixed_view[border] = 1

cloth_obj = scene.objects().create("trampoline")
cloth_slot, _ = cloth_obj.geometries().create(cloth)
recorder.track("trampoline", cloth_slot, "tri", color="#c3cad4", opacity=0.75)
print(f"  trampoline: {len(CVs)} verts, {len(CFs)} tris, {border.sum()} pinned")

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
recorder.save(os.path.join(OUT, "play_trampoline.npz"))
