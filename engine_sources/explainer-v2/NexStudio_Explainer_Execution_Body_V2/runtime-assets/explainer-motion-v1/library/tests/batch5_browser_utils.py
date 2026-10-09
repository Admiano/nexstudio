from pathlib import Path

def inline_file(html,old,path,tag='style'):
    return html.replace(old,f'<{tag}>{path.read_text()}</{tag}>')

def bundled_creator_explorer(root:Path):
    html=(root/'creator-icon-explorer.html').read_text()
    reps=[
      ('<link rel="stylesheet" href="styles/tokens.css">',root/'styles/tokens.css','style'),
      ('<link rel="stylesheet" href="styles/paper.css">',root/'styles/paper.css','style'),
      ('<link rel="stylesheet" href="styles/motion.css">',root/'styles/motion.css','style'),
      ('<link rel="stylesheet" href="styles/icons.css">',root/'styles/icons.css','style'),
      ('<link rel="stylesheet" href="styles/creator-icons.css">',root/'styles/creator-icons.css','style'),
      ('<link rel="stylesheet" href="styles/icon-explorer.css">',root/'styles/icon-explorer.css','style'),
      ('<link rel="stylesheet" href="styles/creator-explorer.css">',root/'styles/creator-explorer.css','style'),
      ('<script src="vendor/gsap-compat.js"></script>',root/'vendor/gsap-compat.js','script'),
      ('<script src="runtime/theme.js"></script>',root/'runtime/theme.js','script'),
      ('<script src="runtime/motion-registry.js"></script>',root/'runtime/motion-registry.js','script'),
      ('<script src="runtime/motion-engine.js"></script>',root/'runtime/motion-engine.js','script'),
      ('<script src="runtime/creator-icon-registry.js"></script>',root/'runtime/creator-icon-registry.js','script'),
      ('<script src="components/creator-icons.js"></script>',root/'components/creator-icons.js','script'),
      ('<script src="runtime/creator-icon-explorer.js"></script>',root/'runtime/creator-icon-explorer.js','script'),
    ]
    for old,p,tag in reps:html=inline_file(html,old,p,tag)
    return html

def bundled_creator_scene(root:Path,name:str):
    html=(root/f'compositions/{name}.html').read_text()
    reps=[
      ('<link rel="stylesheet" href="../styles/tokens.css">',root/'styles/tokens.css','style'),
      ('<link rel="stylesheet" href="../styles/paper.css">',root/'styles/paper.css','style'),
      ('<link rel="stylesheet" href="../styles/motion.css">',root/'styles/motion.css','style'),
      ('<link rel="stylesheet" href="../styles/icons.css">',root/'styles/icons.css','style'),
      ('<link rel="stylesheet" href="../styles/creator-icons.css">',root/'styles/creator-icons.css','style'),
      ('<link rel="stylesheet" href="../styles/creator-scenes.css">',root/'styles/creator-scenes.css','style'),
      ('<script src="../vendor/gsap-compat.js"></script>',root/'vendor/gsap-compat.js','script'),
      ('<script src="../runtime/theme.js"></script>',root/'runtime/theme.js','script'),
      ('<script src="../runtime/motion-registry.js"></script>',root/'runtime/motion-registry.js','script'),
      ('<script src="../runtime/motion-engine.js"></script>',root/'runtime/motion-engine.js','script'),
      ('<script src="../runtime/creator-icon-registry.js"></script>',root/'runtime/creator-icon-registry.js','script'),
      ('<script src="../components/creator-icons.js"></script>',root/'components/creator-icons.js','script'),
      ('<script src="../runtime/creator-scene-demo.js"></script>',root/'runtime/creator-scene-demo.js','script'),
    ]
    for old,p,tag in reps:html=inline_file(html,old,p,tag)
    return html
