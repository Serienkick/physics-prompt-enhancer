# Character Skeleton System (人物骨骼系统模块)

Feature module for the Physics Prompt Enhancer. Derived from a **character mesh (人物建模)**,
this module defines how the skill treats character anatomy and motion so that generated
**3D / video** characters are anatomically and dynamically plausible, and — critically — how
every principle maps onto the skill's two outputs (`enhanced_prompt` injection + `reality_checklist`
items). It is the `character` dimension's deep reference; the compact seed lives in
`references/physics_dimensions.md §8`.

The skeleton is the internal hierarchy of bones/joints inside a 3D character. The **rig** is the
complete control system built on top of the skeleton: skeleton + animation controls + constraints +
IK/FK + skinning + helper/twist bones. A prompt that asks for a believable character must describe
the *rigged* result, not just a posed mesh.

This module is organized to mirror the request:
- **A. Skeleton System Design** — hierarchy, joints, binding & weights
- **B. Stability Mechanism** — physics constraints, inertia balance, collision response, anti-clip/anti-jitter
- **C. Operation Space Expansion** — multi-joint IK linkage, mocap input, custom poses
- **D. References & Reference Implementations** — authoritative docs + best-practice systems
- **E. Business-Logic Alignment** — exact mapping to the skill's outputs (actionable, not theory)

---

## A. Skeleton System Design (骨骼系统设计)

### A.1 Standard humanoid hierarchy
A game-ready humanoid skeleton flows **root → pelvis → spine chain → clavicles → arms → hands**,
with **neck → head** off the upper spine and **thighs → calves → feet → toes** off the pelvis.
Rotations are relative to the parent: rotating `upperarm_l` moves `lowerarm_l`, `hand_l`, and
fingers because they are children in the hierarchy.

```
root
└─ pelvis
   ├─ spine_01            (lower torso)
   │  └─ spine_02         (upper torso)
   │     └─ spine_03      (upper chest, optional)
   │        ├─ clavicle_l ─ upperarm_l ─ lowerarm_l ─ hand_l ─ (thumb/index/middle/ring/pinky ×3)
   │        └─ clavicle_r ─ upperarm_r ─ lowerarm_r ─ hand_r ─ (... )
   │  ├─ neck_01 ─ head
   ├─ thigh_l ─ calf_l ─ foot_l ─ ball_l
   └─ thigh_r ─ calf_r ─ foot_r ─ ball_r
```

**Bone-name convention (UE5 / Unity Humanoid compatible — recommended default):**
`root, pelvis, spine_01, spine_02, spine_03, clavicle_l/r, upperarm_l/r, lowerarm_l/r, hand_l/r,
neck_01, head, thigh_l/r, calf_l/r, foot_l/r, ball_l/r`. Fingers: `thumb_01..03_l/r`,
`index_01..03_l/r`, `middle_01..03_l/r`, `ring_01..03_l/r`, `pinky_01..03_l/r`.
Use a single suffix convention — `_l` / `_r` (lowercase) is what UE5's auto-mapper expects;
`UpperArm_L` vs `upperarm_l` mismatch silently breaks auto-retarget.

**Bone budget:** a basic humanoid needs ~50 bones (root, pelvis, 3 spine, neck, head, shoulders,
arms, forearms, hands, legs). Add 30–40 for fingers → typical game rig 50–100; AAA with full
finger + facial rigs reaches 150–200. Keep the count inside the runtime budget for `target == 3d`.

### A.2 Joint roles (主要关节)
- **Spine (脊柱):** 3 segments carry the torso and transmit pelvis motion upward. `spine_01` lower,
  `spine_02` upper, `spine_03` upper chest. Misaligned spine propagates error to every child.
- **Limbs (四肢):** 2-bone chains. Arm = `upperarm + lowerarm`; leg = `thigh + calf`. Elbow/knee
  are ~1-DoF hinge; shoulder/hip are ~3-DoF ball-and-socket. Give knees/elbows a *slight* rest bend
  so IK solvers know the joint direction.
- **Hands (手部):** wrist + 5×3 finger bones. Add a `Forearm_Twist` helper bone to avoid
  "candy-wrapper" twisting at the wrist during pronation/supination.
