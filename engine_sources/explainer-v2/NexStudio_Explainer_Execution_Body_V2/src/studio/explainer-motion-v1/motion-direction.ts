import type { CameraDirection, ContinuityObjectState, MotionCapabilityMetadata, MotionDirectionPlan, ScenePlan, SemanticMotionAction, SemanticMotionActionName, SemanticTransitionFamily, TransitionDirection, VisualEntity, VisualRelationship } from "./types";
import { executionMotionVersions, motionActionRegistry } from "./execution-grammar";

export const semanticMotionCapabilityInventory: MotionCapabilityMetadata[] = [
  { entityType: "path", capabilities: ["path-drawable", "growable", "branchable", "continuity-capable"] },
  { entityType: "growth-structure", capabilities: ["growable", "path-drawable", "branchable", "orientable", "transformable", "continuity-capable"] },
  { entityType: "substance", capabilities: ["flow-source", "flow-target", "transformable"] },
  { entityType: "object", capabilities: ["rotatable", "orientable", "transformable", "continuity-capable"] },
  { entityType: "energy", capabilities: ["flow-source", "flow-target", "transformable"] },
  { entityType: "signal", capabilities: ["flow-source", "flow-target", "transformable"] },
  { entityType: "typography", capabilities: ["transformable"] }, { entityType: "media", capabilities: ["transformable"] },
  { entityType: "data", capabilities: ["growable", "transformable"] }, { entityType: "workflow", capabilities: ["path-drawable", "branchable", "transformable"] },
];

const round = (value: number) => Math.round(value * 100) / 100;
const at = (duration: number, fraction: number, minimum = .1) => round(Math.max(minimum, duration * fraction));
const entities = (scene: ScenePlan) => [scene.visualConstruction?.heroEntity, ...(scene.visualConstruction?.supportingEntities ?? [])].filter((entity): entity is VisualEntity => Boolean(entity));

/** Fits semantic actions before a protected readable result window. */
export function enforceResultPersistence(plan: MotionDirectionPlan, sceneDurationSec: number, resultPersistenceFrames = 24, frameRate = 30): MotionDirectionPlan {
  const transitionDuration = plan.transitionOut?.durationSec ?? .6;
  const readableEnd = Math.max(.6, sceneDurationSec - transitionDuration - .1);
  const persistenceSec = Math.min(.8, Math.max(.4, resultPersistenceFrames / frameRate));
  const targetActionEnd = Math.max(.45, readableEnd - persistenceSec);
  const latestActionEnd = Math.max(.01, ...plan.actions.map((item) => item.startSec + item.durationSec));
  const factor = Math.min(1, targetActionEnd / latestActionEnd);
  const actions = factor < .999 ? plan.actions.map((item) => ({ ...item, startSec: round(item.startSec * factor), durationSec: round(Math.max(.18, item.durationSec * factor)) })) : plan.actions;
  const completedAt = Math.max(.01, ...actions.map((item) => item.startSec + item.durationSec));
  return { ...plan, actions, settledStoryboardState: round(Math.min(readableEnd, Math.max(completedAt + Math.min(.35, persistenceSec * .5), readableEnd - .05))) };
}

function action(scene: ScenePlan, id: string, verb: SemanticMotionActionName, actor: string, startFraction: number, durationFraction: number, options: Partial<SemanticMotionAction> = {}): SemanticMotionAction {
  if (!motionActionRegistry.includes(verb)) throw new Error(`UNSUPPORTED_SEMANTIC_MOTION_ACTION: ${verb}`);
  const startSec = at(scene.durationSec, startFraction);
  return { id: `${scene.id}:${id}`, action: verb, actor, startState: "not-yet-expressed", endState: "expressed", startSec, durationSec: round(Math.min(Math.max(.18, scene.durationSec * durationFraction), Math.max(.18, scene.durationSec - startSec - .12))), priority: "primary", easingProfile: "educational", ...options };
}

