# Editorial Motion v1

A script-led editorial motion system, forked from the NexMind paper-motion
(paperbook) foundation. Animated type and icons carry the film; an Open Peeps
figure appears — **still**, never animated — only on the beats that earn human
emphasis; uploaded media is placed only where the script actually calls for it.
Every film is authored natively for **16:9**, **1:1** and **9:16**.

Nothing is scene-specific. Type components, icons, media containers, poses,
faces and layouts are all resolved from the script against manifests.

## How a script becomes a film

```
script
  -> runtime/script-context.js     sentences -> beats: role, emotion, emphasis,
                                   person evidence, entities, keywords
  -> runtime/editorial-director.js one typographic component per beat, earned
                                   icons, fitting media, the character gate
  -> runtime/peeps-library.js      emotion + posture -> a still Open Peeps figure
  -> runtime/layout-engine.js      ratio-native bands, proven collision free
  -> runtime/editorial.js          DOM + one paused, seekable master timeline
```

### Text leads

Each beat picks the typographic component whose intents match its role and
conditions (question, statistic, quote, list, short phrase, long body…). A
component is only eligible when the beat carries what it is built to show — a
list needs list items, a quote card needs a quote — so no component ever pads
itself by repeating the sentence. Only the script's own words reach the screen:
kickers, labels, CTA stingers and vendored sample copy are stripped.

### Icons are earned

An icon is drawn only when one of its registry keywords is spoken as a whole
word in that beat, is not a generic word, and is not ambiguous across the
registry. Icons are budgeted per ratio, cooled down between shots, and
suppressed when media or a character already holds the frame.

### The character is a still

`character.personFloor` requires person evidence in the beat itself; on top of
that the beat must clear the emphasis gate, respect spacing from the previous
character shot, and stay under the share cap for the film. When a figure does
appear, its face is chosen from the beat's emotion (valence/arousal) and its
pose from the beat's posture and vocabulary. The figure fades in and holds:
no transform, no loop, no idle.

### Media only where it fits

Uploaded items are scored against the beat's show-cues and vocabulary; the
container (browser window, device frame, photo, video card…) is chosen from the
media type and the beat's hints. An upload that fits nothing is never used.

### Ratios are authored, not scaled

`runtime/layout-engine.js` holds authored band plans per ratio for every
element combination, plus a per-ratio element budget. Regions are proven
disjoint before rendering; if a frame cannot hold everything, the lowest
priority element is dropped rather than overlapped.

## Run it

```bash
npm run build                 # regenerate the browser data bundle + manifest
npm test                      # 31 checks: directing, layout, cast, packaging
python3 -m http.server 8901   # then open compositions/editorial-explorer.html
```

See [INSTALL.md](INSTALL.md) for embedding it in a paper-motion tree, the
runtime API and reel capture.
