/* clip_select — narration text -> vault clip.
 * Deterministic pattern table over the merged vault (CMU corpus + NEX performance carrier + EX_*
 * exercise set + nexstick actions). First matching pattern wins; order
 * goes most-specific to most-general so "does a push-up" beats "up".
 * Returns the clip name or null — callers fall back to a neutral clip.
 */
'use strict';

const TABLE = [
  // host gestures — standing, authored for this character (file1 rig)
  [/explains?|explain(ing)? to|talks? (about|to)/, 'NEX_HOST_EXPLAIN_MEDIUM'],
  [/present(s|ing|ation)?|show(s|ing)? (this|that|you)/, 'NEX_HOST_PRESENT_OPEN'],
  [/question|asks?\b|wonder/, 'NEX_HOST_QUESTION_OPEN'],
  [/nods?|agrees?\b/, 'NEX_HOST_AGREE_NOD'],
  [/listens?|hear/, 'NEX_HOST_LISTEN_ATTENTIVE'],
  [/emphas(is|ize|izes)|important|key point/, 'NEX_HOST_EMPHASIS_SMALL'],

  // exercises — authored dense actions (MECHANIC set)
  [/push[\s-]?up|press[\s-]?up/, 'NEX_MECHANIC_PUSHUP_CYCLE'],
  [/squat/, 'NEX_MECHANIC_PARTIAL_SQUAT'],
  [/dead[\s-]?lift|hip hinge|hinges? (at )?(the )?hips?/, 'NEX_MECHANIC_HIP_HINGE'],
  [/lunge/, 'NEX_MECHANIC_LUNGE'],
  [/jumping jack|star jump/, 'NEX_MECHANIC_JUMPING_JACK_CYCLE'],
  [/overhead press|shoulder press|vertical press/, 'NEX_MECHANIC_VERTICAL_PRESS'],
  [/kettlebell|kb swing|ballistic hinge/, 'NEX_MECHANIC_BALLISTIC_HINGE'],
  [/bicep curl|curls? (the )?(dumbbell|barbell|weight)?/, 'NEX_MECHANIC_CURL_BILATERAL'],
  [/plank/, 'NEX_MECHANIC_PLANK_DYNAMIC'],
  [/mountain climber/, 'NEX_MECHANIC_PLANK_DYNAMIC'],
  [/bear crawl/, 'NEX_MECHANIC_CRAWL_CYCLE_BEAR'],
  [/crab walk/, 'NEX_MECHANIC_CRAWL_CYCLE_CRAB_WALK'],
  [/inchworm/, 'NEX_MECHANIC_CRAWL_CYCLE_INCHWORM'],
  [/burpee/, 'NEX_MECHANIC_BURPEE_CYCLE'],
  [/sit[\s-]?up|crunch|core flex/, 'NEX_MECHANIC_CORE_FLEXEXTEND'],
  [/glute bridge|hip (bridge|thrust)|bridge march/, 'NEX_MECHANIC_CONTRALATERAL_CORE_CYCLE_BRIDGE_MARCH'],
  [/dead bug/, 'NEX_MECHANIC_CONTRALATERAL_CORE_CYCLE_DEAD_BUG'],
  [/bird[\s-]?dog/, 'NEX_MECHANIC_CONTRALATERAL_CORE_CYCLE_BIRD_DOG'],
  [/dips?\b/, 'NEX_MECHANIC_DIP_CYCLE'],
  [/calf raise/, 'NEX_MECHANIC_CALF_RAISE'],
  [/side bend/, 'NEX_MECHANIC_SIDE_BEND_LEFT'],
  [/torso (rotate|twist)|twists?/, 'NEX_MECHANIC_TORSO_ROTATE_LEFT'],
  [/step[\s-]?up|step(s|ping)? (up|on)/, 'NEX_MECHANIC_STEP_VERTICAL'],
  [/single[\s-]?leg squat|pistol/, 'NEX_MECHANIC_SINGLE_LEG_SQUAT'],
  [/athletic (stance|ready|position)/, 'NEX_MECHANIC_ATHLETIC_READY'],
  [/brace|core hold/, 'NEX_MECHANIC_BRACE_HOLD'],
  [/carr(y|ies|ying) (weights?|load)/, 'NEX_MECHANIC_CARRY_CYCLE'],
  [/lateral raise|side raise/, 'NEX_MECHANIC_LATERAL_RAISE_BILATERAL'],
  [/arm circles?/, 'NEX_MECHANIC_JOINT_MOBILITY_CYCLE_ARM_CIRCLES'],
  [/leg swings?/, 'NEX_MECHANIC_JOINT_MOBILITY_CYCLE_LEG_SWINGS'],
  [/wall walk|handstand|inverted/, 'NEX_MECHANIC_INVERTED_TRANSITION'],
  [/chest fly|fly arc/, 'NEX_MECHANIC_FLY_ARC_STANDING'],
  [/rows?\b|rowing/, 'NEX_MECHANIC_ROW_PULL_RIGHT'],
  [/back extension|superman/, 'NEX_MECHANIC_BACK_EXTENSION'],
  [/overhead reach|reach(es|ing)? (up|overhead|high)/, 'NEX_MECHANIC_OVERHEAD_REACH_BILATERAL'],
  [/pull[\s-]?down|vertical pull|pulls? down/, 'NEX_MECHANIC_VERTICAL_PULL'],
  [/hip abduction|leg(s| lifts?)? out/, 'NEX_MECHANIC_HIP_ABDUCTION'],
  [/leg raise|knee raise/, 'NEX_MECHANIC_LEG_RAISE'],
  [/cardio|aerobic/, 'NEX_MECHANIC_CARDIO_CYCLE'],
  [/weight shift|shift(s|ing)? weight/, 'NEX_MECHANIC_WEIGHT_SHIFT_LEFT'],
  [/pull[\s-]?up|chin[\s-]?up/, 'EX_PULL_UP'],
  [/downward dog|down dog/, 'EX_DOWNWARD_DOG'],

  // authored emotion/motion (STICKMAN + MOTION set)
  [/danc(e|es|ing)/, 'NEX_MOTION_DANCE'],
  [/cheer(s|ing)?|celebrat/, 'NEX_MOTION_CHEER'],
  [/clap(s|ping)?|applau/, 'NEX_MOTION_CLAP'],
  [/box(ing|es)?|punch(es|ing)?/, 'NEX_MOTION_BOXING'],
  [/push(es|ing)? (a |the )?(car|box|wall|cart|door|it)/, 'NEX_MOTION_PUSH'],
  [/jumps?\b|jumping/, 'NEX_MOTION_JUMP'],
  [/floats?|swim(s|ming)?/, 'NEX_MOTION_FLOAT_ON_WATER'],
  [/wave|waves|waving|goodbye|hello/, 'NEX_STICKMAN_WAVE'],

  // interactions + everyday CMU (specific first)
  [/handshake|shake hands|shakes hands|greets?/, 'CMU_SHAKE_HANDS'],
  [/comfort|hug|console/, 'CMU_INTERACT_COMFORT'],
  [/pull(s|ing)? apart|tug/, 'CMU_INTERACT_PULL'],
  [/catch(es|ing)?|throw(s|ing)?|toss/, 'CMU_CATCH_THROW'],
  [/sit(s|ting)? down|get(s|ting)? up|stand(s|ing)? up/, 'CMU_SIT_GETUP'],
  [/sit(s|ting)? (on|at)|seated|sits\b/, 'NEX_MOTION_SIT'],
  [/hopscotch/, 'CMU_HOPSCOTCH'],
  [/ladder/, 'CMU_LADDER'],
  [/stairs?/, 'CMU_STAIRS'],
  [/write|writes|writing|chalkboard|whiteboard|teaches?/, 'CMU_WRITE_BOARD'],
  [/piano|plays? (the )?(piano|keys)/, 'CMU_PIANO'],
  [/phone|calls?|dials?|texts?|answers? (the )?phone/, 'CMU_PHONE_ANSWER'],
  [/sweeps?|sweeping|broom/, 'CMU_SWEEP'],
  [/pick(s|ing)? up|lift(s|ing)? (a |the )?(box|bag)/, 'CMU_PICKUP_BOX'],
  [/carr(y|ies|ying) (a |the )?(suitcase|bag|luggage)/, 'CMU_CARRY_SUITCASE'],
  [/wave|waves|waving|goodbye|hello/, 'CMU_WAVE_HELLO'],
  [/yawn|yawns|yawning|stretch/, 'CMU_STRETCH_YAWN'],
  [/paces?|pacing/, 'CMU_PACE'],
  [/laughs?|laughing/, 'CMU_LAUGH'],
  [/cries|crying|weep|weeping/, 'CMU_CRY'],
  [/scared|afraid|frightened/, 'CMU_SCARED_IDLE'],
  [/joy|celebrat/, 'CMU_JOY'],
  [/shrug/, 'CMU_SHRUG'],
  [/curtsy|bows?|bowing/, 'CMU_CURTSEY'],
  [/mope|moping/, 'CMU_MOPE'],
  [/waits?|waiting|stands? still|idle/, 'NEX_MOTION_LIVING_IDLE'],
  [/talks?|speaks?|explains?|tells?|presenting|presenter/, 'CMU_TALK_GESTURE'],
  [/sneak(s|ing|y)?|tiptoe|stealth/, 'CMU_SNEAK'],
  [/\bruns?\b|\brunning\b|\bjogs?\b|\bjogging\b|\bsprints?\b/, 'CMU_RUN_STOP'],
  [/march(es|ing)?/, 'CMU_MARCH'],

  // character walks (mood/style)
  [/drunk|drunken|stagger|stumble/, 'CMU_WALK_DRUNK'],
  [/swagger|macho|strut|confident/, 'CMU_WALK_MACHO'],
  [/depress|dejected|downcast/, 'CMU_WALK_DEPRESSED'],
  [/walks? sad|sad(ly)? walks?/, 'CMU_WALK_SAD'],
  [/sad|unhappy/, 'NEX_MOTION_SAD'],
  [/elated|excited/, 'CMU_WALK_ELATED'],
  [/happy|cheerful|jaunty/, 'CMU_WALK_JAUNTY'],
  [/shy|timid|nervous/, 'CMU_WALK_SHY'],
  [/angry|furious|storms?/, 'CMU_WALK_ANGRY'],
  [/scared walk|walks? scared|afraid/, 'CMU_WALK_SCARED'],
  [/graceful|elegant/, 'CMU_WALK_GRACEFUL'],
  [/clumsy|awkward/, 'CMU_WALK_CLUMSY'],
  [/old man|elderly|senior/, 'CMU_IDLE_OLD_MAN'],
  [/childish|child|kid/, 'CMU_WALK_CHILDISH'],
  [/gangly|lanky/, 'CMU_WALK_GANGLY'],
  [/relaxed|cool|laid back/, 'CMU_WALK_RELAXED'],
  [/rushed|hurried|hurry/, 'CMU_WALK_RUSHED'],
  [/strong/, 'CMU_WALK_STRONG'],
  [/chicken/, 'CMU_WALK_CHICKEN'],
  [/dinosaur/, 'CMU_WALK_DINOSAUR'],
  [/cat/, 'CMU_WALK_CAT'],
  [/stealthy/, 'CMU_WALK_STEALTHY'],

  // generic walk last — most general
  [/walks?|walking|stroll|goes?|moves?/, 'CMU_WALK'],
];

function selectClip(text, catalog) {
  const s = String(text || '').toLowerCase();
  for (const [re, clip] of TABLE) {
    if (re.test(s) && (!catalog || catalog[clip])) return clip;
  }
  return null;
}

module.exports = { selectClip, TABLE };
