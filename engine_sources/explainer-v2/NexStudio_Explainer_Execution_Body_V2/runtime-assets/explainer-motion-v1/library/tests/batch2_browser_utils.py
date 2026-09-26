from pathlib import Path

def inline_file(html: str, old: str, path: Path, tag='style') -> str:
    content=path.read_text()
    return html.replace(old, f'<{tag}>{content}</{tag}>')

def bundled_object_composition(root: Path) -> str:
    html=(root/'compositions/paper-objects-demo.html').read_text()
    reps=[
      ('<link rel="stylesheet" href="../styles/tokens.css">',root/'styles/tokens.css','style'),
      ('<link rel="stylesheet" href="../styles/paper.css">',root/'styles/paper.css','style'),
      ('<link rel="stylesheet" href="../styles/objects.css">',root/'styles/objects.css','style'),
      ('<link rel="stylesheet" href="../styles/object-composition.css">',root/'styles/object-composition.css','style'),
      ('<script src="../vendor/gsap-compat.js"></script>',root/'vendor/gsap-compat.js','script'),
      ('<script src="../runtime/theme.js"></script>',root/'runtime/theme.js','script'),
      ('<script src="../runtime/object-registry.js"></script>',root/'runtime/object-registry.js','script'),
      ('<script src="../components/paper-objects.js"></script>',root/'components/paper-objects.js','script'),
      ('<script src="../runtime/object-demo.js"></script>',root/'runtime/object-demo.js','script'),
    ]
    for old,p,tag in reps: html=inline_file(html,old,p,tag)
    return html

def bundled_object_explorer(root: Path) -> str:
    html=(root/'index.html').read_text()
    reps=[
      ('<link rel="stylesheet" href="styles/tokens.css">',root/'styles/tokens.css','style'),
      ('<link rel="stylesheet" href="styles/paper.css">',root/'styles/paper.css','style'),
      ('<link rel="stylesheet" href="styles/objects.css">',root/'styles/objects.css','style'),
      ('<link rel="stylesheet" href="styles/explorer.css">',root/'styles/explorer.css','style'),
      ('<script src="vendor/gsap-compat.js"></script>',root/'vendor/gsap-compat.js','script'),
      ('<script src="runtime/theme.js"></script>',root/'runtime/theme.js','script'),
      ('<script src="runtime/object-registry.js"></script>',root/'runtime/object-registry.js','script'),
      ('<script src="components/paper-objects.js"></script>',root/'components/paper-objects.js','script'),
      ('<script src="runtime/object-explorer.js"></script>',root/'runtime/object-explorer.js','script'),
    ]
    for old,p,tag in reps: html=inline_file(html,old,p,tag)
    return html