- **Head (头部):** `neck_01 + head`. A look-at controller distributes the head-target angle across
  the spine→head chain (not just the neck) for natural tracking.

### A.3 Binding & skin weights (绑定与权重分配)
The skeleton "matches the model" only when binding and weights are correct.

- **Bind pose = T-pose or A-pose, all transforms zeroed** (Blender *Apply All Transforms* / Maya
  *Freeze Transforms*) before binding. Binding in any other pose bakes in offsets → wrong rest
  pose → can't share animation. This is the #1 rigging anti-pattern.
- **Skinning:** each mesh vertex is weighted to its influencing bones; cap at **≤4 influences per
  vertex** and **normalize weights so they sum to 1.0** per vertex. A vertex at the elbow is
  typically influenced by both `upperarm` and `lowerarm`; the weight split decides how the mesh
  deforms at the bend.
- **Common failure modes & fixes (validate these in generated characters):**
  | Symptom | Cause | Fix |
  |---|---|---|
  | Shoulder collapses into chest when arm lifts >90° | auto-weights spread armpit over 3–4 bones | give shoulder clear weight in delta zone, zero spine on outer shoulder |
  | Wrist twist transfers to forearm mesh | no separate twist bone | add `Forearm_Twist` with ~0.5 weight mid-forearm |
  | Knee pinches | auto-weights too soft (60% segment) | limit each bone to ~40% of segment length |
  | Fingers stick together on grasp | cross-contamination between finger groups | manual vertex-group isolation |
  | Tears / "weight islands" | disconnected weight clusters | smooth boundaries, topology-aware transfer |
- **Twist / corrective bones:** forearm & shoulder twist bones (driven by constraints, not in base
  FK chain) fix candy-wrapper deformation; corrective blend shapes activate at extreme angles
  (film quality).

**Prompt-level translation (what to inject):** "anatomically correct joint hierarchy, clean
UE5/Unity-Humanoid-compatible bone naming, T-pose bind with normalized ≤4-bone skin weights, smooth
deformation without candy-wrapper twisting".

---

## B. Stability Mechanism (稳定性机制)

A character animation looks natural and avoids clipping/jitter when three layers are respected:
physics constraints, inertia (COM) balance, and collision response.

### B.1 Physics constraints (物理约束)
- **Joint limits:** swing (cone) + twist (band) limits mirror human range; use *soft* constraints
  (compliance) before hard stops to avoid singular/locked poses. Twists get narrow limits —
  especially elbows/knees where a single-axis hinge is appropriate.
- **Mass distribution:** torso carries ~half the total mass; upper limbs lighter than lower limbs.
  Keep **adjacent mass ratios < 3:1** — extreme ratios increase solver error and make limits feel
  spongy. Recalculate inertia from axis-aligned colliders.
- **Damping:** start high on distal parts (calm oscillation), then reduce until motion looks natural
  without jitter. Lower restitution on distal shapes.
- **Collision filtering:** disable self-collision on bone pairs that never separate (upper/lower
  arm) but keep contact for hands and environment. Separate collision layers (ragdoll / environment
  / dynamic props) to avoid O(n²) contact generation.

### B.2 Inertia balance (惯性平衡)
- Model the character as an **inverted pendulum** using the **center of mass (COM)**. Human COM sits
  near the pelvis and *shifts with posture* (e.g. lifting a load shifts COM forward → lean torso
  back to bring COM over the pelvis/support).
- **Keep COM inside the support polygon** (the area under the feet) or the character falls. Balance
  is maintained by a PD/PID "muscle" system driving the physical bones toward a target pose defined
  by a *ghost rig* (procedural/IK/animation). On a large impulse or when COM leaves the support
  area, drop to a fully limp ragdoll, then a procedural state machine blends back to standing.
- **Lean = f(acceleration):** derive the effective gravity vector from the character's acceleration
  and apply a lean angle across the spine joints. This communicates velocity, weight, and direction
  of travel with *zero authored lean animation*.

### B.3 Collision response (碰撞响应)
- Each limb is a rigid body with a collider: **capsules for limbs, boxes for torso, spheres for
  head**. Joints impose constraints (hinge / ball-and-socket) that mimic anatomical limits.
