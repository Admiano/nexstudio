# SceneBam Sketch + Data Viz — 90+ Commercial Production Gate

**Production policy:** 90+ is a repeatable *measured output*, not a code-coverage percentage and not a single attractive demonstration. Voice quality is excluded from the creative readiness score, but the continuous audio / word-timing authority and integrity must still be tested. Never slice playback voice per beat.

**Scope:** native engine + compiler, original artwork, Sketch, Data Viz, and compatibility with the five other registered explainer styles, including Newscast's source-authored shade variants. Do not deploy or merge into `main` while this PR is draft.

## A. Source-faithful visual director
- [ ] Narration -> claims, evidence, entities, action/role relationships, no unsupported inferences
- [ ] One continuous master narration track, voice words/pauses control all visual timing
- [ ] No repeated-word anchor rewinds, skipped claims, phantom content or missing content
- [ ] Resolve pronouns and continuing objects across scenes safely; fail closed where ambiguous
- [ ] Visual beat cadence and hold durations adapt to the actual audio, never fixed dogma
- [ ] Visual reveal order and attention hierarchy form a coherent beginning, argument and payoff
- [ ] Transfer/morph/reconfigure verbs generate distinct physical actions
- [ ] Repeated visual units avoid template monotony, with deterministic reproducible output

## B. Data Viz
- [x] No duplicate lower-third karaoke captions: enforce in treatment, compiler and render verification
- [x] Sequential on-canvas voice-linked phrase reveals; no permanently stacked sentence transcript
- [x] Fix identical starter-word timing (January/February/March)
- [x] Retain precise source values and measured periods, protect sign/precision/units
- [x] Correct chart progress derived from source numeric value, not fake interpolation
- [ ] Source-value chart labels are legible, directly associated with their points, not faux buttons
- [ ] Chart axes/scales/grid/labels are honest and legible; no invented categories or units
- [ ] Meaningful chart choreography: rise, fall, stable, compare, rank, share, counter, time series
- [ ] Viewer always knows which claim or datum is currently emphasized
- [ ] Meaningful opening state and payoff; avoid blank waiting time or irrelevant wallpaper
- [ ] Clear typography scale and hierarchy independent of the spoken transcript
- [ ] Multiple scripts across scales, negatives, zero, units, percentages, irregular periods and sparse data
- [ ] Source-grounded caption/text policy works identically across all entrypoints
- [ ] Chart geometry + phrase panel use full available canvas without overlap

## C. Sketch
- [x] Protect source-bound entities and relations; no random substitute icons
- [x] Source-bound `flows_to` uses a moving payload, not only a dotted connector
- [ ] Arrival response: recipient receives and acknowledges the transfer
- [ ] Distinct send, receive, attach, split, combine, transform, compare, connect and grow performances
- [ ] Staging conveys cause -> action -> consequence with recognizable motion
- [ ] Preserve semantic payload, sender, destination and object identities across beats
- [ ] Primary subject and subordinate objects have intentional proportions and emphasis
- [ ] Artwork should read as an authored illustrated system, not a stock icon slide
- [ ] Camera motion and transition connect real story changes; no gratuitous zooms
- [ ] Multiple non-tech examples prove generality rather than the phone/server-only showcase
- [ ] No stranded connector, no wrong relationship, no intersection or clipping

## D. Aspect-native composition, motion and craft
- [ ] 16:9, 9:16, 1:1 separately composed with meaningful hierarchy, NOT only re-scaled
- [ ] Typography minimum sizes and line wrapping readable at normal playback dimensions
- [ ] Direct label/visual/camera safe areas, zero text-illustration collisions
- [ ] Balanced use of empty space and visual mass in each aspect
- [ ] Coherent typography, strokes, illustration asset scale, color/contrast, accent discipline
- [ ] Natural easing, anticipation, follow-through, staged holds and exit continuity
- [ ] No flashing, orphan objects, unintended disappearance or persistence
- [ ] Frame-to-frame visual truth verified (not merely successful native compiler gates)
- [ ] Motion and frame pacing coherent under slow, fast and variable narration

