# NexStudio Universal Paper Icon API

Batch 4 adds 40 reusable universal action icons. The source of truth is `components/universal-icons.js`; individual editable SVG exports live in `assets/icons/universal/`.

## Create an icon

```html
<div id="mount"></div>
<script>
  const icon = NexIcons.create("upload", {
    size: 96,
    treatment: "paper-cutout",
    state: "active"
  });
  document.querySelector("#mount").appendChild(icon);
</script>
```

`create()` accepts either a slug such as `upload`, a full component ID such as `icon.universal.upload.paper-01`, or a manifest object.

## Animate it

```js
const timeline = NexIcons.animate(icon, {
  motion: "cut-paper-pop",
  duration: 1.2,
  energy: "medium"
});

timeline.restart();
timeline.seek(0.6);
timeline.progress(0.5);
```

The entrance comes from the Batch 3 motion engine. Icons marked `bespokeInternalMotion: true` also animate their semantic SVG parts.

## Change state without editing SVG

```js
NexIcons.setState(icon, "inactive");
NexIcons.setState(icon, "active");
NexIcons.setState(icon, "completed");
```

Unsupported states fall back to the icon's first valid state. State support is documented in each manifest.

## Change treatment or size

```js
NexIcons.setTreatment(icon, "printed-outline");
NexIcons.setSize(icon, 180);
```

Supported treatments:

- `paper-cutout`
- `printed-outline`

Supported production range: 24–420px. The component automatically simplifies edge texture at small UI sizes.

## Replace configuration

```js
const replacement = NexIcons.update(icon, {
  size: 42,
  treatment: "paper-cutout",
  state: "active"
});
```

## Theme tokens

Icons inherit the approved library tokens:

```css
--paper-surface
--paper-surface-alt
--ink
--ink-muted
--primary
--secondary
--accent
--highlight
--shadow-color
--shadow-opacity
--grain-opacity
--outline-width
```

Use `NexTheme.applyPalette()` or set the tokens directly. No SVG path editing is required.

## Agent selection

Read `runtime/icon-registry.js`, `manifests/icons/*.json`, or the combined `manifests/index.json`. Every manifest contains:

- intents and keywords
- accessible label
- compatible motion presets
- supported states and treatments
- duration limits
- sound tags
- paper styles and aspect ratios
