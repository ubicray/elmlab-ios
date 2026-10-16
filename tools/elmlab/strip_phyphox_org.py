#!/usr/bin/env python3
"""Elm Lab: remove references to the phyphox.org website and phyphox branding from the git submodules
(experiments, remote-access web interface), and add the museum's demo experiments. After the script of
the same name in the Android fork. Run from the repository root; the release workflow runs it before
the archive, so the submodules themselves stay untouched upstream checkouts.
- experiments of the special "phyphox.org" category (support / sensor database) are deleted
- <link> elements pointing to phyphox.org are removed (root and translation blocks)
- the demo experiments in tools/elmlab/demo_experiments are copied into the experiment collection
- the web interface gets the Elm Lab logo and colours"""
import re, pathlib, shutil
ROOT = pathlib.Path(__file__).resolve().parents[2]
EXP = ROOT / "phyphox-experiments"
WEB = ROOT / "phyphox-webinterface"
DEMOS = ROOT / "tools/elmlab/demo_experiments"
deleted = links = 0
for p in EXP.rglob("*.phyphox"):
    s = p.read_text(encoding="utf-8")
    if "<category>phyphox.org</category>" in s:
        p.unlink(); deleted += 1; continue
    s2, n = re.subn(r'\s*<link\b[^>]*>[^<]*phyphox\.org[^<]*</link>', '', s)
    if n: p.write_text(s2, encoding="utf-8"); links += n
left = [p.name for p in EXP.rglob("*.phyphox") if "phyphox.org" in p.read_text(encoding="utf-8")]
print(f"experiments: {deleted} deleted, {links} phyphox.org links removed, left: {left}")
for p in sorted(DEMOS.glob("*.phyphox")):
    shutil.copy(p, EXP / f"elmlab_demo_{p.name}")
print(f"demo experiments added: {len(list(DEMOS.glob('*.phyphox')))}")
if WEB.is_dir():
    shutil.copy(ROOT / "tools/elmlab/assets/webinterface_logo.png", WEB / "phyphox_orange.png")
    css = WEB / "style.css"; c = css.read_text(encoding="utf-8")
    css.write_text(re.sub(r'#ff7e22', '#2f6fd6', c, flags=re.I), encoding="utf-8")
    idx = WEB / "index.html"; h = idx.read_text(encoding="utf-8")
    idx.write_text(h.replace("The phyphox session has changed", "The Elm Lab session has changed"), encoding="utf-8")
