# Motion Rules

- Build the most visible static layout first.
- Add entrances from an offset into the CSS-defined final position.
- All timelines start paused and register synchronously.
- Ambient loops use finite repeat counts derived from composition duration.
- Prefer transform and opacity over layout animation.
- Use at least three easing personalities in multi-element scenes.
- Multi-scene demonstrations use transitions rather than empty-frame exits.
- Low energy: 0.8× travel, 1.25× duration. Medium: baseline. High: 1.25× travel, 0.8× duration.

## Batch 3 runtime rules

1. Motion code must not reference a specific paper-object ID or renderer.
2. Entrances end at the target's normal CSS layout position.
3. Actions and ambient behaviour are finite and deterministic.
4. Energy variants modify amplitude, duration and finite cycle count through parameters.
5. Generated motion layers use `data-motion-layer` and remain subordinate to the reusable target.
6. A transition owns the outgoing scene's departure; no separate fade-to-empty is permitted.
7. Every motion manifest declares at least three compatible target types.
8. Sound is represented only through semantic tags until a later audio batch binds approved files.
9. Timeline construction is synchronous and every composition timeline begins paused.
10. New primitives must pass the matrix, seekability, responsive-layout and animation-map audits before entering the master registry.
