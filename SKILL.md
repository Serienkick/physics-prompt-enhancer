---
name: physics-prompt-enhancer
description: Rewrite a base creative prompt into a physics-grounded prompt plus a structured reality checklist, so AI image/video/3D generation looks physically plausible (correct gravity, lighting, materials, trajectory, causal consistency) — including concretely specified two-object interactions written as a "contact narrative" (contact state: contacted / not contacted / about to contact; contact medium: direct / via tool / through medium / proximity; action dynamics like chase = approach→dodge→close or miss), a light aesthetic touch (focus, unified lighting, restrained palette), a Character Skeleton System for humanoid/character subjects (anatomical joint hierarchy, balance/stability, IK/FK operation space), and — for video targets — a prompt-length guard that detects the chosen video model's prompt char-limit and compresses the enhanced prompt to fit if it would overflow. The guard first asks the **local LLM** to compress intelligently (preserving subject + physics-critical detail), with a deterministic rule-based trimmer as a final hard guarantee, so the pasted prompt is never over the cap. The enhanced prompt is self-reviewed to drop redundant phrasing, keeping only the more specific sentence. Use when the user wants a prompt to feel "real", "physical", "not AI-plastic", asks to add physics/realism factors, make two objects' interaction more specific (did they actually touch? how? through what?), make a character's pose/anatomy look right (bones/joints aligned, no clipping/jitter), keep the prompt within a specific video model's length cap, or add a bit of aesthetics without losing realism. Model-agnostic; runs on a local 5B-class LLM (Ollama/LM Studio) with a rule-based fallback.
metadata:
  author: codexclaw
  version: "1.5"
  tags: [prompt, physics, realism, interaction, aesthetic, character, rigging, contact-narrative, prompt-length-guard, image-generation, video-generation, 3d, local-llm]
---

# Physics Prompt Enhancer (物理真实感提示词增强器)

Turn a thin, imagination-only prompt into one that obeys real-world physics, and emit a
machine-checkable "reality checklist" the user can use to verify the generated result.
Sits in front of ANY generator (Midjourney / Stable Diffusion / Flux / ImageGen / 可灵 / 3D),
as a lightweight, portable, physics-constraint layer. It does not generate pixels — it
improves the instructions and the acceptance criteria.

Closest prior art (for context, not dependency):
- `nv-tlabs/ChronoEdit` (14B/2B diffusion model, bakes physics into pixels — heavy, editing-only).
- `artokun/ComfyUI-Photoreal-Prompt-Builder` (dropdown descriptor catalog, no causal/physics enforcement).
- This skill targets the gap those leave: a *prompt-level*, *model-agnostic*, *physics-checklist*
  enforcer that runs on a 5B local LLM with zero GPU Cloud cost.

## When to use
- "把这句提示词加物理/真实感" / "让图更符合现实" / "别那么 AI 塑料"
- "给这个生图/生视频/3D 提示词加物理因素"
- "让这两个物体的互动更真实/更具体" / "两个人/物体之间的动作关系写清楚点"
- "加一点点美学/氛围，但别失真" (物理真实优先，美学轻量点缀)
- "让角色/人物骨骼对、动作别穿模别抖" / "挥剑劈砍的姿势要符合人体结构"
  — humanoid/character prompts for `video`/`3d`; the enhancer auto-includes the
  `character` (Character Skeleton System) dimension.
  Try: `python scripts/enhance.py "一个战士挥剑劈砍" --target video --dims mechanics,causality,character --lang zh`
