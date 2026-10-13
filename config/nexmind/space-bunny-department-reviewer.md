The user-selected Space Bunny profile applies to all eight department reviewers,
including Art. Creative directors, Showrunner selections, final Producer and
perceptual auditor keep their own configured routes. Space Bunny's published
modalities do not include native audio, so this profile does not claim audio
review capability.

`node scripts/configure-space-bunny-reviewer.cjs --check` shows the planned route
without modifying `.env`. After adding `OPENROUTER_API_KEY` locally, `--apply`
performs one synthetic text/image inference against the exact model and checks
plain JSON output, image perception, and rejection of unsupported execution.
Only a passing probe updates department routes and clears the old boot
attestation. Refresh the real runtime boot attestation and restart the app/worker
after successful activation. A passing synthetic test is transport/conformance
evidence, not proof of production review quality.

On 2026-10-05, the authenticated model catalog returned HTTP 200 but listed no
Space Bunny entry or variant. Inference against `stealth/space-bunny-alpha`
returned HTTP 404: `No endpoints found for stealth/space-bunny-alpha.`
Activation was blocked and `.env` routing was not changed. The supplied key was
not printed or copied into reports. Probe evidence is saved in
`reports/openrouter-space-bunny-reviewer/activation.json`.

Sources: https://openrouter.ai/stealth/space-bunny-alpha and the exact live
OpenRouter `/api/v1/models` and `/api/v1/chat/completions` checks. The model page
alone does not establish that an inference endpoint is currently routable.
