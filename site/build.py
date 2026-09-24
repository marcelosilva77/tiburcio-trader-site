"""Gera site/index.html a partir de index.template.html embutindo as fotos tratadas.

Uso:  python build.py
Fotos esperadas em site/fotos/ (qualquer um destes nomes, jpg/jpeg/png):
  sobre.*  -> foto da secao Sobre (Expert Trader XP)  -> {{FOTO_B3}}
  b3.*     -> alternativa: foto no estande da B3      -> {{FOTO_B3}}
  hero.*   -> ultimo recurso, se as duas faltarem
  hl-resultados.*, hl-analises.*, hl-fechamento.* -> capas dos destaques do Instagram (opcionais)
Se uma foto não existir, entra um placeholder dourado no lugar.
"""
import re, base64, io, glob, os, sys
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
# Base das fotos no site publicado. "fotos/" usa os arquivos ao lado do index.html (ideal quando a
# hospedagem servir os arquivos). A CDN do jsDelivr serve direto do repositório público.
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
    # foto da secao "Sobre": procura sobre.*, depois b3.*, e por fim hero.*
    sobre = find("sobre"); b3 = find("b3"); hero = find("hero")
    foto_sobre = sobre or b3 or hero

    if b3 and not sobre:
        stamp_sup, stamp = "Onde tudo acontece", "B3 · Bolsa do Brasil"
        alt_b3 = "Ramon Tibúrcio no estande da B3, a bolsa brasileira."
    else:
        stamp_sup, stamp = "Onde o título foi conquistado", "Expert Trader XP · Arena"
        alt_b3 = "Ramon Tibúrcio no evento Expert Trader XP."

    # (token, origem, nome publico, largura, proporcao, foco vertical, qualidade, rotulo)
    specs = [
        ("{{FOTO_B3}}", foto_sobre, "sobre.jpg", 900, (4, 3), 0.30, 78, "FOTO: EXPERT TRADER XP"),
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
    # Imagens de marca em public/img/: {{IMG:arquivo}} -> data URI no artifact, URL no site
    import re, mimetypes
    IMG_URL = FOTOS_URL.replace("/fotos/", "/img/")
    def img_uri(name):
        path = os.path.join(pub_dir, "img", name)
        mt = mimetypes.guess_type(name)[0] or "image/png"
        return "data:%s;base64,%s" % (mt, base64.b64encode(open(path, "rb").read()).decode())
    artifact_html = re.sub(r"\{\{IMG:([\w.\-]+)\}\}", lambda m: img_uri(m.group(1)), artifact_html)
    public_html = re.sub(r"\{\{IMG:([\w.\-]+)\}\}", lambda m: IMG_URL + m.group(1), public_html)
    # Destaques do Instagram: {{HL:nome|Rótulo|svg}} -> capa real se existir fotos/hl-nome.(jpg|png), senão ícone
    def hl(m, mode):
        name, label, svg = m.group(1), m.group(2), m.group(3)
        src = find("hl-" + name)
        if src:
            uri = treat(src, 160, (1, 1), 0.5, 80)
            raw = base64.b64decode(uri.split(",", 1)[1])
            open(os.path.join(pub_dir, "fotos", "hl-" + name + ".jpg"), "wb").write(raw)
            img = uri if mode == "artifact" else FOTOS_URL + "hl-" + name + ".jpg"
            return '<span><i><img src="%s" alt="" loading="lazy"></i>%s</span>' % (img, label)
        return ('<span><i class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                'stroke-linecap="round" stroke-linejoin="round">%s</svg></i>%s</span>' % (svg, label))
    HL = r"\{\{HL:([\w-]+)\|([^|]+)\|(.*?)\}\}"
    artifact_html = re.sub(HL, lambda m: hl(m, "artifact"), artifact_html)
    public_html = re.sub(HL, lambda m: hl(m, "public"), public_html)
    out = os.path.join(HERE, "index.html")
    open(out, "w", encoding="utf-8").write(artifact_html)
    print(f"\nGerado: {out} ({os.path.getsize(out)//1024} KB)  [fragmento para o Artifact do Claude]")
    # Versão completa (com <!doctype html>) para hospedar em qualquer servidor
    head_end = public_html.index("<div class=\"progress\"")
    full = ("<!doctype html>\n<html lang=\"pt-BR\">\n<head>\n" + public_html[:head_end] + "</head>\n<body>\n"
            + public_html[head_end:] + "\n</body>\n</html>\n")
    # trava: um comentario de CSS aberto e nao fechado engole as regras seguintes em silencio.
    # O sinal e um "/*" aparecendo dentro de um comentario: ele roubou o fecho do comentario seguinte.
    for bloco in re.findall("<style>(.*?)</style>", full, re.S):
        pos, suspeito = 0, None
        while True:
            a = bloco.find("/*", pos)
            if a < 0:
                break
            b = bloco.find("*/", a + 2)
            if b < 0 or bloco.find("/*", a + 2, b) >= 0:
                suspeito = a
                break
            pos = b + 2
        if suspeito is None and bloco.count("/*") == bloco.count("*/"):
            continue
        if suspeito is None:
            suspeito = bloco.rfind("/*")
        linha = bloco.count(chr(10), 0, suspeito) + 1
        raise SystemExit("ERRO: comentario de CSS aberto e nao fechado na linha %d do <style> "
                         "(linha %d do template). Tudo depois dele para de valer no navegador. "
                         "Feche o comentario e rode de novo." % (linha, linha + 15))

    pub = os.path.join(pub_dir, "index.html")
    open(pub, "w", encoding="utf-8").write(full)
    print(f"Gerado: {pub} ({os.path.getsize(pub)//1024} KB)  [site completo para publicar]")
    if not foto_sobre:
        print("\nAVISO: nenhuma foto em site/fotos/ (sobre.*, b3.* ou hero.*). Placeholder usado.")


if __name__ == "__main__":
    main()
