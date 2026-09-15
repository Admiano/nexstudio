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

  /**
   * The kinetic component animates one letter per inline-block span, which
   * lets a line wrap mid-word. Letters are regrouped per word so a word breaks
   * only between words, and the fitter shrinks the type instead.
   */
  function keepWordsWhole(node) {
    node.querySelectorAll('.kinetic-letters').forEach((line) => {
      const letters = [...line.children];
      if (!letters.length) return;
      const text = line.textContent;
      let index = 0;
      const frag = document.createDocumentFragment();
      let word = null;
      for (const ch of text) {
        if (ch === ' ') {
          word = null;
          frag.appendChild(document.createTextNode(' '));
          continue;
        }
        if (!word) {
          word = document.createElement('span');
          word.className = 'ed-word';
          frag.appendChild(word);
        }
        word.appendChild(letters[index] || document.createTextNode(ch));
        index += 1;
      }
      line.innerHTML = '';
      line.appendChild(frag);
    });
    return node;
  }

  const RULES = () => window.NEX_EDITORIAL_RULES || {};

  /**
   * The vendored fitter shrinks type until the card fits, which can take
   * supporting copy down to a size nobody reads. Below that floor the copy
   * holds its size and sheds its own trailing words instead, so what is on
   * screen is always legible and always the script's words.
   */
  function enforceReadableCopy(scene, frameHeight) {
    const rules = RULES().typography || {};
    const floors = [
      ['.type-body', rules.minBodyHeightRatio],
      ['.type-meta', rules.minMetaHeightRatio]
    ];
    const paper = scene.querySelector('.type-paper');
    const content = scene.querySelector('.type-content') || paper;
    if (!paper || !content) return;
    const overflows = () =>
      content.scrollHeight > paper.clientHeight - 42 ||
      content.scrollWidth > paper.clientWidth - 38;

    floors.forEach(([selector, ratio]) => {
      if (!ratio) return;
      const min = frameHeight * ratio;
      scene.querySelectorAll('.ed-type ' + selector).forEach((node) => {
        if (!node.textContent.trim()) return;
        if ((parseFloat(getComputedStyle(node).fontSize) || 0) >= min) return;
        node.style.fontSize = min + 'px';
        node.style.lineHeight = '1.18';
        node.style.letterSpacing = 'normal';
        const words = node.textContent.trim().split(/\s+/);
        let guard = 0;
        while (words.length > 1 && overflows() && guard < 400) {
          words.pop();
          node.textContent = words.join(' ') + '…';
          guard += 1;
        }
        if (words.length <= 1 && overflows()) markEmpty(node);
      });
    });
  }

  function markEmpty(node) {
    node.textContent = '';
    node.classList.add('ed-empty');
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
    // An upload that will not load is dropped rather than shown as a broken
    // frame: the file name is not the script's copy and never reaches screen.
    node.querySelectorAll('img, video').forEach((el) => {
      el.removeAttribute('alt');
      el.addEventListener('error', () => { wrap.classList.add('ed-empty'); }, { once: true });
    });
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
      keepWordsWhole(typeNode);
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
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const frameHeight = host.getBoundingClientRect().height;
    if (frameHeight) shots.forEach(({ scene }) => enforceReadableCopy(scene, frameHeight));
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
    const crossfade = Number(options.crossfade ?? (RULES().shots || {}).crossfade ?? 0.28);

    shots.forEach((built, i) => {
      const { shot, scene } = built;
      const start = shot.start;
      const end = shot.start + shot.duration;
      tl.set(scene, { opacity: 0, pointerEvents: 'none' }, 0);
      tl.set(scene, { opacity: 1 }, start);
      // The outgoing shot holds under the incoming one while its type arrives,
      // so the boundary itself never lands on an empty frame. The last shot
      // holds to the end.
      if (i < shots.length - 1) {
        const overlap = Math.min(crossfade, shots[i + 1].shot.duration * 0.4);
        tl.to(scene, { opacity: 0, duration: overlap, ease: 'none' }, end);
      }

      const typeTl = window.NexTypography.animate(built.typeNode, {
        duration: Math.min(1.6, shot.duration * 0.55),
        energy: built.typeNode.dataset.energy,
        // The card itself is present from the first frame of its shot; only its
        // words animate in.
        visibleStart: true
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
        // A still: the figure fades up once and holds. Opacity only — no
        // transform, no loop, no idle.
        tl.fromTo(built.character, { opacity: 0 }, { opacity: 1, duration: hold, ease: 'power1.out' }, start);
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
