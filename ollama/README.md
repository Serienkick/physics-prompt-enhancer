# Ollama 专用模型 · gemma3:4b 固化版

把 physics-prompt-enhancer v1.2 的增强系统提示词**固化进模型本体**——创建后调用时
无需再传 system prompt，模型自带「物理真实感增强」能力（接触叙事 + 审校去重 + 美学点缀）。

## 创建模型

```bash
cd ollama
ollama create physics-enhancer -f Modelfile.gemma3-4b
```

## 使用（直接对话）

```bash
ollama run physics-enhancer "猫追逐蝴蝶"
```

或通过 API：

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "physics-enhancer",
  "messages": [{"role": "user", "content": "猫追逐蝴蝶"}],
  "stream": false
}'
```

模型会输出两部分（JSON）：
- `enhanced_prompt` —— 增强后的提示词（中文散文 + 英文 tag）
- `reality_checklist` —— 逐项可核对的物理验收清单（interaction 项以「接触状态=…」开头）

## 与 enhance.py 的关系

- `scripts/enhance.py` 每次调用时把 SYSTEM_PROMPT 作为 system message 发给底层模型（灵活，可换模型）；
- 本 Modelfile 把同一份 SYSTEM_PROMPT 固化进 `physics-enhancer` 模型（省事，system 不占上下文、模型即专用）。
  两者效果等价；直接改 `enhance.py` 的 SYSTEM_PROMPT 后，若想同步到模型，重新执行
  `ollama create physics-enhancer -f Modelfile.gemma3-4b` 即可。

## 模型要求

- 基础模型 `gemma3:4b`（约 3.3GB，4-bit 量化，8GB 显存 / Apple Silicon 可跑）
- Ollama 0.3.x+（本机实测 0.32.13）

## 版本

- v1.2：接触叙事（接触状态/媒介/动作过程）+ 审校去重 + 美学基调
