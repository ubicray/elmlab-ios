#!/usr/bin/env python3
"""Elm Lab rebrand of the phyphox iOS source (GPL-3.0), after tools/elmlab/rebrand.py of the
Android fork (github.com/Abbasovel/phyphox-android, branch elmlab).
Run from the repository root:  python3 tools/elmlab/rebrand_ios.py   (needs Pillow)
Idempotent. Keeps the phyphox/RWTH attribution texts (credits, GPL notice) intact,
replaces the phyphox and RWTH logos (registered trademarks), the product name and the orange."""
import re, math, json, pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = ROOT / "phyphox-iOS/phyphox"
ASSETS = APP / "Assets.xcassets"
FONTS = pathlib.Path(__file__).resolve().parent / "fonts"
NAME = "Elm Lab"
NAVY, NAVY2, GRID, BLUE, RED, WHITE, MUTED, INK = (14,24,38), (20,34,51), (43,63,88), (122,170,255), (255,123,111), (255,255,255), (154,170,189), (20,36,59)
PRIMARY = (0x2f, 0x6f, 0xd6)  # Android phyphox_primary in the Elm Lab fork

def font(name, size): return ImageFont.truetype(str(FONTS / name), size)

# ---------- icon art (same drawing as Android) ----------
def art(S, box, im=None, bg=None):
    """Draw grid + decaying sine inside box=(x0,y0,x1,y1) on an S*S RGBA image."""
    im = im or Image.new("RGBA", (S, S), bg or (0,0,0,0)); d = ImageDraw.Draw(im)
    x0,y0,x1,y1 = box; w = x1-x0; lw = max(1, S//160)
    for i in range(7):
        x = x0 + i*w/6; y = y0 + i*w/6
        d.line([(x,y0),(x,y1)], fill=GRID, width=lw); d.line([(x0,y),(x1,y)], fill=GRID, width=lw)
    r = max(2, S//52)
    for i in range(3001):
        t = i/3000; x = x0 + t*w
        y = (y0+y1)/2 - math.sin(t*2*math.pi*1.5)*math.exp(-1.2*t)*(w/2)*0.85
        d.ellipse([x-r,y-r,x+r,y+r], fill=BLUE)
    R = S//20; d.ellipse([x0-R,(y0+y1)/2-R,x0+R,(y0+y1)/2+R], fill=RED)
    return im

def app_icon():
    """iOS masks the corners itself, so the icon is a full opaque square (no alpha allowed)."""
    S = 4096
    big = art(S, (S*0.2,S*0.2,S*0.8,S*0.8), bg=NAVY+(255,)).convert("RGB")
    d = ASSETS / "AppIcon.appiconset"
    for img in json.loads((d / "Contents.json").read_text())["images"]:
        f = img.get("filename")
        if not f: continue
        n = round(float(img["size"].split("x")[0]) * int(img.get("scale", "1x")[:-1]))
        big.resize((n, n), Image.LANCZOS).save(d / f)

# ---------- logos ----------
def wordmark(d, x, baseline, size):
    fb = font("IBMPlexSansCondensed-Bold.ttf", size)
    d.text((x, baseline), "Elm", font=fb, fill=WHITE, anchor="ls")
    d.text((x + d.textlength("Elm ", font=fb), baseline), "Lab", font=fb, fill=BLUE, anchor="ls")
    return d.textlength("Elm Lab", font=fb)

def header_png():
    """Main-screen title image (was the phyphox wordmark), 718x192."""
    W,H = 718*2, 192*2
    im = Image.new("RGBA",(W,H),NAVY+(255,)); d = ImageDraw.Draw(im)
    sq = Image.new("RGBA",(H,H),NAVY2+(255,)); art(H,(H*0.16,H*0.16,H*0.84,H*0.84),im=sq); im.paste(sq,(0,0))
    x = H + 44; wordmark(d, x, 262, 238)
    d.text((x+4, 350), "fizika təcrübələri telefonla", font=font("IBMPlexSans-Regular.ttf", 58), fill=MUTED, anchor="ls")
    im.resize((718, 192), Image.LANCZOS).save(ASSETS / "phyphox_dark.imageset/phyphox_dark.png")

def launch_png():
    """Launch screen logo (was the phyphox + RWTH stack), 827x666 on the dark launch background."""
    W,H = 827*2, 666*2
    im = Image.new("RGBA",(W,H),(0,0,0,0)); d = ImageDraw.Draw(im)
    S = 760; sq = Image.new("RGBA",(S,S),(0,0,0,0))
    m = Image.new("L",(S,S),0); ImageDraw.Draw(m).rounded_rectangle([0,0,S-1,S-1], radius=S*0.18, fill=255)
    sq.paste(art(S,(S*0.2,S*0.2,S*0.8,S*0.8),bg=NAVY+(255,)),(0,0),m); im.paste(sq,((W-S)//2,0),sq)
    fb = font("IBMPlexSansCondensed-Bold.ttf", 330); w = d.textlength("Elm Lab", font=fb)
    wordmark(d, (W-w)/2, H-60, 330)
    im.resize((827, 666), Image.LANCZOS).save(ASSETS / "logo_stack.imageset/logo_stack.png")

def museum_png():
    """Credits logo (was RWTH), 827x378: Interaktiv Elm Muzeyi."""
    W,H = 827*2, 378*2
    im = Image.new("RGBA",(W,H),(0,0,0,0)); d = ImageDraw.Draw(im)
    d.text((W/2, 300), "İnteraktiv", font=font("IBMPlexSans-SemiBold.ttf", 150), fill=INK+(255,), anchor="ms")
    d.text((W/2, 610), "Elm Muzeyi", font=font("IBMPlexSansCondensed-Bold.ttf", 270), fill=INK+(255,), anchor="ms")
    im.resize((827, 378), Image.LANCZOS).save(ASSETS / "rwth.imageset/rwth_rgb.png")

# ---------- colour ----------
def colours():
    p = APP / "Constants.swift"; s = p.read_text(encoding="utf-8")
    r,g,b = PRIMARY
    s = re.sub(r"let kHighlightColor = UIColor\([^\n]*\)",
               f"let kHighlightColor = UIColor(red: ({r}.0/255.0), green: ({g}.0/255.0), blue: ({b}.0/255.0), alpha: 1.0)", s)
    p.write_text(s, encoding="utf-8")
    c = APP / "color.xcassets/highlightColor.colorset/Contents.json"; j = json.loads(c.read_text())
    for e in j["colors"]:
        e["color"]["components"].update({"red": str(r), "green": str(g), "blue": str(b)})
    c.write_text(json.dumps(j, indent=2) + "\n")

# ---------- strings ----------
KEEP = {"creditsRWTH","gpl","categoryPhyphoxOrg","categoryPhyphoxOrgHint"}
WORD = re.compile(r'(?<![\w./:@#-])[Pp]hyphox(?![\w®]|\.org|\.[a-z])')
ENTRY = re.compile(r'^("([^"]+)"\s*=\s*")((?:[^"\\]|\\.)*)(";)', re.M)
def strings():
    for p in sorted(APP.glob("*.lproj/*.strings")):
        s = p.read_text(encoding="utf-8")
        def fix(m):
            name, body = m.group(2), m.group(3)
            if name in ("app_name","title_activity_experiment"): return f'{m.group(1)}{NAME}{m.group(4)}'
            if name in KEEP or name.startswith("elmlab") or name.endswith("URL") or name.endswith("_url"): return m.group(0)
            return m.group(1) + WORD.sub(NAME, body) + m.group(4)
        s2 = ENTRY.sub(fix, s)
        # grammar after the rename, as on Android
        if p.parent.name == "tr.lproj": s2 = s2.replace(f"{NAME}'t", f"{NAME}'d").replace(f"{NAME}'u", f"{NAME}'ı")
        if p.parent.name == "en.lproj": s2 = re.sub(rf"\b([Aa]) {NAME}", rf"\1n {NAME}", s2)
        if s2 != s: p.write_text(s2, encoding="utf-8")

if __name__ == "__main__":
    app_icon(); header_png(); launch_png(); museum_png(); colours(); strings()
    print("Elm Lab rebrand applied")
