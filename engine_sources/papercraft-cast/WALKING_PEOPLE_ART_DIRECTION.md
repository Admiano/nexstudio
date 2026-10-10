# Walking People Pack — NexStudio paper-character construction authority (R&D)

Source branch: `devin/1791589734-walking-people-pack`
Source: `assets/walking-people-pack/WalkingPeoplepack2024.fbx`
Source SHA-256, verified by GitHub Actions: `887b4b52c6fecc52ba32ebbf6cdc36847f017ec11e9b1f0c028f2fce8909e2ec`
Seller: gihatasarim (CGTrader #6025432), Royalty Free (No AI).

## Actual imported Blender 5.2 asset structure

- woman1 — 152047 vertices; 304116 polygons
- man1 — 147266 vertices; 294533 polygons
- woman2 — 141721 vertices; 283443 polygons
- woman3 — 146924 vertices; 293874 polygons
- woman4 — 194097 vertices; 388487 polygons
- Plane001 — separate floor, 25 verts/16 faces (must hide)
- Zero Blender armature objects — **static walking-pose figures**, no certified face shapes or skinned skeletons.
- Five available JPEG atlases, named gihapeopletex1.jpg … gihapeopletex5.jpg.
- FBX links its atlases to missing texture_0.png file references. Temporary renderer relinks atlases by import order; visual audit of exact assignments mandatory.

## Rendering evidence

- Full Blender source + paper preview run (successful, untextured first pass):
  https://github.com/Admiano/nexstudio/actions/runs/38008445296
- Actual individually framed geometry preview, woman1/man1:
  https://github.com/Admiano/nexstudio/actions/runs/38008929843
- Close-up textured proof run:
  https://github.com/Admiano/nexstudio/actions/runs/38008955478

All CI artifacts contain rendered PNGs and JSON only. No licensed raw assets should be re-exported publicly.

## Product decision

Use this pack as anatomical, hairstyling, clothing and silhouette references. These detailed *posed* 3D scans cannot directly replace the existing certified V19/illustrated speaking performer: there is no skeleton, no neutral rest pose, no facial shape keys or mouth shapes. Retopologize a single chosen source figure into an optimized author-controlled neutral pose and bind it to an isolated duplicate of the certified NexStudio performer rig. Preserve the scan as a hidden guide, never ship the original high-poly body as a user-downloadable asset.

For paper visual art, design real sheet components instead of procedural uniform triangulation: forehead/temples, eyelid brow architecture, eye shells, nose bridge and cheeks, jaw/lip folds, hair sheets rooted in scalp, clothing panels and garment overlaps, hand plates/finger folds. Use modest physical sheet thickness and deliberate crease paths. Facial identity and reference quality must pass front, three-quarter and profile renders before animation work.

## No false certifications

The current script's decimation + matte paper + Solidify output is a **technical feasibility experiment**. It is not physically unfoldable, not hero-quality stylized paper, and not rig/viseme certified. No change has been made to production cast authorities.

## License gate

CGTrader item is marked Royalty Free (No AI); no machine-learning training use. Check terms for model derivative workflows, since the underlying FBX and texture files must not be redistributed independently. Current source pack is in a public repo, requiring a rights/privacy review before production. Maintain vendor attribution.