from pathlib import Path
import base64,mimetypes

CSS_FILES=['styles/tokens.css','styles/paper.css','styles/objects.css','styles/icons.css','styles/creator-icons.css','styles/agent-icons.css','styles/business-icons.css','styles/typography.css','styles/media-containers.css','styles/data-visualisations.css','styles/creator-modules.css','styles/documentary-modules.css','styles/scene-rigs.css']
JS_FILES=['vendor/gsap-compat.js','runtime/theme.js','runtime/motion-registry.js','runtime/motion-engine.js','runtime/object-registry.js','runtime/icon-registry.js','runtime/creator-icon-registry.js','runtime/agent-icon-registry.js','runtime/business-icon-registry.js','runtime/typography-registry.js','runtime/media-container-registry.js','runtime/data-visualisation-registry.js','runtime/creator-module-registry.js','runtime/documentary-module-registry.js','runtime/scene-rig-registry.js','components/paper-objects.js','components/universal-icons.js','components/creator-icons.js','components/agent-icons.js','components/business-icons.js','components/typography.js','components/media-containers.js','components/data-visualisations.js','components/creator-modules.js','components/documentary-modules.js','components/scene-rigs.js']

def uri(p:Path):
    mime=mimetypes.guess_type(str(p))[0] or 'application/octet-stream'
    return f'data:{mime};base64,'+base64.b64encode(p.read_bytes()).decode()

def common(root:Path):
    css='\n'.join((root/p).read_text() for p in CSS_FILES)
    chunks=[(root/p).read_text() for p in JS_FILES]
    # Replace all local media references in all JS chunks.
    media=root/'assets/media'
    for p in media.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in {'.svg','.png','.jpg','.jpeg','.webp','.mp4','.webm'}: continue
        rel=p.relative_to(root).as_posix(); u=uri(p)
        chunks=[c.replace(rel,u).replace('../'+rel,u).replace('../../'+rel,u) for c in chunks]
    return css,'\n'.join(chunks)

def harness(root:Path):
    css,js=common(root)
    return f'<!doctype html><html data-paper-style="clean-editorial"><head><style>{css}</style></head><body><main id="stage"></main><script>{js}</script></body></html>'

def bundle_explorer(root:Path):
    css,js=common(root);css+='\n'+(root/'styles/scene-explorer.css').read_text();extra=(root/'runtime/scene-rig-explorer.js').read_text();src=(root/'scene-rig-explorer.html').read_text();body=src.split('<body>',1)[1].split('<script src=',1)[0]
    return f'<!doctype html><html data-paper-style="clean-editorial"><head><style>{css}</style></head><body>{body}<script>{js}\n{extra}</script></body></html>'

def bundle_scene(root:Path,name:str):
    css,js=common(root);css+='\n'+(root/'styles/scene-films.css').read_text();films=(root/'runtime/scene-films.js').read_text();src=(root/f'compositions/{name}.html').read_text();body=src.split('<body>',1)[1].split('<script src=',1)[0]
    return f'<!doctype html><html data-paper-style="clean-editorial"><head><style>{css}</style></head><body>{body}<script>{js}\n{films}\nNexSceneFilms.init("{name}");</script></body></html>'
