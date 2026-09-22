# Nex Performance Critic Spec V1

This phase defines the critic only; it does not build a heavyweight autonomous agent.

## Anatomy — automatic hard reject
- disconnected shoulder, elbow, wrist;
- segment-length stretch;
- torso/hand penetration;
- broken palm/hand orientation;
- root/foot movement during a planted-presenter beat.

## Gesture quality — reject or repair
- gesture density above plan; duplicate/repeated/looped gestures;
- semantic mismatch; motion during pause/silence;
- unnecessary two-hand activity;
- missing prepare/stroke/hold/recovery; insufficient recovery;
- excessive amplitude, wrist flip, raw-mocap or puppet behavior.

## Face / speech
- expression contradicts delivery; frozen or popping face;
- mouth active for non-speaker; viseme timing drift; excessive smile;
- amplitude-only mouth movement must never be labelled phoneme lip sync.

## Gaze / head
- permanent camera stare; excessive/random gaze breaks;
- head/gaze disagreement; repetitive nodding/head bob.

## Overall performance
Reject robotic, twitchy, floppy, uncontrolled, puppet-like, over-energetic, emotionally contradictory or obviously procedural motion. Also flag excessive staticness only when the semantic plan clearly calls for an emphasis/reaction.

## Decision shape
`PASS | REPAIR | REJECT`, with machine-readable reason codes and timestamps. Mechanical correctness alone can never certify visual/performance quality.
