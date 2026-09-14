/**
 * NexStudio Paper Cast — script context extraction
 *
 * Turns a user script (or a single beat of one) into the structured context the
 * cast selector ranks against: who is on screen, what they are doing, who they
 * are addressing, and where the beat's attention sits. Orientation lives here
 * too, because "she turns to the whiteboard" is a script fact, not a render
 * option.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.NexCastContext = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const ROLE_CUES = {
    presenter: ['present', 'host', 'narrat', 'introduc', 'welcome', 'speaker', 'keynote'],
    teacher: ['teach', 'lesson', 'classroom', 'tutor', 'instruct', 'explain to the class', 'lecture'],
    student: ['student', 'learner', 'pupil', 'study', 'homework', 'exam', 'course'],
    child: ['child', 'kid', 'toddler', 'son', 'daughter', 'playground'],
    executive: ['ceo', 'executive', 'director', 'board', 'leadership', 'stakeholder', 'strategy'],
    office_worker: ['office', 'desk', 'spreadsheet', 'inbox', 'colleague', 'admin', 'back office'],
    creator: ['creator', 'designer', 'studio', 'edit', 'film', 'record', 'publish', 'content'],
    technician: ['technician', 'engineer', 'repair', 'machine', 'sensor', 'maintenance', 'fault', 'diagnos'],
    healthcare_worker: ['nurse', 'doctor', 'clinic', 'patient', 'hospital', 'care team', 'triage'],
    builder: ['builder', 'construction', 'site', 'scaffold', 'install', 'warehouse', 'lift'],
    parent: ['parent', 'mum', 'mom', 'dad', 'family', 'household', 'at home'],
    customer: ['customer', 'shopper', 'buyer', 'client', 'checkout', 'cart', 'subscriber'],
    helper: ['support', 'help desk', 'assist', 'service agent', 'onboarding', 'guide the user'],
    salesperson: ['sales', 'pitch', 'quote', 'deal', 'prospect', 'upsell', 'demo call'],
    friend: ['friend', 'peer', 'teammate', 'partner', 'together', 'the two of them'],
    mentor: ['mentor', 'coach', 'advisor', 'veteran', 'senior', 'years of experience'],
    analyst: ['analyst', 'data', 'dashboard', 'metric', 'chart', 'report', 'research'],
    reporter: ['reporter', 'journalist', 'interview', 'field', 'documentary', 'camera crew']
  };

  const INTENT_CUES = {
    capture_attention: ['imagine', 'picture this', 'meet ', 'welcome', 'hook'],
    introduce_topic: ['introduc', 'today we', 'this is', 'start with', 'meet '],
    explain_concept: ['explain', 'because', 'means that', 'in other words', 'how it works', 'so that'],
    teach_step: ['step ', 'first,', 'next,', 'then ', 'finally', 'follow along'],
    guide_attention: ['look at', 'notice', 'point', 'here you can see', 'focus on', 'highlight'],
    compare_options: ['versus', ' vs ', 'compare', 'on the other hand', 'instead of', 'either'],
    show_data: ['chart', 'graph', 'number', 'percent', '%', 'growth', 'metric', 'dashboard'],
    demonstrate: ['demo', 'show you', 'watch', 'let me show', 'walkthrough'],
    investigate: ['investigat', 'inspect', 'why is', 'root cause', 'check the', 'diagnos'],
    show_work: ['typing', 'at the desk', 'working on', 'builds', 'configur', 'writes'],
    move_through_story: ['walks', 'heads to', 'moves to', 'travels', 'arrives', 'goes to'],
    handoff: ['hands over', 'passes', 'gives', 'sends it to', 'hand off', 'delegat'],
    collaborate: ['together', 'team up', 'with her colleague', 'with his colleague', 'pair'],
    converse: ['says', 'asks', 'replies', 'talks to', 'conversation', 'chats'],
    receive_information: ['listens', 'hears', 'learns', 'is told', 'reads'],
    reassure: ['reassur', 'don\u2019t worry', 'dont worry', 'calm', 'safe', 'supported'],
    celebrate_outcome: ['celebrat', 'success', 'finally', 'done!', 'wins', 'achiev', 'result is'],
    exit_scene: ['leaves', 'walks off', 'exits', 'turns away', 'heads out'],
    close_story: ['in summary', 'to recap', 'that\u2019s how', 'thats how', 'get started', 'sign up']
  };

  const ACTION_CUES = [
    { pose: 'walk-stride', cues: ['walks', 'walking', 'strides', 'heads to', 'arrives', 'moves across'] },
    { pose: 'turn-away', cues: ['turns away', 'walks off', 'leaves', 'exits', 'heads into'] },
    { pose: 'point-at-detail', cues: ['points', 'pointing', 'taps on', 'indicates', 'highlights'] },
    { pose: 'present-to-content', cues: ['presents', 'gestures to', 'reveals', 'shows the', 'turns to the'] },
    { pose: 'think-considering', cues: ['thinks', 'wonders', 'considers', 'unsure', 'puzzled', 'hesitat'] },
    { pose: 'hand-over', cues: ['hands over', 'passes', 'gives', 'offers', 'delivers'] },
    { pose: 'listen-attentive', cues: ['listens', 'nods', 'watches', 'waits', 'hears'] },
    { pose: 'celebrate-lift', cues: ['celebrates', 'cheers', 'throws her hands', 'throws his hands', 'delighted'] },
    { pose: 'work-at-surface', cues: ['types', 'typing', 'at the desk', 'at the laptop', 'writes', 'sketches'] },
    { pose: 'inspect-crouch', cues: ['crouches', 'kneels', 'bends down', 'inspects', 'examines'] },
    { pose: 'carry-load', cues: ['carries', 'lifts', 'hauls', 'loads', 'boxes'] },
    { pose: 'sit-and-talk', cues: ['sits', 'seated', 'sitting', 'at the table', 'interview'] },
    { pose: 'explain-open-hands', cues: ['explains', 'describes', 'talks through', 'walks us through'] },
    { pose: 'address-audience', cues: ['says to camera', 'to the viewer', 'addresses', 'greets', 'welcomes'] }
  ];

  const TARGET_CUES = [
    { target: 'camera', cues: ['to camera', 'to the viewer', 'at us', 'addresses the audience', 'looks at you'] },
    { target: 'content', cues: ['whiteboard', 'screen', 'chart', 'diagram', 'board', 'slide', 'the graph', 'the map', 'the product'] },
    { target: 'peer', cues: ['to her colleague', 'to his colleague', 'to the customer', 'to the student', 'each other', 'the other', 'to them'] }
  ];

  const ENERGY_CUES = {
    high: ['rush', 'fast', 'burst', 'excited', 'races', 'suddenly', 'explodes', 'celebrat', '!'],
    low: ['calm', 'slowly', 'quietly', 'gently', 'reflect', 'pause', 'steady']
  };

  const AGE_CUES = {
    child: ['child', 'kid', 'toddler', 'playground', 'seven-year', 'young son', 'young daughter'],
    teen: ['teen', 'student', 'school', 'college', 'pupil'],
    senior: ['senior', 'veteran', 'retired', 'grandmother', 'grandfather', 'elder', 'decades of']
  };

  const count = (text, cues) => cues.reduce((total, cue) => total + (text.includes(cue) ? 1 : 0), 0);

  function rank(text, table, limit) {
    const scored = Object.entries(table)
      .map(([key, cues]) => ({ key, score: count(text, cues) }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score || a.key.localeCompare(b.key));
    return limit ? scored.slice(0, limit) : scored;
  }

  /**
   * @param {string} script one beat, or a whole script
   * @param {object} [hints] explicit overrides that always beat inferred values
   */
  function analyze(script, hints) {
    const raw = String(script || '');
    const text = raw.toLowerCase();
    const h = hints || {};

    const roles = rank(text, ROLE_CUES).map((entry) => entry.key);
    const intents = rank(text, INTENT_CUES).map((entry) => entry.key);
    const actions = ACTION_CUES.map((entry) => ({ pose: entry.pose, score: count(text, entry.cues) }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score || a.pose.localeCompare(b.pose))
      .map((entry) => entry.pose);

    const targets = TARGET_CUES.map((entry) => ({ target: entry.target, score: count(text, entry.cues) }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => b.score - a.score);

    const ageBands = rank(text, AGE_CUES).map((entry) => entry.key);
    const high = count(text, ENERGY_CUES.high);
    const low = count(text, ENERGY_CUES.low);

    const directionCue = /\b(left|right)\b/.exec(text);
    const speakerCount = Math.max(
      roles.length >= 2 ? 2 : 1,
      count(text, ['each other', 'they both', 'the two of them', 'together']) ? 2 : 1
    );

    return {
      script: raw,
      roles: h.roles || roles,
      role: h.role || roles[0] || null,
      intents: h.intents || intents,
      intent: h.intent || intents[0] || null,
      actions: h.actions || actions,
      action: h.action || actions[0] || null,
      addressing: h.addressing || (targets[0] ? targets[0].target : null),
      secondaryTarget: targets[1] ? targets[1].target : null,
      ageBand: h.ageBand || ageBands[0] || null,
      motionEnergy: h.motionEnergy || (high > low ? 'high' : low > high ? 'low' : 'medium'),
      direction: h.direction || (directionCue ? directionCue[1] : null),
      castSize: h.castSize || speakerCount,
      useCase: h.useCase || null,
      paperStyle: h.paperStyle || null,
      aspectRatio: h.aspectRatio || null
    };
  }

  return { analyze, ROLE_CUES, INTENT_CUES, ACTION_CUES, TARGET_CUES, AGE_CUES };
});
