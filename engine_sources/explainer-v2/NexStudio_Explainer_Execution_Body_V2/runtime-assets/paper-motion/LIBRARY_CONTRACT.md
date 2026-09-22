# NexStudio Paper Motion Library Contract

1. Editable HTML, CSS, SVG and JavaScript are the source of truth.
2. Every item has a stable ID, configuration API and JSON manifest.
3. Artwork, animation and sound remain separate.
4. Theme changes occur through design tokens; ordinary use never requires editing SVG paths.
5. Components adapt to 16:9, 1:1 and 9:16 compositions.
6. Timelines are paused, registered under `window.__timelines`, deterministic and seekable.
7. No component is accepted if it exists only inside the explorer or a rendered preview.
8. Batches extend the project and must not break approved previous components.
9. A manifest inventory test must match the runtime registry count.
10. Audio is optional and selected by semantic tags, never permanently embedded.