- Collision detection prevents interpenetration between bodies and the world. Real-time solvers
  (semi-implicit Euler / Verlet integration; sequential-impulse or projected Gauss-Seidel / PBD
  constraint solvers) compute forces & torques per frame and keep the system stable under impact.
- Use a **fixed timestep + solver iterations** for deterministic, repeatable behavior. Enable
  **CCD (continuous collision)** only on fast-moving parts after confirming discrete collision is
  insufficient (it carries cost).

### B.4 Anti-clip / anti-jitter (防穿模 / 防抖动)
- Mass-ratio <3:1 + axis-aligned inertia recalculation stops most explosions.
- Jitter → increase angular damping on distal parts, lower restitution, cap max angular velocity
  after high impulses (slightly overdamped, then back off).
- **Foot sliding** → foot-gluing state machine + plant-weight gating so IK *enhances* rather than
  overrides the base animation; smooth IK targets (raw snaps feel ungrounded).
- Use projection / joint correction **only if drift appears** — aggressive correction causes popping.

**Prompt-level translation:** "joints constrained within anatomical limits, center of mass kept over
the support base (no floating/falling without cause), inertial lean matching velocity, collision-
aware limbs that do not interpenetrate, damped motion without jitter".

---

## C. Operation Space Expansion (操作空间拓展)

The skeleton system is what makes a character *operable*, not just poseable.

### C.1 Multi-joint linkage control (多关节联动控制)
- **FK (Forward Kinematics):** set a parent joint angle, children follow. Best for spine and arm
  arcs. Direct, predictable, one solution.
- **IK (Inverse Kinematics):** set an end-effector target (e.g. hand/foot position), solver computes
  the joint angles. Essential wherever the body touches a surface (foot planting, hand reach).
  - **FABRIK** (position-space, 2011): forward+backward reaching passes; fast, smooth, handles
    multi-end-effector chains, converges in <30 iterations, no oscillation. Preferred for arms/long
    chains.
  - **CCD** (angular, tip→root): cheaper but biased on long chains and prone to jitter; good for
    quick short-chain fixes.
  - **Jacobian** methods: flexible with constraints but heavier; robotics-grade precision.
- **IK/FK switching** is what production rigs actually use. **Procedural IK** builds on it:
  - *Foot placement:* body-height adjust (pelvis drops on uneven terrain) + foot rotation to terrain
    normal + temporal smoothing + plant-weight gating.
  - *Look-at:* distribute head-target angle across spine→head chain; smoothed target gives inertia
    (fast = alert, slow = relaxed).
  - *Three-point tracking:* head + 2 hands as IK targets → full-body pose for VR/VTuber avatars.

### C.2 Mocap data input (动作捕捉数据接入)
- **Formats:** FBX (universal), BVH (raw bone data), BIP (3ds Max / Character Studio), VMD (MMD),
  glTF / USD. Pick FBX/BVH for engine interchange.
- **Pipeline (non-negotiable retarget):** capture → **retarget** (map source joints → target joints,
  rescale proportions) → cleanup (foot-sliding, contact, occlusion) → apply. *Skipping retarget
  produces floating feet, joint popping, broken contacts.* Tools: UE5 IK Retargeter, Unity
  Animation Rigging, Blender BVH retarget.
- **2026 markerless mocap** (no suit/markers, phone video → FBX/BVH): Move.ai (multi-cam, high
  accuracy, <100 ms live), DeepMotion (real-time + 2D cleanup), Plask (browser), QuickMagic (13+
  formats incl. VMD/Mixamo, text-to-motion), Rokoko Vision (free single-cam). Biomechanical
  accuracy ~10–50 mm positional, 2–5° joint-angle error; limits: occlusion, loose clothing, fast
  motion blur.

### C.3 Custom pose adjustment (自定义姿态调整)
- **Additive layers** stack on the base pose via reference-pose subtraction: breathing (chest),
  look-at (head), hit flinch, fatigue. Gate with **Avatar Masks** (upper-body / spine-only / head)
  so additives don't affect the whole body. Clamp rotations to avoid hyperextension; use max-blend
  not sum for stacked additives.
