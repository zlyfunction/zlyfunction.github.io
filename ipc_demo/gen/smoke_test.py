"""Minimal GPU smoke test: two tetrahedra fall and collide with the ground.

Verifies that pyuipc's CUDA engine runs on this machine before building real scenes.
"""

import numpy as np

import uipc
from uipc import Logger
from uipc.core import Engine, World, Scene
from uipc.geometry import tetmesh, label_surface, ground
from uipc.constitution import StableNeoHookean, ElasticModuli
from uipc.unit import kPa

Logger.set_level(Logger.Level.Warn)

engine = Engine("cuda", "./smoke_output")
world = World(engine)

config = Scene.default_config()
config["dt"] = 0.02
config["gravity"] = [[0.0], [-9.8], [0.0]]
scene = Scene(config)

snh = StableNeoHookean()
scene.contact_tabular().default_model(0.5, 1e9)

Vs = np.array(
    [[0, 1, 0], [0, 0, 1], [-np.sqrt(3) / 2, 0, -0.5], [np.sqrt(3) / 2, 0, -0.5]],
    dtype=np.float64,
)
Ts = np.array([[0, 1, 2, 3]])

mesh = tetmesh(Vs, Ts)
snh.apply_to(mesh, ElasticModuli.youngs_poisson(100 * kPa, 0.48))
label_surface(mesh)
pos = uipc.view(mesh.positions())  # shape (N, 3, 1): column vectors
pos += np.array([[0.0], [1.0], [0.0]])

obj = scene.objects().create("tet")
geo_slot, _ = obj.geometries().create(mesh)

ground_obj = scene.objects().create("ground")
ground_obj.geometries().create(ground(-1.0))

world.init(scene)

for i in range(25):
    world.advance()
    world.retrieve()

p = np.array(uipc.view(geo_slot.geometry().positions())).reshape(-1, 3)
print("final positions:\n", p)
assert np.isfinite(p).all(), "NaN/Inf in positions!"
assert p[:, 1].min() > -1.001, "vertex went through the ground!"
assert p[:, 1].min() < 0.0, "tet did not fall (positions not updating)!"
print("OK: CUDA engine works, tet fell from y=+1 and rests above ground (min y = %.4f)" % p[:, 1].min())
