# Creator Module API

```js
const module = NexCreatorModules.create("module.creator.social-post.paper-01", {
  title: "Maya Cole", handle: "@mayamakes", caption: "Replaceable copy",
  media: "assets/media/website-screenshot.svg", contentLength: "medium",
  style: "clean-editorial", energy: "medium"
});
mount.append(module);
NexCreatorModules.animate(module, { duration: 1.8, motion: "paper-slide" }).restart();
```

Public methods: `create`, `animate`, `update`, `fitText`, `getDef`. Modules are platform-neutral and never contain baked-in third-party logos. `logoSrc` accepts only user-authorized brand artwork.
