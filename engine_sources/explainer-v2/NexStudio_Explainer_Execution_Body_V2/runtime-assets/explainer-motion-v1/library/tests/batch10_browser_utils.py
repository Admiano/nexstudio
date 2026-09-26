from pathlib import Path

def inline(html, root, css_files, js_files):
    for f in css_files:
        html=html.replace(f'<link rel="stylesheet" href="{f}">',f'<style>{(root/f).read_text()}</style>')
        html=html.replace(f'<link rel="stylesheet" href="../{f}">',f'<style>{(root/f).read_text()}</style>')
    for f in js_files:
        html=html.replace(f'<script src="{f}"></script>',f'<script>{(root/f).read_text()}</script>')
        html=html.replace(f'<script src="../{f}"></script>',f'<script>{(root/f).read_text()}</script>')
    return html

def bundle_editor(root:Path, workflow=False):
    name='workflow-editor.html' if workflow else 'data-editor.html'
    return inline((root/name).read_text(),root,
      ['styles/tokens.css','styles/paper.css','styles/data-visualisations.css','styles/data-editors.css'],
      ['vendor/gsap-compat.js','runtime/theme.js','runtime/data-visualisation-registry.js','components/data-visualisations.js','runtime/data-editor.js'])

def bundle_scene(root:Path,name:str):
    return inline((root/f'compositions/{name}.html').read_text(),root,
      ['styles/tokens.css','styles/paper.css','styles/data-visualisations.css','styles/data-scenes.css'],
      ['vendor/gsap-compat.js','runtime/theme.js','runtime/data-visualisation-registry.js','components/data-visualisations.js','runtime/data-scene-demo.js'])

def component_harness(root:Path):
    return f'''<!doctype html><html data-paper-style="clean-editorial"><head><style>{(root/'styles/tokens.css').read_text()}</style><style>{(root/'styles/paper.css').read_text()}</style><style>{(root/'styles/data-visualisations.css').read_text()}</style></head><body><main id="stage"></main><script>{(root/'vendor/gsap-compat.js').read_text()}</script><script>{(root/'runtime/theme.js').read_text()}</script><script>{(root/'runtime/data-visualisation-registry.js').read_text()}</script><script>{(root/'components/data-visualisations.js').read_text()}</script></body></html>'''
