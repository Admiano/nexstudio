# SceneBam brand compatibility notes — October 13, 2026

## Public names
- Platform: **SceneBam**. Assistant/creative director: **Bam**.
- Platform icon: `app/icon.svg`. Shared React symbol: `src/studio-v2/SceneBamMark.tsx`.
- Public homepage and the authenticated Studio share the same symbol and wordmark.
- Core palette stays amber `#FFB000`, ink `#111612`, background `#F4F3EF`, paper `#FBFAF7`.

## Intentional legacy technical identifiers
These are internal compatibility interfaces, **not public brands**. Rename only with a reviewed migration.

- `src/studio-v2/nexstudio-v2.css`, `src/lib/nexmind.ts`, `src/lib/nexmind-routing.ts` and internal `nexmind-*`/ `nx-*` CSS selectors remain so existing components and rendering integrations do not break.
- `nx.*` browser storage keys (including `nx.brief`, `nx.family`, `nx.flow`, `nx.welcomed`) remain to preserve active user drafts, context, and navigation state.
- `NEXSTUDIO_PUBLIC_OPEN` remains an environment compatibility flag for guest-access routing.
- `nexmind` as an API response source identifier remains for compatibility with current consumers; it is not user-facing copy.
- `services/studio-nexmind-p8`, historic engine directories, workflow, database and migration identifiers are retained. Their data and contract changes are **out of scope** for the brand pass.
- Repo owner/name and legacy historical documents remain unchanged; rewriting project history is neither safe nor required.

## UX corrections in this pass
- The public brief composer no longer pretends to call Bam with a timed, fixed direction. Its CTA carries the actual entered brief into the Studio, where the real direction flow begins.
- A sample renderer clip or staged presenter demonstration is presented as an example, not proof that unshipped interactions are available.
- Public navigation directs visitors to production families, proof and the how-it-works intelligence section.
- A hard-coded render-time promise is removed because actual rendering time varies.

## Verification
The GitHub changes require a full Next.js runtime install, `npm run typecheck`, `npm run build` and browser checks of desktop/mobile sizes. Do not treat a source audit as a successful build.
Check auth handoff, brief carry-over, Bam state transitions, production family eligibility, and final review/publish behaviour on a test environment before merging.
No production deployment is authorized by this brand pass.
