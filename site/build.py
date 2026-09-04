"""Gera site/index.html a partir de index.template.html embutindo as fotos tratadas.

Uso:  python build.py
Fotos esperadas em site/fotos/ (qualquer um destes nomes, jpg/jpeg/png):
  hero.*   -> foto no Expert Trader XP (crachá)   -> {{FOTO_HERO}}
  b3.*     -> foto no estande da B3               -> {{FOTO_B3}}
  avatar.* -> foto de perfil (opcional; se faltar usa a hero) -> {{FOTO_AVATAR}}
Se uma foto não existir, entra um placeholder dourado no lugar.
"""
import base64, io, glob, os, sys
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
# Base das fotos no site publicado. "fotos/" usa os arquivos ao lado do index.html (ideal quando a
# Vercel estiver ligada ao GitHub). A CDN do jsDelivr serve direto do repositório público.
FOTOS_URL = os.environ.get("FOTOS_URL", "https://cdn.jsdelivr.net/gh/marcelosilva77/tiburcio-trader-site@main/site/public/fotos/")
FOTOS = os.path.join(HERE, "fotos")
OUT_FOTOS = os.path.join(FOTOS, "tratadas")
os.makedirs(OUT_FOTOS, exist_ok=True)


def find(name):
    for ext in ("jpg", "jpeg", "png", "webp", "JPG", "JPEG", "PNG"):
        hits = glob.glob(os.path.join(FOTOS, f"{name}.{ext}"))
        if hits:
            return hits[0]
    return None


def treat(path, size, ratio, focus_y=0.30, quality=82):
    """Corrige orientação, recorta na proporção pedida, dá um leve tratamento e devolve data URI."""
    im = Image.open(path)
    im = ImageOps.exif_transpose(im).convert("RGB")
    w, h = im.size
    target = ratio[0] / ratio[1]
    if w / h > target:  # larga demais -> corta laterais
        nw = int(h * target); x0 = (w - nw) // 2; im = im.crop((x0, 0, x0 + nw, h))
    else:               # alta demais -> corta topo/base com foco no rosto
        nh = int(w / target); y0 = int((h - nh) * focus_y); im = im.crop((0, y0, w, y0 + nh))
    im.thumbnail((size, size * 2), Image.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(1.05)
    im = ImageEnhance.Brightness(im).enhance(1.02)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=3))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    out = os.path.join(OUT_FOTOS, os.path.splitext(os.path.basename(path))[0] + "_tratada.jpg")
    with open(out, "wb") as f: f.write(buf.getvalue())
    print(f"  {os.path.basename(path)} -> {os.path.relpath(out, HERE)} ({im.size[0]}x{im.size[1]}, {len(buf.getvalue())//1024} KB)")
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def placeholder(label, ratio):
    w, h = 800, int(800 * ratio[1] / ratio[0])
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>
<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#1a1608'/><stop offset='1' stop-color='#0e0e14'/></linearGradient></defs>
<rect width='{w}' height='{h}' fill='url(#g)'/>
<circle cx='{w/2}' cy='{h*0.38}' r='{w*0.16}' fill='none' stroke='#ffd11a' stroke-opacity='.5' stroke-width='3'/>
<path d='M{w*0.22} {h*0.78} Q{w/2} {h*0.5} {w*0.78} {h*0.78}' fill='none' stroke='#ffd11a' stroke-opacity='.5' stroke-width='3'/>
<text x='{w/2}' y='{h*0.9}' text-anchor='middle' font-family='monospace' font-size='22' fill='#ffd11a' fill-opacity='.8'>{label}</text></svg>"""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def main():
    tpl = open(os.path.join(HERE, "index.template.html"), encoding="utf-8").read()
    print("Fotos:")
    hero = find("hero"); b3 = find("b3"); av = find("avatar") or hero
    # Enquanto não houver foto da B3, a segunda seção usa a foto do evento com um recorte
    # mais aberto (mostra o ambiente do Expert Trader XP) e o carimbo muda de texto.
    if b3:
        b3_src, b3_focus = b3, 0.25
        stamp_sup, stamp, alt_b3 = "Onde tudo acontece", "B3 · Bolsa do Brasil", "Ramon Tibúrcio no estande da B3, a bolsa brasileira."
    else:
        b3_src, b3_focus = hero, 0.42
        stamp_sup, stamp, alt_b3 = "Onde o título foi conquistado", "Expert Trader XP · Arena", "Ramon Tibúrcio na arena de competidores do Expert Trader XP."

    # (token, arquivo de origem, nome público, tamanho, proporção, foco vertical, qualidade, rótulo do placeholder)
    specs = [
        ("{{FOTO_HERO}}",   hero,   "hero.jpg",   660, (4, 5), 0.18,    72, "FOTO: EXPERT TRADER XP"),
        ("{{FOTO_B3}}",     b3_src, "b3.jpg",     620, (3, 4), b3_focus, 72, "FOTO: B3"),
        ("{{FOTO_AVATAR}}", av,     "avatar.jpg", 160, (1, 1), 0.12,    80, ""),
    ]
    pub_dir = os.path.join(HERE, "public"); os.makedirs(os.path.join(pub_dir, "fotos"), exist_ok=True)
    tpl = (tpl.replace("{{STAMP_B3_SUP}}", stamp_sup)
              .replace("{{STAMP_B3}}", stamp)
              .replace("{{ALT_B3}}", alt_b3))
    artifact_html, public_html = tpl, tpl
    for token, src, name, size, ratio, focus, q, label in specs:
        if src:
            uri = treat(src, size, ratio, focus, q)
            raw = base64.b64decode(uri.split(",", 1)[1])
            open(os.path.join(pub_dir, "fotos", name), "wb").write(raw)
            artifact_html = artifact_html.replace(token, uri)
            public_html = public_html.replace(token, FOTOS_URL + name)   # arquivo separado (site mais leve)
        else:
            ph = placeholder(label, ratio)
            artifact_html = artifact_html.replace(token, ph)
            public_html = public_html.replace(token, ph)
    out = os.path.join(HERE, "index.html")
    open(out, "w", encoding="utf-8").write(artifact_html)
    print(f"\nGerado: {out} ({os.path.getsize(out)//1024} KB)  [fragmento para o Artifact do Claude]")
    # Versão completa (com <!doctype html>) para hospedar na Vercel ou em qualquer servidor
    head_end = public_html.index("<div class=\"progress\"")
    full = ("<!doctype html>\n<html lang=\"pt-BR\">\n<head>\n" + public_html[:head_end] + "</head>\n<body>\n"
            + public_html[head_end:] + "\n</body>\n</html>\n")
    pub = os.path.join(pub_dir, "index.html")
    open(pub, "w", encoding="utf-8").write(full)
    print(f"Gerado: {pub} ({os.path.getsize(pub)//1024} KB)  [site completo para publicar]")
    if not hero:
        print("\nAVISO: falta site/fotos/hero.jpg. Placeholder dourado foi usado.")
    if not b3:
        print("\nAVISO: falta site/fotos/b3.jpg. A segunda secao esta usando a foto do evento\n"
              "       com recorte aberto. Salve a foto da B3 nesse caminho e rode de novo.")


if __name__ == "__main__":
    main()