function relationshipAction(relationship: VisualRelationship): SemanticMotionActionName {
  const action = ({ enters: "enter", exits: "travel", "flows-to": "flow", "grows-from": "extend", "branches-from": "branch", "points-to": "orient-toward", surrounds: "reveal", "transforms-into": "transform", feeds: "transfer", absorbs: "absorb", produces: "assemble", "splits-into": "split", "merges-into": "merge", "travels-through": "travel", "rotates-around": "rotate", "accumulates-in": "accumulate", reveals: "reveal", replaces: "replace", "attaches-to": "connect", "detaches-from": "disconnect", "orients-toward": "orient-toward", validates: "highlight", "passes-to": "travel", "routes-to": "travel", "compares-with": "highlight", blocks: "close", unlocks: "open" } as const)[relationship.kind];
  if (!action) throw new Error(`UNSUPPORTED_VISUAL_RELATIONSHIP: ${relationship.kind}`);
  return action;
}

type MotionDeltaContext = {
  continuityId?: string;
  establishedEntities: Set<string>;
  establishedRelations: Set<string>;
};

const structuralRelationshipKinds = new Set<VisualRelationship["kind"]>(["grows-from", "branches-from", "attaches-to", "travels-through"]);
const boundaryContextRelationshipKinds = new Set<VisualRelationship["kind"]>(["exits", "travels-through"]);
const relationSignature = (relationship: VisualRelationship) => `${relationship.from}|${relationship.kind}|${relationship.to}`;