- A rig supports custom poses only if it has **correct joint orientation + clean hierarchy** — then
  poses retarget and blend cleanly between keyframed, mocap, and procedural sources.

**Prompt-level translation:** "coherent multi-joint motion driven by IK/FK linkage, motion-capture-
derived or physically plausible poses, additive secondary motion (breathing/lean) layered on the
base, contacts maintained through pose changes".

---

## D. References & Reference Implementations (资料搜集与整合)

Authoritative sources reviewed and synthesized for this module (used to ground every claim above;
no claim is invented):

**Skeleton design / naming / skinning**
- CGTyphoon — *Human Rig Bone Names and Standard Skeleton Hierarchy* — bone-list + UE5/Unity/VRChat
  slot mapping. https://cgtyphoon.com/?p=3004
- MoCap Online — *Character Rigging for Games* — skeleton, skinning, engine naming conventions.
  https://mocaponline.com/blogs/mocap-news/character-rigging-game-dev-guide
- MoCap Online — *Character Rigging Basics* — bone budgets (50–100, AAA 150–200), FK vs IK, mocap
  stress test. https://mocaponline.com/blogs/mocap-news/character-rigging-basics-guide
- skillmd.ai — *rigging-animation* — anti-patterns (non-zeroed transforms, wrong bind pose, weight
  islands). https://skillmd.ai/skills/rigging-animation
- BlackSparc — *Manual Weight Refinement* — armpit/wrist/knee/finger fixes, ≤4 influences + normalize.
  https://blacksparc.tech/games-development/services/rigging-animation/character-mesh-skinning-for-animation.html
- Blender Rigify docs — meta-rig → Generate Rig. https://docs.blender.org/manual/en/3.2/addons/rigging/rigify/

**Stability (ragdoll / COM / collision)**
- PulseGeek — *Ragdoll Setup and Stability Tips* — pelvis-out build, mass ratios <3:1, damping,
  collision filtering, validation. https://pulsegeek.com/articles/ragdoll-setup-and-stability-tips-for-reliable-collisions/
- EndlessWiki — *Ragdoll Physics* — articulated rigid bodies + joint constraints + solvers.
  https://www.endlesswiki.com/wiki/ragdoll-physics
- Jettelly — *Self-Balancing Active Ragdoll* — dual ghost/physical rig, PID "muscles", inverted-
  pendulum COM balance, foot-gluing. https://jettelly.com/blog/self-balancing-active-ragdoll-in-unity-breakdown-of-an-upcoming-tool
- TCD thesis (2020) — *Root Balance Spring* + COM position under load.
  https://publications.scss.tcd.ie/theses/diss/2020/TCD-SCSS-DISSERTATION-2020-058.pdf

**Operation (IK / mocap)**
- Khronos Vulkan tutorial — *Procedural Animation: IK* — CCD vs FABRIK, foot placement, look-at,
  physics-driven lean. https://github.khronos.org/Vulkan-Site/tutorial/latest/Advanced_glTF/Procedural_Animation_IK/07_conclusion.html
- vrarwiki — *Inverse Kinematics* — analytic/CCD/FABRIK/Jacobian survey + VR three-point tracking.
  https://vrarwiki.com/index.php?title=Inverse_kinematics
- mysimulator.uk — *FABRIK vs CCD* interactive solver notes. https://www.mysimulator.uk/inverse-kinematics
- QuickMagic — *Best AI Motion Capture Tools 2026* + *Markerless Mocap Explained* — format matrix,
  retargeting, accuracy. https://www.quickmagic.ai/Learning/getting-started/Best-AI-Motion-Capture-Tools-Comparison
- youngju.dev — *AI Motion Capture & Animation 2026* — Move.ai / DeepMotion / Plask landscape.
  https://www.youngju.dev/blog/culture/2026-05-16-ai-motion-capture-animation-2026-move-ai-cascadeur-deepmotion-wonder-studio-rokoko-plask-animatediff-runway-deep-dive.en
- MoCap Online — *What Is Motion Tracking* — retargeting tools, FBX/BVH/BIP formats.
  https://mocaponline.com/blogs/mocap-news/what-is-motion-tracking

