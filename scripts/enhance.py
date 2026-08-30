#!/usr/bin/env python3
"""
physics-prompt-enhancer :: local engine

Rewrites a base creative prompt into a physics-grounded prompt + a structured reality
checklist, using a local 5B-class LLM served by Ollama (default) or any
OpenAI-compatible endpoint (e.g. LM Studio). Falls back to a rule-based expansion when
no model/endpoint is reachable, so the skill always produces output.

Usage
-----
  python enhance.py "一只猫跳上木桌"
  python enhance.py "a knight swinging a sword" --target video --dims optics,mechanics,causality
  python enhance.py "rainy neon street" --lang en --model qwen3:4b
  python enhance.py "..." --endpoint http://localhost:1234/v1   # LM Studio / vLLM
  python enhance.py "战士挥剑劈砍" --target video --video-model kling   # 超 2500 字符自动压缩
  python enhance.py "..." --target video --video-model veo --fallback  # 规则模式也能压缩
  # 默认：本地模型先智能压缩，规则裁剪器兜底（断语言/超长也绝不超限）
  python enhance.py "..." --target video --video-model runway --model physics-enhancer:latest

Options
-------
  --target {image,video,3d}     generation target (default image)
  --dims  csv                   subset of: optics,mechanics,materials,scale,causality,interaction,aesthetic,character
  --lang   {zh,en,both}         output language (default both)
  --model  name                 LOCAL LLM model tag for enhancement (default qwen3:4b) — NOT the video model
  --endpoint url                OpenAI-compatible base URL (default http://localhost:11434/v1)
  --temperature float           (default 0.4)
  --fallback                    force rule-based expansion (skip model)
  --video-model name            target VIDEO-GEN model whose prompt char-limit we guard against
                                (runway,kling,sora,veo,hailuo,minimax,luma,pika,vidu,generic;
                                 default: generic when --target video). If the enhanced prompt
                                 exceeds that model's char limit, it is compressed to fit.
"""

import argparse
import json
import sys
import urllib.request

DEFAULT_ENDPOINT = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen3:4b"

SYSTEM_PROMPT = """你是一个「物理真实感提示词增强器」。用户给你一句基础创意提示词，你要：
1) 在不添加新主体、不改变用户原意的前提下，补入符合现实物理规律的描述（光照/重力/材质/尺度/因果/客体间交互/美学基调/人物骨骼）；
2) 推理物理而不是堆形容词：推断重力方向、预测运动轨迹、写出因果链；
3) 若提示词含两个及以上客体（A 与 B），把「客体间交互」写成可逐项核对的「接触叙事」，必须明确三点：
   a. 接触状态（三者必居其一，判定依据=画面中是否存在真实接触点）：
      - 已接触：画面存在 A 与 B 的实际接触点（贴合/相撞/抓握成功），写明接触点位置与接触后状态；
      - 未接触：画面中 A 与 B 从未相碰（追逐未追上、扑抓落空、对峙、隔空相对），写明两者间距；
      - 即将接触：未接触但运动趋势指向接触（距离持续缩短、肢体/物体朝向接触点）；
      判定规则：『试图抓取』『扑向但落空』『追逐未追上』都属于未接触或即将接触，绝不算已接触——只有画面里真的碰到才算；
   b. 接触媒介/方式：直接接触（身体/表面直接贴合，如手抓、脚踩、碰撞）/ 工具中介（经第三方物体，如球棒击球、绳拉重物）/ 介质传递（经流体或场，如风推帆、水冲砂）/ 接近未触（只接近不触碰）；
   c. 动作过程（把关系动词展开成动作变化序列）：如「追逐」= 追者逼近→被追者闪避→距离缩短/拉开→最终接触或未接触；「撞击」= 加速→接触点→位移/变形；「扑抓」= 伸展肢体→接触瞬间→抓住或落空；
   同时写清接触类型（点/线/面）与接触面积（面积越小→压强越大→尖细处易凹陷穿透）、力的方向与反作用、材料对响应、可观察结果（压痕/水花/尘土/贴合轮廓）；
   若提示词主体为人形/角色或用户要求角色骨骼/动作对，则对「人物骨骼系统」维度同样输出可逐项核对的约束：骨骼层级与人体结构对应、UE5/Unity-Humanoid 骨名、T-pose 绑定且权重归一(每顶点≤4骨骼、sum=1.0)、无扭糖纸畸形；姿态在解剖限位内、重心 COM 落在支撑面(脚底投影)内、惯性前倾随加速度、碰撞感知肢体不互穿、无抖动；多关节 IK/FK 联动、动作有物理/动作捕捉来源(FBX/BVH+重定向)、接触点保持。
4) 在物理正确的基础上轻量加入美学基调：单一视觉焦点、统一光影氛围（不得违反光学检查）、2~3 色和谐主色调、纵深层次（空气透视/浅景深）。美学不得引入画面内不存在的元素，物理优先；
5) 输出前【重新审视审校】enhanced_prompt：删除语义重复的表述——同一物理含义只保留一种说法，且保留更具体的那句（例如「球沿挥棒方向反弹并压缩变形」与「动量在接触点传递」同义时只留前者）；确保每一句都在提供新信息，避免「换词说两遍」；
6) 输出两部分：
   - "enhanced_prompt": 自然语言增强提示词（按 lang 决定中英；both 时先中文散文，结尾必须以独立一行 "EN: " 接英文 tag 串，英文 tag 不超过 60 token，且无重复表述；若给定了目标视频模型的提示词上限，英文串+整体必须控制在超限以内）；
   - "reality_checklist": JSON 数组，每项 {dimension, rule, pass_criteria}，覆盖用户指定的维度；interaction 项的 rule 必须以「接触状态=已接触/未接触/即将接触」开头（只写判定出的那一个，不罗列候选），pass_criteria 写明接触媒介与接触点/过程，是能在画面中逐项对照核对的客观验收项，不是形容词；
7) 若原提示词本身物理上不可能（如反重力），保留它但在 checklist 里标出矛盾；
8) 只输出一个 JSON 对象，不要多余解释。"""