const p8VerbMap: Record<string, SemanticMotionActionName> = {
  REVEAL:"reveal", PRESENT:"reveal", HIGHLIGHT:"highlight", ENTER:"enter", EXIT:"exit",
  MOVE:"travel", WALK:"travel", RUN:"travel", CARRY:"travel", ROUTE:"travel", TRAVEL:"travel",
  GROW:"grow", SHRINK:"shrink", EXTEND:"extend", RETRACT:"retract", BRANCH:"branch", SPLIT:"split", MERGE:"merge",
  ABSORB:"absorb", FLOW:"flow", FALL:"fall", RISE:"rise", ROTATE:"rotate", ORIENT:"orient-toward", LOOK:"orient-toward",
  OPEN:"open", CLOSE:"close", UNFOLD:"unfold", PULSE:"pulse", ACCUMULATE:"accumulate", TRANSFORM:"transform",
  CONNECT:"connect", ATTACH:"connect", DISCONNECT:"disconnect", DETACH:"disconnect", SCAN:"scan", TRANSFER:"transfer",
  HANDOFF:"transfer", HANDOFF_DIRECT:"transfer", HANDOFF_PLACE_AND_TAKE:"transfer", ASSEMBLE:"assemble", DISPERSE:"disperse",
  REPLACE:"replace", VALIDATE:"validate", CHECK:"validate", PRESS:"highlight", TAP:"highlight", PLACE:"transfer", PICKUP:"transfer"
};
const p8CameraMap: Record<string, CameraDirection["action"]> = {
  HOLD:"hold", PUSH_IN:"gentle-push", PUSH:"gentle-push", PULL_BACK:"pull-back", PULL_OUT:"pull-back",
  FOLLOW:"follow-object", TRACK:"follow-object", PAN:"pan-along-path", REFRAME:"reframe", MACRO:"macro-focus",
  MACRO_FOCUS:"macro-focus", REVEAL:"ecosystem-reveal", FOCUS_TRANSFER:"focus-transfer", PARALLAX:"depth-parallax"
};
function exactP8MotionPlan(scene: ScenePlan): MotionDirectionPlan | undefined {
  const construction=scene.visualConstruction;
  const raw=construction?.p8MotionActions;
  const cameraRaw=construction?.p8CameraAtom;
  if(!raw && !cameraRaw) return undefined;
  const actionsRaw=Array.isArray(raw)?raw:[];
  const actions:SemanticMotionAction[]=actionsRaw.map((item,index)=>{
    const execution=(item && typeof item.execution==="object" && item.execution)?item.execution as Record<string,unknown>:{};
    const resolved=String(execution.resolved_verb??item.resolved_verb??item.requested_verb??"").trim().toUpperCase();
    const verb=p8VerbMap[resolved];
    if(!verb) throw new Error(`P8_EXPLAINER_EXECUTION_VERB_UNSUPPORTED:${resolved||"MISSING"}`);
    const actor=String(item.actor??item.performer??item.performer_ref??construction?.heroEntity.id??"subject");
    const target=String(item.target??item.semantic_target??execution.target??"").trim();
    const durationRaw=Number(item.duration_sec??item.durationSeconds??execution.duration_sec??0);
    const startRaw=Number(item.start_sec??item.startSeconds??execution.start_sec??NaN);
    const slot=scene.durationSec/Math.max(1,actionsRaw.length);
    const startSec=Number.isFinite(startRaw)?Math.max(0,startRaw):round(index*slot);
    const durationSec=durationRaw>0?durationRaw:round(Math.max(.18,slot*.78));
    return {id:String(item.action_id??`${scene.id}:p8-${index+1}`),action:verb,actor,...(target?{target}:{}),startState:String(item.start_state??"p8-authored-start"),endState:String(item.end_state??"p8-authored-end"),startSec,durationSec,priority:"primary",easingProfile:"precise"};
  });
  const atom=(cameraRaw&&typeof cameraRaw==="object"?cameraRaw:{}) as Record<string,unknown>;
  const atomName=String(atom.atom??"HOLD").trim().toUpperCase();
  const cameraAction=p8CameraMap[atomName];
  if(!cameraAction) throw new Error(`P8_EXPLAINER_CAMERA_ATOM_UNSUPPORTED:${atomName||"MISSING"}`);
  const cameraPlan:CameraDirection={action:cameraAction,target:String(atom.target??construction?.heroEntity.id??"subject"),reason:String(atom.motivation??"P8 committed camera atom"),startSec:0,durationSec:scene.durationSec};
  const visible=entities(scene).map(e=>e.id);
  return enforceResultPersistence({sceneId:scene.id,entryState:{id:`${scene.id}:entry`,description:"Exact P8-authored execution entry state.",visibleEntities:visible},actions,cameraPlan,settledStoryboardState:round(Math.max(.1,scene.durationSec-.2)),emotionalEnergy:String(scene.emotionalEnergy??"p8-authored"),motionDensity:actions.length>4?"active":actions.length>2?"moderate":"minimal",reducedMotionPlan:{strategy:"essential-path-only",preserveActions:actions.map(a=>a.id),suppressActions:[]}},scene.durationSec,24);
}

/**
 * Build the action delta for a scene rather than replaying its whole visual graph.
 * Structural relationships carried from an earlier continuity state are context,
 * not entrance animations. Primary growth on established structure becomes a
 * positive state delta instead of a zero-to-full redraw.
 */
