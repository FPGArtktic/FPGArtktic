#!/usr/bin/env python3
# gen-svg.py — regenerates assets/{boot,dir}-{day,night}.svg for the profile README.
#
# Inputs (positional):
#   1. a working directory that contains
#        theme/c64/      a clone of FPGArtktic/hugo-theme-c64-boot (palette + font)
#        repos.json      output of:
#          gh repo list FPGArtktic --limit 100 --json name,diskUsage,stargazerCount \
#            --jq 'map({(.name): {kb: .diskUsage, stars: .stargazerCount}}) | add'
#   2. the output directory (assets/)
#
# Colours come from the theme's 00-tokens.css (nice-city = day, nice-night = night);
# the font is the theme's bundled Press Start 2P (SIL OFL 1.1), embedded as base64.
# Block counts in the directory listing are real: repository size / 254 bytes.
# A repository GitHub reports as 0 KB (a new one, before GitHub computes its size)
# keeps the count already in the listing. .github/workflows/refresh-dir.yml runs this weekly.
import base64, json, math, re, sys, html
S = sys.argv[1]; OUT = sys.argv[2]
css = open(f"{S}/theme/c64/assets/css/00-tokens.css").read()
def pal(name):
    return dict(re.findall(rf"--p-{name}-([a-z0-9-]+):\s*(#[0-9a-f]{{6}})", css))
pals = {"day": pal("nice-city"), "night": pal("nice-night")}
font = base64.b64encode(open(f"{S}/theme/c64/static/fonts/PressStart2P-Regular.woff2","rb").read()).decode()
repos = json.load(open(f"{S}/repos.json"))

CELL, LINE, BORDER, COLS = 16, 24, 48, 40
W = COLS*CELL + 2*BORDER

def svg(lines, p, title):
    """lines: list of (text, role, t_appear_s, extras). role in text/bright/ok/accent"""
    H = len(lines)*LINE + 2*BORDER
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" xml:space="preserve" role="img" aria-label="{html.escape(title)}">',
           f'<title>{html.escape(title)}</title>',
           '<style>@font-face{font-family:"PS2P";src:url(data:font/woff2;base64,' + font + ') format("woff2")}'
           f'text{{font-family:"PS2P","Press Start 2P",monospace;font-size:{CELL}px;white-space:pre}}'
           f'.text{{fill:{p["text"]}}}.bright{{fill:{p["bright"]}}}.ok{{fill:{p["ok"]}}}.accent{{fill:{p["accent"]}}}.dim{{fill:{p["dim"]}}}'
           '@media (prefers-reduced-motion:reduce){.a{opacity:1!important}}</style>',
           f'<rect width="{W}" height="{H}" fill="{p["border"]}"/>',
           f'<rect x="{BORDER}" y="{BORDER}" width="{COLS*CELL}" height="{len(lines)*LINE}" fill="{p["screen"]}"/>']
    y0 = BORDER + LINE - 4
    for i, (text, role, t, cursor) in enumerate(lines):
        y = y0 + i*LINE
        attrs = f'class="a {role}" x="{BORDER}" y="{y}"'
        anim = ''
        if t is not None:
            attrs = f'class="a {role}" x="{BORDER}" y="{y}" opacity="0"'
            anim = f'<set attributeName="opacity" to="1" begin="{t}s" fill="freeze"/>'
        out.append(f'<text {attrs}>{html.escape(text)}{anim}</text>')
        if cursor is not None:
            cx = BORDER + len(text)*CELL
            cy = y - CELL + 2
            start, end = cursor
            out.append(f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" fill="{p["text"]}" opacity="0">'
                       f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" begin="{start}s" ' + (f'end="{end}s" fill="remove"' if end else 'repeatCount="indefinite"') + '/></rect>')
    out.append('</svg>')
    return "\n".join(out)

boot = [
 ("    **** COMMODORE 64 BASIC V2 ****", "bright", None, None),
 ("", "text", None, None),
 (" 64K RAM SYSTEM  38911 BASIC BYTES FREE", "bright", None, None),
 ("", "text", None, None),
 ("READY.", "text", 0.3, (0.3, 0.9)),
 ('LOAD"FPGARTKTIC",8,1', "text", 0.9, None),
 ("", "text", None, None),
 ("SEARCHING FOR FPGARTKTIC", "text", 1.6, None),
 ("LOADING", "ok", 1.9, None),
 ("READY.", "text", 2.6, None),
 ("RUN", "text", 2.8, (2.9, None)),
]

entries = [  # (repo, 1541 name)
 ("GnuRAMage","GNURAMAGE"), ("AutoGit-o-Matic","AUTOGIT-O-MATIC"), ("gpygap","GPYGAP"),
 ("podman_base","PODMAN-WRK"), ("shuttle-stack","SHUTTLE-STACK"), ("glosator","GLOSATOR"),
 ("tachygraf","TACHYGRAF"), ("weft-mcp","WEFT-MCP"), ("rtk-embedded-linux","RTK-EMBED-LINUX"),
 ("hyprtilt","HYPRTILT"),
 ("lazysubmodules","LAZYSUBMODULES"), ("ohmyzsh-mtsh-theme","MTSH-THEME"),
 ("setup-DotFiles","SETUP-DOTFILES"), ("hugo-theme-c64-boot","C64-BOOT-THEME"),
 ("copilot-export-json-to-markdown","COPILOT-TO-MD"),
]
try:
    prev = {n: int(b) for b, n in re.findall(r">(\d+) +&quot;(\S+) *&quot; PRG<", open(f"{OUT}/dir-day.svg").read())}
except FileNotFoundError:
    prev = {}
used = 0
dirlines =[('LOAD"$",8', "text", None, None), ("", "text", None, None),
            ("SEARCHING FOR $", "text", None, None), ("LOADING", "ok", None, None),
            ("READY.", "text", None, None), ("LIST", "text", None, None), ("", "text", None, None),
            ('0 "FPGARTKTIC      " 2A', "bright", None, None)]
for repo, name in entries:
    kb = repos[repo]["kb"]
    blocks = math.ceil(kb*1024/254) if kb else prev.get(name, 1)
    used += blocks
    dirlines.append((f'{blocks:<6}"{name:<16}" PRG', "text", None, None))
free = max(0, 664 - used)
dirlines += [(f"{free} BLOCKS FREE.", "bright", None, None), ("", "text", None, None), ("READY.", "text", None, (0, None))]

for k, p in pals.items():
    open(f"{OUT}/boot-{k}.svg","w").write(svg(boot, p, "Commodore 64 boot screen: LOAD FPGARTKTIC,8,1"))
    open(f"{OUT}/dir-{k}.svg","w").write(svg(dirlines, p, "1541 disk directory listing of FPGArtktic projects"))
print(json.dumps({k:{r:repos[r]["stars"] for r,_ in entries} for k in ["stars"]}, indent=0))
