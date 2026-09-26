from pathlib import Path
import base64,mimetypes,json

def data_uri(path:Path):
    mime=mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
    return f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode()

def bundle_media_explorer(root:Path):
    html=(root/'media-container-explorer.html').read_text()
    for f in ['styles/tokens.css','styles/paper.css','styles/motion.css','styles/media-containers.css','styles/media-explorer.css']:
        html=html.replace(f'<link rel="stylesheet" href="{f}">',f'<style>{(root/f).read_text()}</style>')
    for f in ['vendor/gsap-compat.js','runtime/theme.js','runtime/motion-registry.js','runtime/motion-engine.js','runtime/media-container-registry.js','components/media-containers.js','runtime/media-container-explorer.js']:
        html=html.replace(f'<script src="{f}"></script>',f'<script>{(root/f).read_text()}</script>')
    for asset in (root/'assets/media').iterdir():
        if asset.is_file(): html=html.replace('assets/media/'+asset.name,data_uri(asset))
    return html

def bundle_media_scene(root:Path,name:str):
    html=(root/f'compositions/{name}.html').read_text()
    for f in ['styles/tokens.css','styles/paper.css','styles/motion.css','styles/media-containers.css','styles/media-scenes.css']:
        html=html.replace(f'<link rel="stylesheet" href="../{f}">',f'<style>{(root/f).read_text()}</style>')
    asset_map={a.name:data_uri(a) for a in (root/'assets/media').iterdir() if a.is_file()}
    for f in ['vendor/gsap-compat.js','runtime/theme.js','runtime/motion-registry.js','runtime/motion-engine.js','runtime/media-container-registry.js','components/media-containers.js','runtime/media-scene-demo.js']:
        payload=(root/f).read_text()
        if f=='runtime/media-scene-demo.js':payload='window.NEX_MEDIA_ASSETS='+json.dumps(asset_map)+';\n'+payload
        html=html.replace(f'<script src="../{f}"></script>',f'<script>{payload}</script>')
    return html
