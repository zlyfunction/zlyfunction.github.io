"""Scene 2: codimensional rods draping over a fixed ball.

A grid of 1D elastic rods (HookeanSpring + KirchhoffRodBending) falls onto a
fixed sphere and the ground, bending, sliding and piling on each other —
showcasing IPC contact for codimension-2 geometry (curves), where classic
mesh-based collision handling struggles.

Run:  python scenes/rod_tangle.py   (from ipc_demo/gen, inside the venv,
      with LD_LIBRARY_PATH set — see env.sh)
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uipc
from uipc import Logger, Transform, Vector3
import uipc.builtin as builtin
from uipc.core import Engine, World, Scene
from uipc.geometry import (
    SimplicialComplexIO,
    ground,
    label_surface,
    label_triangle_orient,
    flip_inward_triangles,
    linemesh,
)
from uipc.constitution import (
    HookeanSpring,
    KirchhoffRodBending,
    AffineBodyConstitution,
)
from uipc.unit import MPa

from export import Recorder

ASSETS = os.path.expanduser("~/Toolchain/libuipc/assets/sim_data/tetmesh")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw")
os.makedirs(OUT, exist_ok=True)

FPS = 60.0
DT = 1.0 / FPS
FRAMES = 300  # 5 seconds

Logger.set_level(Logger.Level.Warn)

engine = Engine("cuda", os.path.join(OUT, "rod_tangle_ws"))
world = World(engine)

config = Scene.default_config()
config["dt"] = DT
config["gravity"] = [[0.0], [-9.8], [0.0]]
config["contact"]["friction"]["enable"] = True
config["contact"]["d_hat"] = 0.005
scene = Scene(config)

# friction ratio, contact resistance
scene.contact_tabular().default_model(0.5, 1e9)

hs = HookeanSpring()
krb = KirchhoffRodBending()
abd = AffineBodyConstitution()

recorder = Recorder(FPS)

# ----------------------------------------------------------------------
# Rods: horizontal strands in a criss-cross pattern above the ball
# ----------------------------------------------------------------------
N_SEG = 48
ROD_LEN = 1.5

rod_obj = scene.objects().create("rods")


def add_rod(name, y, direction, offset):
    t = np.linspace(-ROD_LEN / 2, ROD_LEN / 2, N_SEG + 1)
    Vs = np.zeros((N_SEG + 1, 3))
    if direction == "x":
        Vs[:, 0] = t
        Vs[:, 2] = offset
    else:
        Vs[:, 2] = t
        Vs[:, 0] = offset
    Vs[:, 1] = y
    Es = np.stack([np.arange(N_SEG), np.arange(N_SEG) + 1], axis=1).astype(np.int32)

    mesh = linemesh(Vs, Es)
    label_surface(mesh)
    hs.apply_to(mesh, 40e3)
    krb.apply_to(mesh, 5e2)
    slot, _ = rod_obj.geometries().create(mesh)
    recorder.track(name, slot, "rod")


# criss-cross layers right above the ball top (0.75), 2cm apart
spacings = np.linspace(-0.21, 0.21, 7)
for i, off in enumerate(spacings):
    add_rod(f"rod_x{i}", 0.80 + 0.020 * i, "x", off)
for i, off in enumerate(spacings):
    add_rod(f"rod_z{i}", 0.97 + 0.020 * i, "z", off)

# ----------------------------------------------------------------------
# Fixed ball obstacle + ground
# ----------------------------------------------------------------------
io = SimplicialComplexIO()
ball = io.read(f"{ASSETS}/ball.msh")
p = uipc.view(ball.positions()).reshape(-1, 3)
center = (p.max(0) + p.min(0)) / 2
p[:] = (p - center) * (0.35 / np.abs(p - center).max()) + np.array([0.0, 0.4, 0.0])
label_surface(ball)
label_triangle_orient(ball)
ball = flip_inward_triangles(ball)
abd.apply_to(ball, 100 * MPa)
is_fixed = ball.instances().find(builtin.is_fixed)
uipc.view(is_fixed)[:] = 1

ball_obj = scene.objects().create("ball")
ball_slot, _ = ball_obj.geometries().create(ball)
recorder.track("ball", ball_slot, "tri", static=True)

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
recorder.save(os.path.join(OUT, "rod_tangle.npz"))
