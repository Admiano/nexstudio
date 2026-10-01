# Vita / Nita — performance review and direction brief

Reviewed: `VITA_FRONT_FACING_TORTURE_TEST_V3_5_720P_30FPS_1200F.mp4` (720×720, 30 fps, 40 s, 1200 frames) and GPT's "Elite Social Character Readiness Report".

---

## 1. What the video actually shows (measured, not impressions)

I sampled every frame, computed inter-frame motion energy per region, and inspected bursts at 3-frame intervals plus crops of eyes, mouth and hands.

| Finding | Evidence |
| --- | --- |
| **No speech at all.** The mouth is a closed line in all 30 mouth samples across the 40 s. | Frame crops at every 40th frame |
| **Gaze is locked on the lens.** Pupils are dead-centre in 28 of 30 samples; only blinks change the eye region. No saccade, no look-away, no brow change. | Eye crops |
| **Body is in one rest pose for most of the film.** Arms hang straight (locked elbows), hands beside the thighs, fingers straight and splayed like sticks. The 20-frame contact sheet (one frame every 2 s) is nearly identical in 16 of 20 cells. | Contact sheet; per-second motion energy is < 0.05 (on a 0–255 grey scale at 180 px) in 19 of 39 seconds; longest near-still run = **120 frames (4 s)** |
| **Gestures are isolated events:** rest → single arm raise → rest. Median frame-to-frame change 0.06, 95th percentile 0.63 — a "silence / spike / silence" profile, exactly the *pose → event → recover → neutral* pattern GPT's report describes. | Motion-energy series |
| **Hand-through-body confirmed.** At ~5 s (frame 150) the right forearm passes into the hip and the hand disappears inside the torso. | Frame 150 crop |
| **No autocorrelation peaks** in body motion — so no loop repetition, which is good; but also no breathing periodicity detectable at this framing/scale. | Autocorrelation of body energy |
| **Framing and render make judgement impossible:** the character fills ~30 % of frame height, flat unlit shading, black void, no ground contact or shadow, no motion blur. Face is ~70 px tall. Nobody can judge "naturalness" from this. | Any frame |

Bottom line: this is not a performance test. It is a silent idle with occasional arm events, filmed in a way that hides the face. It cannot be scored for realism because the two things that carry realism in a talking character — **speech-driven face** and **gaze/attention** — are absent, and the body layer is at "rest pose + clip" level.

## 2. Assessment of GPT's report

**What it gets right (keep it):**
- Identity/provenance as Gate Zero — correct and non-negotiable; preview-vs-video mismatch invalidates every comparison.
- Body/head/eye authority separation — correct.
- "meaning → clip" is the architectural cause of the robotic look — correct, and the video confirms it.
- Hands-in-body is a **swept** self-collision problem, not a height/distance rule — correct diagnosis.
- Emotion leads, hands follow; eyes → head → chest propagation; reaction latency 150–300 ms — all correct targets.
- Acting QA in three levels (impossible / mechanical / believable) — correct.

**Where it is wrong or will waste time:**
1. **It is a whole-platform architecture (scene graphs, object pickup, podcast-listener mode, personality distributions) written for a character that does not yet open its mouth.** Sections 9–13 and 18 are 12–24 months of work and irrelevant until a 30-second direct-to-camera monologue is convincing. Cut the scope to that one shot.
2. **It never names the actual production method.** Every paragraph describes *what* a human does; none says *how* the motion gets generated. Reading between the lines, GPT is authoring bone curves procedurally in Python from transcript labels. That method has a hard ceiling — no studio ships realistic talking characters this way. Realism comes from **captured or learned human motion** with procedural layers only for control and repair.
3. **Audio is listed as "input 16" when it should be input 1.** There is no realism without the voice driving mouth, brows, head and hand timing. The test video has no audio track at all.
4. **It treats "continuous body state" as a state-variable design problem.** It is mainly an animation-data problem: a 30-second captured idle/talking body layer already contains weight shifts, breath, settling and asymmetry. Modelling those as variables and synthesising them is the slow road.
5. **No baseline, no reference, no acceptance numbers.** "55–65 % of elite" is a feeling. Every claim needs a measurable test and a side-by-side human reference clip.
6. **It does not mention the rig's rest-pose and finger problems**, which are visible in every frame and cheaper to fix than anything else on the list.