- "把提示词压到可灵/Runway 的长度上限以内" / "别超 Sora 的提示词字数"
  — for `video` targets, pass `--video-model <model>` (runway/kling/sora/veo/hailuo/
  minimax/luma/pika/vidu/generic). The enhancer detects that model's prompt char-limit
  and compresses the enhanced prompt to fit if it would overflow.
  Try: `python scripts/enhance.py "战士挥剑劈砍，慢镜头，雨夜霓虹" --target video --video-model kling --lang en`
  With a local LLM reachable (default), over-cap text is first compressed by the local model
  (`method: "local-model"` in `prompt_compression`); pass `--fallback` to skip the model and
  use only the deterministic trimmer (`method: "rule-based"`).
  Try: `python scripts/enhance.py "战士挥剑劈砍，慢镜头，雨夜霓虹" --target video --video-model runway --model physics-enhancer:latest`
- Any request to make a creative prompt more physically plausible.

## Core workflow
1. Collect inputs: `base_prompt` (required), `target` ∈ {image, video, 3d} (default image),
   `dimensions` (subset of the 8 physics dimensions below; default = all), `lang` ∈ {zh, en, both}
   (default: both — output Chinese prose + an English prompt ready to paste into generators).
   8 维度 = optics, mechanics, materials, scale, causality, **interaction(客体间交互)**,
   **aesthetic(美学基调)**, **character(人物骨骼系统)**。
   当主体为人形/角色且 `target` ∈ {video, 3d} 时，与以上维度并列带上 `character`
   （人物骨骼系统模块）。
2. Run the enhancer (preferred: local 5B LLM via `scripts/enhance.py`; fallback: apply the
   rule-based expansion in `references/physics_dimensions.md` directly, no model needed).
   For `video` targets, optionally pass `--video-model <model>` so the enhancer enforces
   that model's prompt char-limit (see "Video model prompt-length guard" below).
3. Produce exactly two outputs:
   - **enhanced_prompt**: natural-language prompt with physics descriptors woven in, plus a
     compact English tag string for the generator.
   - **reality_checklist**: JSON list of physics constraints the result MUST satisfy
     (see spec below). This is the differentiator — existing tools don't emit it.
4. Return both to the user, clearly labeled.

## reality_checklist spec
A JSON array; each item has `dimension`, `rule` (human-readable), and `pass_criteria`
(what to look for in the generated image/video to confirm compliance). Seed dimensions from
`references/physics_dimensions.md`. Minimum coverage:
- `optics` — single consistent light source; shadows point away from it; soft vs hard shadow matches distance.
- `mechanics` — gravity direction consistent; supported objects rest on surfaces; motion follows inertia/trajectory.
- `materials` — surface response matches stated material (metal reflects, glass transmits, fabric drapes, skin has pores).
- `scale` — relative sizes and perspective are self-consistent; no floating/missing contact shadows.
- `causality` — depicted action has a physically valid cause→effect (splash implies impact; bent object implies force).
- `interaction` (客体间交互，双客体时优先，v1.2 为「接触叙事」) — 必须明确三点：① 接触状态（已接触 / 未接触 / 即将接触）；② 接触媒介（直接接触 / 工具中介 / 介质传递 / 接近未触）；③ 动作过程（把关系动词展开成动作变化，如追逐 = 逼近→闪避→接触或未接触）。同时写清接触类型（点/线/面）、力方向与反作用、可观察结果。pass_criteria 必须能判断「A 与 B 到底接触没有」：已接触→接触点与方式可指认；未接触→两者间有明确空隙，不得画"假接触"。可在画面中逐项核对，不是形容词。
- `aesthetic` (美学基调，轻量) — 单一视觉焦点；光影氛围统一且不违反 optics；主色调 ≤3 且统一；纵深层次（空气透视/浅景深）。物理真实优先，美学不得引入画面内不存在的元素。
- `character` (人物骨骼系统，主体为人形/角色且 `target` ∈ {video, 3d} 时) — 与人体结构对应的骨骼层级、绑定干净权重归一；姿态在解剖限位内、重心落在支撑面内不无故失衡；肢体不穿模、运动无抖动；多关节经 IK/FK 联动、接触点保持。

