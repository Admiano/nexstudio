# Cast V12 mouth and ear refinement

V12 replaces the simplified 160-vertex upper tooth mesh and painted speaking aperture with fitted source anatomy on both approved characters. It retains the V10 complexion/makeup treatment and V11 fibre grooms.

## Mouth construction

The original `Guest.teeth_base` contains 32 distinct tooth crowns and gingiva. Its upper/lower arches are fitted independently against corresponding semantic helper vertices in the assembled body, including its selected anatomical morphs. The fitted upper arch uses the original head bone, the lower arch the original jaw. The tongue is extracted from the original body helper topology and retains the original tongue/facial weights. It receives a shallow median groove, fine papillary relief and a soft wet finish.

Enamel uses a natural ivory physical material with bounded oral contact shading, a restrained gloss and fine surface relief. Gums, tongue and internal mouth lining have separate physical materials. The former tooth bar and vertex-parented painted mouth interior stay hidden. Inner mouth tissue is independently coloured without recolouring the outside face or selected lipstick. New oral meshes are excluded from the original head ink collection; marked internal tissue is excluded from the head outline/crease passes. Existing eye, nose and facial artwork remains.

The original facial jaw shape opens farther than the old dental jaw movement. Additional local oral shape keys follow that existing jaw control: upper dental exposure is bounded at 4 mm, lower dental correction at 30 mm times the jaw value, and tongue correction at 20 mm times the jaw value. A bounded 12 mm recess follows lip closure. A closed-lip visibility guard removes subpixel enamel glints only when jaw opening and both lip lifts are small; it preserves FV tooth exposure. The separate `FACE_FINE` Freestyle pass is disabled because it contains only the obsolete painted mouth aperture. A remaining dark crescent below the female lower lip was traced by camera rays to the new lower gingiva protruding through the chin. A separate rest-basis corrective key recesses gum tissue by 2–10 mm, increasing toward its base, while leaving tooth crowns unchanged. A fresh speaking render confirms that the exposed crescent is gone. These are fitted articulation corrections, not a new phoneme action, narration track or performance rig.

All new shape keys explicitly use the unmixed rest basis. In particular, the ear corrective key cannot capture a speaking pose. The audit checks that every non-ear vertex has exactly zero displacement in that key.

## Ear and temple hair

The male's old bone-parented V10 ear ink no longer follows the fitted ear accurately and is hidden. A small symmetrical corrective key reduces protrusion by up to 12% and height by up to 7%, fading toward the attachment. The original ear cage and every original shape key remain unchanged; only the new ear key supplies this adjustment. Female ears and fitted earrings retain their existing construction.

The quiff's long lower temple strips are masked below the ear's middle region, and any groom curve entering that unwanted front/lateral extension has zero radius. The production default masks 48 carrier vertices and removes 1,491 curves from visibility. Hair behind the head and the deliberately long/swept/braided styles retain their intended length. The V11 fibre module itself is unchanged.

## Verification and limits

`v12-facial.audit.json` records both character audits over frames 1, 27, 71, 106, 160, 260, 360, 500, 650, 820 and 998. Sampled oral positions match the original head/jaw/tongue deformation to within 0.5 µm. The audit also rejects any oral-mucosa polygon touching a semantic lip vertex. Original mesh cages, original shape-key coordinates, original weights, UVs and bones remain intact. Added temple mask weights and the ear corrective key are explicitly authorized changes. Reapplying the treatment adds no additional geometry or materials.

Actual source renders cover closed, open and rounded speaking poses, mouth/ear before-and-after closeups and full character portraits. Render metadata, image hashes and fresh production assembly metadata are recorded in `v12-render-verification.json`. The focused worker tests and complexion/lip/custom-colour configuration checks pass. The original 129 source assets remain byte-identical.

The renderer and customizer share `approved-v3-v6-face-v12-upper-thigh`. The worker forces `CAST_FACIAL_REFINEMENT=1` server-side. Reference tooling can use `--no-facial` to reproduce V11 hair and V10 skin without this mouth/ear treatment. `render-facial-detail.py` creates actual camera-matched source closeups. No image generation is used.

No full application build was run in this restored source-render workspace. This remains a draft source upgrade, not a merged or deployed app change. The original illustrated face shapes and performance are retained; this does not claim a new photoreal face, speech performance, dental simulation or tongue motion library.
