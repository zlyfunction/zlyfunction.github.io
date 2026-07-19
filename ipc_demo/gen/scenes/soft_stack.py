"""Scene 1: soft bodies piling up and squishing against each other.

Soft balls, bunnies and torus links (StableNeoHookean tet meshes) dropped one
above another so they collide, stack and squeeze — showcasing IPC's guaranteed
penetration-free frictional contact between many deformable bodies.

Run:  source env.sh && python scenes/soft_stack.py   (from ipc_demo/gen)
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uipc
from uipc import Logger, Vector3
from uipc.core import Engine, World, Scene
from uipc.geometry import (
    SimplicialComplexIO,
    ground,
    label_surface,
    label_triangle_orient,
    flip_inward_triangles,
)
from uipc.constitution import StableNeoHookean, ElasticModuli
from uipc.unit import kPa

from export import Recorder

ASSETS = os.path.expanduser("~/Toolchain/libuipc/assets/sim_data/tetmesh")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw")
os.makedirs(OUT, exist_ok=True)

FPS = 60.0
DT = 1.0 / FPS
FRAMES = 300  # 5 seconds

Logger.set_level(Logger.Level.Warn)

engine = Engine("cuda", os.path.join(OUT, "soft_stack_ws"))
world = World(engine)

config = Scene.default_config()
config["dt"] = DT
config["gravity"] = [[0.0], [-9.8], [0.0]]
config["contact"]["friction"]["enable"] = True
scene = Scene(config)

# friction ratio, contact resistance
scene.contact_tabular().default_model(0.4, 1e9)

snh = StableNeoHookean()
soft = ElasticModuli.youngs_poisson(40 * kPa, 0.48)   # squishy
firm = ElasticModuli.youngs_poisson(120 * kPa, 0.48)  # a bit firmer

recorder = Recorder(FPS)


def rot_matrix(angle_deg, axis):
    """Rodrigues rotation matrix."""
    axis = np.asarray(axis, dtype=np.float64)
    axis /= np.linalg.norm(axis)
    a = np.deg2rad(angle_deg)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * (K @ K)


def add_body(name, mesh_file, half_extent, pos, angle_deg, axis, moduli):
    """Load a tet mesh, normalize to given half-extent, place at pos."""
    io = SimplicialComplexIO()
    mesh = io.read(mesh_file)
    p = uipc.view(mesh.positions())  # (N,3,1) float64, writable
    flat = p.reshape(-1, 3)
    center = (flat.max(0) + flat.min(0)) / 2
    scale = half_extent / np.abs(flat - center).max()
    R = rot_matrix(angle_deg, axis)
    flat[:] = (flat - center) * scale @ R.T + np.asarray(pos)

    label_surface(mesh)
    label_triangle_orient(mesh)
    mesh = flip_inward_triangles(mesh)
    snh.apply_to(mesh, moduli, mass_density=1000.0)
    obj = scene.objects().create(name)
    slot, _ = obj.geometries().create(mesh)
    recorder.track(name, slot, "tri")
    lo = flat.min(0)
    print(f"  {name}: min_y={lo[1]:.3f}")


ball = f"{ASSETS}/ball.msh"
bunny = f"{ASSETS}/bunny0.msh"
link = f"{ASSETS}/link.msh"

# Staggered drop heights; bounding spheres never overlap at t=0.
add_body("bunny", bunny, 0.34, [0.00, 0.36, 0.00], -15, [0, 1, 0], firm)
add_body("ball_a", ball, 0.22, [0.06, 1.00, 0.04], 0, [0, 1, 0], soft)
add_body("link_a", link, 0.30, [-0.05, 1.65, -0.03], 90, [1, 0.2, 0], soft)
add_body("ball_b", ball, 0.17, [0.10, 2.25, -0.07], 0, [0, 1, 0], firm)
add_body("link_b", link, 0.26, [-0.03, 2.85, 0.06], 60, [0.3, 0, 1], soft)

ground_obj = scene.objects().create("ground")
ground_obj.geometries().create(ground(0.0, Vector3.UnitY()))

world.init(scene)

for f in range(FRAMES):
    world.advance()
    world.retrieve()
    recorder.capture()
    if (f + 1) % 30 == 0:
        print(f"frame {f + 1}/{FRAMES}")

recorder.report()
recorder.save(os.path.join(OUT, "soft_stack.npz"))
