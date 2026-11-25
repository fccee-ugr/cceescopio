"""Logo de CCEEscopio D+I con el lema (SVG + PNG): python tools/make_logo_di.py"""
import subprocess, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OR, MG, GR = "#F29200", "#B5175F", "#3C3C3B"
FONT = "font-family=\"Inter,'Source Sans 3','Segoe UI',Arial,sans-serif\""
LEMA = ("Observatorio de indicadores económicos y empresariales",
        "al servicio de la Docencia y la Investigación")

def icon(x, y, s):
    return f'''<g transform="translate({x},{y}) scale({s})">
<line x1="128" y1="128" x2="178" y2="178" stroke="{MG}" stroke-width="22" stroke-linecap="round"/>
<circle cx="86" cy="86" r="66" fill="#fff" stroke="{OR}" stroke-width="16"/>
<rect x="50" y="98" width="15" height="28" rx="3" fill="{MG}"/>
<rect x="72" y="82" width="15" height="44" rx="3" fill="{MG}"/>
<rect x="94" y="66" width="15" height="60" rx="3" fill="{MG}"/>
<rect x="116" y="74" width="15" height="52" rx="3" fill="{MG}" opacity=".55"/>
<polyline points="50,86 72,70 94,54 124,48" fill="none" stroke="{OR}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="124" cy="48" r="7" fill="{OR}"/></g>'''

W, H = 2000, 440
body = icon(25, 45, 1.65) + f'''
<text x="398" y="232" {FONT} font-size="190" font-weight="800" fill="{MG}" letter-spacing="-2">CCEE<tspan fill="{GR}" font-weight="600">scopio</tspan><tspan fill="{OR}" font-weight="800" dx="40">D+I</tspan></text>
<text x="404" y="330" {FONT} font-size="54" font-weight="600" fill="{OR}">{LEMA[0]}</text>
<text x="404" y="400" {FONT} font-size="54" font-weight="600" fill="{OR}">{LEMA[1]}</text>'''
svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{body}</svg>'
open("images/brand/cceescopio_logo_di.svg", "w").write(svg)
subprocess.run(["rsvg-convert", "-w", "2400", "images/brand/cceescopio_logo_di.svg", "-o", "images/brand/cceescopio_logo_di.png"], check=True)
print("ok")
