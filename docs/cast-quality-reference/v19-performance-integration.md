# Original native performance restored

The V19 integration is withdrawn at the user's request. The active native scenes now use the original pre-upgrade `Host.rigAction.001` and `baseAction` preserved in the approved source files. The V18 diagnostic action copies and V19 reduced gesture bake do not control the restored characters. The complete original 998-frame timeline, all gesture variations and original facial performance are preserved without retiming.

The current visual refinements remain: character mesh and shape geometry, UVs, materials, hair, garments and centered watch construction. A geometry/shape/UV/material identity digest matches the current pre-rollback scenes. Exact hashes of every original rig/face animation curve, key, interpolation and handle match after saving each restored front and fixed left three-quarter scene.

The assembled renderer is restored byte-for-byte to its pre-V19 version. The V19 exporter, director, adapter and runtime hook are removed from this branch, preventing them from replacing the original actions again. The withdrawn implementation remains in Git history for reference. PR 63 is closed; no production deployment is claimed.

Preview images use the original saved actions at their actual gesture frames, with fresh garment fitting and fixed cameras. No audio is added or retimed. The old V19 conversation and clips are historical review artifacts and are not the active performance authority.
