MiMo V2.6 Flash reviewer routing
==============================

The user selected `xiaomi/mimo-v2.6-flash` through Vercel AI Gateway to replace
all Inkling review roles: the eight department Executive Producer tasks, the
Independent Final Executive Producer, and the Independent Perceptual Auditor.
Directors, factual source analysis, preview and Supreme Showrunner selection
retain their configured routes.

Keep the Gateway credential in local `.env` as `VERCEL_AI_GATEWAY_API_KEY`.
The profile is `mimo-reviewers.json`; model identities belong to operator
configuration, not hard-coded provider fallbacks.

Run `node scripts/configure-mimo-reviewers.cjs --check` to inspect the proposed
configuration without model calls or `.env` changes. Run with `--apply` to check
the authenticated catalog and use P8's live provider for synthetic conformance.
The department probe must reject an unbound waterline supporting role and the
unavailable TRACE_FLOW verb using the actual department-review schema. Each
final role independently inspects a generated color image and offline speech,
then returns its own schema-valid synthesis. Expected speech is not included in
the audio prompt. Only successful conformance permits local activation; a
concurrent `.env` edit aborts activation.

Final roles advertise images and native audio. Vercel Chat Completions requires
the `file`/`file_data` data-URL payload (`chat_file_audio`), rather than
`input_audio`. P8 already implements that transport. Separate inspections and
synthesis retain their evidence hashes and uncertainty; they do not establish
simultaneous audiovisual perception. Both roles remain independent calls with
blind auditor context and existing production gates.

Activation clears the old runtime boot attestation. Refresh it with
`node scripts/run-nexmind-runtime-boot-probe.cjs reports/vercel-mimo-reviewers/boot-attestation.json`.
This also probes the unchanged Story, Visual and Art routes. Studio requires a
successful attestation bound to the current build/configuration and no older
than 15 minutes. Restart a running app process to load changed environment
variables. Local activation does not change deployment environment variables.

Evidence: `reports/vercel-mimo-reviewers/activation.json`, `conformance.json`,
and `boot-attestation.json`. Synthetic verdicts are not production verdicts.
This model change does not repair the unresolved P8 Art-to-renderer binding
problem described in `HANDOVER_ENCLAVE_P8.md`.

Official references:
- https://vercel.com/ai-gateway/models/mimo-v2.6-flash
- https://vercel.com/docs/ai-gateway/inputs-and-tools/audio-input
