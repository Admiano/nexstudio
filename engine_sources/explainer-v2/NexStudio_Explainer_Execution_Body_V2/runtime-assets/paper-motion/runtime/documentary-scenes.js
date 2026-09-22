window.NexDocumentaryScenes = (() => {
  const scenes = {"company-history":{"title":"ONE ROOM. THIRTY YEARS.","kicker":"COMPANY HISTORY \u00b7 ARCHIVAL STORY","style":"clean-editorial","palette":"warm","mood":"celebratory","cards":[["chapter-divider",{"title":"CHAPTER ONE","caption":"THE ROOM WHERE IT STARTED","date":"1986"},0.72,"hero"],["archival-photograph",{"title":"The first workshop","date":"1986","location":"North Works","caption":"A rented floor, twelve people and one impossible deadline."},0.66,"wide"],["character-introduction",{"title":"Mara Okafor","role":"Founder \u00b7 Engineer \u00b7 Reluctant public speaker","caption":"She believed the clearest proof was work that survived scrutiny."},0.62,"tall"],["timeline-wall",{"title":"Thirty years in six moments","items":[{"date":"1986","text":"First workshop"},{"date":"1992","text":"National contract"},{"date":"2001","text":"Second facility"},{"date":"2016","text":"Digital rebuild"},{"date":"2024","text":"Global team"}]},0.61,"wide"],["newspaper-headline",{"title":"THE SMALL WORKSHOP THAT CHANGED THE CITY","date":"SUNDAY EDITION \u00b7 17 MAY 1992","source":"The Morning Ledger"},0.58,"small"],["historical-statistic",{"title":"31 YEARS","value":31,"suffix":" YEARS","caption":"From first workshop to global network.","source":"Company archive \u00b7 verified 2026"},0.58,"small"],["then-versus-now",{"title":"Then / Now","beforeLabel":"1986","afterLabel":"2026","caption":"One room became a distributed creative network."},0.57,"wide"],["closing-reflection",{"title":"THE WORK REMAINS.","caption":"A company is the memory of what people built together.","source":"1986\u20142026"},0.7,"hero"]]},"investigative-example":{"title":"THE RECORD DOES NOT AGREE.","kicker":"INVESTIGATIVE EXPLAINER \u00b7 VERIFIED EVIDENCE","style":"technical-notebook","palette":"charcoal","mood":"investigative","cards":[["newspaper-headline",{"title":"WHEN DID THE SHIPMENT REALLY LEAVE?","date":"FIELD REVIEW \u00b7 CASE 14-B","source":"THE PUBLIC RECORD"},0.58,"hero"],["redacted-document",{"title":"Internal field report","date":"04 NOV 2019","caption":"Sensitive names may be revealed or concealed through configuration.","redactions":true},0.6,"tall"],["highlighted-passage",{"title":"The key passage","caption":"The shipment was recorded three days before the public announcement.","highlight":"three days before"},0.62,"small"],["investigation-board",{"title":"What connects the records?","items":[{"id":"report","label":"Report 14-B"},{"id":"invoice","label":"Invoice 082"},{"id":"witness","label":"Witness call"},{"id":"route","label":"Delivery route"}],"connections":[["report","invoice"],["invoice","route"],["witness","report"]]},0.62,"wide"],["map-journey",{"title":"A journey across the city","routeLabels":["Archive","Old Market","North Works","River Ward"],"caption":"Routes and labels are supplied through configuration."},0.61,"wide"],["event-sequence",{"title":"The sequence of events","items":[{"date":"08:10","text":"Report filed"},{"date":"11:45","text":"Shipment logged"},{"date":"16:20","text":"Approval issued"},{"date":"18:05","text":"Public statement"}]},0.59,"tall"],["source-card",{"title":"Primary source","source":"North Works archive","date":"Box 12 \u00b7 Folder 4","caption":"Meeting minutes, signed 17 May 1992."},0.61,"small"],["endnote",{"title":"A note on the record","caption":"Where accounts differed, the film uses the version supported by dated documents.","source":"Editorial note \u00b7 Version 1.0"},0.66,"hero"]]},"personal-memory":{"title":"THE HOUSE REMEMBERS.","kicker":"PERSONAL MEMORY \u00b7 WARM SCRAPBOOK","style":"handmade-scrapbook","palette":"warm","mood":"warm","cards":[["chapter-divider",{"title":"SUNDAY","caption":"A FAMILY STORY IN SMALL OBJECTS","date":"1998"},0.65,"hero"],["memory-montage",{"title":"Small moments, kept","caption":"The birthdays, bus rides and Sunday afternoons between the milestones."},0.58,"wide"],["character-introduction",{"title":"Aunty Bisi","role":"Keeper of the photographs","caption":"She wrote every date on the back so nobody would forget.","media":"assets/media/documentary/founder-portrait.svg"},0.58,"tall"],["object-close-up",{"title":"The radio in the corner","date":"1998","caption":"It played every Sunday while the family prepared lunch."},0.6,"small"],["handwritten-note",{"title":"Remember this part","date":"UNDATED","caption":"The room was loud, the tea was cold, and nobody wanted to leave."},0.61,"small"],["audio-transcript-card",{"title":"ARCHIVE AUDIO \u00b7 00:42","speaker":"MARA","caption":"The doors opened before sunrise. By eight, every table was full.","items":["00:42 The doors opened before sunrise.","00:47 By eight, every table was full.","00:53 Nobody complained about the noise."]},0.57,"wide"],["photo-collage",{"title":"The people behind the work","caption":"Replace every image without changing the collage animation."},0.57,"wide"],["closing-reflection",{"title":"KEEP THE SMALL THINGS.","caption":"They are often where the whole story is hiding.","source":"FAMILY ARCHIVE"},0.66,"hero"]]}};

  function mount(host, slug, cfg, scale, kind) {
    const wrap = document.createElement('div');
    wrap.className = 'dms-card ' + kind;
    wrap.style.setProperty('--scene-scale', scale);
    const el = NexDocumentaryModules.create('module.documentary.' + slug + '.paper-01', cfg);
    wrap.append(el);
    host.append(wrap);
    const tl = NexDocumentaryModules.animate(el, { duration: 2.4, energy: 'medium' });
    return { wrap, el, tl };
  }

  function init(name) {
    const cfg = scenes[name];
    const root = document.querySelector('[data-composition-id]');
    const host = root.querySelector('.dms-board');
    NexTheme.applyPalette(cfg.palette);
    NexTheme.setStyle(cfg.style);
    const cards = cfg.cards.map((x) => mount(host, x[0], { ...x[1], style: cfg.style, mood: cfg.mood }, x[2], x[3]));
    const master = NexMotion.createTimeline({ defaults: { ease: 'power3.out' } });
    cards.forEach((card, index) => {
      const time = 0.25 + index * 3.45;
      master.fromTo(card.wrap,
        { x: index % 2 ? -110 : 110, y: 55, rotation: index % 2 ? -5 : 5, opacity: 0, scale: 0.86 },
        { x: 0, y: 0, rotation: (index % 3 - 1) * 0.5, opacity: 1, scale: 1, duration: 0.8, ease: 'back.out(1.45)' },
        time
      );
      if (index > 0) {
        master.fromTo(cards[index - 1].wrap, { scale: 1 }, { scale: 0.94, duration: 0.75, ease: 'power2.out' }, time);
      }
      master.fromTo(card.wrap, { y: 0 }, { y: -4 - (index % 2) * 2, duration: 0.92, ease: 'sine.inOut', repeat: 5, yoyo: true }, time + 1.15);
    });
    const baseSeek = master.seek.bind(master);
    master.seek = (time) => {
      baseSeek(time);
      cards.forEach((card, index) => card.tl.seek(Math.max(0, Math.min(card.tl.duration(), time - (0.2 + index * 3.45)))));
      return master;
    };
    master.duration(30);
    window.__timelines = window.__timelines || {};
    window.__timelines[name] = master;
    window.seekComposition = (time) => master.seek(time);
    master.seek(0);
    return master;
  }

  return { init, scenes };
})();
