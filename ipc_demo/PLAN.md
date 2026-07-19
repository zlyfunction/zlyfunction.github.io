# IPC 网页演示 — 实施计划与进度

> 完整调研背景见 git 历史或 `~/.claude/plans/ipc-incremental-potential-contact-fuzzy-karp.md`。
> 本文件是**执行进度追踪**，每完成一小项就勾掉一项并在"进度日志"补一行，方便随时中断/继续。

## 方案概要

离线用 GPU (RTX 2070) 跑 [libuipc](https://github.com/spiriMirror/libuipc) (`pip install pyuipc`) 生成 IPC 仿真逐帧数据，
烘焙成紧凑二进制，浏览器端用 three.js (CDN) 纯静态回放。两个场景：

1. **soft_stack** — 多个软体互相堆叠挤压（改自 libuipc-samples `34_cloth_stack`）
2. **rod_tangle** — 绳/链条 codimensional 接触（改自 libuipc-samples `23_kirchoff_rod_bending`）

目录结构：

```
ipc_demo/
  PLAN.md          # 本文件
  gen/             # 离线生成（公开）
    requirements.txt
    export.py      # headless 逐帧导出工具
    bake.py        # npz → mesh.json + frames.bin (Int16 量化)
    scenes/soft_stack.py
    scenes/rod_tangle.py
  data/<scene>/mesh.json + frames.bin   # 网页直接 fetch
  index.html       # three.js 回放页
```

## 任务清单

- [x] **1. 环境搭建**：源码编译 libuipc（sm_75）成功，pyuipc 0.9.0 装进 venv；FEM 冒烟测试通过（四面体真实下落、位置有更新、无穿地）。⚠️ 两个坑：① venv 的 python 来自 miniconda，其 RPATH 会优先加载 conda 旧版 libstdc++，需 `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6`（已写进 env.sh）；② ABD（AffineBody）几何的 `positions()` 不随仿真更新（状态在 instance transform 里），FEM 本构（StableNeoHookean 等）才更新——录制动的物体必须用 FEM，固定不动的 ABD 无所谓
- [x] **2. 导出工具**：`export.py`（headless 步进 + 逐帧收集 `positions()` + 存 npz）— 已写好，Transform/Vector3/AngleAxis API 已用 pip 版验证
- [x] **3. 场景 1 soft_stack**：跑通并烘焙完成。bunny+2 球+2 圆环（6145 顶点，300 帧），落地堆叠挤压、最低点 y≈0.01（=d_hat 间隙，零穿透）、末帧静止。第一版曾因资产网格尺寸不一（ball.msh 半径 4 不居中）初始穿透被 sanity checker 拒绝 → 已改为 numpy 归一化后摆放。浏览器截图验证 OK。
- [x] **4. 场景 2 rod_tangle**：跑通并烘焙完成。14 根绳（49 顶点/根）交叉下落搭在固定圣诞球上（ball.msh 原来是带挂环的装饰球）。第一版绳太软+逐点抖动导致"皱面条"且全部滑落 → 调参：KirchhoffRodBending 1e-2→5e2、摩擦 0.3→0.5、去抖动、起始位置贴近球顶，效果良好（几根挂在球上、其余盘绕球底）。
- [x] **5. 数据检查**：两场景均过——录制器断言 finite、final_speed≈0、最低点 y≈d_hat（零穿透）、浏览器目测无穿模；delta 编码 roundtrip 误差 0.047mm
- [x] **6. bake.py**：npz → `mesh.json` + `frames.bin`（Int16 量化）— 已写好并用合成数据测试通过
- [x] **7. index.html**：three.js 回放页 — 已写好；用合成数据 + headless Chromium (playwright) 验证：渲染、阴影、fat-line 绳、播放/时间轴/主题切换/场景切换均正常、无控制台错误
- [x] **8. 主站集成**：主页 misc 区块已加"IPC Simulation"卡片（双语）
- [x] **9. 端到端验证**：headless Chromium 全套通过——两场景加载播放、about 弹窗、倍速、明暗主题、移动端 390px 视口、主站卡片跳转，全程无控制台错误。真实数据总体积 2.4MB。
- [ ] **10. (可选) 耦合场景**：绳子搭在软体堆上的混合演示 —— 未做，随时可加（复用 soft_stack + rod 的搭建代码即可）

## 二期任务（2026-07-18 追加）

- [x] **11. google_pile 场景**：GOOGLE 六个字母（5x7 像素字体 → 体素 → Kuhn 六四面体剖分，`gen/voxmesh.py`）软体下落成排互靠，Google 品牌配色（per-object `color`）。调参 3 轮：字母从 depth2/30kPa/高空带旋转落（全摔平）→ depth4/70kPa/低空零倾角/摩擦 0.6（成排斜靠、字形可读）。
- [x] **12. play_trampoline 场景**（用户选定的 YouTube demo）：果冻红播放按钮（白三角形为第二材质组 `groups`/`groupColors`）落到四边固定布料弹床。调参 3 轮：布 60kPa 陷太深吞按钮 → 250kPa 太弹按钮飞出 → 150kPa+倾角 -6°（负角让白面朝上落）刚好：弹跳后稳窝在弹床里、白三角朝上清晰可见。布料半透明（`opacity` 字段）且不投影。
- [x] **13. 手机端取景优化**：竖屏 aspect<0.8 时 FOV 40→60、视角中心抬高——手机截图确认主体完整居中。
- [x] **14. viewer 四 tab + 多颜色支持**：场景按钮 ×4、per-object color/opacity、双色组（material 数组 + addGroup）、线框开关兼容材质数组。全部无控制台错误。

## 收尾备注（2026-07-18）

- **全部核心任务完成，未提交 git**（等用户确认后再 commit/push）。
- 本地预览：仓库根目录 `python3 -m http.server 8642` → http://localhost:8642/ipc_demo/index.html
- 重新生成数据的完整流程：`cd ipc_demo/gen && source env.sh && python scenes/soft_stack.py && python scenes/rod_tangle.py && python bake.py raw/soft_stack.npz ../data/soft_stack && python bake.py raw/rod_tangle.npz ../data/rod_tangle`
- 依赖的本机环境（不入库）：`~/Toolchain/libuipc`（源码+build）、`~/cuda-12.8`、`~/.local/tools`（zip/ninja/chromium 库等）、`gen/.venv`
- GitHub Pages 是静态托管，`.gz` 文件会原样返回，viewer 里用 `DecompressionStream` 手动解压，不依赖服务器 Content-Encoding。

## 进度日志

- 2026-07-18: 计划批准，开始实施。
- 2026-07-18: venv 建好，`pip install pyuipc==0.0.25 numpy` 成功；补装了 `nvidia-cublas/cusparse/cusolver/cuda-runtime-cu12`（wheel 不捆绑，需加到 `LD_LIBRARY_PATH`）。
- 2026-07-18: 冒烟测试失败：`cudaErrorSymbolNotFound`。用 `strings` 检查确认 **PyPI wheel（新旧版本都是）只编译了 sm_89**，RTX 2070 是 sm_75 → 决定源码编译。注意 pyuipc 的 `positions()` 视图形状是 `(N,3,1)` 列向量。
- 2026-07-18: 编译前置检查：CMake 3.31.2 ✓、g++ 11.4 ✓、16 核/31GB 内存/911GB 磁盘 ✓；缺 CUDA toolkit 和 zip/unzip/pkg-config/ninja/libtool（需 sudo 安装，等用户执行）；NVIDIA keyring deb 已下载到 scratchpad。
- 2026-07-18: 无 sudo 方案落地：zip/unzip/pkg-config/ninja 从 Ubuntu deb 解包到 `~/.local/tools/usr/bin`（需加进 PATH）；CUDA 12.8.1 runfile 正在下载到 scratchpad（装到 `~/cuda-12.8`，不需要 root）；vcpkg 和 libuipc 已 clone 到 `~/Toolchain/`，vcpkg 已 bootstrap；14 个 C++ 依赖（eigen/libigl/tbb 等）正在后台预编译暖缓存。
- 2026-07-18: 场景 1 soft_stack 跑通（第二版，网格归一化后）；烘焙 2.15MB（delta 编码把 5.31MB 压到 2.15MB）；浏览器截图验证堆叠挤压效果。场景 2 rod_tangle 第一版效果差（皱面条+全滑落），调参重跑后效果好，烘焙 0.17MB。端到端最终验证全过。**项目完成，待 git 提交。**
- 2026-07-18: CUDA 12.8 toolkit 装好（runfile 直接 `--silent` 会报 exec 错，用 `bash xxx.run --extract=DIR` 解包后把 cuda_nvcc/libcublas 等组件 `cp -a` 合并进 `~/cuda-12.8`，nvcc 12.8.93 可用）；vcpkg 14 个依赖 5.9 分钟全部编好进二进制缓存（注意 manifest 需要 vcpkg.json + vcpkg-configuration.json 两个文件都在）。
- 2026-07-18: libuipc CMake configure 成功（Ninja / Release / sm_75 / pybind on / tests·examples·benchmarks off，python 指向 `gen/.venv`），正在后台编译。恢复方法：`cd ~/Toolchain/libuipc/build && PATH=$HOME/.local/tools/usr/bin:$HOME/cuda-12.8/bin:$PATH cmake --build . -j14`，编完后 pybind 应自动装进 venv（若没有则 `cd build/python && pip install .`），然后跑 `gen/smoke_test.py`（先 `source gen/env.sh`）。
- 2026-07-18: 编译成功（~1090 目标，约 35 分钟），pyuipc 0.9.0 自动装入 venv；数据格式升级：录制器支持 static 物体、bake 降采样到 30fps + gzip（`frames.bin.gz`），viewer 用 `DecompressionStream` 解压、静态物体只写一次。
- 2026-07-18: 编译等待期间完成 6/7/8 号任务：`bake.py`、`index.html` 回放页、主站卡片全部就位。验证方法：合成动画数据（scratchpad/make_fake_npz.py）走完整 bake 管线放进 `data/`，本地 `python -m http.server 8642`（在仓库根目录），headless Chromium（playwright，chromium 系统库同样用 deb 解包进 `~/.local/tools`，跑时需 `LD_LIBRARY_PATH=$HOME/.local/tools/usr/lib/x86_64-linux-gnu`）截图确认渲染正确。**注意：目前 `data/` 里是假数据占位，真数据跑出来后覆盖。**
