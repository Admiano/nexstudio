# Cast V9 deployment checkpoint

This continues PR #45 on `devin/1790231957-offerings-trim-two-families`
from `4801b3d3b8e90dfd4cc639b91ab1f6b7dcb7aa58`. Do not rebuild or redesign
the modular Cast implementation. Presenter source remains PR #55 at
`bf88447b8f898bea078c44b9202cfe2b7ff13be5`.

## Verified before deployment

- Remote PR #45 still matched the supplied head.
- Manifest version is 9, at 720 x 1080 pixels.
- All 62 required plates are present: 25 female dress style/colour variants,
  25 male outfit/top-colour variants, and 12 face-specific lipstick plates.
- Existing Cast spec persistence regression passes, including explicit None,
  legacy authored colours, and Coral plate resolution.
- Full `npm run typecheck` and standard `npm run build` pass after the narrow
  pre-existing build repairs in this checkpoint. Type checking is enabled.
- Existing runtime security unit checks pass (7/7).
- Existing source-intelligence QA passes.
- JSON response/cookie verification passes with the actual helper functions.
- Upload scan worker verification passes: extraction happens before publishing;
  extraction failure retains quarantine and queues a retry.

No Cast component, option catalog, compositor, or baked asset was changed.
The repairs preserve narrowed values across callbacks, complete missing input
types, parse default brand authority through its field defaults, return a
cookie-capable JSON response, and restore an upload extraction statement that
was accidentally commented out by literal newline escapes.

## Deployment state

The user confirmed there is no existing host and installed Railway for this
deployment. The installation is confirmed. At this checkpoint, the active
session has not received Railway action tools, so no project, database, public
URL, or deployment has been created. Refresh the integration tools and resume;
do not ask the user to install Railway again.

Use the original Next.js 16 / Node 24 / Prisma 7 / PostgreSQL architecture.
Deploy this PR branch as an isolated preview, using its normal build command.
Configure `DATABASE_URL`, a new random `STUDIO_TRUST_SECRET` of at least 32
characters, and the deployed HTTPS `APP_ORIGIN`. Run the existing
`npm run db:deploy` migrations before serving traffic. The existing guest-pass
route can provide tester access without needing to change authentication.
Keep payment/render execution outside this Cast certification task.

## Remaining certification

All deployed browser checks are pending; source regressions are not browser
certification. Verify the public URL before handing it to the user.

Female: test all 5 dress styles and 5 colours independently, 6 skins, all 5
hairstyles and 5 hair colours, all 3 faces, all lipstick shades (especially real
Coral), all neckwear and explicit None. Save, leave/reopen, change only dress
colour, save/reopen again. Confirm style and colour never reset one another.

Male: test all 5 outfit styles and 5 top colours independently, authored
trousers/shoes, all 3 faces, 6 skins, all 5 hairstyles and 5 hair colours, all
5 watches and explicit None. Save/reopen, change only top colour, save/reopen.

Inspect fully composited browser characters: seams, transparency, hand/garment
occlusion, hair/body overlap, hair/earrings, neckwear, watches/cuffs, face/skin
changes, lip alignment, Coral, selector/preview colour correspondence, missing
images, and any fallback to fixed-colour plates. Fix proven defects, redeploy,
and retest the affected cases.

Capture at least 8 screenshots from the deployed application: female builder,
female non-default colour, clear Coral detail, second female style/colour,
male builder, male non-default colour, second male style/colour, and saved
female/male gallery after reopening. Show the screenshots directly in chat.
Do not use image generation. Do not begin motion/performance integration.
