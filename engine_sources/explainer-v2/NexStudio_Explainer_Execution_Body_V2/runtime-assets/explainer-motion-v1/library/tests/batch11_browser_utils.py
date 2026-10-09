from pathlib import Path
import base64

def data_uri(path:Path):
    mime='image/svg+xml' if path.suffix=='.svg' else 'image/png'
    return f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode()

def common(root:Path):
    js=(root/'components/creator-modules.js').read_text()
    for name in ['photo-creator.svg','website-screenshot.svg','photo-product.svg']:
        js=js.replace('assets/media/'+name,data_uri(root/'assets/media'/name))
    css='\n'.join((root/p).read_text() for p in ['styles/tokens.css','styles/paper.css','styles/icons.css','styles/creator-icons.css','styles/creator-modules.css'])
    scripts='\n'.join((root/p).read_text() for p in ['vendor/gsap-compat.js','runtime/theme.js','runtime/motion-engine.js','runtime/creator-icon-registry.js','components/creator-icons.js','runtime/creator-module-registry.js'])+'\n'+js
    return css,scripts

def harness(root:Path):
    css,js=common(root)
    return f'<!doctype html><html data-paper-style="clean-editorial"><head><style>{css}</style></head><body><main id="stage"></main><script>{js}</script></body></html>'

def bundle_explorer(root:Path):
    css,js=common(root)
    css+='\n'+(root/'styles/creator-module-explorer.css').read_text()
    extra=(root/'runtime/creator-module-explorer.js').read_text()
    body=(root/'creator-module-explorer.html').read_text().split('<body>',1)[1].split('<script src=',1)[0]
    return f'<!doctype html><html data-paper-style="clean-editorial"><head><style>{css}</style></head><body>{body}<script>{js}\n{extra}</script></body></html>'

def bundle_scene(root:Path,name:str):
    css,js=common(root)
    css+='\n'+(root/'styles/creator-module-scenes.css').read_text()
    src=(root/f'compositions/{name}.html').read_text()
    body=src.split('<body>',1)[1].split('<script src=',1)[0]
    scene=(root/'runtime/creator-module-scenes.js').read_text()
    return f'<!doctype html><html data-paper-style="clean-editorial"><head><style>{css}</style></head><body>{body}<script>{js}\n{scene}\nNexCreatorModuleScenes.init("{name}");</script></body></html>'
