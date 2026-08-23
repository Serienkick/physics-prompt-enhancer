# Physics Dimensions Reference (物理维度参考)

Knowledge core for the Physics Prompt Enhancer. Loaded on demand by the enhancer (LLM or
rule-based fallback). Each dimension lists: what to inject into the prompt, and the
checklist rule + pass criteria used to verify the generated result.

Seed dimensions are inspired by the physical-consistency benchmarks used by physics-aware
image models (e.g. ChronoEdit's PBench-Edit: gravity, support contact, trajectory, lighting
consistency, causal effect). This skill applies them at the *prompt* layer instead of the
*pixel* layer.

**v1.2 (2026-08-23):** Interaction 深化为「接触叙事」——接触状态（已接触/未接触/即将接触）
+ 接触媒介（直接/工具/介质/接近未触）+ 动作过程（追逐=逼近→闪避→接触或未接触）。
**v1.1 (2026-08-23):** + `interaction` (客体间交互：把两个客体的互动写具体、写客观)；
+ `aesthetic` (美学基调：在物理正确之上轻量点缀，物理优先)。

---

## 1. Optics (光学)
**Inject:** single dominant light source + its direction; shadow type (soft = far/diffuse,
hard = near/direct); ambient bounce; subsurface/transmission behavior for translucent materials;
consistent color temperature.

**Descriptor phrases (EN):** `single key light from upper left, physically correct cast shadows,
ambient occlusion in crevices, consistent light temperature, soft contact shadow`

**Checklist rule:** All shadows point away from one light source; no object lit from conflicting
directions; shadow hardness matches object distance to surface.

**Pass criteria:** trace any shadow to its caster and confirm direction matches the lit side;
check under-objects have contact shadow.

---

## 2. Mechanics (力学)
**Inject:** gravity direction (default down); support/rest contact; trajectory for moving
objects (parabolic arc under gravity, straight under thrust); inertia; collision/deformation.
碰撞/变形的**具体接触细节**见维度 6 Interaction。

**Descriptor phrases (EN):** `subject obeys gravity, resting firmly on surface, parabolic motion
arc, momentum carried through the pose, believable contact deformation`

**Checklist rule:** every unsupported object falls along gravity; moving objects follow a
physically valid path; contacts show reaction (dent, splash, compression).

**Pass criteria:** nothing floats without a stated cause; a jumping subject shows crouch→launch
and a landing impact; liquids/solids deform on contact.

---

## 3. Materials (材质)
**Inject:** surface response per material — metal reflects + specular, glass transmits + refracts,
rough wood matte, fabric drapes + wrinkles, skin has pores/micro-imperfection, water caustics.

**Descriptor phrases (EN):** `PBR-accurate materials, anisotropic metal reflections, refractive
glass, cloth with natural wrinkles and gravity sag, micro-skin detail, no plastic sheen`

**Checklist rule:** each surface's look matches its stated material; no "plastic AI sheen" on
organic/matte subjects.

**Pass criteria:** metal shows environment reflection; glass shows see-through + edge refraction;
cloth sags under gravity; skin not waxy-smooth.

---

## 4. Scale & Perspective (尺度比例)
**Inject:** real relative sizes; camera focal length implied by perspective; consistent
vanishing points; depth ordering.

**Descriptor phrases (EN):** `correct relative scale, single consistent vanishing point,
shallow depth of field isolating subject, believable perspective`

**Checklist rule:** relative object sizes are self-consistent; one perspective system; near
objects larger / far objects smaller and hazier.

**Pass criteria:** a cup next to a human is cup-sized; parallel lines converge to one point;
no two-scale contradiction.

---

## 5. Causality (因果一致)
**Inject:** explicit cause→effect — splash needs impact, bent needs force, trail needs motion,
steam needs heat, wet needs liquid source. 在双客体场景中，因果链通常是
「A 施力 → B 位移/变形」——具体化见维度 6 Interaction。

**Descriptor phrases (EN):** `visible cause for every effect, motion trail consistent with path,
impact splash at contact point, heat haze above warm surfaces`

**Checklist rule:** every depicted effect has a physically valid cause present in the frame;
no spontaneous/teleporting changes.

**Pass criteria:** a wet floor has a spill source; a knocked-over cup has a force direction;
smoke rises from its emitter.

---

## 6. Interaction (客体间交互) ★ v1.1 新增 · v1.2 接触叙事化
**适用:** 基础提示词含**两个及以上客体**（A 与 B）发生 接触/碰撞/支撑/悬挂/堆叠/嵌入/
包裹/拖拽/推拉/投掷/击打/摩擦/分离/追逐 等关系。**一旦存在双客体，本维度优先**——交互写
不具体，其余物理再对也"假"。

**核心：把交互写成「接触叙事」，回答三个问题——**

**① 接触状态（到底接触过没有，三者必居其一）:**
- **已接触**（contacted）：A 与 B 实际发生物理接触；写明接触点与接触后状态
- **未接触**（not contacted）：从未触碰，仅在空间上接近（追逐/对峙/隔空相对）；写明间距与趋势
- **即将接触**（about to contact）：运动趋势表明下一秒将接触（距离在缩短、相对速度指向接触点）

**② 接触媒介/方式（怎么接触的）:**
- **直接接触**（direct）：身体/表面直接贴合——手抓、脚踩、碰撞、拥抱、堆叠
- **工具中介**（via tool）：经第三方物体传递——球棒击球、绳拉重物、手持刀刃、杠杆撬动
- **介质传递**（through medium）：经流体或场——风推帆、水冲砂、冲击波掀桌、热传导
- **接近未触**（proximity only）：只接近不触碰——对峙、追逐未追上、虎视