## Local 5B LLM (preferred engine)
`scripts/enhance.py` calls a local Ollama (or LM Studio OpenAI-compatible) endpoint with the
system prompt bundled in this skill. Recommended models (any 5B-class instruct works):
- `qwen3:4b` / `qwen2.5:7b-instruct` (best zh + physics commonsense)
- `gemma3:4b`, `llama3.1:8b`
Quantized to 4-bit these fit an 8GB GPU or Apple Silicon and run ~30–50 tok/s.
The script auto-detects Ollama; if unavailable it returns a clear error telling the user to
start Ollama or falls back to the rule-based path.

## Rule-based fallback (no model)
When no local LLM is available, expand the prompt by appending the dimension descriptors from
`references/physics_dimensions.md` and synthesize a checklist from the same rules. Quality is
lower (static, no reasoning about trajectory/causality) but the skill still works offline.

## Authoring notes for the LLM system prompt
- Instruct the model to REASON about physics, not just pad adjectives: infer gravity direction,
  predict the object's trajectory, and state the causal chain.
- Forbid inventing new subjects; only add physically-grounded context to what the user gave.
- When the base prompt has two or more objects (A & B), require the model to write a CONTACT
  NARRATIVE, not a vague verb: contact state (contacted / not contacted / about to contact),
  contact medium (direct / via tool / through medium / proximity only), and action dynamics
  (chase = approach → dodge → close or miss). The checklist must let the user judge whether A
  and B actually touched.
- After enhancement, require the model to SELF-REVIEW and drop redundant phrasing: the same
  physical meaning should appear once, keeping the more specific sentence. No "same thing
  said twice in different words".
- Aesthetic is a light garnish: single visual focus, unified lighting (must not violate
  optics), ≤3 cohesive hues, depth layers. Physics wins on any conflict.
- Always output valid JSON for the checklist (the script parses it).
- Keep the English tag string under ~60 tokens for generator compatibility.

## Character Skeleton System (人物骨骼系统模块)
Derived from **character modeling (人物建模)**, this module turns "make the character look right"
into concrete, checkable anatomy/motion constraints. It is the `character` dimension's deep
reference and is fully integrated with the two-output model above.

**When to use it**
- "让这个角色/人物更真实" / "骨骼/关节要对" / "动作别穿模别抖" — for `video`/`3d` character prompts.
- Any request where the subject is a humanoid and you care about pose plausibility, contacts, or motion.

**What it enforces (full detail in `references/skeleton_system.md`)**
1. **Skeleton design** — standard humanoid hierarchy (root→pelvis→spine chain→clavicles→arms→hands;
   neck→head; thighs→calves→feet), UE5/Unity-Humanoid bone naming, T-pose bind with normalized
   ≤4-bone skin weights, no candy-wrapper twisting.
2. **Stability** — joints within anatomical limits; center of mass kept over the support base
   (inverted-pendulum balance); inertial lean matching velocity; collision-aware limbs; damped,
   jitter-free motion.
3. **Operation space** — IK/FK-linked multi-joint control (FABRIK for arms/long chains, CCD for
   short fixes), motion-capture-derived poses (FBX/BVH + retarget), additive custom poses
   (breathing/lean) with contacts maintained.

**How it plugs in (no extra steps for the caller)**
- The LLM path reasons about joint hierarchy / COM / contact when `character` is selected.
- The rule-based fallback pulls its seed from `references/physics_dimensions.md §8`.
- `scripts/enhance.py` already supports `--dims ...,character` (see `DIMS`, `FALLBACK_PHRASES`,
  `FALLBACK_RULE`). Example:
  `python enhance.py "一个战士挥剑劈砍" --target video --dims mechanics,causality,character`

## Video model prompt-length guard (视频模型提示词长度护栏)
Different video generators enforce different prompt character caps; exceeding them gets the
request truncated or rejected (400/422). This skill detects the chosen model's cap and
**compresses the enhanced prompt down to it** when needed, so what you paste always fits.

