# Physics Dimensions Reference (物理维度参考)

Knowledge core for the Physics Prompt Enhancer. Loaded on demand by the enhancer (LLM or
rule-based fallback). Each dimension lists: what to inject into the prompt, and the
checklist rule + pass criteria used to verify the generated result.

Seed dimensions are inspired by the physical-consistency benchmarks used by physics-aware
image models (e.g. ChronoEdit's PBench-Edit: gravity, support contact, trajectory, lighting
consistency, causal effect). This skill applies them at the *prompt* layer instead of the
*pixel* layer.

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
steam needs heat, wet needs liquid source.

**Descriptor phrases (EN):** `visible cause for every effect, motion trail consistent with path,
impact splash at contact point, heat haze above warm surfaces`

**Checklist rule:** every depicted effect has a physically valid cause present in the frame;
no spontaneous/teleporting changes.

**Pass criteria:** a wet floor has a spill source; a knocked-over cup has a force direction;
smoke rises from its emitter.

---

## Video-only extensions (视频专属)
When `target == video`, append temporal rules to the checklist:
- **Trajectory continuity:** object position changes smoothly frame-to-frame; no teleport.
- **Motion blur:** blur direction matches velocity vector; faster = more blur.
- **Secondary motion:** hair/cloth/liquid lag and settle after the primary motion.
- **Conservation:** no object appears/disappears without a cause.

---

## Rule-based fallback template
When no LLM is present, append the EN descriptor phrases of the selected dimensions to the base
prompt and emit one checklist item per selected dimension using its `rule` + `pass_criteria`.
Example (image, all dims, base "一只猫跳上木桌"):

Enhanced (EN tag): `a cat leaping onto a wooden table, single key light from upper left, physically
correct cast shadows, subject obeys gravity with a parabolic launch arc, PBR wood grain with natural
grain and gravity sag, correct scale, visible crouch-then-launch cause and landing contact shadow`

Checklist (zh):
- 光学: 阴影统一来自左上光源，猫与桌底有接触阴影
- 力学: 猫呈抛物线起跳，落桌处有压痕/冲击
- 材质: 木桌为哑光木纹，无塑料高光
- 尺度: 猫与桌比例真实
- 因果: 起跳前有蹬地蓄力（原因），落地有接触（结果）
