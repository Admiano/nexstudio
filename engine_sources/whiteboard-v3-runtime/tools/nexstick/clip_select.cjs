/* clip_select — narration text -> vault clip.
 * Deterministic pattern table over the merged vault (CMU corpus + EX_*
 * exercise set + nexstick actions). First matching pattern wins; order
 * goes most-specific to most-general so "does a push-up" beats "up".
 * Returns the clip name or null — callers fall back to a neutral clip.
 */
'use strict';

const TABLE = [
  // exercises (EX_* authored keypose clips)
  [/push[\s-]?up|press[\s-]?up/, 'EX_PUSH_UP'],
  [/squat/, 'EX_SQUAT'],
  [/dead[\s-]?lift/, 'EX_DEADLIFT'],
  [/lunge/, 'EX_LUNGE'],
  [/jumping jack|star jump/, 'EX_JUMPING_JACK'],
  [/overhead press|shoulder press/, 'EX_OVERHEAD_PRESS'],
  [/kettlebell|kb swing/, 'EX_KETTLEBELL_SWING'],
  [/bicep curl|curls? (the )?(dumbbell|barbell|weight)/, 'EX_BICEP_CURL'],
  [/plank/, 'EX_PLANK'],
  [/mountain climber/, 'EX_MOUNTAIN_CLIMBER'],
  [/bear crawl|crawl/, 'EX_BEAR_CRAWL'],
  [/downward dog|down dog/, 'EX_DOWNWARD_DOG'],
  [/burpee/, 'EX_BURPEE'],
  [/sit[\s-]?up|crunch/, 'EX_SIT_UP'],
  [/glute bridge|hip (bridge|thrust)/, 'EX_GLUTE_BRIDGE'],
  [/pull[\s-]?up|chin[\s-]?up/, 'EX_PULL_UP'],
  [/dips?\b/, 'EX_DIP'],
  [/bird[\s-]?dog/, 'EX_BIRD_DOG'],

  // interactions + everyday CMU (specific first)
  [/handshake|shake hands|shakes hands|greets?/, 'CMU_SHAKE_HANDS'],
  [/comfort|hug|console/, 'CMU_INTERACT_COMFORT'],
  [/pull(s|ing)? apart|tug/, 'CMU_INTERACT_PULL'],
  [/catch(es|ing)?|throw(s|ing)?|toss/, 'CMU_CATCH_THROW'],
  [/sit(s|ting)? down|get(s|ting)? up|stand(s|ing)? up/, 'CMU_SIT_GETUP'],
  [/sit(s|ting)? (on|at)|seated/, 'CMU_SIT_STOOL'],
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
  [/waits?|waiting|stands? still|idle/, 'CMU_WAIT_IDLE'],
  [/talks?|speaks?|explains?|tells?|presenting|presenter/, 'CMU_TALK_GESTURE'],
  [/sneak(s|ing|y)?|tiptoe|stealth/, 'CMU_SNEAK'],
  [/\bruns?\b|\brunning\b|\bjogs?\b|\bjogging\b|\bsprints?\b/, 'CMU_RUN_STOP'],
  [/march(es|ing)?/, 'CMU_MARCH'],

  // character walks (mood/style)
  [/drunk|drunken|stagger|stumble/, 'CMU_WALK_DRUNK'],
  [/swagger|macho|strut|confident/, 'CMU_WALK_MACHO'],
  [/depress|dejected|downcast/, 'CMU_WALK_DEPRESSED'],
  [/sad|unhappy/, 'CMU_WALK_SAD'],
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
