// Deterministic content guardrails for user-facing generated text.
// The provider prompt carries the full policy; this pass is the hard backstop:
// anything flagged here never reaches a video render.

export type GuardCategory =
  | "profanity"
  | "crime"
  | "self_harm"
  | "sexual_minors"
  | "hate"
  | "official_attack"
  | "extremism"
  | "fraud";

const RULES: Array<{ category: GuardCategory; re: RegExp }> = [
  // Vulgar / profanity — covers the common set plus leetspeak-light variants.
  { category: "profanity", re: /\b(fuck|shit|cunt|bitch|bastard|whore|slut|cock|pussy|dick|asshole|motherfuck\w*|faggot|nigg\w+|retard\w*)\b/i },
  // Crime promotion / instructions — how-to harm, weapons, drugs-for-sale, evasion.
  { category: "crime", re: /\b(how to (make|build|get|buy)\w*.{0,24}(bomb|explosive|weapon|gun|drug|poison)|make a bomb|molotov|synthesize.{0,16}(drug|meth|fentanyl)|sell(ing)? drugs|launder(ing)? money|shoplift\w*|pickpocket\w*|carjack\w*|hack(ing)? (into|a|the)|steal(ing)? (a |an |the )?(car|identity|credit card)|counterfeit\w*)\b/i },
  // Self-harm instructions or encouragement.
  { category: "self_harm", re: /\b(kill yourself|how to (commit )?suicide|ways to (end it|die)|self[- ]?harm (guide|how)|cutting yourself)\b/i },
  // Sexual content involving minors — zero tolerance.
  { category: "sexual_minors", re: /\b(child|minor|kid|underage|schoolgirl|schoolboy).{0,30}(sexy|nude|naked|porn|sexual)|(sexy|nude|naked|porn|sexual).{0,30}(child|minor|kid|underage)\b/i },
  // Hate / dehumanization of protected classes.
  { category: "hate", re: /\b(all|those|these)\s+(jews|muslims|christians|blacks|whites|asians|immigrants|gays|trans(gender)?s?|women)\s+(are|should|must|deserve)\s+(be|die|burn|leave|suffer|deported)|\b(ethnic cleansing|master race|racial purity)\b/i },
  // Attacks on government officials / public figures — violence or defamation aimed at officeholders.
  { category: "official_attack", re: /\b(kill|hang|execute|assassinat\w+|shoot|lynch|imprison|arrest)\w*\s+(the\s+)?(president|prime minister|minister|senator|governor|mayor|mp|congressman|congresswoman|official|politician)s?\b|\b(president|prime minister|minister|senator|governor|mayor)\w*\s+(is|are|should be|must be|deserves?)\s+\w*\s*(killed|hanged|executed|shot|arrested|corrupt|a criminal|a dictator|evil|a traitor)/i },
  // Extremist praise / recruitment.
  { category: "extremism", re: /\b(join|support|donate to|praise)\s+(isis|al[- ]?qaeda|hamas|hezbollah|the taliban|boko haram)|\bjihad\b.{0,20}\b(recruit|join|attack)/i },
  // Fraud / deception-as-instruction.
  { category: "fraud", re: /\b(how to (scam|defraud|embezzle|forge)|fake (id|passport|invoice|receipt)s? (for|to)|phish(ing)? (emails|links)|ponzi|pyramid scheme)\b/i },
];

export interface GuardResult {
  ok: boolean;
  categories: GuardCategory[];
  flagged: string[];
}

export function checkText(text: string): GuardResult {
  const categories = new Set<GuardCategory>();
  const flagged: string[] = [];
  for (const { category, re } of RULES) {
    const m = re.exec(text);
    if (m) {
      categories.add(category);
      flagged.push(m[0].slice(0, 80));
    }
  }
  return { ok: categories.size === 0, categories: [...categories], flagged };
}

export function checkScriptLines(lines: string[]): GuardResult {
  const categories = new Set<GuardCategory>();
  const flagged: string[] = [];
  for (const line of lines) {
    const r = checkText(line);
    for (const c of r.categories) categories.add(c);
    flagged.push(...r.flagged);
  }
  return { ok: categories.size === 0, categories: [...categories], flagged };
}
