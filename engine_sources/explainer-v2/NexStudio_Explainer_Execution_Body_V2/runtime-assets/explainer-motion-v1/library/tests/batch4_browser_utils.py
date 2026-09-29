from pathlib import Path

def inline_file(html: str, old: str, path: Path, tag='style') -> str:
    content=path.read_text()
    return html.replace(old,f'<{tag}>{content}</{tag}>')

def bundled_icon_explorer(root: Path) -> str:
    html=(root/'icon-explorer.html').read_text()
    reps=[
      ('<link rel="stylesheet" href="styles/tokens.css">',root/'styles/tokens.css','style'),
      ('<link rel="stylesheet" href="styles/paper.css">',root/'styles/paper.css','style'),
      ('<link rel="stylesheet" href="styles/motion.css">',root/'styles/motion.css','style'),
      ('<link rel="stylesheet" href="styles/icons.css">',root/'styles/icons.css','style'),
      ('<link rel="stylesheet" href="styles/icon-explorer.css">',root/'styles/icon-explorer.css','style'),
      ('<script src="vendor/gsap-compat.js"></script>',root/'vendor/gsap-compat.js','script'),
      ('<script src="runtime/theme.js"></script>',root/'runtime/theme.js','script'),
      ('<script src="runtime/motion-registry.js"></script>',root/'runtime/motion-registry.js','script'),
      ('<script src="runtime/motion-engine.js"></script>',root/'runtime/motion-engine.js','script'),
      ('<script src="runtime/icon-registry.js"></script>',root/'runtime/icon-registry.js','script'),
      ('<script src="components/universal-icons.js"></script>',root/'components/universal-icons.js','script'),
      ('<script src="runtime/icon-explorer.js"></script>',root/'runtime/icon-explorer.js','script'),
    ]
    for old,p,tag in reps: html=inline_file(html,old,p,tag)
    return html

def bundled_aspect_demo(root: Path, ratio: str) -> str:
    html=(root/f'compositions/universal-icons-{ratio}.html').read_text()
    reps=[
      ('<link rel="stylesheet" href="../styles/tokens.css">',root/'styles/tokens.css','style'),
      ('<link rel="stylesheet" href="../styles/paper.css">',root/'styles/paper.css','style'),
      ('<link rel="stylesheet" href="../styles/motion.css">',root/'styles/motion.css','style'),
      ('<link rel="stylesheet" href="../styles/icons.css">',root/'styles/icons.css','style'),
      ('<link rel="stylesheet" href="../styles/icon-composition.css">',root/'styles/icon-composition.css','style'),
      ('<script src="../vendor/gsap-compat.js"></script>',root/'vendor/gsap-compat.js','script'),
      ('<script src="../runtime/theme.js"></script>',root/'runtime/theme.js','script'),
      ('<script src="../runtime/motion-registry.js"></script>',root/'runtime/motion-registry.js','script'),
      ('<script src="../runtime/motion-engine.js"></script>',root/'runtime/motion-engine.js','script'),
      ('<script src="../runtime/icon-registry.js"></script>',root/'runtime/icon-registry.js','script'),
      ('<script src="../components/universal-icons.js"></script>',root/'components/universal-icons.js','script'),
      ('<script src="../runtime/icon-aspect-demo.js"></script>',root/'runtime/icon-aspect-demo.js','script'),
    ]
    for old,p,tag in reps: html=inline_file(html,old,p,tag)
    return html

def bundled_icon_dock(root: Path) -> str:
    html=(root/'compositions/icon-dock-demo.html').read_text()
    reps=[
      ('<link rel="stylesheet" href="../styles/tokens.css">',root/'styles/tokens.css','style'),
      ('<link rel="stylesheet" href="../styles/paper.css">',root/'styles/paper.css','style'),
      ('<link rel="stylesheet" href="../styles/motion.css">',root/'styles/motion.css','style'),
      ('<link rel="stylesheet" href="../styles/icons.css">',root/'styles/icons.css','style'),
      ('<link rel="stylesheet" href="../styles/icon-dock.css">',root/'styles/icon-dock.css','style'),
      ('<script src="../vendor/gsap-compat.js"></script>',root/'vendor/gsap-compat.js','script'),
      ('<script src="../runtime/theme.js"></script>',root/'runtime/theme.js','script'),
      ('<script src="../runtime/motion-registry.js"></script>',root/'runtime/motion-registry.js','script'),
      ('<script src="../runtime/motion-engine.js"></script>',root/'runtime/motion-engine.js','script'),
      ('<script src="../runtime/icon-registry.js"></script>',root/'runtime/icon-registry.js','script'),
      ('<script src="../components/universal-icons.js"></script>',root/'components/universal-icons.js','script'),
      ('<script src="../runtime/icon-dock-demo.js"></script>',root/'runtime/icon-dock-demo.js','script'),
    ]
    for old,p,tag in reps: html=inline_file(html,old,p,tag)
    return html
