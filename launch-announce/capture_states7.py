#!/usr/bin/env python3
import asyncio, base64
from playwright.async_api import async_playwright

PREV = '/home/ubuntu/work/v1full/engine_sources/makehuman-lineart/out/cast-previews'
IMGS = {
    'man': PREV + '/ddc3a8c99efa7bc4009732d15c364a9d5e76f47b3bee39c7e29baa27d15e3e8a/preview.png',
    'braids': PREV + '/dfc7e805e07b0fdeef481169bbf3e8fa36170f429759b290e102f04bfd745631/preview.png',
    'outfit': PREV + '/17d4a1a21e9c344818d389e3cddec4b1b9f284ae82b6b0901c0cc374a0116ca6/preview.png',
    'saved':  PREV + '/a01b42544151679442c365c897d96971af5c197821f446d47e85f367bb06ab95/preview.png',
}
OUT = '/home/ubuntu/work/launch'

def datauri(p):
    return 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode()

async def set_preview(page, key):
    await page.evaluate("""(src) => {
        const imgs=[...document.querySelectorAll('img')].filter(i=>i.getBoundingClientRect().width>250);
        const big=imgs.sort((a,b)=>b.getBoundingClientRect().width-a.getBoundingClientRect().width)[0];
        if(big){big.srcset='';big.src=src;}
    }""", datauri(IMGS[key]))

async def tidy(page):
    await page.evaluate("""() => {[...document.querySelectorAll('*')].forEach(e=>{
        const r=e.getBoundingClientRect();
        if(e.children.length===0 && r.height<70 && /Rendering your selected look|Waiting for preview/.test(e.textContent||'')){
            let n=e.parentElement; if(n && n.getBoundingClientRect().height<90) n.style.display='none';}})}""")

async def click_text(page, txt):
    ok = await page.evaluate("""(txt) => {
        const els=[...document.querySelectorAll('button,[role=button],div,span,label')].filter(e=>{
            const t=(e.textContent||'').trim();
            return t===txt || (e.children.length<3 && t.startsWith(txt) && t.length<txt.length+16);
        });
        const el=els.pop();
        if(!el) return false;
        el.scrollIntoView({block:'nearest'}); el.click(); return true;
    }""", txt)
    print('CLICK', txt, ok, flush=True)
    await asyncio.sleep(0.9)
    return ok

async def modal_rect(page):
    r = await page.evaluate("""() => {
        const t=[...document.querySelectorAll('*')].find(e=>e.children.length<3 && /Build your presenter/.test(e.textContent||''));
        if(!t) return null;
        let el=t;
        while(el && !(el.getBoundingClientRect().width>900 && el.getBoundingClientRect().height>700)) el=el.parentElement;
        if(!el) return null;
        const b=el.getBoundingClientRect();
        return {x:Math.max(0,b.x-6),y:Math.max(0,b.y-6),width:b.width+12,height:Math.min(b.height+12,window.innerHeight-b.y+6)};
    }""")
    print('RECT', r, flush=True)
    return r

async def scroll_opts(page, px):
    await page.evaluate("""(px) => {
        const cols=[...document.querySelectorAll('div')].filter(d=>d.scrollHeight>d.clientHeight+200 && d.getBoundingClientRect().width<900);
        const c=cols.sort((a,b)=>b.scrollHeight-a.scrollHeight)[0];
        if(c) c.scrollTop=px;}""", px)
    await asyncio.sleep(0.5)

async def shot(page, name, clip):
    await tidy(page)
    await asyncio.sleep(0.2)
    await page.screenshot(path=f'{OUT}/state_{name}.png', clip=clip)
    print('SHOT', name, flush=True)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.connect_over_cdp('http://localhost:29229')
        page = b.contexts[0].pages[0]
        # taller viewport so the full modal (name field + avatar box) renders in frame
        cdp = await page.context.new_cdp_session(page)
        await cdp.send('Emulation.setDeviceMetricsOverride',
                       {'width': 1680, 'height': 1200, 'deviceScaleFactor': 1, 'mobile': False})
        await asyncio.sleep(1.2)
        # ensure the avatar modal is open
        await page.goto('http://localhost:3000/api/v1/auth/guest?token=2yQ4cNCr3RoATsz8iyCeqLm1KqcllSht')
        await asyncio.sleep(3)
        await page.goto('http://localhost:3000/studio#cast')
        await asyncio.sleep(5)
        ok = await page.evaluate("""()=>{const e=[...document.querySelectorAll('button,a,[role=button]')].find(x=>(x.textContent||'').trim().toLowerCase().includes('build an avatar'));if(e){e.click();return true}return false}""")
        print('modal open', ok, flush=True)
        await asyncio.sleep(2.5)
        clip = await modal_rect(page)
        await shot(page, '0_default', clip)      # fresh default: Woman selected
        await click_text(page, 'Man')
        await set_preview(page, 'man')
        await shot(page, '1_man', clip)          # Man card picked
        await scroll_opts(page, 700)             # reveal Hair section
        await click_text(page, 'Braids')
        await set_preview(page, 'braids')
        await shot(page, '2_braids', clip)
        await scroll_opts(page, 1100)            # reveal Tops
        await click_text(page, 'Tee')
        await set_preview(page, 'outfit')
        await shot(page, '3_tee', clip)
        await scroll_opts(page, 1500)            # reveal Trousers
        await click_text(page, 'Straight jeans')
        await set_preview(page, 'saved')
        await shot(page, '4_jeans', clip)
        await scroll_opts(page, 99999)           # Add to cast button
        await shot(page, '5_save', clip)
        await b.close()

asyncio.run(main())
