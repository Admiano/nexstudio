from pathlib import Path

def inline_file(html,old,path,tag='style'):
    return html.replace(old,f'<{tag}>{path.read_text()}</{tag}>')

def bundled_business_explorer(root:Path):
    html=(root/'business-icon-explorer.html').read_text()
    reps=[
      ('<link rel="stylesheet" href="styles/tokens.css">',root/'styles/tokens.css','style'),
      ('<link rel="stylesheet" href="styles/paper.css">',root/'styles/paper.css','style'),
      ('<link rel="stylesheet" href="styles/motion.css">',root/'styles/motion.css','style'),
      ('<link rel="stylesheet" href="styles/icons.css">',root/'styles/icons.css','style'),
      ('<link rel="stylesheet" href="styles/business-icons.css">',root/'styles/business-icons.css','style'),
      ('<link rel="stylesheet" href="styles/icon-explorer.css">',root/'styles/icon-explorer.css','style'),
      ('<link rel="stylesheet" href="styles/business-explorer.css">',root/'styles/business-explorer.css','style'),
      ('<script src="vendor/gsap-compat.js"></script>',root/'vendor/gsap-compat.js','script'),
      ('<script src="runtime/theme.js"></script>',root/'runtime/theme.js','script'),
      ('<script src="runtime/motion-registry.js"></script>',root/'runtime/motion-registry.js','script'),
      ('<script src="runtime/motion-engine.js"></script>',root/'runtime/motion-engine.js','script'),
      ('<script src="runtime/business-icon-registry.js"></script>',root/'runtime/business-icon-registry.js','script'),
      ('<script src="components/business-icons.js"></script>',root/'components/business-icons.js','script'),
      ('<script src="runtime/business-icon-explorer.js"></script>',root/'runtime/business-icon-explorer.js','script'),
    ]
    for old,p,tag in reps:html=inline_file(html,old,p,tag)
    return html

def bundled_business_scene(root:Path,name:str):
    html=(root/f'compositions/{name}.html').read_text()
    reps=[
      ('<link rel="stylesheet" href="../styles/tokens.css">',root/'styles/tokens.css','style'),
      ('<link rel="stylesheet" href="../styles/paper.css">',root/'styles/paper.css','style'),
      ('<link rel="stylesheet" href="../styles/motion.css">',root/'styles/motion.css','style'),
      ('<link rel="stylesheet" href="../styles/icons.css">',root/'styles/icons.css','style'),
      ('<link rel="stylesheet" href="../styles/business-icons.css">',root/'styles/business-icons.css','style'),
      ('<link rel="stylesheet" href="../styles/business-scenes.css">',root/'styles/business-scenes.css','style'),
      ('<script src="../vendor/gsap-compat.js"></script>',root/'vendor/gsap-compat.js','script'),
      ('<script src="../runtime/theme.js"></script>',root/'runtime/theme.js','script'),
      ('<script src="../runtime/motion-registry.js"></script>',root/'runtime/motion-registry.js','script'),
      ('<script src="../runtime/motion-engine.js"></script>',root/'runtime/motion-engine.js','script'),
      ('<script src="../runtime/business-icon-registry.js"></script>',root/'runtime/business-icon-registry.js','script'),
      ('<script src="../components/business-icons.js"></script>',root/'components/business-icons.js','script'),
      ('<script src="../runtime/business-scene-demo.js"></script>',root/'runtime/business-scene-demo.js','script'),
    ]
    for old,p,tag in reps:html=inline_file(html,old,p,tag)
    return html