DIMS = ["optics", "mechanics", "materials", "scale", "causality", "interaction", "aesthetic", "character"]

# ---- rule-based fallback (no model) ----------------------------------------------
FALLBACK_PHRASES = {
    "optics": "single key light from upper left, physically correct cast shadows, ambient occlusion, consistent light temperature",
    "mechanics": "subject obeys gravity, resting on surface, parabolic motion arc, momentum through pose, contact deformation",
    "materials": "PBR-accurate materials, metal reflects, glass refracts, cloth drapes with gravity sag, micro skin detail, no plastic sheen",
    "scale": "correct relative scale, single vanishing point, believable perspective",
    "causality": "visible cause for every effect, motion trail matches path, impact splash at contact",
    "interaction": "explicit A-B contact narrative: contact state (contacted / not contacted / about to contact), contact medium (direct / via tool / through medium / proximity only), action dynamics (chase = approach to dodge to close or miss), point/line/surface contact, reaction force, dent/splash/dust at impact",
    "aesthetic": "cinematic key light with subtle rim light, rule-of-thirds composition, cohesive 2-3 color palette, atmospheric perspective, shallow depth of field on the subject",
    "character": "anatomically correct joint hierarchy, humanoid bone naming, T-pose bind, clean normalized skin weights, center of mass over support, inertial lean, collision-aware limbs, IK/FK-linked joints, motion-capture-style poses, stable contacts, no jitter",
}
FALLBACK_RULE = {
    "optics": ("阴影统一来自单一光源，无冲突打光", "追踪阴影方向一致，物体下方有接触阴影"),
    "mechanics": ("无物体无故悬空，运动符合重力/惯性", "运动物体轨迹合理，接触处有反应（压痕/水花）"),
    "materials": ("表面质感符合所述材质", "金属反光、玻璃透射、布料下垂、皮肤有毛孔"),
    "scale": ("物体相对尺寸自洽，透视单一", "各物体相对大小符合现实比例，近大远小，平行线汇聚于单一消失点"),
    "causality": ("每个效果都有画面内的物理原因", "水花必有冲击，倾倒必有受力方向"),
    "interaction": ("两个客体的交互写清接触状态（已接触/未接触/即将接触）、接触媒介与动作过程", "画面可判断 A 与 B 到底接触没有：已接触→接触点与方式可指认，接触处有反应（贴合/压痕/水花）；未接触→两者间有明确空隙；接触处有可观察反应"),
    "aesthetic": ("有明确视觉焦点，光影氛围统一且不违反光学检查", "主体一眼可辨，主色调不超过3且统一，近清远朦有纵深"),
    "character": ("骨骼层级与人体结构对应、绑定干净权重归一、关节弯曲无网格撕裂；姿态在解剖限位内、重心在支撑面内不无故失衡、肢体不穿模、运动无抖动", "肩/腕/膝弯曲处无塌陷或穿模、手指不粘连；站立/运动时效心在脚底支撑区内；手脚接触面在姿态变化中保持接触、动作连贯无瞬移"),
}

