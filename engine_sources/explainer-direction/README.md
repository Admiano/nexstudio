# Explainer direction: local execution and proof

**Checkpoint warning:** the actual compact lightning film renders, but fails the
requested visual standard. Passing contracts/tests does not establish good
explanatory motion, readable labels or production readiness. Read the
[full scope, progress and roadmap](../../docs/explainer-direction-checkpoint/README.md),
[preserved failure evidence](../../docs/explainer-direction-checkpoint/evidence/visual-audit.md)
and [recovery guide](../../docs/explainer-direction-checkpoint/RECOVERY.md) first.

This is a semantic production language, **not an approved public engine or a
Creative Lock path**. P8 remains creative authority. Standalone live authoring is
`DEVELOPMENT_PREFLIGHT`; authenticated semantic binding is `P8_SEMANTIC_BOUND`.
Neither passes exact-media independent review, human calibration or commercial
certification. The new adapter is deliberately not registered in public dispatch;
legacy adapters, approved engines and frozen vendor governance are unchanged.

Canonical authority: [CANONICAL_SOURCE_README.md](../../CANONICAL_SOURCE_README.md),
[CANONICAL_CREATIVE_AUTHORITY.md](../../docs/studio-v1/CANONICAL_CREATIVE_AUTHORITY.md), and
[NEXMIND_AUTONOMOUS_CREATIVE_AUTHORITY.md](../../docs/studio-v1/NEXMIND_AUTONOMOUS_CREATIVE_AUTHORITY.md).
The [historical interface note](../../docs/explainer-direction-checkpoint/historical-contract-interface.md)
is archived for context; the current validators are authoritative for this checkpoint.

## Executable integration

Loopback inference uses an explicitly selected, commercially permitted local
model. Check the weights' licence, not just the inference server's licence.
`EXPLAINER_DIRECTION_TIMEOUT_SECONDS` (default 120, maximum 3600) and
`EXPLAINER_DIRECTION_MAX_TOKENS` (default 12000) configure the local transport.
Staged calls use the exact stage response schema for OpenAI-format `json_schema`
constrained sampling, including repairs. Only the prose copy factors repeated
schema nodes into local references, reducing CPU prefill without weakening the
grammar. Sampling keeps the expanded schema because llama.cpp cannot reliably
resolve nested references. The redundant whole-score schema is omitted. Fixed
schema precedes variable inputs to support local prompt-cache reuse. Brief,
evidence, context, history and candidate content are never truncated.
Large scene-schema calls on a slow CPU may need an explicit longer timeout;
increasing it does not relax validation or accept truncated completions.
The local server must support schema-constrained JSON. An unsupported schema
fails visibly; the transport never silently retries with unconstrained JSON.
Contracts still validate semantics, evidence, quantities and choreography:
syntactically valid structured output is not creative approval.
For a failing palette role, local preflight can ask the model to select a
contrast-feasible tint or shade of its authored colour. The controller supplies
mathematically checked candidates and applies only that role's replacement.
All other film decisions remain unchanged; declared brand colours are never
overwritten by this repair. This is not a preset palette or a Creative Lock.

`--staged --concept-first` first generates genuinely distinct, whole-brief
semantic strategies and obtains an explicit qualitative selection in
`DEVELOPMENT_PREFLIGHT`. Only then does it author scenes for the selected
strategy. This avoids rendering or fully authoring rejected concepts on a
CPU-only machine. It does **not** compare two completed films or constitute
independent visual review. Without `--concept-first`, the existing full-score
candidate comparison remains available. A repeated strategy, missing review,
unsupported scene or failed final score still fails closed.
Competition cannot offer unavailable raster assets or numeric chart concepts
without a comparable, compatible pair of sourced measurements. A standalone
source-supported quantity can still become a number actor.

