from pathlib import Path
import re,html

def bundle(root:Path, rel:str, strip_iframe=False):
 p=root/rel;s=p.read_text()
 def css(m):
  href=m.group(1);f=(p.parent/href).resolve();return '<style>'+f.read_text()+'</style>' if f.exists() else ''
 s=re.sub(r'<link[^>]+href="([^"]+)"[^>]*>',css,s)
 def js(m):
  src=m.group(1);f=(p.parent/src).resolve();return '<script>'+f.read_text()+'</script>' if f.exists() else ''
 s=re.sub(r'<script[^>]+src="([^"]+)"[^>]*></script>',js,s)
 s=s.replace('assets/audio/',(root/'assets/audio').as_uri()+'/').replace('assets/media/',(root/'assets/media').as_uri()+'/')
 if strip_iframe:s=re.sub(r'src="master-preview.html"','src="about:blank"',s)
 return s
