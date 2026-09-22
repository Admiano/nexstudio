from pathlib import Path

def inline_file(html,old,path,tag='style'):
    return html.replace(old,f'<{tag}>{path.read_text()}</{tag}>')

def bundle(root:Path,rel:str):
    html=(root/rel).read_text()
    prefix='../' if rel.startswith('compositions/') else ''
    files=[
      ('styles/tokens.css','style'),('styles/paper.css','style'),('styles/motion.css','style'),('styles/typography.css','style'),('styles/typography-explorer.css','style'),('styles/typography-scenes.css','style'),
      ('vendor/gsap-compat.js','script'),('runtime/theme.js','script'),('runtime/motion-registry.js','script'),('runtime/motion-engine.js','script'),('runtime/typography-registry.js','script'),('runtime/typography-samples.js','script'),('components/typography.js','script'),('runtime/typography-explorer.js','script'),('runtime/kinetic-typography-demo.js','script')]
    for f,tag in files:
        old=f'<link rel="stylesheet" href="{prefix}{f}">' if tag=='style' else f'<script src="{prefix}{f}"></script>'
        if old in html:html=inline_file(html,old,root/f,tag)
    return html