Before live visual construction, the author must produce a typed meaning graph
from the supplied evidence in two dependent stages. Entities are typed first;
fact schemas then admit only those physical entities as transport endpoints and
only material, energy or signal entities as carriers. Each fact cites its source
claims, including more than one when the relationship needs both. Causal edges
cannot claim an input creates a material or an energy carrier: processes and
physical producers are distinguished from transported material; `powers` and
`stores` describe energy supply and retention separately from material transport.
A local source-only review compares proposed facts and coverage to the cited
claims before live scene authoring and requests scoped repairs. This review is
development preflight, not factual certification or P8 approval.
The review sees neutral fact IDs, with a checked bijection back to the original
graph. IDs are lookup keys, not relation labels; kinds, endpoints and citations
are unchanged, and unsupported review IDs fail before a veto is applied.
An entity definition and a fact using that entity may have different source
claims; both are individually provenance-checked. Quantity subjects are answered
once per measured claim, with `null` explicitly omitting an ungrounded measurement.
Relations cannot rewrite the accepted entity list, and schema-patch repairs replace
only the invalid entity or fact, preserving the other decisions. Actor provenance
includes both an entity's definition and the explicit facts in which it participates.
Process scene briefs acquire the source claims needed to preserve spatial facts
on their endpoints, without inventing new facts. Meaning extraction uses a separate
source-only prompt, not the film's layout, style, library or motion instructions.
The graph separates physical places and devices from material, energy and signals;
records directed transport with a distinct carrier
and optional intermediate device; and assigns each sourced quantity to the
entity it counts or measures. The selected strategy restricts which actor kinds
can represent this meaning. Scenes bind each actor to a graph entity or fact,
and compiled plans preserve those exact bindings in every aspect. The Python
score, frozen-plan and browser-runtime boundaries reject contradictory visual
bindings, missing physical ordering and material movement against a declared
route. A path's `direction` alone does not license reverse motion: path-bound
`flow` must advance through time. This graph establishes types and provenance,
**not** that source prose entails the proposed facts or that a visual metaphor is
truthful. Independent factual and perceptual review remain necessary.

Scene construction jointly authors narration, actors, initialized states and
relationships. Only evidence declared for that scene is supplied to scene
construction; this reduces cross-scene borrowing, but source entailment still
requires independent creative review.
Choreography follows against that validated, immutable graph.
The live route and final pipeline reject no-op performances, hidden performed
changes (including ancestor masks), and verbs that contradict their state
direction. Hidden preparation with `update` is allowed only if the actor is
revealed later in the scene. Attached connectors are paths, not moving material:
their endpoints or a shared group drive geometry; their own move/scale is
unsupported. These are declared-effect checks, not pixel or factual review.

Actors may initialize signed-degree `rotation` and author a `rotate` event about
their native box centre. Rotation composes with scale, motion and nested groups;
attached connectors and path-bound particles follow the same affine transforms.
Those attached actors cannot rotate independently. Groups containing source-bound
physical ordering cannot rotate, since that could reverse an above/below fact.
Shape payloads may specify a width-to-height `aspect_ratio` (0.1 to 10); native
fitting preserves that proportion and reserves a full rotation envelope when
rotation is authored. Neither a transform angle nor a shape ratio is a factual
measurement or bearing.

Meaning facts also admit `aligns_with`: a sourced qualitative orientation of a
physical subject relative to another physical entity, a field/carrier, or a
direction concept. This
does not establish a route, a physical link, stored energy or measured degrees.
It therefore cannot bind a transport connector or path-bound particles.
When the source explicitly states alignment with the **direction of** something,
live authoring requires that literal direction as a concept, not the field,
material or physical object itself. Missing direction concepts use the same
source-bound entity-append repair as missing carriers and counted collections.
Equivalent facts with different IDs are coalesced before source review, without
combining different provenance or process annotations. Scoped repairs still use
the original response indices. A source-review rejection of an unsupported
relation admits deletion, rather than forcing an invented replacement. If
deletion is the only admitted repair, the controller performs and logs it
without another model call. Static orientation is not causation or storage,
and each orientation citation is checked separately rather than letting one
supporting citation hide an unrelated one.
Review quotes are constrained to their selected source claim. A qualitative
orientation is kept out of the uncertain local model's factual review only
when its physical subject, verb and literal direction are directly attested
by every claim it cites and it has no other fields. The reviewer still sees
its source-backed coverage and checks the remaining facts and entities;
extra or unsupported citations remain under review.
An unambiguous source phrase about a carrier moving from one place to another
is required before live authoring even offers a transport-fact branch; type
eligibility alone never implies movement.

### Compact authoring