**When it triggers**
- Pass `--video-model <model>` for any `video` target. Supported keys:
  `runway, kling, sora, veo, hailuo, minimax, luma, pika, vidu, generic`.
- If `--target video` is set but `--video-model` is omitted, it defaults to `generic`
  (a conservative 2000-char cap) — you can always override with an explicit model.
- The cap is a **character** count and applies to the text pasted into the generator:
  the English tag string in `both` mode (the line after `EN:`), the whole prompt in
  `en` / `zh` mode. Character counts work for both Chinese and English since these are char limits.

**How compression works (three layers — local model first)**
1. **Soft self-limit (LLM generation path):** when a video model is given, the system prompt
   tells the model that model's cap so it stays under it while writing.
2. **Local-model compression (LLM path, when over cap):** if the generated prompt still
   exceeds the cap *and* a local LLM is reachable (i.e. not `--fallback`), `apply_video_limit()`
   calls `compress_with_local_model()` — a second, low-temperature call that asks the same
   local model to re-write the text to ≤ the cap while keeping the subject and every
   physics-critical detail (gravity / shadow / contact / momentum / COM / joint / collision …).
   This is the smarter, meaning-preserving pass.
3. **Deterministic trimmer (always on, final guarantee):** `compress_to_limit()` runs on the
   result regardless. It keeps the subject (first clause) + every physics-critical clause,
   drops lowest-priority trailing modifiers, and **hard-guarantees the result is ≤ the cap** —
   so even if the local model returns a hair over, the pasted text is never truncated. Works
   identically in `--fallback` (rule-based) mode, where it is the only compression layer.

**Output:** the JSON gains a `prompt_compression` object so you can verify it fired, including
which layer actually did the compress:
```json
"prompt_compression": {
  "video_model": "kling", "limit_chars": 2500, "limit_type": "hard",
  "original_chars": 3120, "compressed_chars": 2478, "applied": true,
  "method": "local-model",
  "note": "可灵/Kling API 上限 2500 字符（3.0 最高 3072，建议 ≤2500）"
}
```
`method` is one of `"none"` (already within cap), `"local-model"` (compressed by the local LLM),
or `"rule-based"` (deterministic trimmer only — e.g. in `--fallback` mode).
`applied: false` means the prompt was already within the cap.

**The limit table** (source-verified 2026; full table + references in
`references/video_model_limits.md`):

| model | prompt cap | type | note |
|-------|-----------|------|------|
| runway | 1000 | hard | Gen-4/4.5 官方上限 |
| kling (可灵) | 2500 (3.0 最高 3072) | hard | API 上限，建议 ≤2500 |
| sora (Sora 2) | 2500 | soft | 接口常见上限，OpenAI 未公布硬上限 |
| veo (Veo 3/3.1) | 4000 | hard | 上限约 4000 字符 |
| hailuo / minimax | 7000 | soft | Hailuo 3 上限约 7000 |
| luma | 1000 | soft | 无正式上限；>500 字符质量下降 |
| pika | 1000 | soft | 无正式上限，建议 ≤1000 |
| vidu | 1000 | soft | 无正式上限，建议 ≤1000 |
| generic (默认) | 2000 | soft | 未指定模型时的保守默认 |

## Gotchas
- A 5B model follows patterns, it does not truly simulate physics. The checklist is an
  acceptance tool, not a guarantee — final fidelity still depends on the downstream generator.
- Don't let the model "fix" impossible premises silently; if the base prompt is physically
  impossible (e.g. "anti-gravity cat"), keep it but flag the contradiction in the checklist.
- For `video`, extend the checklist with temporal items (trajectory continuity across frames,
  no teleporting, motion blur direction consistent with velocity) + interaction continuity
  (contact deformation/splash/rebound consistent across frames, no clipping or glued drifting).
- Aesthetics must NEVER override physics: "cinematic" is fine, "impossible glow that breaks
  the single light source" is not.