## 3. Direction — the order that actually gets there

### Phase 0 — Make evaluation possible (do first, one session)
- **Provenance gate** as GPT proposed: rendered MP4 carries `.blend` path, body/face mesh hashes, rig hash, action list, frame range; mismatch = render aborts. Preview still and video must come from the same script run.
- **Standard test shot** for every torture test from now on: medium close-up (top of head to just below the hips, character ≥ 80 % of frame height), 1080p, 30 fps, three-point light with a visible contact shadow or ground plane, neutral grey backdrop, camera at eye height, 35–50 mm equivalent. Same shot every time so renders are comparable.
- **Every test has audio and a transcript.** No silent torture tests. Use the ElevenLabs line or a recorded human read; export word timings.
- **Human reference clip** (a real presenter, same framing, ~30 s) rendered side by side in every review video. Judgement is comparative or it is not judgement.
- Review at 1.0× and 0.5×, in that order.

### Phase 1 — Fix the rig floor (visible in every frame; cheap)
- **Rest pose:** elbows 15–25° flexed, forearms slightly pronated, hands resting *in front of* the thigh plane (not beside it), wrists ~10° ulnar, shoulders dropped and slightly forward, spine with a small thoracic curve. A straight-armed A-pose is the single loudest "rig, not person" signal.
- **Fingers:** relaxed curl (MCP ~20°, PIP ~30–40°, DIP ~10°), slight abduction spread, thumb opposed. Never fully straight, never fully splayed. Add a finger-curl "tension" control 0–1 that the performance layer can modulate; keep it in the 0.2–0.6 band during speech.
- **Arm IK/pole vectors** set so elbows flare outward and slightly back on any raise (natural elbow path curves; a straight elbow-in path is what drives hands through the torso).
- **Shoulder → clavicle coupling:** any arm raise above the elbow line drives clavicle elevation/protraction. Locked clavicles are why raises look bolted on.

### Phase 2 — Self-collision as a trajectory constraint (not a repulsion)
- Collision proxies: capsules for rib cage, abdomen, pelvis, each upper leg, each upper arm/forearm; small spheres for palm, wrist, finger groups. Attach to bones.
- **Swept test:** sample every generated arm trajectory at 4 sub-steps per frame; any proxy intersection = failure. Report per gesture, not per frame.
- Repair ladder in this order: (1) re-time the stroke, (2) flare elbow/rotate shoulder, (3) move the hand waypoint outward along the body normal, (4) reduce amplitude, (5) **drop the gesture.** Never push per-frame.
- Acceptance: **0 penetrations per minute** on the torture suite; anything above zero blocks the render.

### Phase 3 — Voice-driven face (this is where realism is won or lost)
- Blender has no native audio solver, so bring one in. Options, cheapest first:
  - **Rhubarb Lip Sync** (open source): phoneme timing from audio → drive the 5 visemes, then add coarticulation in script (start each viseme 60–90 ms before its phoneme, cross-blend neighbours, scale amplitude by RMS energy, decay to a relaxed—not neutral—mouth in pauses).
  - **NVIDIA Audio2Face** (open-sourced 2025, I believe; verify current licence): audio → 52-style blendshape curves, remapped to the 41 morphs. Gives mouth + jaw + brow + head co-motion from voice.
  - **Phone face capture** (ARKit-class apps such as Live Link Face / iFacialMocap) of a human reading the line, remapped to the 41 morphs. Highest realism per hour spent; also gives you real blink/brow/head timing.
- Continuous affect controls (valence, arousal, certainty, warmth, attention, effort) as GPT proposed — but derive their **timing from the audio** (pitch, energy, pause structure), not from transcript labels. Brows follow pitch rises; eyes narrow on stressed low-pitch words; blinks cluster at phrase boundaries and gaze shifts.
- Acceptance: 30-s monologue where the mouth reads as speech at 1.0× with the sound off; blink rate 10–25/min, non-periodic, ≥ 60 % at phrase boundaries.

