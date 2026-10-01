/**
 * NexStudio Paper Motion — "Cast in context" reel
 *
 * A 30 second film in six beats. Each beat hands its script line to the same
 * pipeline the product uses: the scene rig is chosen for the environment, the
 * cast stage resolves who appears and which way they face. Nothing is
 * hand-placed, and the whole film is one paused, seekable timeline.
 */
window.NexCastReel = (() => {
  const DURATION = 30;
  const BEAT = 5;

  const BEATS = [
    {
      rig: 'question',
      kicker: '01 · CONTEXT',
      title: 'WHO IS HERE?',
      script: 'A presenter welcomes the audience and speaks to camera about the new system.'
    },
    {
      rig: 'feature-introduction',
      kicker: '02 · ROLE',
      title: 'CAST BY ROLE',
      script: 'The teacher explains the diagram on the board while the student listens and takes notes.'
    },
    {
      rig: 'product-demonstration',
      kicker: '03 · ATTENTION',
      title: 'EYES ON WORK',
      script: 'The analyst turns to the chart on the screen and points at the spike in the data.'
    },
    {
      rig: 'human-agent-handoff',
      kicker: '04 · RELATIONSHIP',
      title: 'EACH OTHER',
      script: 'The customer asks the support agent a question and they talk to each other.'
    },
    {
      rig: 'process',
      kicker: '05 · MOVEMENT',
      title: 'MOVEMENT',
      script: 'The field reporter walks across the site toward the crowd, then heads out of frame.'
    },
    {
      rig: 'closing-statement',
      kicker: '06 · RESULT',
      title: 'IT READS',
      script: 'The mentor turns back to the viewer and closes the story with the team beside her.'
    }
  ];

  function beatElement(beat, index, style) {
    const wrap = document.createElement('article');
    wrap.className = 'reel-beat';
    wrap.dataset.beat = String(index + 1);

    const backdrop = document.createElement('div');
    backdrop.className = 'reel-backdrop';
    const rigBox = document.createElement('div');
    rigBox.className = 'reel-rig-box';
    backdrop.append(rigBox);
    let rigTl = null;
    try {
      const rig = window.NexSceneRigs.create(beat.rig, {
        title: beat.title,
        body: beat.script,
        subtitle: beat.kicker,
        style,
        energy: 'medium',
        variant: index % 2 ? 'B' : 'A',
        duration: BEAT
      });
      rigBox.append(rig);
      rigTl = window.NexSceneRigs.animate(rig, { duration: BEAT * 0.62 });
    } catch (error) {
      rigBox.classList.add('reel-backdrop-fallback');
      rigBox.textContent = beat.title;
    }

    const stage = window.NexCastStage.create({
      script: beat.script,
      paperStyle: style,
      aspectRatio: '16:9',
      duration: BEAT,
      seed: `cast-reel:${index}`
    });

    const caption = document.createElement('p');
    caption.className = 'reel-caption';
    caption.textContent = beat.script;

    const readout = document.createElement('p');
    readout.className = 'reel-readout';
    readout.textContent = stage.__castPlan.cast
      .map((m) => `${m.role.replace(/_/g, ' ')} · ${m.pose} · ${m.view.viewAxis} → ${m.view.addressing}`)
      .join('     ');

    wrap.append(backdrop, stage, caption, readout);
    return { wrap, stage, stageTl: window.NexCastStage.animate(stage, { duration: BEAT }), rigTl };
  }

  function init(options = {}) {
    const style = options.paperStyle || 'clean-editorial';
    const root = document.querySelector('[data-composition-id="cast-reel"]');
    if (!root) throw new Error('cast-reel composition root missing');
    document.documentElement.dataset.paperStyle = style;
    const stageHost = root.querySelector('.reel-stage');
    const beats = BEATS.map((beat, index) => {
      const built = beatElement(beat, index, style);
      stageHost.append(built.wrap);
      return built;
    });

    const master = window.NexMotion.createTimeline();
    master.addUpdate(0, DURATION, (p, raw, time) => {
      beats.forEach((item, index) => {
        const start = index * BEAT;
        const local = time - start;
        const active = local >= 0 && local < BEAT;
        item.wrap.style.opacity = active ? String(Math.min(1, local / 0.4, (BEAT - local) / 0.45)) : '0';
        item.wrap.style.pointerEvents = active ? 'auto' : 'none';
        if (!active) return;
        item.stageTl.seek(Math.min(item.stageTl.duration(), local));
        if (item.rigTl) item.rigTl.seek(Math.min(item.rigTl.duration(), local));
        item.wrap.style.transform = `translateY(${Math.max(0, (0.4 - local) * 40)}px)`;
      });
      const bar = root.querySelector('.reel-progress i');
      if (bar) bar.style.width = `${(time / DURATION) * 100}%`;
    }, 'none');

    window.__timelines = window.__timelines || {};
    window.__timelines['cast-reel'] = master;
    window.seekComposition = (t) => master.seek(t);

    const params = new URLSearchParams(location.search);
    if (params.has('t')) master.seek(Number(params.get('t')));
    else if (params.get('autoplay') === '1') master.play();
    else master.seek(0);
    return master;
  }

  return { init, BEATS, DURATION, BEAT };
})();
