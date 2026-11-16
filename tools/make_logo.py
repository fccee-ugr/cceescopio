"""Logo de CCEEscopio (SVG + PNG). Colores de la Facultad de CC. Económicas y Empresariales (UGR)."""
import subprocess, os
OR, MG, GR = "#F29200", "#B5175F", "#3C3C3B"
os.makedirs("images/brand", exist_ok=True)

def icon(x=0, y=0, s=1.0, bg=None):
    """Lupa naranja con barras crecientes magenta y línea de tendencia."""
    g = [f'<g transform="translate({x},{y}) scale({s})">']
    if bg: g.append(f'<rect width="200" height="200" rx="36" fill="{bg}"/>')
    g += [
        # mango
        f'<line x1="128" y1="128" x2="178" y2="178" stroke="{MG}" stroke-width="22" stroke-linecap="round"/>',
        # lente
        f'<circle cx="86" cy="86" r="66" fill="#fff" stroke="{OR}" stroke-width="16"/>',
        # barras
        f'<rect x="50" y="98" width="15" height="28" rx="3" fill="{MG}"/>',
        f'<rect x="72" y="82" width="15" height="44" rx="3" fill="{MG}"/>',
        f'<rect x="94" y="66" width="15" height="60" rx="3" fill="{MG}"/>',
        f'<rect x="116" y="74" width="15" height="52" rx="3" fill="{MG}" opacity=".55"/>',
        # tendencia
        f'<polyline points="50,86 72,70 94,54 124,48" fill="none" stroke="{OR}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>',
        f'<circle cx="124" cy="48" r="7" fill="{OR}"/>',
        '</g>']
    return "\n".join(g)

FONT = "font-family=\"'Source Sans 3','Segoe UI',Inter,Arial,sans-serif\""
def wordmark(x, y, size, tag=True, dark=False):
    c1 = MG
    c2 = "#ffffff" if dark else GR
    t = [f'<text x="{x}" y="{y}" {FONT} font-size="{size}" font-weight="800" fill="{c1}">CCEE<tspan fill="{c2}" font-weight="600">scopio</tspan></text>']
    if tag:
        t.append(f'<text x="{x+4}" y="{y+size*0.55}" {FONT} font-size="{size*0.30}" font-weight="600" fill="{OR}">Observando la economía y la empresa</text>')
    return "\n".join(t)

def svg(w, h, body, bg=None):
    b = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{b}\n{body}\n</svg>'

files = {
    "cceescopio_logo.svg": svg(980, 240, icon(10, 20, 1.0) + wordmark(235, 140, 120)),
    "cceescopio_logo_negativo.svg": svg(980, 240, icon(10, 20, 1.0) + wordmark(235, 140, 120, dark=True), bg="#1E1E2A"),
    "cceescopio_navbar.svg": svg(760, 200, icon(0, 0, 1.0) + wordmark(220, 132, 118, tag=False)),
    "cceescopio_icono.svg": svg(200, 200, icon(0, 0, 1.0)),
}
for f, s in files.items():
    open(f"images/brand/{f}", "w").write(s)
for f, w in [("cceescopio_logo", 1960), ("cceescopio_logo_negativo", 1960), ("cceescopio_navbar", 760), ("cceescopio_icono", 512)]:
    subprocess.run(["rsvg-convert", "-w", str(w), f"images/brand/{f}.svg", "-o", f"images/brand/{f}.png"], check=True)
print("ok")
