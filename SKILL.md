---
name: physics-prompt-enhancer
description: Rewrite a base creative prompt into a physics-grounded prompt plus a structured reality checklist, so AI image/video/3D generation looks physically plausible (correct gravity, lighting, materials, trajectory, causal consistency) — including concretely specified two-object interactions (contact type, force direction, reaction) and a light aesthetic touch (focus, unified lighting, restrained palette). Use when the user wants a prompt to feel "real", "physical", "not AI-plastic", asks to add physics/realism factors, make two objects' interaction more specific, or add a bit of aesthetics without losing realism. Model-agnostic; runs on a local 5B-class LLM (Ollama/LM Studio) with a rule-based fallback.
metadata:
  author: codexclaw
  version: "1.1"
  tags: [prompt, physics, realism, interaction, aesthetic, image-generation, video-generation, 3d, local-llm]
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
- Any request to make a creative prompt more physically plausible.

## Core workflow
1. Collect inputs: `base_prompt` (required), `target` ∈ {image, video, 3d} (default image),
   `dimensions` (subset of the 7 dimensions; default = all), `lang` ∈ {zh, en, both}
   (default: both — output Chinese prose + an English prompt ready to paste into generators).
   7 维度 = optics, mechanics, materials, scale, causality, **interaction(客体间交互)**,
   **aesthetic(美学基调)**。
2. Run the enhancer (preferred: local 5B LLM via `scripts/enhance.py`; fallback: apply the
   rule-based expansion in `references/physics_dimensions.md` directly, no model needed).
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
- `interaction` (客体间交互，双客体时优先) — 明确 A/B 的关系动词（接触/碰撞/支撑/悬挂/堆叠/嵌入/包裹/拖拽/推拉/投掷/击打/摩擦/分离）；接触类型（点/线/面）与接触面积自洽；B 的位移/变形方向与 A 施力方向一致，接触处有反作用证据（压痕/水花/贴合/绷直的绳）。pass_criteria 必须具体到 A/B，可在画面中逐项核对，不是形容词。
- `aesthetic` (美学基调，轻量) — 单一视觉焦点；光影氛围统一且不违反 optics；主色调 ≤3 且统一；纵深层次（空气透视/浅景深）。物理真实优先，美学不得引入画面内不存在的元素。

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
- When the base prompt has two or more objects (A & B), require the model to SPECIFY the
  interaction with structured fields — relation verb, contact type (point/line/surface),
  force direction & reaction, material-pair response, observable result — so the checklist
  item is verifiable, not vague.
- Aesthetic is a light garnish: single visual focus, unified lighting (must not violate
  optics), ≤3 cohesive hues, depth layers. Physics wins on any conflict.
- Always output valid JSON for the checklist (the script parses it).
- Keep the English tag string under ~60 tokens for generator compatibility.

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
