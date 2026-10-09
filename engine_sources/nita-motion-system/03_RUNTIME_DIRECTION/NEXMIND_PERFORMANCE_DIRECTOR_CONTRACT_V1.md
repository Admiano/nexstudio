# NexMind Performance Director Contract V1

## Role

`SCRIPT + AUDIO/PROSODY + ROLE + PERSONALITY + SCENE CONTEXT -> NexPerformancePlanV1`

The Performance Director is a semantic acting authority. It decides **what the performance means**, not how NexStick joints are physically solved.

## It MAY choose

- gesture vs explicit stillness (`gesture.suppress`);
- semantic intent and delivery intent;
- emotional tone/intensity;
- dominant hand and approximate gesture class;
- semantic emphasis/stroke anchor;
- gaze target/attention;
- head behavior;
- stylized facial intention;
- posture/openness/settle intention;
- speaker ownership and references to word/viseme/prosody timing.

## It MUST NOT choose or emit

- shoulder/elbow/wrist/finger/knee/ankle coordinates;
- `pose3d`, skeleton poses, joint rotations, raw SVG geometry;
- direct foot/root displacement;
- raw external-model animation playback;
- renderer artwork or character identity changes.

## Performance law

Stillness is first class. Not every sentence or clause gets a gesture. Gesture strokes align to semantic/vocal emphasis. One hand normally leads; the other returns to/rests. Face, gaze, gesture, posture and speaker state must be mutually coherent.

## External model relationship

An external/open model may produce `NexExternalMotionProposalV1`. The Performance Director does not pass that proposal to the renderer. `NexExternalMotionAdapterV1` first converts it into bounded semantic suggestions; existing NexStick authorities remain final physical/render authorities.