## E. Rigorous certification
- [x] Original source assets verified from `editorial-motion-v2/assets` via symlink
- [x] Data Viz and Sketch authoring suites pass on recovery baseline
- [x] 16:9 actual engine render smoke proofs exist and include real MP4 + PNG frames
- [x] Oct 15 paper-tile candidate `9b101b9` passes authoring, native director, three-aspect and diverse-story CI; compiled native 16:9 manifests inspected with zero authorship findings and zero page errors. Later edits must independently pass these gates.
- [ ] Test matrix: 5+ distinct claims, 5+ action types, short/medium/long script, 3 aspects
- [ ] Negative/zero/decimals/units/comparisons/ambiguous story tests
- [ ] Automatic semantic checks, overflow/legibility checks, blank/frozen intervals, duration/audio integrity
- [x] Native render regression for all five non-director families (photo_story, emoji, journey, collage, newscast.neon) succeeded on Oct 15 at `9b101b9` (run `38683778560`); base Newscast without its shade variant correctly fails closed.
- [ ] Three separate unbiased visual audits by reviewing actual MP4 frames, including motion at 25/50/75% times
- [ ] Independent 90+/100 scoring *for each style* on at least 5 diverse videos, not just the two demo reels
- [ ] Change review, source manifest and rollback plan before `main` merge or production deployment

## Score rubric (voice excluded; 100 points)
- Storytelling fidelity/semantic clarity: **20**
- Visual hierarchy, composition and typography: **20**
- True meaning-driven animation/action: **20**
- Aspect-native layout and legibility: **15**
- Distinctiveness/coherence of art direction: **15**
- Finish and delivery reliability: **10**

**90+ requires:** no major failure in an individual category; zero material semantic mistakes, collisions, invented facts or dead frames, sustained quality across all tested subjects and aspect ratios. CI PASS is a prerequisite, **not** a commercial-readiness score.

## Progress evidence
- Recovery base: PR #87 (`recovery/devin-dataviz-sketch-20261014`)
- Verified Oct 15 native candidate `9b101b9`: source-scoped Data Viz period/value handoffs, source-bound portable Sketch delivery, carrier attachment, transformation strokes, illustrated paper vs enamel tiles. CI at this commit: director 16:9 `38683778563` PASS, three aspects `38683778575` PASS, five diverse stories `38683778594` PASS, authoring validation `38683783196` PASS, all five non-director families `38683778560` PASS. These are engineering prerequisites, not 90+ commercial certification.
- Real 16:9 video and PNG extracted from workflow artifact `11949726354`; both `render_16x9.json` manifests inspected: `page_errors=[]`, `authorship.findings=[]`.
- Source-exact chart metric heading and expanded 10-story matrix authored in subsequent commits: native outputs and regressions must be checked separately before granting credit.
- Interim single-reviewer visual impression at the verified `9b101b9` candidate (NOT a certified five-video/audience score): **Data Viz 65/100; Sketch 68/100**, voice-quality excluded. Neither reaches the 90 bar. Material remaining gaps are richer semantic illustration/action, source-specific chart compositions, distinct payoff choreography, sustained visual hierarchy, and rigorous unbiased multi-video frame review. No merge or deployment.
- Quality upgrade: PR #88 (`quality/dv-sketch-director-20261015`)
- Oct 15 earlier checkpoint: Sketch **63/100**, Data Viz **55/100**, 16:9.
- Latest source changes add exact value-label contracts, remove false button-like datum chrome, make chart state direct and introduce a responding receiver animation; **do not mark those completed until their output is visually reviewed.**
- Baseline users' request: no redundant burned captions, copy follows the actual voice, no segmented playback voice.
- Scope exclusions: production voice *quality* is not part of rating; the real audio synchronization workflow remains required before shipping.

**Release state:** NOT PRODUCTION READY. No Oracle deployment, no merge.
