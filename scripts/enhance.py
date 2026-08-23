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

Options
-------
  --target {image,video,3d}     generation target (default image)
  --dims  csv                   subset of: optics,mechanics,materials,scale,causality,interaction,aesthetic
  --lang   {zh,en,both}         output language (default both)
  --model  name                 Ollama model tag (default qwen3:4b)
  --endpoint url                OpenAI-compatible base URL (default http://localhost:11434/v1)
  --temperature float           (default 0.4)
  --fallback                    force rule-based expansion (skip model)
"""

import argparse
import json
import sys
import urllib.request

DEFAULT_ENDPOINT = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen3:4b"

SYSTEM_PROMPT = """你是一个「物理真实感提示词增强器」。用户给你一句基础创意提示词，你要：
1) 在不添加新主体、不改变用户原意的前提下，补入符合现实物理规律的描述（光照/重力/材质/尺度/因果/客体间交互/美学基调）；
2) 推理物理而不是堆形容词：推断重力方向、预测运动轨迹、写出因果链；
3) 若提示词含两个及以上客体（A 与 B），把「客体间交互」写具体、写客观（双客体时本项优先）：
   - 明确关系动词：接触/碰撞/支撑/悬挂/堆叠/嵌入/包裹/拖拽/推拉/投掷/击打/摩擦/分离；
   - 明确接触类型：点接触/线接触/面接触，并说明接触面积（面积越小→压强越大→尖细处易凹陷穿透）；
   - 明确力的方向与反作用：B 的位移/变形方向与 A 施力方向一致，接触处有反作用证据（A 推 B，B 沿推力方向动，A 姿态发力）；
   - 说明材料对响应：硬-硬（碰撞反弹或破损）、软-硬（软物贴合包裹硬物）、软-软（双方同时变形）；
   - 给出可观察结果：压痕/水花/尘土/摩擦痕迹/绷直的吊绳/贴合轮廓；
4) 在物理正确的基础上轻量加入美学基调：单一视觉焦点、统一光影氛围（不得违反光学检查）、
   2~3 色和谐主色调、纵深层次（空气透视/浅景深）。美学不得引入画面内不存在的元素，物理优先；
5) 输出两部分：
   - "enhanced_prompt": 自然语言增强提示词（按 lang 决定中英；both 时先中文散文再给英文 tag 串，英文 tag 不超过 60 token）；
   - "reality_checklist": JSON 数组，每项 {dimension, rule, pass_criteria}，覆盖用户指定的维度；
     interaction 项的 rule/pass_criteria 必须具体到 A/B 两客体，是能在画面中逐项对照核对的客观验收项，不是形容词；
6) 若原提示词本身物理上不可能（如反重力），保留它但在 checklist 里标出矛盾；
7) 只输出一个 JSON 对象，不要多余解释。"""

DIMS = ["optics", "mechanics", "materials", "scale", "causality", "interaction", "aesthetic"]

# ---- rule-based fallback (no model) ----------------------------------------------
FALLBACK_PHRASES = {
    "optics": "single key light from upper left, physically correct cast shadows, ambient occlusion, consistent light temperature",
    "mechanics": "subject obeys gravity, resting on surface, parabolic motion arc, momentum through pose, contact deformation",
    "materials": "PBR-accurate materials, metal reflects, glass refracts, cloth drapes with gravity sag, micro skin detail, no plastic sheen",
    "scale": "correct relative scale, single vanishing point, believable perspective",
    "causality": "visible cause for every effect, motion trail matches path, impact splash at contact",
    "interaction": "explicit A-B contact (point/line/surface), reaction force opposing the push, soft object deforms to hug the rigid one, momentum transfer at contact, dent/splash/dust at impact",
    "aesthetic": "cinematic key light with subtle rim light, rule-of-thirds composition, cohesive 2-3 color palette, atmospheric perspective, shallow depth of field on the subject",
}
FALLBACK_RULE = {
    "optics": ("阴影统一来自单一光源，无冲突打光", "追踪阴影方向一致，物体下方有接触阴影"),
    "mechanics": ("无物体无故悬空，运动符合重力/惯性", "运动物体轨迹合理，接触处有反应（压痕/水花）"),
    "materials": ("表面质感符合所述材质", "金属反光、玻璃透射、布料下垂、皮肤有毛孔"),
    "scale": ("物体相对尺寸自洽，透视单一", "各物体相对大小符合现实比例，近大远小，平行线汇聚于单一消失点"),
    "causality": ("每个效果都有画面内的物理原因", "水花必有冲击，倾倒必有受力方向"),
    "interaction": ("两个客体的关系动词可识别，接触类型与力的方向自洽", "A 与 B 接触处有可观察反应（贴合/压痕/水花/反作用位移），B 位移方向与 A 施力方向一致"),
    "aesthetic": ("有明确视觉焦点，光影氛围统一且不违反光学检查", "主体一眼可辨，主色调不超过3且统一，近清远朦有纵深"),
}


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
def call_model(base_prompt, dims, lang, target, endpoint, model, temperature):
    dims_str = ", ".join(dims)
    user = (
        f"基础提示词: {base_prompt}\n"
        f"目标类型: {target}\n"
        f"物理维度: {dims_str}\n"
        f"输出语言: {lang}"
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
    args = ap.parse_args()

    dims = [d.strip() for d in args.dims.split(",") if d.strip() in DIMS] or DIMS

    result = None
    if not args.fallback:
        try:
            result = call_model(
                args.prompt, dims, args.lang, args.target,
                args.endpoint, args.model, args.temperature,
            )
        except Exception as e:
            sys.stderr.write(f"[warn] {e}; using rule-based fallback\n")
    if result is None:
        result = rule_based(args.prompt, dims, args.lang, args.target)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
