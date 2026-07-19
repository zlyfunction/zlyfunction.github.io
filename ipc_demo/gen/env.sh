# Source this before running scene scripts:  source env.sh
# Sets up the venv python + CUDA runtime libraries on LD_LIBRARY_PATH.
VENV="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/.venv"
NV="$VENV/lib/python3.12/site-packages/nvidia"
# /usr/lib first so the system libstdc++ (GLIBCXX >= 3.4.30) beats any conda one
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:$NV/cublas/lib:$NV/cusparse/lib:$NV/cusolver/lib:$NV/cuda_runtime/lib:$NV/nvjitlink/lib:$NV/cuda_nvrtc/lib:$HOME/cuda-12.8/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
# The venv python comes from miniconda, whose RPATH pins conda's older libstdc++
# ahead of LD_LIBRARY_PATH — preload the system one so GLIBCXX_3.4.30 resolves.
export LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libstdc++.so.6${LD_PRELOAD:+:$LD_PRELOAD}"
export PATH="$VENV/bin:$HOME/cuda-12.8/bin:$PATH"
