from pathlib import Path

def bundled_composition(root: Path) -> str:
    html=(root/'compositions/foundation-demo.html').read_text()
    replacements={
      '<link rel="stylesheet" href="../styles/tokens.css">':f'<style>{(root/"styles/tokens.css").read_text()}</style>',
      '<link rel="stylesheet" href="../styles/paper.css">':f'<style>{(root/"styles/paper.css").read_text()}</style>',
      '<link rel="stylesheet" href="../styles/composition.css">':f'<style>{(root/"styles/composition.css").read_text()}</style>',
      '<script src="../vendor/gsap-compat.js"></script>':f'<script>{(root/"vendor/gsap-compat.js").read_text()}</script>',
      '<script src="../runtime/theme.js"></script>':f'<script>{(root/"runtime/theme.js").read_text()}</script>',
      '<script src="../runtime/foundation-registry.js"></script>':f'<script>{(root/"runtime/foundation-registry.js").read_text()}</script>',
      '<script src="../components/foundation-components.js"></script>':f'<script>{(root/"components/foundation-components.js").read_text()}</script>',
      '<script src="../runtime/composition.js"></script>':f'<script>{(root/"runtime/composition.js").read_text()}</script>',
    }
    for old,new in replacements.items(): html=html.replace(old,new)
    return html

def bundled_explorer(root: Path) -> str:
    html=(root/('foundation-explorer.html' if (root/'foundation-explorer.html').exists() else 'index.html')).read_text()
    replacements={
      '<link rel="stylesheet" href="styles/tokens.css">':f'<style>{(root/"styles/tokens.css").read_text()}</style>',
      '<link rel="stylesheet" href="styles/paper.css">':f'<style>{(root/"styles/paper.css").read_text()}</style>',
      '<link rel="stylesheet" href="styles/explorer.css">':f'<style>{(root/"styles/explorer.css").read_text()}</style>',
      '<script src="vendor/gsap-compat.js"></script>':f'<script>{(root/"vendor/gsap-compat.js").read_text()}</script>',
      '<script src="runtime/theme.js"></script>':f'<script>{(root/"runtime/theme.js").read_text()}</script>',
      '<script src="runtime/foundation-registry.js"></script>':f'<script>{(root/"runtime/foundation-registry.js").read_text()}</script>',
      '<script src="components/foundation-components.js"></script>':f'<script>{(root/"components/foundation-components.js").read_text()}</script>',
      '<script src="runtime/explorer.js"></script>':f'<script>{(root/"runtime/explorer.js").read_text()}</script>',
    }
    for old,new in replacements.items(): html=html.replace(old,new)
    return html