`--compact` opts into a smaller directing boundary while preserving the typed
meaning graph, existing score validators, compiler and renderer. The first
response contains two distinct explanatory concepts, a selected argument,
contextual palette roles and source-bound scene direction. It writes narration
as complete sentences under a controller-checked word budget, not renderer actors,
IDs, aspect ratios, pixel geometry, audio alignment or property tracks.

Each narration sentence is source-checked before preparing actual voice. A
second scene-local request receives the measured words and duration; its schema
admits only supported actions, source-bound targets and real spoken-word cues.
Motion is an action/target-to-word map, so the same action on the same target
cannot be requested repeatedly. Figure construction and admitted links are
required; attention and view changes are optional. Cue punctuation is normalized,
and `#2` selects the second occurrence of a repeated word. The controller orders
measured cues and combines simultaneous changes without dropping their effects.
No-op actions and unreadably short intervals still fail.
When the evidence permits it, the first pass requires multiple cited claims
per scene rather than stretching one narrow claim with unsupported filler.
Requested word ranges are also expressed as a bounded English-sentence pattern
in the response schema, with explicit per-scene limits in the prompt. Word
counting and source checks remain controller gates; a grammar is not evidence
of fluent or correct narration. Figure/fact compatibility is checked before
voice. Independent draft errors are reported together in one scoped correction
rather than spending a new call discovering each successive error.
Transport requires a physical flow fact, and orientation requires an alignment
fact. The controller builds stable actors, attached connectors, initial states
and coordinated tracks, then validates the expanded score and native plans.
Unsupported direction fails rather than becoming a generic card.

When an unambiguous source sentence names two accepted processes as one joint
cause, the controller preserves that complete phrase as a source-bound process.
A causal or producing fact must retain that joint subject instead of splitting
it into unsupported constituent causes. This normalizes source meaning, not
imagery, narration or model-authored motion.

The Python entry point is `author_score(..., compact=True,
prepare_narration=callable)`. The callback must return actual provider alignment;
compact mode will not invent uniform word timing or proceed without voice.
Local inference remains `DEVELOPMENT_PREFLIGHT`. These checks do not establish
visual quality, authenticated P8 authority or production readiness.

`--compact --source-quote-narration` explicitly selects a narrower development
sample: the controller speaks the supplied evidence sentences unchanged,
partitions them in supplied order within the requested word range and includes
their admitted relationship endpoints. The model directs their visual treatment
and measured motion, not their narration or source-fact selection. Every block
must contain an admitted relationship. Evidence that cannot fit fails; this mode
is never an automatic fallback for failed original narration. The request and
manifest disclose the limitation. It does not prove general narration authoring.

Material transport uses `particles` with `arrangement: "stream"` and an explicit
`payload.path` containing a connector actor ID and `direction: "forward"` or
`"reverse"`. Initialized `flow` advances particles by arc length along that
connector's actual native route, including moving/scaling endpoints and groups.
The compiler does not reserve a separate layout box for this material.
Invalid bindings, self-endpoints and independent particle transforms fail closed.
Unbound streams remain box-local illustrative motion; they cannot enact transport
between other actors. Particle count and speed are schematic, never measurements.

Evidence-bound `above`, `below`, `left_of` and `right_of` constrain physical
axes independently of causal/process edges. Native compilation preserves these
axes in all three aspects. Endpoints share a layout scope and use fitted home
poses; coordinated transport requires moving a shared group, not sending one
endpoint to a global anchor. Contradictions and unsupported scope crossings fail
explicitly. Rectangular entities use their native fitted rectangle rather than
being reduced to square icon geometry.

