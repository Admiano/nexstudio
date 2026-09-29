from pathlib import Path
import re

def bundle(root:Path, rel:str):
 p=root/rel;s=p.read_text()
 # inline stylesheet links
 def css(m):
  href=m.group(1);f=(p.parent/href).resolve()
  return '<style>'+f.read_text()+'</style>' if f.exists() else ''
 s=re.sub(r'<link[^>]+href="([^"]+)"[^>]*>',css,s)
 # inline script src
 def js(m):
  src=m.group(1);f=(p.parent/src).resolve()
  return '<script>'+f.read_text()+'</script>' if f.exists() else ''
 s=re.sub(r'<script[^>]+src="([^"]+)"[^>]*></script>',js,s)
 # asset paths for inline audio still relative to project root; convert to file URI
 s=s.replace('assets/audio/',(root/'assets/audio').as_uri()+'/')
 return s
