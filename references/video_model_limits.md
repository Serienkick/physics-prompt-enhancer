# Video Model Prompt-Length Guard (视频模型提示词长度护栏)

不同视频生成模型对提示词有不同**字符上限**。超限会被截断或返回 400/422 错误，导致
物理描述丢失、生成结果偏离预期。本模块在 `enhance.py` 中识别所选视频模型的可用长度，
并在增强提示词超限时**确定性压缩到上限以内**。

> 上限为**字符数（character）**统计，对中文与英文同时适用（这些模型的上限通常以字符计，
> 而非 token）。压缩目标是"要贴进生成器的文本"：`both` 模式下的 `EN:` 英文串、
> `en`/`zh` 模式下的整段提示词。

---

## 1. 上限对照表（2026 联网核实）

| model key | 提示词上限 | 类型 | 说明 / 来源 |
|-----------|-----------|------|------------|
| `runway` | **1000** | hard | Runway Gen-4 / Gen-4.5 官方上限（help.runwayml.com 明确 "Text prompt character limit 1000 characters"）|
| `kling` (可灵) | **2500**（3.0 最高 3072）| hard | Kling API 上限 2500 字符；3.0 Omni API 文档允许 ≤3072，但建议 ≤2500。来源：klingai.com API 文档、atlascloud 指南 |
| `sora` (Sora 2) | **2500** | soft | sora-2 接口常见上限 2500 字符（七牛 sora API 文档 "最大 2500 字符"）；OpenAI 官方未正式公布硬上限 |
| `veo` (Veo 3 / 3.1) | **4000** | hard | Veo 3 上限约 4000 字符（azerion API 文档 "Maximum 4000 characters"；aiapiplaybook "1–4096"）|
| `hailuo` / `minimax` | **7000** | soft | MiniMax Hailuo 3 上限约 7000 字符（morphed.app 对比："up to roughly 7,000 characters"）；无官方硬上限 |
| `luma` | **1000** | soft | Luma 无正式上限；>500 字符质量下降，建议 ≤1000（aiagentsquare："500+ characters sometimes degrade quality"）|
| `pika` | **1000** | soft | Pika 无正式上限，短视频为主，建议 ≤1000 |
| `vidu` | **1000** | soft | Vidu 无正式上限，建议 ≤1000 |
| `generic`（默认）| **2000** | soft | 未指定视频模型时的保守默认上限（`--target video` 且未传 `--video-model` 时启用）|

**类型说明**
- `hard` = 官方明确公布的硬上限，超限必被拒绝/截断。
- `soft` = 无官方硬上限，该值为"质量开始下降 / 建议不要超过"的最佳实践上限；超出可能被截断或质量劣化。

**参考来源（2026-08 检索）**
- Runway Gen-4 官方帮助：<https://help.runwayml.com/hc/en-us/articles/37327109429011>
- Kling AI 视频提示词指南 2026：<https://www.atlascloud.ai/zh/blog/tips/kling-ai-video-prompt-guide>
- Kling 3.0 Omni API 文档：<https://www.klingai.com/document-api/api/video/3-0-omni/image-to-video>
- Veo 3 API 文档（azerion）：<http://docs.azerion.ai/api-reference/create-video/veo-3>
- Veo 3 API 教程（aiapiplaybook）：<https://aiapiplaybook.com/zh/blog/veo-3-api-tutorial-generate-cinematic-video-with-google-s-latest-model/>
- Hailuo 3 vs Veo 3（morphed.app）：<https://morphed.app/blog/hailuo-3-vs-veo-3>
- Luma Dream Machine（aiagentsquare）：<https://aiagentsquare.com/agents/luma-ai>
- Sora 2 视频生成 API（OpenAI）：<https://developers.openai.com/api/docs/guides/video-generation>
- Sora 系列视频生成（七牛，sora-2 上限 2500）：<https://developer.qiniu.com/aitokenapi/13216/video-generate-sora-api>

> 注：模型版本迭代快，上限可能变化。若某模型上线新版本调整了上限，只需更新
> `enhance.py` 中的 `VIDEO_MODEL_LIMITS` 字典即可，无需改动其他逻辑。

---

## 2. 压缩策略（三层：本地模型优先）

