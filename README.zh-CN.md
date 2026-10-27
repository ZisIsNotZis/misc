<p align="center"><img src="assets/logo.svg" alt="misc" width="200" height="40"></p>

[English](README.md) | **简体中文**

# misc

一个摊平的抽屉：为回答具体工程问题而写下的一次性脚本、notebook 和笔记，原样留存。

**八十来个彼此独立的文件，每个只解决一个窄问题——从零写的 ANSI 终端、asyncio
HTTP 服务器、工业视觉的配置搬运、llama.cpp 的编译配方——之所以公开，是因为这些
问题总会再来一次，而答案通常已经躺在里面了。**

> **状态：归档。** 这是一个干活的杂物抽屉，不是库，也不是项目：没有包、没有清单、
> 没有统一入口、没有测试。内容大致横跨 2020–2026，不再维护。读它、抄它，但别依赖它。

## 快速开始

只有一个文件既无依赖、又自包含、还能直接跑——那个单文件的虚拟终端：

```bash
git clone https://github.com/ZisIsNotZis/misc.git
cd misc
python3 term.py      # 在 pty 上起一个 shell，自己渲染屏幕；Ctrl-D 或 exit 退出
```

其余文件都依赖上下文：多数脚本要求数据就摆在旁边、本地有某个服务、或者工具链
是特定版本（见[依赖](#依赖)）。跑之前先看文件头——有些还带着当初那台机器上的
绝对路径和主机名。

## 里面有什么

**终端与系统** —— `term.py` 是一个约 685 行的 VT/ANSI 模拟器：开 pty、解析
SGR/OSC 与按键序列、维护屏幕缓冲，再用差分后的 JSON 重绘，纯标准库。`pow` 把 CPU
核心拉上线并锁频；`kil` 停掉笔记本上那些常驻进程；`nic.py` 从 `/proc/net/dev`
打各网卡计数；`remove_r.py` 用 `readv`/`writev` 过滤回车刷新型进度输出；
`mycdll.py`、`util.py`、`mymisc.py` 从类型注解生成 `ctypes` 签名。

**服务器与协议** —— `mysvr.py` 是一个小 asyncio HTTP 服务器（路由、Range、tar
流式传输）；`myminio.py` / `myminios.py` 是对象存储客户端与架在其上的 S3 兼容
外壳；`mreq.py` 用 MQTT 主题实现请求/响应式 RPC（`gmqtt` + `uvloop`），
`mreqtest.py` 是它的驱动器；`fromtobytes.py` 让字节块穿过 FastAPI；`mdview.htm`
在浏览器里预览 Markdown。

**异步管道** —— `cb.py`、`cb2.py`、`sub.py`、`val3.py`、`futs.py`、`myasync.py`、
`connectcoro.py` 可以按顺序读成一条演进线：在不引入框架的前提下，用裸 `asyncio`
future 把回调、订阅与取消接起来。

**数值与类型** —— `lns.py` 是 log 数系张量类型（对数幅值 + 符号位），用于动态范围
极大的运算；`qkvfft.py` 把滑窗注意力写成 FFT 卷积；`cast.py` 依据 `Union` /
`TypedDict` / dataclass 注解做运行时类型转换；`mutuple.py` 是可变元组；
`npjson.py` 让 numpy 结构化数组与 JSON 互转；`vec.py` 是 memmap 支撑的
`ndarray`；`selfcallable.py` 与 `stub.py` 是类型系统的玩具。

**工业视觉** —— `featbox2xywcfg.py` 与 `imgcls2featbox.py`（各 10–12 KB）在特征框、
图像分类与 `x/y/w/cfg` 任务配置之间互转；`roi2.py`、`roi2cfg.py`、`fix2cfg.py`
基于 YAML + cv2 处理区域（其中 `roi2.py` 还用到商业库 MVTec **halcon**）；
`dinoseg*.py` 用 DINOv3 嵌入做分割；`featmap2seg.py`、`feat2cls.py`、`img2cls.py`、
`img2clsall.sh` 是喂给它们的标注流水线。

**LLM 基建** —— `mk.sh` 用调过的编译参数跨编译器、跨后端编译 llama.cpp；
`ggmlmk.txt` 记录了更早一版的构建；`analyze.py` 与 `graphics.md` 把 `llama-bench`
的 CSV 输出整理成 GPU/量化吞吐表；`beam.py` 对着本地 `llama-server` 跑 beam
search；`trtllm.sh` 是一份 TensorRT-LLM 服务配置；`k3s.sh` 引导一个 k3s 节点；
`dl.sh` 拉取模型集合；`ds2txt.py` 与 `jsonl2txt.py` 把对话格式的数据集渲染成文本。

**日常脚本** —— `apt.sh`、`99clean`、`sources.list`、`pip.sh`、`clean.re`、
`gitclean`、`bashsqhist.sh`（sqlite 支撑、按使用频度排序的 shell 历史）、
`htmlconv.sh`、`duext.py`、`greprate.py`。

**Notebook** —— 八个手写的小实验，不需要任何数据集：`quant`（训练后量化）、
`packmask` / `packmask2`（位打包掩码）、`aps`（交替投影）、`minla`（PCA 嵌入上的
最小线性排列）、`fitsin`（SwiGLU 容量）、`thres`（阈值化）、`continuousatn`
（连续注意力）。

**笔记** —— `graphics.md`（GPU 规格/吞吐表）、`sandbox.md`（隔离手段，从无沙箱到
完全虚拟化）、`train.md`（加速训练、降低显存）、`v4lqsvrtsp.txt`（v4l2 /
QuickSync / RTSP）、`road.drawio`。

## 架构

没有架构，而且是有意为之。仓库是平的：每个文件都是一座孤岛，自带 import，没有被
超过一两个邻居引用过。真正存在的边只有这几条：

```
mysvr.py ──► myminio.py        对象存储架在 asyncio HTTP 服务器上
   │
   └──────► myminios.py        S3 兼容外壳（aiohttp 客户端一侧）

mreq.py ◄──► mreqtest.py       MQTT 上的请求/响应 RPC，由这个测试驱动
term.py                        自包含：pty + VT 解析器 + 渲染器

dinoseg*.py ──► featmap2seg.py ──► featbox2xywcfg.py ──► roi2.py
   （嵌入）        （解码）          （配置映射）         （halcon 区域）
```

共用件（`feat.py`——直接由掩码算面积、长宽比、协方差、离心率这类矩不变量；
`util.py`、`cast.py`、`futs.py`）是复制粘贴的源头，不是库：后来的文件直接把更好的
那版内联了。在你自己的副本里随便改名、搬位置——这里没有任何 API 会被破坏。

## 依赖

没有任何清单文件，依赖是从 import 里读出来的：

```
numpy torch torchvision opencv-python matplotlib scikit-learn PyYAML Pillow
pyarrow orjson requests aiohttp pydantic fastapi uvloop pulp miniopy_async gmqtt
```

`roi2.py` 另外需要商业库 MVTec **halcon**（要授权）。使用 PEP 695 泛型的文件
（`cb.py`、`sub.py`、`mutuple.py`、`cast.py` 等）需要 Python 3.12+；`term.py`
和那些 shell 脚本只要有 Python 3 和 `/bin/sh`。

## 怎么改

没有构建、没有测试套件、没有 linter 配置、没有 lockfile。现存的自检只有你手动跑
的那几个：

```bash
python3 -m py_compile some_script.py   # 单个文件的语法检查
python3 term.py                        # 唯一的端到端冒烟测试
bash -n mk.sh                          # shell 脚本同理
```

这个仓库的编辑规矩：保持平铺，保持单文件自包含，绝不提交凭据（见下文）。说明写进
文件头的 docstring 或某篇 `.md` 笔记里，不要新建文档。

## 发布前的清理

这个目录是从私有存档里搬出来的，公开前删掉了带凭据的文件、抹掉了内联的密钥：

- `lm.yml` / `lm.json` —— 多家供应商（约 24 家）的 API key 库 —— 已删除。
- `github-recovery-codes.txt` —— GitHub 双因素恢复码 —— 已删除。
- `p.txt` —— 一个不受限制、拒绝作答的「no refusals」提示词 —— 已删除。
- `chengzhi.sh` —— 真实用户名、跳板机、非标准端口 —— 已打码。
- `trtllm.sh` —— 一个真实主机 IP —— 已打码。

在这棵树上出现过的每一个凭据都应视为已泄露，请轮换。`.gitignore` 屏蔽了
`.env*`、`*.pem`、`*.key`、`lm.yml`/`lm.json` 和恢复码类文件，防止它们误入。

## 路线图

**已实现** —— [里面有什么](#里面有什么)一节列出的全部内容：终端、那组 asyncio
服务器、MQTT RPC、LNS/FFT 的数值草稿、视觉配置流水线、llama.cpp 的构建与压测、
日常脚本、八个 notebook 以及那些笔记。

**计划** —— 没有。这是归档：不加功能、不修 bug、不更新依赖。已知过时的部分是有意
保留的时代记录：`sources.list` 锁在 Ubuntu focal（20.04，2025 年 5 月已停止支持），
`train.md` 面向 `THUDM/chatglm2-6b` 和 2023 年的微调 CLI，`ggmlmk.txt` 记的是
2024 年那版 llama.cpp 的编译参数。

如果这个抽屉将来真要不止于归档，诚实的做法不是让它长大，而是把其中一条线摘出去
单独立库——`term.py` 和 `mysvr`/`myminio`/`mreq` 这一族是最接近能独立使用的两个——
给它补上测试、放到合适的许可下，剩下的继续当参考。

## 贡献

本仓库不再维护，也不期待 PR——什么值得发、什么不必发，见
[CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可

[GNU Affero 通用公共许可证 v3.0 only](LICENSE)（AGPL-3.0-only），© ZisIsNotZis。

该许可覆盖本仓库中的代码。这些脚本引用到的第三方代码、模型、编译配方与笔记各自
遵循其原有许可；MVTec halcon 是商业软件，从未被内置在这里。
