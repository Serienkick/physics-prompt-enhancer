# Physics Prompt Enhancer · 物理真实感提示词增强器

> Rewrite a thin, imagination-only prompt into one that obeys real-world physics — and get a
> machine-checkable **reality checklist** to verify the generated result.
>
> 把一句「纯想象」的提示词，改写成符合现实物理规律的提示词，并产出一张可机检的**现实检查清单**，用来验收生成结果。

A lightweight, portable, **physics-constraint layer** that sits in front of *any* generator
(Midjourney / Stable Diffusion / Flux / ImageGen / 可灵 / 3D). It does **not** generate pixels —
it improves the *instructions* and the *acceptance criteria*.

模型无关、可移植的**物理约束前置层**，架在任意生成器前面。它不生成像素，只优化「指令」和「验收标准」。

---

## Why this exists · 为什么做这个

Most "realism" prompt tools only add *aesthetic* realism (lighting, material, depth-of-field)
and lock you to one platform. None of them treat **physics as a hard, checkable constraint**.

现有「写实提示词」工具大多只加*美学*真实感（光照/材质/景深），而且绑死某个平台；
**没有任何一个把「物理」当作可勾选的硬约束**。

| Existing tool | What it does | Gap |
|---|---|---|
| `ComfyUI-Photoreal-Prompt-Builder` | dropdown descriptor catalog | no causal/physics enforcement, bound to ComfyUI+FLUX |
| `image-prompt-expander` | LLM + Tracery expansion | generic, not physics-focused |
| `nv-tlabs/ChronoEdit` | 14B diffusion model bakes physics into pixels | heavy, editing-only, its own model |
| **this skill** | prompt-level + model-agnostic + emits a reality checklist, runs on a 5B local LLM | ✅ fills the gap |

Inspired by physics-aware image benchmarks (e.g. ChronoEdit's *PBench-Edit*: gravity, support
contact, trajectory, lighting consistency, causal effect) — but applied at the **prompt layer**,
not the pixel layer. Lightweight, portable, zero cloud GPU cost.

灵感来自物理感知图像模型的评测维度（如 ChronoEdit 的 PBench-Edit：重力 / 支撑接触 / 轨迹 / 光照一致 / 因果），
但作用在**提示词层**而非像素层。轻量、可移植、零云端 GPU 成本。

---

## Features · 功能

- 🧲 **5 physics dimensions** — optics, mechanics, materials, scale, causality
  五大物理维度：光学、力学、材质、尺度比例、因果一致
- ✅ **reality checklist** — a JSON list of physics constraints the result *must* satisfy
  现实检查清单：一份结果必须通过的物理约束（JSON）
- 🔌 **model-agnostic** — works in front of any image/video/3D generator
  模型无关：架在任意生图 / 生视频 / 3D 工具前都能用
- 🖥️ **local 5B LLM** — preferred engine runs on Ollama / LM Studio, free & private
  本地 5B 模型：推荐 Ollama / LM Studio 跑本地模型，免费且私有
- 🪢 **rule-based fallback** — still works offline with no model installed
  规则兜底：没装模型也能离线出活
- 🌏 **bilingual output** — Chinese prose + a compact English tag string for generators
  中英双输出：中文散文 + 可直接粘贴进生成器的英文 tag 串

---

## Quick start · 快速开始

### As a WorkBuddy skill · 作为 WorkBuddy 技能
Drop the folder into your skills directory:
把整个文件夹放进你的技能目录：

```
~/.workbuddy/skills/physics-prompt-enhancer/
```

Then just say in chat: *"给这句提示词加物理/真实感"* / *"别那么 AI 塑料"* — the skill runs automatically.
对话里直接说「给这句提示词加物理/真实感」就会自动触发。