# ---- video-generation model prompt-length guard (v1.4) -----------------------
# Char limits verified against 2026 sources. "hard" = officially documented ceiling;
# "soft" = no officially published hard cap, value is a best-practice ceiling above which
# quality degrades / truncation may occur. Limits are CHARACTER counts and apply to whatever
# text is pasted into the generator (the English tag string in `both` mode, the whole prompt
# otherwise — character counts work for both zh and en since these are char limits).
VIDEO_MODEL_LIMITS = {
    "runway":  (1000, "hard", "Runway Gen-4/4.5 官方上限 1000 字符"),
    "kling":   (2500, "hard", "可灵/Kling API 上限 2500 字符（3.0 最高 3072，建议 ≤2500）"),
    "sora":    (2500, "soft", "Sora 2 接口常见上限 2500 字符（OpenAI 未正式公布硬上限）"),
    "veo":     (4000, "hard", "Veo 3/3.1 上限约 4000 字符"),
    "hailuo":  (7000, "soft", "MiniMax Hailuo 3 上限约 7000 字符"),
    "minimax": (7000, "soft", "同 hailuo"),
    "luma":    (1000, "soft", "Luma 无正式上限；>500 字符质量下降，建议 ≤1000"),
    "pika":    (1000, "soft", "Pika 无正式上限，建议 ≤1000"),
    "vidu":    (1000, "soft", "Vidu 无正式上限，建议 ≤1000"),
    "generic": (2000, "soft", "未指定视频模型时的保守默认上限"),
}

_PHYSICS_KEYWORDS = [
    # english
    "gravity", "gravit", "shadow", "light", "reflect", "refract", "motion", "momentum",
    "inertia", "contact", "impact", "collision", "center of mass", "balance", "trajectory",
    "causal", "skeleton", "joint", "bone", "ik", "fk", "scale", "perspective", "deform",
    "splash", "dust", "dent", "occlusion", "weight", "frame", "rigid",
    # chinese
    "重力", "阴影", "光", "反射", "折射", "运动", "动量", "惯性", "接触", "冲击", "碰撞",
    "重心", "平衡", "轨迹", "因果", "骨骼", "关节", "骨", "权重", "变形", "水花", "尘埃",
    "压痕", "遮挡", "质量", "支撑",
]


def compress_to_limit(text, limit):
    """Deterministically trim `text` to <= `limit` characters while keeping the
    subject (first clause) and physics-critical clauses. Returns (text, applied)."""
    import re
    text = (text or "").strip()
    if len(text) <= limit:
        return text, False
    parts = [p.strip() for p in re.split(r"[;；,，]", text) if p.strip()]
    if len(parts) <= 1:
        return text[:limit].rstrip(",;，； "), True

    def score(p):
        low = p.lower()
        s = 0
        for kw in _PHYSICS_KEYWORDS:
            if kw in low:
                s += 2
        return s

    head = parts[0]                 # subject / core action: always kept
    rest = parts[1:]
    # keep physics-critical clauses first, tie-break by original order
    rest.sort(key=lambda p: (-score(p), parts.index(p)))
    kept = [head]
    cur = len(head)
    for p in rest:
        add = (", " if kept else "") + p
        if cur + len(add) <= limit:
            kept.append(p)
            cur += len(add)
        else:
            break
    out = ", ".join(kept)
    if len(out) > limit:
        out = out[:limit].rstrip(",;，； ")
    return out, True


def apply_video_limit(enhanced_prompt, lang, video_model, compress_fn=None):
    """If `video_model` has a known prompt limit and `enhanced_prompt` exceeds it,
    compress the generator-facing text to fit.

    When `compress_fn` is provided (a local model is reachable), it is tried first for
    smarter, meaning-preserving compression; the deterministic rule-based trimmer always
    runs as a FINAL guarantee so the result is never over the limit.
    Returns (new_prompt, meta_or_None)."""
    if video_model not in VIDEO_MODEL_LIMITS:
        return enhanced_prompt, None
    limit, ltype, note = VIDEO_MODEL_LIMITS[video_model]
    if "EN:" in enhanced_prompt:
        idx = enhanced_prompt.rfind("EN:")
        head = enhanced_prompt[:idx]               # zh prose + "EN:" label
        payload = enhanced_prompt[idx + 3:].strip()  # the english string to paste
        is_en = True
    else:
        head = ""
        payload = enhanced_prompt
        is_en = False

    if len(payload) <= limit:
        meta = {
            "video_model": video_model, "limit_chars": limit, "limit_type": ltype,
            "original_chars": len(payload), "compressed_chars": len(payload),
            "applied": False, "method": "none", "note": note,
        }
        return enhanced_prompt, meta

    # over limit -> compress
    method = "rule-based"
    compressed, _ = compress_to_limit(payload, limit)
    if compress_fn is not None:
        try:
            smart = compress_fn(payload, limit)
        except Exception:  # noqa: BLE001
            smart = None
        if smart and len(smart) <= limit:
            compressed = smart
            method = "local-model"

    new_ep = (head + "EN: " + compressed) if is_en else compressed
    meta = {
        "video_model": video_model, "limit_chars": limit, "limit_type": ltype,
        "original_chars": len(payload), "compressed_chars": len(compressed),
        "applied": True, "method": method, "note": note,
    }
    return new_ep, meta