function causalActions(scene: ScenePlan, context: MotionDeltaContext) {
  const relationships = scene.visualConstruction?.relationships ?? [];
  const entityMap = new Map(entities(scene).map((entity) => [entity.id, entity]));
  const roles = new Map((scene.visualConstruction?.artDirectionPlan?.supportingRoles ?? []).map((role) => [role.entityId, role]));
  const selected: Array<{ relationship: VisualRelationship; verb: SemanticMotionActionName; delta: "normal" | "positive-growth" }> = [];

  for (const relationship of relationships) {
    const signature = relationSignature(relationship);
    const source = entityMap.get(relationship.from);
    const sourceRole = roles.get(relationship.from)?.role;
    const attachedSurface = sourceRole === "attached-child" || source?.visualClass === "attached-surface";
    const structuralActor = Boolean(source && (source.type === "growth-structure" || source.capabilities?.some((capability) => ["growable", "path-drawable", "branchable"].includes(capability))));
    const bothEstablished = context.establishedEntities.has(relationship.from) && context.establishedEntities.has(relationship.to);
    const relationEstablished = context.establishedRelations.has(signature);
    const structural = structuralRelationshipKinds.has(relationship.kind);

    // Secondary boundary/location relationships on a structural actor describe
    // where a growth performance occurs; they are not a second animation that
    // should translate or hide the already-grown structure.
    if (relationship.emphasis === "secondary" && structuralActor && boundaryContextRelationshipKinds.has(relationship.kind)) continue;

    // Secondary structural edges only describe the settled topology when both
    // endpoints already exist. Replaying them produces the familiar "rebuild the
    // object every scene" failure.
    if (structural && bothEstablished && relationship.emphasis === "secondary") continue;

    // An attached surface is physically performed as one anchored unfold. Do not
    // first "branch" it into existence and then unfold the same pixels again.
    if (attachedSurface && (relationship.kind === "branches-from" || relationship.kind === "attaches-to")) {
      if (relationEstablished && relationship.emphasis === "secondary") continue;
      selected.push({ relationship, verb: "unfold", delta: relationEstablished || bothEstablished ? "positive-growth" : "normal" });
      continue;
    }

    // Exact carried structure is also settled context unless this beat explicitly
    // asks for further growth/branching. Those are rendered as positive deltas.
    if (structural && relationEstablished) {
      if (relationship.emphasis === "primary" && (relationship.kind === "grows-from" || relationship.kind === "branches-from")) {
        selected.push({ relationship, verb: relationship.kind === "branches-from" ? "branch" : "grow", delta: "positive-growth" });
      }
      continue;
    }

    // A new primary growth relation between already-established nodes should
    // develop the existing geometry rather than draw it from nothing.
    if (structural && bothEstablished && relationship.emphasis !== "secondary" && (relationship.kind === "grows-from" || relationship.kind === "branches-from")) {
      selected.push({ relationship, verb: relationship.kind === "branches-from" ? "branch" : "grow", delta: "positive-growth" });
      continue;
    }

    // "Exits" in a visual relationship means crossing/emerging through a
    // boundary. It must not use the scene-exit performer that makes the actor
    // disappear. Growable/path actors extend through the boundary; other actors
    // travel across it.
    if (relationship.kind === "exits" && structuralActor) {
      selected.push({ relationship, verb: "extend", delta: bothEstablished ? "positive-growth" : "normal" });
      continue;
    }

    selected.push({ relationship, verb: relationshipAction(relationship), delta: "normal" });
  }

  const count = Math.max(1, selected.length);
  const actions: SemanticMotionAction[] = [];
  selected.forEach(({ relationship, verb, delta }, index) => {
    const prior = actions.at(-1);
    actions.push(action(scene, `relationship-${index + 1}`, verb, relationship.from, .06 + index * (.55 / count), Math.min(.2, .48 / count), {
      target: relationship.to,
      relationship: relationship.kind,
      direction: relationship.direction,
      startState: delta === "positive-growth" ? "established" : "not-yet-expressed",
      endState: delta === "positive-growth" ? "further-developed" : "expressed",
      priority: relationship.emphasis === "secondary" ? "secondary" : "primary",
      chainAfter: prior?.id,
      easingProfile: ["travels-through", "passes-to", "routes-to", "validates"].includes(relationship.kind) ? "technical" : ["grows-from", "branches-from", "absorbs"].includes(relationship.kind) ? "organic-controlled" : "educational",
    }));
  });

  const append = (verb: SemanticMotionActionName, actor: string, label: string, options: Partial<SemanticMotionAction> = {}) => {
    const prior = actions.at(-1);
    actions.push(action(scene, label, verb, actor, Math.min(.78, .12 + actions.length * .14), .14, { chainAfter: prior?.id, easingProfile: "organic-controlled", ...options }));
  };

  for (const { relationship } of selected) {
    const source = entityMap.get(relationship.from);
    if (relationship.kind === "absorbs" && source?.capabilities?.includes("openable")) {
      append("grow", source.id, `${source.id}-responds`, { startState: "dry", endState: "expanded" });
      append("open", source.id, `${source.id}-opens`, { startState: "closed", endState: "open" });
    }
    // Do not invent extra branching merely because an entity is branchable.
    // Branching must come from an explicit semantic relationship or action.
  }
  return actions.length ? actions : [action(scene, "hero-hold", "highlight", scene.visualConstruction?.heroEntity.id ?? "subject", .08, .18, { startState: "established", endState: "emphasized", easingProfile: "calm" })];
}

