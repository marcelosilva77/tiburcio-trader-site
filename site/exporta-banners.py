# -*- coding: utf-8 -*-
"""Exporta as artes dos canais para o site, no peso certo.

Origem:  site/banners/<nome>-original.png   (arte intacta, nunca editar)
Destino: site/public/img/banner-<nome>.jpg  (o que o site entrega)

As artes aparecem com cerca de 490 px de largura no computador e 343 px no
celular. Exportar com 1000 px cobre telas retina (o dobro do tamanho exibido)
e corta pela metade o peso do arquivo. Isso muda apenas o peso: o desenho da
arte nao e alterado.

Rode com:  python exporta-banners.py
"""
import os
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGENS = os.path.join(AQUI, "banners")
DESTINO = os.path.join(AQUI, "public", "img")

LARGURA = 1000
QUALIDADE = 82

ARTES = ["comunidade", "instagram", "youtube", "mentoria"]


def kb(caminho):
    return os.path.getsize(caminho) // 1024


def main():
    os.makedirs(DESTINO, exist_ok=True)
    total_antes = total_depois = 0
    faltando = []

    for nome in ARTES:
        origem = os.path.join(ORIGENS, nome + "-original.png")
        destino = os.path.join(DESTINO, "banner-" + nome + ".jpg")
        if not os.path.exists(origem):
            faltando.append(origem)
            continue

        antes = kb(destino) if os.path.exists(destino) else 0
        im = Image.open(origem).convert("RGB")
        largura, altura = im.size
        nova_altura = round(altura * LARGURA / largura)
        im = im.resize((LARGURA, nova_altura), Image.LANCZOS)
        im.save(destino, "JPEG", quality=QUALIDADE, optimize=True, progressive=True)

        depois = kb(destino)
        total_antes += antes
        total_depois += depois
        economia = (100 - 100 * depois // antes) if antes else 0
        print("  %-12s %4dx%-4d -> %4dx%-4d   %4d KB -> %4d KB  (-%d%%)"
              % (nome, largura, altura, LARGURA, nova_altura, antes, depois, economia))

    if faltando:
        print("\nAVISO: nao encontrei estes originais:")
        for f in faltando:
            print("   " + f)

    if total_antes:
        print("\n  total: %d KB -> %d KB  (-%d%%)"
              % (total_antes, total_depois, 100 - 100 * total_depois // total_antes))
    print("\nAgora rode build.py e publique.")


if __name__ == "__main__":
    main()
