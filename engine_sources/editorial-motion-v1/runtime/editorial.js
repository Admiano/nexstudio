/**
 * NexStudio Editorial Motion — browser runtime
 *
 * Turns a director plan into DOM inside a ratio-native frame and builds one
 * paused, seekable master timeline over it. Type and icons animate; uploaded
 * media animates only as a frame; the Open Peeps figure is cut in and held
 * still, then cut out. Nothing about the figure moves while it is on screen.
 */
window.NexEditorial = (() => {
  const ASSET_BASE = 'assets/peeps/';
  const cache = new Map();

  const el = (tag, className, parent) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (parent) parent.appendChild(node);
    return node;
  };

  async function loadPart(file, base) {
    const url = (base || ASSET_BASE) + file;
    if (!cache.has(url)) {
      cache.set(url, fetch(url).then((r) => {
        if (!r.ok) throw new Error('Missing peeps part: ' + url);
        return r.text();
      }));
    }
    return cache.get(url);
  }

  async function figureSvg(character, base) {
    const files = window.NexPeeps.partFiles(character);
    const texts = await Promise.all(files.map((f) => loadPart(f, base)));
    const map = new Map(files.map((f, i) => [f, texts[i]]));
    return window.NexPeeps.compose(character, (file) => map.get(file)).svg;
  }

  /**
   * The vendored components fill empty slots with their own sample copy. The
   * editorial system only ever shows the script's words, so any slot we did not
   * fill is removed rather than left to a placeholder.
   */
  function pruneSlots(node, content = {}) {
    node.querySelectorAll('[data-slot]').forEach((slot) => {
      const key = slot.dataset.slot;
      const value = content[key];
      const filled = Array.isArray(value) ? value.length : String(value ?? '').trim().length;
      if (filled) return;
      // Emptied rather than removed: the vendored animators still address these
      // nodes, they just have nothing to say.
      slot.textContent = '';
      slot.classList.add('ed-empty');
    });
    // Words baked into the component itself ('DEFINITION', a sample URL) are
    // copy the script never wrote, so anything whose letters are absent from
    // the shot's own content is silenced. Numerals and rules are structure, not
    // copy, and stay.
    const corpus = Object.values(content)
      .flat()
      .map((v) => String(v ?? '').toLowerCase())
      .join(' ');
    node.querySelectorAll('*').forEach((el) => {
      if (el.children.length || el.classList.contains('ed-empty')) return;
      const text = (el.textContent || '').trim();
      if (!text || !/[a-z]/i.test(text)) return;
      if (corpus.includes(text.toLowerCase())) return;
      el.textContent = '';
      el.classList.add('ed-empty');
    });
    return node;
  }

  function placeRegion(node, region) {
    node.style.left = (region.x * 100) + '%';
    node.style.top = (region.y * 100) + '%';
    node.style.width = (region.w * 100) + '%';
    node.style.height = (region.h * 100) + '%';
  }

  function buildIcons(region, icons, style) {
    const wrap = el('div', 'ed-icons ed-layer');
    wrap.dataset.flow = region.flow || 'row';
    placeRegion(wrap, region);
    icons.forEach((icon) => {
      const node = window.NexIcons.create(icon.slug, { style, size: 120, label: '' });
      node.classList.add('ed-icon');
      wrap.appendChild(node);
    });
    return wrap;
  }

  function buildMedia(region, media, style) {
    const wrap = el('div', 'ed-media ed-layer');
    placeRegion(wrap, region);
    const content = { title: media.source.caption || '', body: '', meta: '' };
    const node = window.NexMediaContainers.create(media.slug, {
      media: [{ type: media.type, src: media.source.src || media.source.name, alt: media.source.caption || media.source.name || '' }],
      ...content,
      style
    });
    pruneSlots(node, content);
    node.classList.add('ed-media-node');
    wrap.appendChild(node);
    return wrap;
  }

  async function buildCharacter(region, character, base) {
    const wrap = el('div', 'ed-character ed-layer');
    wrap.dataset.anchor = region.anchor || 'bottom';
    wrap.dataset.framing = character.framing;
    placeRegion(wrap, region);
    wrap.innerHTML = await figureSvg(character, base);
    return wrap;
  }

  /**
   * @param {Element|string} target host element
   * @param {object} plan a director plan
   * @param {object} options assetBase, style
   */
  async function create(target, plan, options = {}) {
    const host = typeof target === 'string' ? document.querySelector(target) : target;
    if (!host) throw new Error('Editorial host missing');
    const style = options.style || 'clean-editorial';
    host.innerHTML = '';
    host.className = 'ed-frame ' + (host.className || '').replace(/\bed-frame\b/g, '').trim();
    host.dataset.ratio = plan.ratio;
    host.dataset.paperStyle = style;
    host.setAttribute('data-paper-style', style);

    const shots = [];
    for (const shot of plan.shots) {
      const scene = el('section', 'ed-shot', host);
      scene.dataset.shot = String(shot.index);
      scene.dataset.role = shot.role;
      scene.setAttribute('aria-label', shot.text);

      const textRegion = shot.layout.byId.text;
      const typeWrap = el('div', 'ed-type ed-layer', scene);
      placeRegion(typeWrap, textRegion);
      const typeNode = window.NexTypography.create(shot.typography.slug, {
        ...shot.typography.content,
        style,
        alignment: plan.ratio === '16:9' ? 'left' : 'center',
        energy: shot.emphasis > 0.66 ? 'high' : shot.emphasis > 0.33 ? 'medium' : 'low'
      });
      pruneSlots(typeNode, shot.typography.content);
      typeWrap.appendChild(typeNode);

      const built = { shot, scene, typeNode, icons: null, media: null, character: null };
      if (shot.icons.length && shot.layout.byId.icons) {
        built.icons = buildIcons(shot.layout.byId.icons, shot.icons, style);
        scene.appendChild(built.icons);
      }
      if (shot.media && shot.layout.byId.media) {
        built.media = buildMedia(shot.layout.byId.media, shot.media, style);
        scene.appendChild(built.media);
      }
      if (shot.character && shot.layout.byId.character) {
        built.character = await buildCharacter(shot.layout.byId.character, shot.character, options.assetBase);
        scene.appendChild(built.character);
      }
      shots.push(built);
    }
    host.__editorialPlan = plan;
    host.__editorialShots = shots;
    return host;
  }

  /**
   * Build the master timeline. Paused and seekable: the same time always gives
   * the same frame, which is what the capture tool and the explorer rely on.
   */
  function animate(target, options = {}) {
    const host = typeof target === 'string' ? document.querySelector(target) : target;
    const plan = host.__editorialPlan;
    const shots = host.__editorialShots || [];
    if (!plan) throw new Error('Call NexEditorial.create() before animate()');
    const tl = window.NexMotion.createTimeline({ defaults: { ease: 'power3.out' } });
    const hold = Number(options.hold ?? 0.35);

    shots.forEach((built) => {
      const { shot, scene } = built;
      const start = shot.start;
      const end = shot.start + shot.duration;
      tl.set(scene, { opacity: 0, pointerEvents: 'none' }, 0);
      tl.set(scene, { opacity: 1 }, start);
      tl.set(scene, { opacity: 0 }, Math.max(start, end - 0.01));

      const typeTl = window.NexTypography.animate(built.typeNode, {
        duration: Math.min(1.6, shot.duration * 0.55),
        energy: built.typeNode.dataset.energy
      });
      tl.addUpdate(start, Math.min(1.6, shot.duration * 0.55), (p) => typeTl.progress(p));

      if (built.icons) {
        [...built.icons.children].forEach((node, i) => {
          tl.fromTo(node, { opacity: 0, scale: 0.7, y: 18 },
            { opacity: 1, scale: 1, y: 0, duration: 0.42 }, start + hold + i * 0.14);
        });
      }
      if (built.media) {
        tl.fromTo(built.media, { opacity: 0, scale: 0.94, rotation: -1.2 },
          { opacity: 1, scale: 1, rotation: 0, duration: 0.6, ease: 'back.out(1.4)' }, start + hold * 0.6);
      }
      if (built.character) {
        // A still: the figure is cut into the frame and held. No transform, no
        // loop, no idle — only presence.
        tl.set(built.character, { opacity: 0 }, start);
        tl.set(built.character, { opacity: 1 }, start + hold);
      }
    });

    tl.addUpdate(plan.duration, 0, () => {});
    host.__editorialTimeline = tl;
    return tl;
  }

  async function render(target, script, options = {}) {
    const plan = window.NexEditorialDirector.direct(script, {
      ...options,
      registries: {
        typography: window.NEX_TYPOGRAPHY,
        icons: window.NEX_ICONS,
        media: window.NEX_MEDIA_CONTAINERS
      }
    });
    await create(target, plan, options);
    return { plan, timeline: animate(target, options) };
  }

  return { create, animate, render, figureSvg, loadPart };
})();
