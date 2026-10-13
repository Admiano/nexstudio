import hashlib,os,tempfile,unittest
from pathlib import Path
from test_typography_scene import fixture
from typography_scene import bind_typography_scene
from editorial_adapter import _write_typography_package
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright=None

@unittest.skipUnless(sync_playwright is not None,'Playwright is required for the actual browser test')
class NativeRuntimeTests(unittest.TestCase):
    def test_real_browser_focus_font_copy_and_repeatable_seek(self):
        board,contract=fixture();spec=bind_typography_scene(board,contract)
        with tempfile.TemporaryDirectory() as temp,sync_playwright() as p:
            manifest=_write_typography_package({'typographyScene':spec},Path(temp))
            browser=p.chromium.launch(executable_path=os.environ.get('STUDIO_CHROMIUM_PATH',r'C:\Program Files\Google\Chrome\Application\chrome.exe'),headless=True,args=['--disable-gpu','--no-sandbox'])
            page=browser.new_page(viewport={'width':1280,'height':720});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.set_content(Path(manifest['renderHtml']).read_text(encoding='utf-8'));page.evaluate('() => document.fonts.ready')
            def seek(t):return page.evaluate('(t)=>window.NexFacelessRenderer.seek(t)',t)
            before=seek(0);blurred=page.screenshot();after=seek(1);sharp=page.screenshot()
            self.assertTrue(after['fontLoaded']);self.assertEqual(after['nodes'][1]['text'],'Read slowly.')
            self.assertEqual(before['nodes'][1]['blur'],8);self.assertEqual(after['nodes'][1]['blur'],0)
            self.assertNotEqual(hashlib.sha256(blurred).digest(),hashlib.sha256(sharp).digest())
            seek(0);seek(1.9);self.assertEqual(sharp,page.screenshot())
            self.assertFalse(errors);self.assertEqual(after['visibleAnonymousHelperCount'],0)
            for x,y,w,h in after['lineRects']:self.assertTrue(0<=x<x+w<=1280 and 0<=y<y+h<=720)
            browser.close()

if __name__=='__main__':unittest.main()
