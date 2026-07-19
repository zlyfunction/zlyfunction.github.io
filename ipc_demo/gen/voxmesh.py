"""Voxel-art tet meshes: pixel-font letters and shapes -> conforming tet meshes.

Each filled voxel is split into 6 tets (Kuhn subdivision, translation-invariant
so neighboring voxels share matching faces). Grid nodes are merged globally.
"""

import itertools

import numpy as np

# 5x7 pixel font (rows top->bottom), only the glyphs we need
FONT = {
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
}

_KUHN = []
for _perm in itertools.permutations(range(3)):
    _cur = np.zeros(3, dtype=int)
    _pts = [_cur.copy()]
    for _ax in _perm:
        _cur = _cur.copy()
        _cur[_ax] += 1
        _pts.append(_cur.copy())
    _t = np.array(_pts)
    if np.linalg.det((_t[1:] - _t[0]).astype(float)) < 0:
        _t[[1, 2]] = _t[[2, 1]]  # fix orientation
    _KUHN.append(_t)


def voxels_to_tetmesh(voxels, voxel_size=1.0):
    """voxels: iterable of (i,j,k) filled cells. Returns (Vs float64 (N,3), Ts int32 (M,4))."""
    node_id = {}
    Vs = []
    Ts = []

    def nid(p):
        key = tuple(int(x) for x in p)
        if key not in node_id:
            node_id[key] = len(Vs)
            Vs.append(key)
        return node_id[key]

    for v in voxels:
        base = np.array(v, dtype=int)
        for tet in _KUHN:
            Ts.append([nid(base + c) for c in tet])

    return np.array(Vs, dtype=np.float64) * voxel_size, np.array(Ts, dtype=np.int32), node_id


def letter_voxels(ch, depth=2):
    """Filled (i,j,k) cells for a glyph. x = column, y = row (bottom=0), z = depth."""
    rows = FONT[ch]
    h = len(rows)
    out = []
    for r, row in enumerate(rows):
        for c, bit in enumerate(row):
            if bit == "1":
                for k in range(depth):
                    out.append((c, h - 1 - r, k))
    return out


def play_button_voxels(w=15, h=11, depth=3, corner=2):
    """YouTube-style rounded rect; returns (all_voxels, white_voxel_set).

    White set = front-layer voxels of the centered triangle.
    """
    voxels = []
    white = set()
    # triangle: pointing +x, occupying middle rows/cols
    tri_left = w // 2 - 2
    tri_h_half = 2.6
    cx_span = 5
    for i in range(w):
        for j in range(h):
            # rounded corners: skip cells outside the rounded box
            dx = max(corner - i, i - (w - 1 - corner), 0)
            dy = max(corner - j, j - (h - 1 - corner), 0)
            if dx * dx + dy * dy > corner * corner + 1:
                continue
            for k in range(depth):
                voxels.append((i, j, k))
                if k == depth - 1:  # front layer
                    t = (i - tri_left) / cx_span  # 0..1 across triangle
                    if 0 <= t <= 1 and abs(j - (h - 1) / 2) <= tri_h_half * (1 - t):
                        white.add((i, j, k))
    return voxels, white