**③ 动作过程（把关系动词展开成动作变化序列）:**
- 追逐：追者逼近（前倾/加速）→ 被追者闪避（转向/提速）→ 距离缩短或拉开 → 最终接触或未接触
- 撞击：加速冲向 → 接触点 → B 位移/变形/反弹
- 扑抓：伸展肢体 → 接触瞬间 → 抓住（已接触）或落空（未接触）
- 推拉：施力方向 → B 位移 → 反作用
- 悬挂：挂上 → 绳绷直 → 重物沿重力下垂

**同时写清（沿用 v1.1 字段）:**
- **接触类型**：点接触（球/指尖）/ 线接触（圆柱横放/刀刃）/ 面接触（平放/贴合）；接触面积越小→压强越大→尖细处易凹陷/穿透
- **力的方向与反作用**：A 对 B 施力方向明确；B 对 A 等大反向（推者姿态发力、被推者沿力方向位移）
- **材料对响应**：硬-硬（碰撞反弹/可能破损）；软-硬（软物贴合变形包裹硬物）；软-软（双方同时变形）
- **可观察结果**：压痕 / 凹陷 / 水花 / 尘土 / 摩擦痕迹 / 绷直的吊绳 / 贴合轮廓

**Descriptor phrases (EN):** `explicit A-B contact narrative: contact state (contacted / not
contacted / about to contact), contact medium (direct / via tool / through medium / proximity
only), action dynamics (chase = approach to dodge to close or miss), point/line/surface
contact, reaction force, dent/splash/dust at impact`

**Checklist rule:** 画面中能识别 A 与 B 的关系与动作；**能判断二者到底接触没有**；
若已接触——接触点/媒介/方式可指认，接触处有反作用证据；若未接触——两者间有明确空隙且无虚假粘连痕迹。

**Pass criteria（逐项对照画面核对）:**
- 已接触（碰撞/击打）→ B 沿 A 运动方向位移，接触点有变形/水花/尘土，接触方式可指认（直接撞上 / 经球棒击中）
- 已接触（支撑/堆叠）→ 接触面形状贴合承托轮廓，无悬空
- 未接触（追逐/对峙）→ A 与 B 之间有可见空隙；追者前倾、被追者闪避；**不得画出"假接触"（没有接触却留接触痕迹）**
- 即将接触 → 距离在缩短，肢体/物体朝向接触点，下一秒趋势明显
- 软物裹硬物 → 软物轮廓贴合硬物边缘并因重力下垂
- 悬挂 → 吊绳绷直、重物沿重力方向下垂
- 尖锐物压软物 → 接触点出现与尖端形状一致的凹陷

---

## 7. Aesthetic (美学基调) ★ v1.1 新增（轻量）
**定位:** 锦上添花，不是主角。**物理真实优先**——美学只能建立在物理正确的光影/材质之上，
不得引入画面内不存在的元素、不得违反光学维度的检查。

**Inject:**
- 光氛围: 单一主光 + 电影感轮廓光/体积光（阴影仍须物理正确）
- 构图: 三分法/黄金分割；视觉引导线（道路/光束/视线）指向主体
- 色彩: 统一色温；2~3 色和谐调色板；避免荧光失真
- 纵深: 空气透视（远处变淡变蓝）；由光圈决定的浅景深
- 焦点: 单一视觉重点；背景适度虚化但不破坏主体材质细节

**Descriptor phrases (EN):** `cinematic key light with subtle rim light, rule-of-thirds
composition, cohesive 2-3 color palette, atmospheric perspective, shallow depth of field on the subject`

**Checklist rule:** 视觉焦点明确；光影/阴影仍通过光学检查（美学不覆盖物理）；
主色调 ≤3 且统一；纵深层次清晰。

**Pass criteria:** 一眼找到主体；阴影方向与光源仍自洽；画面不杂乱（色相克制）；
近景清晰、远景淡出。

---

## Video-only extensions (视频专属)
When `target == video`, append temporal rules to the checklist:
- **Trajectory continuity:** object position changes smoothly frame-to-frame; no teleport.
- **Motion blur:** blur direction matches velocity vector; faster = more blur.
- **Secondary motion:** hair/cloth/liquid lag and settle after the primary motion.
- **Conservation:** no object appears/disappears without a cause.
- **Interaction (video):** A 与 B 的接触持续帧内一致——碰撞瞬间的变形/水花/反弹速度与
  相对速度匹配，分离后轨迹独立（无穿模、无粘连漂移）。

---

## Rule-based fallback template
When no LLM is present, append the EN descriptor phrases of the selected dimensions to the base
prompt and emit one checklist item per selected dimension using its `rule` + `pass_criteria`.

Example (image, all dims, base "猫追逐蝴蝶"):

Enhanced (EN tag): `a cat chasing a butterfly in a sunny garden, single key light upper-left,
physically correct cast shadows, cat lunges with front paw extended but the butterfly stays out
of reach (not contacted), chase dynamics: cat closes in, butterfly veers away, gap remains,
correct scale, visible cause and effect, cinematic rim light, shallow depth of field on the pair`

Checklist (zh):
- 光学: 阴影统一来自单一光源，猫与地面有接触阴影
- 力学: 猫的扑跃呈抛物线，未接触前保持运动趋势
- 材质: 猫毛层次、蝶翅半透明质感，无塑料高光
- 尺度: 猫与蝴蝶大小比例真实（蝶约猫掌大小）
- 因果: 猫扑击（因）→ 蝶转向闪避（果）
- 交互: 接触状态=**未接触**；媒介=接近未触；动作过程=猫前扑→蝶转向→距离未归零；
  验收：画面中猫爪与蝶之间有明显空隙，无「假接触」痕迹（未接触却留接触印）
- 美学: 视觉焦点在猫与蝶之间，主光+轮廓光，景深聚焦二者