function cameraFor(scene: ScenePlan): CameraDirection {
  const plan = scene.visualConstruction;
  const hero = plan?.heroEntity.id ?? "subject";
  if (plan?.spatialGrammar === "directional-split" || plan?.artDirectionPlan?.compositionArchetype === "vertical-growth") {
    const upward = plan.relationships.find((item) => item.direction === "up" && ["grows-from", "branches-from", "exits", "orients-toward"].includes(item.kind));
    return { action: "follow-object", target: upward?.from ?? hero, reason: "Follow the upward semantic development so the evolving structure stays inside the focal region.", startSec: at(scene.durationSec, .22), durationSec: at(scene.durationSec, .5), translateYPercent: -5, scaleFrom: 1, scaleTo: 1.045 };
  }
  if (plan?.spatialGrammar === "converging-inputs") return { action: "macro-focus", target: hero, reason: "Make the shared target of the converging inputs readable.", startSec: at(scene.durationSec, .08), durationSec: at(scene.durationSec, .58), scaleFrom: 1, scaleTo: 1.06 };
  if (scene.order === 0 && plan?.continuity) return { action: "gentle-push", target: hero, reason: "Establish the persistent semantic hero.", startSec: at(scene.durationSec, .16), durationSec: at(scene.durationSec, .46), scaleFrom: 1, scaleTo: 1.045 };
  if (plan?.spatialGrammar === "sequential-transformation" && !plan.relationships.some((item) => item.to === hero)) return { action: "pull-back", target: hero, reason: "Reveal the completed transformation and its connected parts.", startSec: at(scene.durationSec, .38), durationSec: at(scene.durationSec, .42), scaleFrom: 1.07, scaleTo: 1 };
  return { action: "hold", target: hero, reason: "Keep the semantic relationship stable while its causal action is demonstrated.", startSec: 0, durationSec: scene.durationSec };
}

function transitionFamily(scene: ScenePlan): SemanticTransitionFamily {
  if (!scene.visualConstruction?.continuity) return "focus-transfer";
  if (scene.visualConstruction.spatialGrammar === "directional-split") return "camera-follow";
  if (scene.visualConstruction.transformation) return "object-transformation";
  return "object-continuation";
}

function transition(scene: ScenePlan, next: ScenePlan | undefined): TransitionDirection | undefined {
  if (!next) return undefined;
  const continuity = scene.visualConstruction?.continuity;
  return { family: transitionFamily(scene), continuityObjectId: continuity?.objectId, fromState: continuity?.state, toState: next.visualConstruction?.continuity?.state, durationSec: round(Math.min(.82, Math.max(.46, scene.durationSec * .13))), reason: continuity?.handoff ?? `Transfer focus from ${scene.heroSubject} to ${next.heroSubject}.` };
}