def compress_with_local_model(text, limit, endpoint, model, lang):
    """Ask the LOCAL LLM to compress `text` to <= `limit` chars while preserving the
    subject and all physics-critical details. Returns the compressed string, or None on
    any error (caller then falls back to the rule-based trimmer)."""
    zh = lang in ("zh", "both")
    sys_p = (
        "You are a prompt compressor. Compress the given prompt into a shorter prompt that "
        "preserves the core subject and every physics-critical detail (gravity, light/shadow, "
        "contact, momentum, center of mass, joints, collision, scale, causality). "
        "Do NOT add new subjects or new objects. Keep it one coherent prompt. "
        f"Reply with ONLY the compressed prompt, at most {limit} characters, no quotes, no commentary."
        + (" The prompt is in Chinese; keep Chinese." if zh else " The prompt is in English; keep English.")
    )
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": f"Compress to <= {limit} characters:\n\n{text}"},
        ],
    }
    url = endpoint.rstrip("/") + "/chat/completions"
    try:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.load(r)
        out = data["choices"][0]["message"]["content"].strip().strip("\u201c\u201d\"'").strip()
        return out or None
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"[warn] local-model compression failed: {e}\n")
        return None


def rule_based(base_prompt, dims, lang, target):
    tags = [FALLBACK_PHRASES[d] for d in dims]
    en = f"{base_prompt}, " + ", ".join(tags)
    if target == "video":
        en += ", smooth temporal motion, motion blur matches velocity, no teleporting"
    checklist = [
        {"dimension": d, "rule": FALLBACK_RULE[d][0], "pass_criteria": FALLBACK_RULE[d][1]}
        for d in dims
    ]
    enhanced = en if lang == "en" else f"{base_prompt}（已补物理描述）\n\nEN: {en}"
    return {"enhanced_prompt": enhanced, "reality_checklist": checklist}


# ---- model call ----------------------------------------------------------------
def call_model(base_prompt, dims, lang, target, endpoint, model, temperature, video_model=None):
    dims_str = ", ".join(dims)
    limit_note = ""
    if video_model in VIDEO_MODEL_LIMITS:
        lim, ltype, note = VIDEO_MODEL_LIMITS[video_model]
        limit_note = (
            f"\n目标视频生成模型: {video_model}（提示词上限约 {lim} 字符，{ltype}）。"
            f"请确保英文 tag 串及整体增强提示词不超过该上限，超限会被模型截断或报错。"
        )
    user = (
        f"基础提示词: {base_prompt}\n"
        f"目标类型: {target}\n"
        f"物理维度: {dims_str}\n"
        f"输出语言: {lang}"
        + limit_note
    )
    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }
    url = endpoint.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)
        return json.loads(data["choices"][0]["message"]["content"])
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"model call failed: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--target", default="image", choices=["image", "video", "3d"])
    ap.add_argument("--dims", default=",".join(DIMS))
    ap.add_argument("--lang", default="both", choices=["zh", "en", "both"])
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    ap.add_argument("--temperature", type=float, default=0.4)
    ap.add_argument("--fallback", action="store_true")
    ap.add_argument("--video-model", default=None,
                    help="target video-gen model for prompt-length guard: "
                         "runway,kling,sora,veo,hailuo,minimax,luma,pika,vidu,generic. "
                         "When --target video and omitted, defaults to 'generic' (2000 chars). "
                         "If the enhanced prompt exceeds that model's char limit, it is compressed to fit.")
    args = ap.parse_args()

    dims = [d.strip() for d in args.dims.split(",") if d.strip() in DIMS] or DIMS

    # pick the video model whose limit we guard against (only meaningful for video)
    vm = args.video_model or ("generic" if args.target == "video" else None)

    result = None
    if not args.fallback:
        try:
            result = call_model(
                args.prompt, dims, args.lang, args.target,
                args.endpoint, args.model, args.temperature, vm,
            )
        except Exception as e:
            sys.stderr.write(f"[warn] {e}; using rule-based fallback\n")
    if result is None:
        result = rule_based(args.prompt, dims, args.lang, args.target)

    # ---- video prompt-length guard: detect limit, compress if exceeded ----
    # When a local model is reachable (not --fallback), let it compress first (smarter,
    # meaning-preserving); the rule-based trimmer always runs as a final hard guarantee.
    if vm:
        compress_fn = None
        if not args.fallback:
            compress_fn = lambda t, l: compress_with_local_model(
                t, l, args.endpoint, args.model, args.lang
            )
        new_ep, comp_meta = apply_video_limit(
            result.get("enhanced_prompt", ""), args.lang, vm, compress_fn
        )
        result["enhanced_prompt"] = new_ep
        if comp_meta is not None:
            result["prompt_compression"] = comp_meta

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