For staged live runs, the pipeline first synthesizes and validates the actual
local narration. Its measured waveform duration and reported word intervals
then constrain choreography, instead of the outline's estimated scene length.
Reported repeated-word occurrences are scene-local. Cached raw waveforms are
hash-checked and reused byte-for-byte in the final voice package; changing
narration or the prepared waveform fails rather than silently resynthesizing it.
If explicitly unaligned preflight is requested, choreography cannot invent
word timing and uses fraction/time cues against the measured waveform.
Speech-budget validation counts punctuation-separated words, not just spaces.
Hard word-count grammar caps are avoided because they can force a local
decoder to pack extra words into comma-joined tokens or an unfinished clause.
When narration needs a scoped repair, the provider instead returns one spoken
word per array item, with an exact array-length budget. The controller rejects
multiword or overlong items, joins the words and normalizes terminal punctuation
before revalidating. This prevents overlong prose without silently truncating
it or changing the scene. Fluency remains a separate semantic review concern.
For a scene-local failing field, the local provider returns only a replacement.
The controller preserves every other field and revalidates the whole scene.
Narration repairs receive the explicit speech-word budget and scene evidence,
without duplicating the full film or actor graph. Optional layout-reference
repairs admit only existing cycle-safe partners, or an explicit null to remove
that reference without reparenting other actors or changing semantic relations.
When several actors name nonexistent layout partners, one bounded repair may
address only those listed reference fields together. All other actor fields are
preserved. The admitted references follow a dependency-first order so individually
legal choices cannot form a new cycle together. The full graph is revalidated.
Its sampling branches admit only actual actor IDs, initialized properties and
compatible verbs. Data values are bounded to compatible typed evidence; numeric
actors are excluded when the scene has no quantities; value bindings are
available only to number/bar actors and are mandatory there. Event targets are a
redundant projection of the authored change-map keys and are derived by the
controller, not inferred from evidence IDs. Dependencies, timing, overlapping
writes and retained state still receive separate semantic validation. No scene
or motion template is substituted when direction fails.

`tools/make_film.py` accepts either `--brief TEXT` / `--brief-file FILE` with
`--evidence FILE`, or `--score FILE`. JSON evidence is a nonempty array of the
frozen evidence records, including explicit commercial-use source provenance.
No source URI is downloaded. `--context FILE` carries exact audience, brand and
creative intent to live authoring. `--family neon|candy|forest|ocean|ember` is a
contextual direction, not a background cycle. `--aspects 16:9,9:16,1:1` defaults
to all three **native** outputs. `--film-id` is stable and cannot rename an approved
score. Approved score evidence, brief and style cannot be silently changed.

The pipeline runs validation, structural score audit, actual per-scene TTS,
reported alignment binding, exact PCM timing conformance, all-aspect compilation,
plan/aspect audits and isolated Chrome/ffmpeg rendering. Any unsupported intent,
invalid event timing, unreadable runtime typography or missing route fails closed.
A short TTS waveform cannot be made to fit long actions by stretching speech,
uniformly inventing words, truncating actions or adding a stock voice. Fraction
cues remain provisional, even when the narration has real word timestamps.

`--out` must be a **new** directory beneath an existing parent outside git. Keep
proofs under `/home/ubuntu/vid_study/explainer_direction`. The pipeline never
attaches to the user's desktop browser or restarts services. `--fps 30` is the
production default; lower values are deliberate sparse test captures, not motion
quality evidence. `--workers` is 2..4. No installation is performed.

Outputs include `request.json`, `authored-score.json`, `score.json`, score/plan/
aspect audits, `voice/` raw and conformed waveforms, complete alignment when
available, exact source/provider ledgers, `sound/` selected immutable snapshots,
native plans, `render-*/frames/*.png`, `render-*/film.mp4`, renderer manifests,
and `manifest.json`. The production manifest hashes every other output byte,
records exact movie/frame/audio identity and authority gaps, and independently
checks encoded native dimensions, duration and audio stream. It deliberately does
not self-hash: callers bind the SHA256 of the completed manifest externally.
Successful live execution reports `RENDER_READY_NOT_CREATIVE_LOCKED`. Failure
retains an honest `FAILED` manifest after output initialization, not a fake film.
Configuration failures before initialization return JSON errors and exit 2.

## Commercial local voice routes

Preferred integration reuses `NEXSTUDIO_TTS_ROUTES_JSON` and the existing
`NexStudioAudioProviderRequestV1` stdin/stdout command protocol, without modifying
`services/studio-family-engines/audio_provider.py`. In addition to its existing
`id`, `command`, `commercialUseAllowed`, `priority`, `timeoutSeconds` and optional
`credentialEnv`, this stricter boundary requires:

- `local: true` (operator declaration; a command alone is not evidence of locality);
- `provider`: the exact identity also returned by `providerEvidence.provider`;
- `source`: the exact frozen `{id,uri,locator,license,commercial_use:true}` commercial
  audio/voice provenance, or an explicit `--voice-source FILE` override.

`--tts-route ID` selects exactly that declared local commercial route. Without an
ID the highest-priority eligible route is chosen **once**; route failure does not
silently fall through to another voice. `--voice-id` passes the declared selection.
The final stdout JSON must provide `audioPath` equal to the requested output,
`rightsEvidence.commercialUseAllowed:true`, `providerEvidence.provider`, and
optionally:

```json
{"alignment":{"provider":"exact-local-provider","method":"provider_word_timestamps","audio_sha256":"SHA256_OF_EXACT_RAW_WAVEFORM","words":[{"word":"Actual","start_ms":85,"end_ms":310},{"word":"speech.","start_ms":390,"end_ms":870}]}}
```

This is a **shape**, not timing evidence. Reported tokens must cover the entire
narration in order and fit the actual waveform. `providerEvidence.alignmentPath`
may instead name precisely `<requested audio path>.alignment.json` with that
same alignment object. No synthesized even/character schedule is admitted. The
existing Chatterbox route explicitly emits `EVEN_SCHEDULE_FROM_GENERATED_AUDIO`;
that is **not** usable word alignment. It may supply actual local voice audio
only with an additional real forced aligner (or explicitly unaligned preflight).
`espeak` voices and fixture transport declarations are forbidden live.

For a voice without timing, declare a local commercial command in
`EXPLAINER_DIRECTION_ALIGNER_ROUTES_JSON`, with the same route identity/locality
fields, then pass `--aligner-route ID`. Its stdin is
`{schema:'explainer-direction.align-request/v1',text,audio_path,audio_sha256,
scene_id,requirements:{local_only:true,real_alignment:true}}`. Final stdout is
`{provider,method:'forced_alignment',audio_sha256,words:[...]}` using the **same
unchanged input bytes**. A missing aligner fails; no aligner is installed by the
pipeline. `--allow-unaligned` is an explicit preflight exception for non-word cues
only, and records the missing complete word-alignment gap. It is not timing proof.

Raw audio is snapshotted and hashed before normalization. 48 kHz stereo PCM24
normalization does not scale timestamps; any duration discrepancy greater than
one millisecond fails. Less than one millisecond of declared trailing PCM padding
conforms each scene to an exact integer-millisecond duration. Every raw/conformed
hash, pad amount and reported alignment remains in the ledger. The final
alignment hash binds the concatenated conformed master voice used by **all**
native renders. Acoustic authenticity still needs independent exact-audio review.

### Installed Kokoro

Alternatively pass `--kokoro-config FILE`, mutually exclusive with route voice
arguments. The file supplies `id`, `model_path`, `config_path`, `voice_path`,
`language:'a'|'b'`, `source` and optional `device:'cpu'`, `speed:1`. All three paths
must already exist; weights/config and a rights-declared local voice are required.
The Python environment must already have compatible Kokoro, torch, numpy, Misaki
and its local `en_core_web_sm` model. Parent handles installation and source
selection. HF/transformer offline flags are enforced and missing spaCy models
fail before Misaki can attempt an implicit download. There is no hosted voice or
stock TTS fallback. Kokoro's optional phonemizer is not an espeak **voice** route.

Kokoro token `start_ts`/`end_ts` are retained from its actual predicted phoneme
durations and chunk offsets. They are labeled **provider predicted durations**,
not independently measured forced alignment. Tokenizer fragments/punctuation may
join only at reported whitespace; missing timing or incomplete token coverage
fails. Raw phoneme strings and predicted duration frames are preserved in the
provider ledger, not turned into fabricated acoustic phoneme intervals. Other
languages use a separately declared route/real forced aligner. This adapter's
installed-model inference must still be exercised on the parent's actual setup;
synthetic regression tests do not establish voice quality or availability.

## Sound direction: semantic, optional, rights-bound

Silence is the default, not a random SFX generator. `--sound-direction FILE` is
caller-authored `{cues:[...],music:[...]}`. A cue has exactly
`{event_id,semantic_tag,asset_id,gain,rationale}`. The local production sound
registry must mark that exact asset `ADMITTED`, selectable and CC0, with matching
production SHA256, source provenance and an existing license file. Unknown-rights
inherited/quarantined sounds fail rather than being laundered as owned.

