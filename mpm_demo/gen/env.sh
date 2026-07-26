# Source this before running sim.py:  source env.sh
# Puts the venv python on PATH and the WSL CUDA driver stub on LD_LIBRARY_PATH
# (taichi's CUDA backend needs libcuda.so, which under WSL2 lives outside the
# normal system lib dirs).
VENV="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/.venv"
export LD_LIBRARY_PATH="/usr/lib/wsl/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PATH="$VENV/bin:$PATH"
