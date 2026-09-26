/**
 * NexStudio Paper Motion — cast stage component
 *
 * Wraps the paper cast in the paperbook component contract: `create` returns a
 * configured DOM element, `animate` returns a paused, seekable timeline, and
 * nothing about the artwork lives only inside an explorer.
 *
 *   const stage = NexCastStage.create({ script: 'The teacher explains the chart.' });
 *   mount.append(stage);
 *   const tl = NexCastStage.animate(stage, { duration: 5 });
 */
window.NexCastStage = (() => {
  const COMPONENT_ID = 'component.cast-stage.paper-01';
  const q = (t) => (typeof t === 'string' ? document.querySelector(t) : t);
  const defaults = {
    script: 'A presenter welcomes the audience.',
    aspectRatio: '16:9',
    paperStyle: 'clean-editorial',
    duration: 5,
    seed: 'cast-stage',
    hints: null
  };

  function cast() {
    if (!window.NexPaperCast) throw new Error('paper-cast runtime is not loaded');
    return window.NexPaperCast;
  }

  function request(config, time) {
    return {
      script: config.script,
      aspectRatio: config.aspectRatio,
      paperStyle: config.paperStyle,
      seed: config.seed,
      duration: config.duration,
      hints: config.hints || undefined,
      time
    };
  }

  function draw(el, time) {
    const config = el.__castConfig;
    const scene = cast().renderScene(request(config, time));
    el.querySelector('.cs-frame').innerHTML = scene.svg;
    el.dataset.castSize = String(scene.cast.length);
    el.__castPlan = scene;
    return scene;
  }

  function create(config = {}) {
    const c = { ...defaults, ...config };
    const el = document.createElement('section');
    el.className = 'nex-cast-stage';
    el.dataset.componentId = COMPONENT_ID;
    el.dataset.style = c.paperStyle;
    el.dataset.ratio = c.aspectRatio;
    el.setAttribute('role', 'group');
    el.setAttribute('aria-label', 'Contextual paper cast stage');
    el.innerHTML = '<div class="cs-frame"></div>';
    el.__castConfig = c;
    draw(el, 0);
    el.setAttribute('aria-label', el.__castPlan.cast.map((m) => `${m.role} ${m.pose} facing ${m.view.viewAxis}`).join(', ') || 'Empty stage');
    return el;
  }

  /** Paused, seekable and registered the same way every paper-motion timeline is. */
  function animate(target, config = {}) {
    const el = q(target);
    if (!el) throw new Error('Cast stage target missing');
    const duration = Number(config.duration || el.__castConfig.duration || 5);
    el.__castConfig.duration = duration;
    const tl = window.NexMotion.createTimeline();
    tl.addUpdate(0, duration, (p, raw, t) => draw(el, typeof t === 'number' ? t : p * duration), 'none');
    tl.seek(0);
    el.__timeline = tl;
    return tl;
  }

  function update(target, config = {}) {
    const el = q(target);
    el.__castConfig = { ...el.__castConfig, ...config };
    draw(el, 0);
    return el;
  }

  const plan = (config = {}) => cast().plan(request({ ...defaults, ...config }));

  return { COMPONENT_ID, create, animate, update, draw, plan };
})();