Currently executable semantic tags are deliberately small:

- `ui.select|ui.switch|ui.toggle`: an actual selector **selection change** in a
  select/update event; sound lands at the discrete property's `end_ms`, when the
  visible selection really changes, not the numeric interpolation's start;
- `motion.ui.expand|motion.ui.contract`: actual increasing/decreasing scale in
  supported grow/reframe/morph/update events;
- `whiteboard.marker.line|whiteboard.marker.short|whiteboard.pencil.short|
  whiteboard.pencil.write`: actual increasing shape/axis/connector stroke trace.

No footsteps, pen-cap contact, drop/glass impacts, scribble or arbitrary whoosh is
inferred from a generic actor. Such requests require an executable P8 replan.
Music has exactly `{path,source,sha256,start_ms,gain,rationale}`: explicit existing
local bytes, declared rights and a semantic motive. Gain is 0..2 and every clip
must fit the film. No implicit downloads, copyrighted stock tracks, loops or
truncation. Supplied licensed music/SFX and the exact voice are mixed by the owned
renderer, which records audio snapshots and encodes AAC with native H264 video.

## P8-approved execution and optional Studio adapter

`--score FILE` with `p8_bound` requires
`--authority-verifier /absolute/trusted_caller.py:function`. The explicitly trusted
caller function receives an isolated validated score and must authenticate the
exact P8 state/board, decision slots, committed semantic score and evidence. A
function merely checking hash syntax or returning True unconditionally is **not**
a valid production authenticator. P8 sound supplied separately additionally
requires `--sound-authority-verifier FILE:FUNCTION`, receiving
`{score,sound_direction}` and verifying the committed Sound slot. No verifier can
promote a development/fixture score to P8.

`services/studio-family-engines/explainer_direction_adapter.py` exposes
`capabilities()` and `build_internal_evidence(request, *, authority_verifier,
voice_provider=None, aligner=None)`. Request schema is
`StudioExplainerDirectionRequestV1`; required fields are `semanticDirection`
(frozen P8 score), exact `evidence`, exact `brief`, and `outputDirectory`.
Optional fields: `aspects`, `soundDirection`, `fps`, `workers`, `assetRoot`,
`ttsRoute`, `voiceSource`, `voiceId`, `alignerRoute`, `proof`.
Here `authority_verifier(deepcopy(request))->True` must authenticate the **whole
request**, including Sound commits. Only after that boundary does the adapter
bind exact score/sound equality into the execution pipeline. It does not author,
restyle, supply fixture voices, register dispatch or certify taste. The result is
`StudioExplainerDirectionExecutionEvidenceV1` with `status:'RENDER_READY'`, exact
manifest/movie hashes, native evidence and explicit unfulfilled authority gaps.

## Parent commands: new factual cache-invalidation proof

These are executable commands, not a recorded output pack. First the parent must
configure the **actual** loopback author model using
`EXPLAINER_DIRECTION_BASE_URL` and `EXPLAINER_DIRECTION_MODEL` (optional API key),
and declare an actual local commercial voice route with real word timing or a
real local forced aligner as above. No route/model/rights are invented here.
Prepare `/home/ubuntu/vid_study/explainer_direction/cache-evidence.json` from a
new factual, commercial-use-declared corpus; preserve supported/uncertain status
and exact observed comparison conditions. Do not pass sample_score or synthetic
provider output as live evidence.

Prepare `cache-short-context.json` with the actual intended audience, brand and a
request for a roughly twenty-second cache hit → invalidation mechanism. Request
narration and linked events jointly, word cues on genuine mechanism changes,
several scenes with addressable cache/key/response actors and varied relations.
Prepare `cache-full-context.json` for a richer roughly one-minute film, retaining
explicit identities where appropriate and explaining invalidation tradeoffs from
the same actual evidence. Context files are creative inputs, not a promise of
measured runtime: the proof duration gates check **actual TTS** results.

From any working directory, after the above local routes/input files exist:

