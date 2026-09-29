from pathlib import Path
import base64,re

def data_uri(path:Path):
    mime='image/svg+xml' if path.suffix.lower()=='.svg' else 'image/png'
    return f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode()

def common(root:Path):
    registry=(root/'runtime/documentary-module-registry.js').read_text()
    comp=(root/'components/documentary-modules.js').read_text()
    scene=(root/'runtime/documentary-scenes.js').read_text()
    for p in (root/'assets/media/documentary').glob('*.svg'):
        uri=data_uri(p)
        for old in [f'assets/media/documentary/{p.name}',f'../assets/media/documentary/{p.name}']:
            registry=registry.replace(old,uri);comp=comp.replace(old,uri);scene=scene.replace(old,uri)
    for p in [root/'assets/media/website-screenshot.svg',root/'assets/media/photo-story-1.svg',root/'assets/media/photo-story-2.svg']:
        if p.exists():
            uri=data_uri(p)
            registry=registry.replace('assets/media/'+p.name,uri);comp=comp.replace('assets/media/'+p.name,uri);scene=scene.replace('assets/media/'+p.name,uri)
    css='\n'.join((root/p).read_text() for p in ['styles/tokens.css','styles/paper.css','styles/documentary-modules.css'])
    js='\n'.join((root/p).read_text() for p in ['vendor/gsap-compat.js','runtime/theme.js','runtime/motion-engine.js'])+'\n'+registry+'\n'+comp
    return css,js,scene

def harness(root:Path):
    css,js,_=common(root)
    return f'<!doctype html><html data-paper-style="clean-editorial"><head><style>{css}</style></head><body><main id="stage"></main><script>{js}</script></body></html>'

def bundle_explorer(root:Path):
    css,js,_=common(root);css+='\n'+(root/'styles/documentary-module-explorer.css').read_text();extra=(root/'runtime/documentary-module-explorer.js').read_text();src=(root/'documentary-module-explorer.html').read_text();body=src.split('<body>',1)[1].split('<script src=',1)[0]
    return f'<!doctype html><html data-paper-style="clean-editorial"><head><style>{css}</style></head><body>{body}<script>{js}\n{extra}</script></body></html>'

def bundle_scene(root:Path,name:str):
    css,js,scene=common(root);css+='\n'+(root/'styles/documentary-scenes.css').read_text();src=(root/f'compositions/{name}.html').read_text();body=src.split('<body>',1)[1].split('<script src=',1)[0]
    return f'<!doctype html><html data-paper-style="clean-editorial"><head><style>{css}</style></head><body>{body}<script>{js}\n{scene}\nNexDocumentaryScenes.init("{name}");</script></body></html>'
