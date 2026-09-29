# CAST_RESOLVER_V1

`CAST_RESOLVER_V1` is the Phase-F semantic resolver for NexStick Cast V1.

## Boundary

It converts a `CastRequest` into role requirements, compatible/ranked Phase-C family identifiers, Phase-B clothing tag recommendations, Phase-E personality recommendations, and final or candidate `CastSpec` objects. It never samples or edits motion, never changes geometry, and never selects scene layout/storyboard/camera.

## Node usage

```js
const CastResolver = require('./CAST_RESOLVER_V1');

const result = CastResolver.resolve('teacher + three children');
console.log(result.status);
console.log(result.slots);
```

Structured requests are preferred for production:

```js
const result = CastResolver.resolve({
  schema_version: '1.0.0',
  request_id: 'demo-001',
  slots: [{
    slot_id: 'presenter',
    count: 1,
    role: 'presenter',
    family: 'adult_woman_average',
    clothing_tag: 'business_casual',
    personality: 'confident'
  }]
});
```

When a family is explicitly selected and semantic constraints are satisfied, the slot returns `final_cast_spec`. When family/demographic choices remain open, the resolver returns `ranked_candidates`; it does not randomly pick a demographic.

## Natural-language scope

The included parser is intentionally bounded. It supports the release examples and common count/gender/age/morphology phrases. It is not a general NLP system. Director/NexMind may produce the structured `CastRequest` directly.

## Determinism

No random or wall-clock data is used. Candidate ranking is score-descending; exact ties use `family_id` lexical order only for stable serialization and are explicitly not a demographic preference.