```sh
PYTHONDONTWRITEBYTECODE=1 /home/ubuntu/.pyenv/versions/3.12.13/bin/python3.12 \
 /home/ubuntu/repos/nexstudio/engine_sources/explainer-direction/tools/make_film.py \
 --brief 'Explain a cache hit and explicit invalidation using only supplied evidence; show the causal mechanism, not a widget per sentence.' \
 --evidence /home/ubuntu/vid_study/explainer_direction/cache-evidence.json \
 --family forest --context /home/ubuntu/vid_study/explainer_direction/cache-short-context.json \
 --aspects 16:9,9:16,1:1 --film-id cache_mechanism_short --proof short \
 --out /home/ubuntu/vid_study/explainer_direction/cache-short-proof-01

PYTHONDONTWRITEBYTECODE=1 /home/ubuntu/.pyenv/versions/3.12.13/bin/python3.12 \
 /home/ubuntu/repos/nexstudio/engine_sources/explainer-direction/tools/make_film.py \
 --brief 'Explain cache reuse, invalidation, stale responses and the causal tradeoffs using only supplied evidence; preserve uncertainty and motivate distinct scene constructions.' \
 --evidence /home/ubuntu/vid_study/explainer_direction/cache-evidence.json \
 --family forest --context /home/ubuntu/vid_study/explainer_direction/cache-full-context.json \
 --aspects 16:9,9:16,1:1 --film-id cache_mechanism_full --proof full --staged \
 --history /home/ubuntu/vid_study/explainer_direction/cache-history.json \
 --out /home/ubuntu/vid_study/explainer_direction/cache-full-proof-01
```

`cache-history.json` is an array containing the actual validated short score or
its audit report, not a canned structural signature. Omit `--history` for the
first full exploration. Add `--tts-route YOUR_DECLARED_ID` to select a route,
`--aligner-route YOUR_DECLARED_ALIGNER` if timing is absent, or replace route
arguments with `--kokoro-config /absolute/installed-kokoro.json`. No production
proof command uses `--allow-unaligned`. `--proof short` requires actual 15..25
seconds; `--proof full` requires more than 25 seconds. Failure means repair the
exact authored timing or return to its causal owner, not stretch a voice or
relabel a failed film. Use new output directory names when rerunning.

For an authenticated P8-approved score instead of standalone exploration:

```sh
PYTHONDONTWRITEBYTECODE=1 /home/ubuntu/.pyenv/versions/3.12.13/bin/python3.12 \
 /home/ubuntu/repos/nexstudio/engine_sources/explainer-direction/tools/make_film.py \
 --score /home/ubuntu/vid_study/explainer_direction/cache-p8-approved-score.json \
 --authority-verifier /absolute/trusted_p8_caller.py:verify_score \
 --aspects 16:9,9:16,1:1 --proof short \
 --out /home/ubuntu/vid_study/explainer_direction/cache-p8-short-proof-01
```

Review the exact `render-16x9/film.mp4`, `render-9x16/film.mp4` and
`render-1x1/film.mp4` and their **native audio** with independent reviewers, binding
the completed manifest and movie hashes. Sparse test captures and structural
warnings are not professional motion/creative certification. Customer delivery,
P8 final lock and public deployment remain disabled here.

## Regression commands and evidence boundary

```sh
PYTHONDONTWRITEBYTECODE=1 /home/ubuntu/.pyenv/versions/3.12.13/bin/python3.12 \
 -m pytest -q -p no:cacheprovider \
 /home/ubuntu/repos/nexstudio/engine_sources/explainer-direction/tests

/home/ubuntu/.nvm/versions/node/v24.19.0/bin/node --test \
 /home/ubuntu/repos/nexstudio/engine_sources/explainer-direction/tests/test_runtime.cjs
```

`tests/test_pipeline.py` uses explicit `is_test_fixture=True` providers and
`test_fixture=True` execution, rejects those in live/P8 modes, exercises real
subprocess transport/ffmpeg and creates native MP4/PNG/AAC **test evidence** outside
git. Synthetic sine waves and synthetic timing are loudly labeled, never speech
or local-inference proof. Test-only renderer injection is forbidden live; the
CLI deliberately exposes no fixture switch. Installed Kokoro inference, actual
source rights, exact-media independent perceptual review and human calibration
are parent integration gates, not accomplishments of these tests.