### As a standalone CLI · 作为独立命令行
Requires Python 3.8+ and (optionally) [Ollama](https://ollama.com).
需要 Python 3.8+，以及（可选）本地 Ollama。

```bash
# rule-based fallback, no model needed — 无需模型，直接出活
python scripts/enhance.py "一只猫跳上木桌" --fallback --lang both

# with a local 5B LLM (recommended) — 用本地 5B 模型（推荐）
ollama pull qwen3:4b
python scripts/enhance.py "一只猫跳上木桌" --target image --lang both
```

---

## Install · 安装

```bash
# WorkBuddy skill — 装成 WorkBuddy 技能
# copy the folder to ~/.workbuddy/skills/  (done if you cloned this repo there)

# CLI dependencies — 命令行无第三方依赖，只用标准库
python -c "import urllib, json, argparse; print('ok')"
```

No `pip install` required — `enhance.py` uses only the Python standard library.
无需 pip 安装，`enhance.py` 只用标准库。

---

## Usage · 用法

```bash
python scripts/enhance.py PROMPT [options]

  PROMPT                     base creative prompt / 基础提示词（必填）
  --target   {image,video,3d}   generation target (default image) / 目标类型
  --dims    csv                subset of: optics,mechanics,materials,scale,causality
  --lang    {zh,en,both}        output language (default both) / 输出语言
  --model   name               Ollama model tag (default qwen3:4b)
  --endpoint url               OpenAI-compatible base URL (default http://localhost:11434/v1)
  --temperature float          (default 0.4)
  --fallback                   force rule-based expansion (skip model) / 强制规则兜底
```

Examples · 示例：
```bash
python scripts/enhance.py "a knight swinging a sword" --target video --dims optics,mechanics,causality
python scripts/enhance.py "rainy neon street" --lang en --model qwen3:4b
python scripts/enhance.py "..." --endpoint http://localhost:1234/v1   # LM Studio / vLLM
```

---

## The 5 physics dimensions · 五大物理维度

| Dimension | Inject · 注入 | Checklist rule · 检查项 |
|---|---|---|
| **optics** 光学 | single light source + direction; shadow hardness; ambient occlusion | all shadows point away from one light; hardness matches distance |
| **mechanics** 力学 | gravity direction; support contact; parabolic trajectory; inertia | nothing floats without cause; motion follows valid path; contacts react |
| **materials** 材质 | per-material response (metal reflects, glass refracts, cloth drapes) | surface look matches stated material; no "plastic AI sheen" |
| **scale** 尺度 | real relative sizes; consistent vanishing point; depth order | sizes self-consistent; one perspective system |
| **causality** 因果 | explicit cause→effect (splash⇒impact, bent⇒force) | every effect has a cause present in frame; no teleporting |

For `video`, the checklist also gains temporal rules: trajectory continuity, motion-blur direction,
secondary motion (hair/cloth lag), and conservation (no spawn/despawn without cause).
视频额外含时序规则：轨迹连续、运动模糊方向、次级运动（头发/布料滞后）、守恒（无凭空出现/消失）。

---

## Output: reality checklist · 输出格式

The script prints one JSON object with two keys:
脚本输出一个 JSON 对象，含两个字段：

```json
{
  "enhanced_prompt": "一只橘猫后腿蹬地蓄力，身体沿抛物线向前上方腾起……\n\nEN: a ginger cat leaping onto a wooden table, crouch-then-launch, parabolic arc, key light upper-left, soft contact shadow beneath, matte PBR wood grain no plastic sheen, correct scale, landing impact dent",
  "reality_checklist": [
    {"dimension": "optics",    "rule": "阴影统一来自左上单一光源",      "pass_criteria": "猫与桌底阴影方向一致，光源侧受光"},
    {"dimension": "mechanics", "rule": "猫呈抛物线起跳，落桌处有冲击",  "pass_criteria": "可见蹬地蓄力与落地压痕"},
    {"dimension": "materials", "rule": "木桌为哑光木纹",              "pass_criteria": "无塑料高光，木纹清晰"},
    {"dimension": "scale",     "rule": "猫与桌比例真实",              "pass_criteria": "猫约为桌高一半"},
    {"dimension": "causality", "rule": "起跳有因、落地有果",          "pass_criteria": "蹬地为因，接触压痕为果"}
  ]
}
```

---

## Example: before → after · 示例

**Base · 原提示词**
```
一只猫跳上木桌
```

**Enhanced · 增强后**
> 一只橘猫后腿蹬地蓄力，身体沿抛物线向前上方腾起，前爪伸展准备落桌；统一来自左上窗光的柔和阴影，桌底与猫身下有接触阴影；木桌为哑光木纹、无塑料高光；猫与桌比例真实，单一透视；起跳前有蹬地（因），落桌有接触压痕（果）。
>
> EN: `a ginger cat leaping onto a wooden table, crouch-then-launch, parabolic arc, key light upper-left, soft contact shadow beneath, matte PBR wood grain no plastic sheen, correct scale, landing impact dent`

**reality_checklist** — see the JSON above. Use it to accept/reject the generated image.
用清单验收生成图：哪一项不达标就重生成或调提示词。

---

## Local LLM setup · 本地模型

`enhance.py` auto-detects Ollama at `http://localhost:11434/v1`. Any 5B-class instruct model works:
脚本默认连本地 Ollama。任意 5B 级指令模型都行：

```bash
ollama pull qwen3:4b          # best zh + physics commonsense / 中英+物理常识最好
# or: qwen2.5:7b-instruct, gemma3:4b, llama3.1:8b
```

Quantized to 4-bit these fit an 8 GB GPU or Apple Silicon and run ~30–50 tok/s.
4-bit 量化约 2.5–3 GB，8GB 显存或 Apple Silicon 即可跑，约 30–50 token/s。

For LM Studio / vLLM (OpenAI-compatible): `--endpoint http://localhost:1234/v1`.
用 LM Studio / vLLM：`--endpoint http://localhost:1234/v1`。

---

## Rule-based fallback · 规则兜底

When no model is reachable, the script appends the dimension descriptors from
`references/physics_dimensions.md` and emits one checklist item per dimension. Quality is lower
(static, no trajectory/causality reasoning) but the skill still works fully offline.
无模型时，脚本按 `references/physics_dimensions.md` 的规则拼描述词并生成清单；质量较低（静态、不推理轨迹/因果），但完全离线可用。

---

## How it works · 原理

1. Collect inputs: `base_prompt`, `target`, `dimensions`, `lang`.
   收集输入：基础提示词、目标类型、物理维度、语言。
2. Run enhancer: local 5B LLM (preferred) or rule-based fallback.
   运行增强器：本地 5B 模型（优先）或规则兜底。
3. Produce two outputs: `enhanced_prompt` + `reality_checklist`.
   产出两份：增强提示词 + 现实检查清单。
4. The model is instructed to *reason* about physics (infer gravity, predict trajectory, state
   causal chain) — not just pad adjectives. It never invents new subjects.
   模型被要求*推理*物理（推断重力、预测轨迹、写因果链），而非堆形容词；不新增主体。

---

## Limitations · 局限（诚实说明）

- A 5B model **follows patterns**, it does not truly simulate physics. The checklist is an
  *acceptance tool*, not a guarantee — final fidelity still depends on the downstream generator.
  5B 模型是「学模式」，不是真模拟物理。清单是验收工具，不是保证；最终质量仍看下游生成器。
- Impossible premises (e.g. "anti-gravity cat") are kept but flagged in the checklist.
  物理上不可能的设定（如反重力猫）会被保留，但在清单中标出矛盾。

---

## Project layout · 目录结构

```
physics-prompt-enhancer/
├── SKILL.md                      # skill definition: workflow + trigger + checklist spec
├── README.md                     # this file
├── references/
│   └── physics_dimensions.md     # 5-dimension knowledge core + video rules + fallback template
└── scripts/
    └── enhance.py                # local 5B LLM engine (Ollama/LM Studio) + rule-based fallback
```

---

## License · 协议

MIT — free to use, modify, and redistribute.
MIT 协议，可自由使用、修改、再分发。
