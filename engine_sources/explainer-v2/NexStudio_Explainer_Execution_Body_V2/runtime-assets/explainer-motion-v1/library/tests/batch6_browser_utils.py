from pathlib import Path

def inline_file(html,old,path,tag='style'):
    return html.replace(old,f'<{tag}>{path.read_text()}</{tag}>')

def bundled_agent_explorer(root:Path):
    html=(root/'agent-icon-explorer.html').read_text()
    reps=[
      ('<link rel="stylesheet" href="styles/tokens.css">',root/'styles/tokens.css','style'),
      ('<link rel="stylesheet" href="styles/paper.css">',root/'styles/paper.css','style'),
      ('<link rel="stylesheet" href="styles/motion.css">',root/'styles/motion.css','style'),
      ('<link rel="stylesheet" href="styles/icons.css">',root/'styles/icons.css','style'),
      ('<link rel="stylesheet" href="styles/agent-icons.css">',root/'styles/agent-icons.css','style'),
      ('<link rel="stylesheet" href="styles/icon-explorer.css">',root/'styles/icon-explorer.css','style'),
      ('<link rel="stylesheet" href="styles/agent-explorer.css">',root/'styles/agent-explorer.css','style'),
      ('<script src="vendor/gsap-compat.js"></script>',root/'vendor/gsap-compat.js','script'),
      ('<script src="runtime/theme.js"></script>',root/'runtime/theme.js','script'),
      ('<script src="runtime/motion-registry.js"></script>',root/'runtime/motion-registry.js','script'),
      ('<script src="runtime/motion-engine.js"></script>',root/'runtime/motion-engine.js','script'),
      ('<script src="runtime/agent-icon-registry.js"></script>',root/'runtime/agent-icon-registry.js','script'),
      ('<script src="components/agent-icons.js"></script>',root/'components/agent-icons.js','script'),
      ('<script src="runtime/agent-icon-explorer.js"></script>',root/'runtime/agent-icon-explorer.js','script'),
    ]
    for old,p,tag in reps:html=inline_file(html,old,p,tag)
    return html

def bundled_agent_scene(root:Path,name:str):
    html=(root/f'compositions/{name}.html').read_text()
    reps=[
      ('<link rel="stylesheet" href="../styles/tokens.css">',root/'styles/tokens.css','style'),
      ('<link rel="stylesheet" href="../styles/paper.css">',root/'styles/paper.css','style'),
      ('<link rel="stylesheet" href="../styles/motion.css">',root/'styles/motion.css','style'),
      ('<link rel="stylesheet" href="../styles/icons.css">',root/'styles/icons.css','style'),
      ('<link rel="stylesheet" href="../styles/agent-icons.css">',root/'styles/agent-icons.css','style'),
      ('<link rel="stylesheet" href="../styles/agent-scenes.css">',root/'styles/agent-scenes.css','style'),
      ('<script src="../vendor/gsap-compat.js"></script>',root/'vendor/gsap-compat.js','script'),
      ('<script src="../runtime/theme.js"></script>',root/'runtime/theme.js','script'),
      ('<script src="../runtime/motion-registry.js"></script>',root/'runtime/motion-registry.js','script'),
      ('<script src="../runtime/motion-engine.js"></script>',root/'runtime/motion-engine.js','script'),
      ('<script src="../runtime/agent-icon-registry.js"></script>',root/'runtime/agent-icon-registry.js','script'),
      ('<script src="../components/agent-icons.js"></script>',root/'components/agent-icons.js','script'),
      ('<script src="../runtime/agent-scene-demo.js"></script>',root/'runtime/agent-scene-demo.js','script'),
    ]
    for old,p,tag in reps:html=inline_file(html,old,p,tag)
    return html
