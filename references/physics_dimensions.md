# Physics Dimensions Reference (物理维度参考)

Knowledge core for the Physics Prompt Enhancer. Loaded on demand by the enhancer (LLM or
rule-based fallback). Each dimension lists: what to inject into the prompt, and the
checklist rule + pass criteria used to verify the generated result.

Seed dimensions are inspired by the physical-consistency benchmarks used by physics-aware
image models (e.g. ChronoEdit's PBench-Edit: gravity, support contact, trajectory, lighting
consistency, causal effect). This skill applies them at the *prompt* layer instead of the
*pixel* layer.

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

## 6. Interaction (客体间交互) ★ v1.1 新增
**适用:** 基础提示词含**两个及以上客体**（A 与 B）发生 接触/碰撞/支撑/悬挂/堆叠/嵌入/
包裹/拖拽/推拉/投掷/击打/摩擦/分离 等关系。**一旦存在双客体，本维度优先**——交互写不
具体，其余物理再对也"假"。

**Inject —— 结构化字段（把交互写具体、写客观的模板）:**
- **关系动词**：接触 / 碰撞 / 支撑 / 悬挂 / 堆叠 / 嵌入 / 包裹 / 拖拽 / 推拉 / 投掷 / 击打 / 摩擦 / 分离
- **接触类型**：点接触（球/指尖）/ 线接触（圆柱横放/刀刃）/ 面接触（平放/贴合）；
  接触面积越小→压强越大→尖细处易凹陷/穿透
- **力的方向与反作用**：A 对 B 施力方向明确；B 对 A 等大反向（推者姿态发力、被推者沿力方向位移）
- **相对运动学**：相对速度与方向（追/撞/擦/拖/推/拉）；动量沿接触点传递（多米诺/链式）
- **材料对响应**：硬-硬（碰撞反弹/可能破损）；软-硬（软物贴合变形包裹硬物）；软-软（双方同时变形）
- **可观察结果**：压痕 / 凹陷 / 水花 / 尘土 / 摩擦痕迹 / 绷直的吊绳 / 贴合轮廓

**Descriptor phrases (EN):** `explicit A-B contact (point/line/surface), reaction force opposing
the push, soft object deforms to hug the rigid one, momentum transfer at the contact point,
dent/splash/dust at the impact site`

**Checklist rule:** 画面中能识别 A 与 B 的关系动词；接触类型与接触面积自洽；
B 的位移/变形方向与 A 施力方向一致；接触处有反作用证据。

**Pass criteria（逐项对照画面核对）:**
- A 压在 B 上 → 接触面形状贴合 B 的承托轮廓，B 无明显反物理悬空
- A 撞 B → B 沿 A 运动方向位移；接触点有变形/水花/尘土
- 软物裹硬物 → 软物轮廓贴合硬物边缘并因重力下垂
- 悬挂 → 吊绳绷直、重物沿重力方向下垂
- 堆叠 → 上层重心在下层承托面内（稳定）或表现为倾倒趋势（不稳）
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

Example (image, all dims, base "运动员挥棒击打飞来的棒球"):

Enhanced (EN tag): `a batter swinging a bat to hit an incoming baseball, single key light from
upper left, physically correct cast shadows, bat and ball meet at a point contact with the ball
rebounding along the bat swing direction, momentum transfer at the contact point, impact seam
deformation on the ball, correct scale, visible swing cause and rebound effect, cinematic key
light with subtle rim light, rule-of-thirds composition, cohesive palette, shallow depth of field`

Checklist (zh):
- 光学: 阴影统一来自单一光源，人与地面有接触阴影
- 力学: 球沿挥棒方向反弹，轨迹符合动量传递
- 材质: 球棒木纹哑光、棒球皮革质感，无塑料高光
- 尺度: 棒球尺寸与握棒手势比例真实（约拳头大小）
- 因果: 击打（因）→ 球变形/反弹（果），击打前有挥棒动作
- 交互: 球棒与球为**点接触**；球反弹方向 = 球棒挥击方向；接触处有球的压缩变形
- 美学: 视觉焦点在接触点；主光+轮廓光氛围统一；主色调克制