**Reference implementations (what to point users at when they want to *build* it)**
| Concern | Reference system |
|---|---|
| Auto humanoid rig | Blender **Rigify** (meta-rig → control rig) |
| Engine retarget + IK | **UE5 IK Retargeter** + **Control Rig**; **Unity Humanoid** + **Animation Rigging** |
| Real-time mocap | **Move.ai** / **DeepMotion** / **Plask** / **QuickMagic** (markerless, FBX/BVH out) |
| Physics stability | **Jettelly Active Ragdoll** pattern (dual-rig + PID muscles + COM balance) |
| IK solver | **FABRIK** (position-space) for arms/long chains; **CCD** for short fixes |

---

## E. Business-Logic Alignment (业务逻辑对齐 — 可落地映射)

This module plugs into the enhancer's existing two-output model. The `character` dimension is the
seed; its compact form lives in `physics_dimensions.md §8` and is consumed by both the LLM path and
the rule-based fallback in `scripts/enhance.py`. Below is the exact mapping used by the skill.

**When to include `character`:** the subject is a humanoid/character **and** `target ∈ {video, 3d}`.
For `image` it is optional (a single frame still needs a plausible pose + contact). Invoke as
`--dims optics,mechanics,materials,scale,causality,character`.

**Inject → Descriptor phrases (EN) → Checklist rule → Pass criteria**, one triple per sub-area:

**E.1 Skeleton / binding** (maps to A)
- Inject: anatomically correct joint hierarchy; UE5/Unity-Humanoid bone naming; T-pose bind;
  normalized ≤4-bone skin weights; no candy-wrapper twisting.
- EN tag: `anatomically correct joint hierarchy, humanoid bone naming, T-pose bind, clean skin weights, no twist artifact`
- Checklist rule (zh): 骨骼层级与人体结构对应，绑定干净、权重归一，关节弯曲无网格撕裂
- Pass criteria (zh): 肩/腕/膝弯曲处无塌陷或穿模；手指不粘连；可见部位符合人体比例

**E.2 Stability** (maps to B)
- Inject: joints within anatomical limits; COM over support base; inertial lean matches velocity;
  collision-aware limbs; damped, no jitter.
- EN tag: `joints within anatomical limits, center of mass over support, inertial lean, collision-aware, no jitter`
- Checklist rule (zh): 姿态在解剖限位内，重心落在支撑面内不无故失衡，肢体不穿模、运动无抖动
- Pass criteria (zh): 站立/运动时效心在脚底支撑区内；受冲量时按惯性倾倒而非悬空；肢体不与躯干互穿

**E.3 Operation** (maps to C)
- Inject: IK/FK-linked multi-joint motion; mocap-derived or physically plausible poses; additive
  secondary motion (breathing/lean); contacts maintained through pose changes.
- EN tag: `IK/FK-linked joints, motion-capture-style poses, layered secondary motion, stable contacts`
- Checklist rule (zh): 多关节联动合理，姿态有物理/动作来源，次动作（呼吸/前倾）叠加自然，接触点保持
- Pass criteria (zh): 手脚接触面在姿态变化中保持接触；动作连贯无瞬移；叠加的呼吸/倾斜不破环主体姿态

**E.4 Skill-internal integration (already wired in code)**
- `scripts/enhance.py`: `character` added to `DIMS`; `FALLBACK_PHRASES["character"]` and
  `FALLBACK_RULE["character"]` added; `SYSTEM_PROMPT` instructs the model to reason about joint
  hierarchy / COM / contact when the dimension is selected.
- `references/physics_dimensions.md §8`: compact seed so the **rule-based fallback** (no LLM)
  emits the same checklist items.
- `SKILL.md`: `character` listed in the dimension set; `reality_checklist` coverage adds the three
  bullets above; a "Character Skeleton System" subsection points here.

**E.5 Relationship to existing dimensions (no duplication)**
- `character` *extends* `mechanics` (adds joint/inertia/COM specifics), `scale` (proportions via bone
  hierarchy), and `causality` (a pose has a physical/mocap cause). It does **not** replace them — keep
  all selected dimensions; `character` adds the anatomy/motion layer on top.