export function createMotionDirectionPlans(scenes: ScenePlan[]): MotionDirectionPlan[] {
  const establishedByContinuity = new Map<string, { entities: Set<string>; relations: Set<string> }>();
  return scenes.map((scene, index) => {
    const exact=exactP8MotionPlan(scene);
    if(exact) return exact;
    const continuity = scene.visualConstruction?.continuity;
    const key = continuity?.objectId;
    const prior = key ? establishedByContinuity.get(key) : undefined;
    const context: MotionDeltaContext = { continuityId: key, establishedEntities: new Set(prior?.entities ?? []), establishedRelations: new Set(prior?.relations ?? []) };
    const actions = causalActions(scene, context), transitionOut = transition(scene, scenes[index + 1]);
    const transitionIn = index ? transition(scenes[index - 1]!, scene) : undefined;
    const resolved = enforceResultPersistence({ sceneId: scene.id, entryState: { id: `${scene.id}:entry`, description: scene.motionIntent?.entryState ?? "Approved construction before its primary action.", visibleEntities: entities(scene).map((entity) => entity.id), continuityState: continuity?.previousState ?? continuity?.state }, actions, cameraPlan: cameraFor(scene), transitionIn, transitionOut, continuityObject: continuity ? { id: continuity.objectId, incomingState: continuity.previousState ?? continuity.state, outgoingState: continuity.nextState ?? continuity.state } : undefined, settledStoryboardState: round(Math.min(scene.durationSec * .84, Math.max(.8, scene.durationSec - (transitionOut?.durationSec ?? .6) - .12))), emotionalEnergy: scene.styleProfile?.motionEnergy ?? scene.visualDirection?.energy ?? "measured", motionDensity: actions.length > 4 ? "active" : actions.length > 2 ? "moderate" : "minimal", reducedMotionPlan: { strategy: continuity ? "essential-path-only" : "settled-state-cuts", preserveActions: actions.filter((item) => item.priority === "primary").map((item) => item.id), suppressActions: actions.filter((item) => item.priority !== "primary").map((item) => item.id) } }, scene.durationSec, scene.visualConstruction?.artDirection?.resultPersistenceFrames ?? 24);
    if (key) {
      const currentEntities = new Set([...context.establishedEntities, ...entities(scene).map((entity) => entity.id)]);
      const currentRelations = new Set([...context.establishedRelations, ...(scene.visualConstruction?.relationships ?? []).filter((relationship) => structuralRelationshipKinds.has(relationship.kind)).map(relationSignature)]);
      establishedByContinuity.set(key, { entities: currentEntities, relations: currentRelations });
    }
    return resolved;
  });
}

export function buildContinuityRegistry(scenes: ScenePlan[]): ContinuityObjectState[] {
  return scenes.flatMap((scene) => {
    const continuity = scene.visualConstruction?.continuity;
    if (!continuity) return [];
    const hero = scene.visualConstruction?.heroEntity;
    const x = Number(hero?.geometry?.x ?? .5), y = Number(hero?.geometry?.y ?? .5), scale = Number(hero?.geometry?.scale ?? 1);
    const anchors = {
      center: { x, y }, top: { x, y: y - 64 * scale }, bottom: { x, y: y + 64 * scale }, left: { x: x - 64 * scale, y }, right: { x: x + 64 * scale, y },
      entry: { x: x - 96 * scale, y }, exit: { x: x + 96 * scale, y }, "growth-origin": { x, y }, "branch-origin": { x, y }, attachment: { x, y }, focus: { x, y },
    };
    return [{ continuityId: continuity.objectId, sceneId: scene.id, stateId: continuity.state, geometryState: { constructionId: scene.visualConstruction?.constructionId, spatialGrammar: scene.visualConstruction?.spatialGrammar, heroEntity: hero?.id }, geometrySnapshot: { heroRepresentation: hero?.representation, heroVisualClass: hero?.visualClass, heroGeometry: hero?.geometry, supportingRepresentations: scene.visualConstruction?.supportingEntities.map((entity) => ({ id: entity.id, representation: entity.representation, geometry: entity.geometry })) ?? [], relationships: scene.visualConstruction?.relationships ?? [] }, anchors, transformState: { cameraTarget: scene.motionDirection?.cameraPlan.target ?? hero?.id, continuityHandoff: continuity.handoff }, visualState: { preserveFeatures: continuity.preserveFeatures ?? [], styleProfile: scene.styleProfile ?? scene.visualConstruction?.styleProfile, motionDirectorVersion: executionMotionVersions.motionRuntimeVersion } }];
  });
}

export function attachMotionDirection(scenes: ScenePlan[]) { const plans = createMotionDirectionPlans(scenes); return scenes.map((scene, index) => ({ ...scene, motionDirection: plans[index] })); }