### Phase 4 — Attention and gaze
- Target model: `lens | thought | off-camera | object`. During speech a human looks away from the lens 20–35 % of the time (mostly up/side during planning and recall) and returns on stressed words and sentence ends.
- Propagation with lag: eyes lead, head follows 80–200 ms later and covers ~30–60 % of the angle, chest only on large shifts. Return to lens is faster than departure.
- Micro-saccades and small fixational drift while "on lens"; the fixed dead-centre pupil in the current render reads as a doll.

### Phase 5 — Body: captured motion first, procedural second
- Acquire or record **speaking-body capture** (a human performer delivering the actual scripts or similar cadence; phone-video mocap such as Move One / Rokoko Video is enough for a chest-up shot). Retarget to the 155-bone rig; this becomes the **continuous carrier** — breath, weight, settling, asymmetry come free and are already human-timed.
- Co-speech hands: from the same captures, cut **phrase-length trajectories** (4–8 s, including preparation and recovery), catalogue by *kinematic* properties (hand, height band, amplitude, peak count, energy) — not by meaning. Selection uses prosody (stress timing, energy contour) and current hand position; the semantic router is retired except for the specialist behaviours (count, point, demonstrate).
- Retarget by **timing, not coordinates**: keep the human's velocity profile and stroke-to-stress offset (stroke apex 0–150 ms before the stressed syllable), re-solve the spatial path to Vita's proportions through the Phase 2 constraint.
- Keep the existing 212 actions as specialist/fallback only.
- If a learned model is preferred over capture: audio-to-gesture research models exist (EMAGE, TalkSHOW, DiffuseStyleGesture families) that output SMPL-X body motion from speech audio — verify current weights/licences before committing; they still need Phase 2 and retargeting.

### Phase 6 — Acting critic and torture suite
Mechanical metrics to compute inside Blender on every render: wrist jerk, acceleration discontinuities, longest still run (target < 2.5 s during speech, unbounded when listening), penetration count, bilateral correlation (< 0.7; mirrored hands read as robotic), head periodicity, blink periodicity, stroke-to-stress alignment, gaze-on-lens ratio, finger tension range.
Torture suite, in order: TT-1 breathing-only 20 s (alive with zero gestures), TT-2 voiced monologue face-only 30 s, TT-3 full 30-s monologue, TT-4 60-s monologue at 0.5×. Do not add two-person, seated, or object tests until TT-4 passes.

## 4. Definition of "pass" for the next review
A 30-second direct-to-camera monologue, standard shot, real voice, side by side with a human reference, in which: the mouth reads as speech with sound off; she looks away from the lens and comes back on emphasis; hands rest naturally and gesture at most 3–5 times, each stroke landing on a stressed syllable; zero body penetrations; no still run over 2.5 s; and a viewer at 0.5× cannot point at where one "animation" ends and the next starts.

## 5. Copy-paste brief for GPT

> Stop expanding the architecture. Before anything in your report's sections 9–13 and 18, deliver one shot: a 30-second direct-to-camera monologue of the verified Vita rig, with real voice audio, in a fixed standard shot (chest-up, ≥80 % frame height, 1080p30, lit, grey backdrop, contact shadow), rendered side by side with a human presenter reference.
> Work in this order and report measured results at each step: (0) provenance gate + standard shot + audio-in-every-test; (1) rig rest pose and finger curl fixed (elbows flexed, hands in front of thighs, relaxed fingers), clavicle coupling; (2) capsule self-collision proxies with a 4-substep swept test and a repair ladder ending in "drop the gesture" — zero penetrations/min; (3) audio-driven mouth with coarticulation and energy scaling (Rhubarb or Audio2Face or phone capture), brows/blinks/head timed from audio prosody; (4) gaze target model with eyes-lead/head-follow lag and 20–35 % off-lens time; (5) captured speaking-body layer as the continuous carrier and phrase-length co-speech hand trajectories catalogued kinematically and selected by prosody — retire meaning→clip mapping except for count/point/demonstrate; (6) mechanical critic metrics on every render (still-run, penetrations, bilateral correlation, stroke-to-stress alignment, gaze ratio, blink periodicity).
> Every claim of improvement must come with the metric values and the render; no silent tests, no proxy bodies, no untextured or unlit renders.