### 2.1 软上限（仅 LLM 路径）
当传了 `--video-model` 且走本地 LLM 时，`call_model()` 会在用户消息里附加：
> 目标视频生成模型: `<model>`（提示词上限约 `<N>` 字符，`<hard|soft>`）。
> 请确保英文 tag 串及整体增强提示词不超过该上限，超限会被模型截断或报错。

让模型在生成阶段就自我约束。

### 2.2 本地模型智能压缩（LLM 路径，超限时触发）
若生成后仍超限、且**本地 LLM 可达**（即未传 `--fallback`），`apply_video_limit()` 会调用
`compress_with_local_model()`——**同一个本地模型**再做一次低温度（temperature=0.2）调用，
要求它把文本重写到 ≤ 上限，同时保留主体与全部物理关键信息（重力/阴影/接触/动量/重心/关节/
碰撞/尺度/因果…），不新增主体、不新增物体。这是更"聪明"、保义的压缩层。

- 若本地模型返回的结果 ≤ 上限 → 采用它，`method="local-model"`；
- 若本地模型返回仍超限或调用失败 → 退化到 2.3 的确定性裁剪器（绝不超限）。

### 2.3 硬兜底（始终生效，规则模式也生效）
`compress_to_limit()` 作为**最终硬保证**，无论前面哪层，生成后都会对"要贴进生成器的文本"再跑一次：

1. 若文本长度 ≤ 上限 → 原样返回，`applied=false`。
2. 否则按 `；;，,` 切分为子句；若只有 1 个子句（单句过长）→ 直接硬截断到上限。
3. 多子句时：
   - **首子句（主体/核心动作）永远保留**；
   - 其余子句按"物理相关性"打分（含 gravity/shadow/contact/momentum/center of mass/
     joint/bone/collision/重心/接触/骨骼/碰撞… 等中英关键词 +2 分），
     分数高的优先保留，同分按原顺序；
   - 依次追加，直到再加一个子句就会超上限为止；
   - 保证拼接后长度 ≤ 上限（必要时末位 `rstrip` 标点后硬截断）。

这种贪心策略优先保住"主体 + 物理约束"，先丢尾部低优先级的修饰词，
既符合本 skill 的"物理优先"原则，也保证长度绝对不超限。

---

## 3. 调用方式

```bash
# 指定视频模型，超限自动压缩（LLM 路径：本地模型先智能压缩，再硬兜底）
python scripts/enhance.py "战士挥剑劈砍，慢镜头，雨夜霓虹" --target video --video-model kling --lang en

# 显式指定本地模型（本机已装 physics-enhancer:latest，基于 gemma3:4b）
python scripts/enhance.py "战士挥剑劈砍，慢镜头，雨夜霓虹" --target video --video-model runway --model physics-enhancer:latest

# 规则模式（无本地 LLM）：只用确定性裁剪器，method="rule-based"
python scripts/enhance.py "战士挥剑劈砍" --target video --video-model runway --fallback

# 不指定视频模型时，--target video 默认按 generic(2000) 护栏
python scripts/enhance.py "一段长描述…" --target video
```

输出 JSON 会多出一个 `prompt_compression` 字段，便于核验是否触发压缩：

```json
{
  "enhanced_prompt": "…（已压缩到上限内的文本）…",
  "reality_checklist": [ … ],
  "prompt_compression": {
    "video_model": "kling",
    "limit_chars": 2500,
    "limit_type": "hard",
    "original_chars": 3120,
    "compressed_chars": 2478,
    "applied": true,
    "method": "local-model",
    "note": "可灵/Kling API 上限 2500 字符（3.0 最高 3072，建议 ≤2500）"
  }
}
```

`applied: false` 表示原提示词已在上限内，无需压缩。
`method` 取值：`"none"`（未超限）/ `"local-model"`（本地模型压缩）/ `"rule-based"`（仅确定性裁剪器，如 `--fallback` 模式）。

---

## 4. 与双输出模型的业务对齐
- **Inject（注入）**：`--video-model` 触发 `VIDEO_MODEL_LIMITS` 查表 + 软上限指令注入。
- **EN descriptor（英文串）**：`compress_to_limit()` 保证英文 tag 串 ≤ 模型上限。
- **checklist rule（校验项）**：`prompt_compression` 提供"是否超限/压缩了多少"的可核验项，
  与 reality_checklist 同属"机器可核验"的输出哲学一致。
- **pass_criteria（验收标准）**：`applied/original/compressed` 三段数值即验收依据——
  用户可据此确认"贴进去的提示词确实没被截断"。
