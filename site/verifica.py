# -*- coding: utf-8 -*-
"""Revisao do site no ar: confere se tudo que deveria estar funcionando esta.

Usa so a biblioteca padrao do Python, de proposito: assim roda na nuvem sem
instalar nada e sem depender do computador do Marcelo.

Rode com:  python site/verifica.py

Codigo de saida:
  0  tudo certo
  1  problema que a republicacao resolve (o que esta no ar saiu do lugar)
  2  problema que precisa de gente olhar
"""
import io
import json
import os
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

SITE = "https://tiburciotrader.com.br"
AQUI = os.path.dirname(os.path.abspath(__file__))
PUBLICO = os.path.join(AQUI, "public")

# Sinais de que o conteudo essencial continua na pagina. Se algum sumir, alguem
# mexeu em algo importante ou a publicacao saiu pela metade.
MARCOS = [
    ("link da comunidade no WhatsApp", "chat.whatsapp.com/"),
    ("perfil do Instagram", "instagram.com/tiburcio_trader"),
    ("canal do YouTube", "youtube.com/@tiburcio_trader"),
    ("destino da lista de espera", "/formResponse"),
    ("politica de privacidade", "privacidade.html"),
    ("aviso de risco", "Aviso de risco"),
]

FORMULARIO = ("https://docs.google.com/forms/d/e/"
              "1FAIpQLSe9rUcI9AwFwE7L04fhOky1FFFN4cd94h1xdj_Y4fIxkaThKw/viewform")
CAMPOS_FORMULARIO = ["1609997170", "963372110", "255066339"]

CABECALHO = {"User-Agent": "revisao-tiburciotrader/1.0", "Cache-Control": "no-cache"}

achados = []


def anota(nome, ok, detalhe, reparavel=False):
    achados.append({"verificacao": nome, "ok": ok, "detalhe": detalhe,
                    "reparavel_republicando": reparavel})
    print(("  ok   " if ok else "  FALHA") + "  " + nome + ("" if ok else " -> " + detalhe))


def busca(url, binario=False):
    req = urllib.request.Request(url, headers=CABECALHO)
    with urllib.request.urlopen(req, timeout=30) as r:
        dados = r.read()
        return r.status, (dados if binario else dados.decode("utf-8", "replace"))


def confere_site_no_ar():
    try:
        status, html = busca(SITE + "/?revisao=1")
        anota("site responde", status == 200, "codigo HTTP %d" % status)
        return html if status == 200 else None
    except Exception as e:
        anota("site responde", False, "nao consegui abrir: %s" % e)
        return None


def confere_igual_ao_repositorio(html):
    """O gh-pages entrega o arquivo cru, entao ele tem que ser identico ao commitado."""
    caminho = os.path.join(PUBLICO, "index.html")
    if not os.path.exists(caminho):
        anota("pagina igual ao repositorio", False, "nao achei %s" % caminho)
        return
    local = io.open(caminho, encoding="utf-8").read().replace("\r\n", "\n")
    # a pagina no ar e buscada com ?revisao=1, o conteudo em si nao muda
    vivo = html.replace("\r\n", "\n")
    igual = local.strip() == vivo.strip()
    anota("pagina igual ao repositorio", igual,
          "o que esta no ar difere do commitado (%d vs %d caracteres)" % (len(vivo), len(local)),
          reparavel=True)


def confere_marcos(html):
    faltando = [nome for nome, trecho in MARCOS if trecho not in html]
    anota("conteudo essencial presente", not faltando,
          "sumiram: " + ", ".join(faltando) if faltando else "")


def confere_recursos(html):
    """Toda imagem e arquivo citado tem que responder. Foi assim que a arte da
    comunidade sumiu: o endereco estava na pagina, mas o arquivo nao chegava."""
    enderecos = sorted(set(re.findall(r'(?:src|href)="(/[^"#?]+\.(?:jpg|jpeg|png|webp|svg|css|js|html))"', html)))
    if not enderecos:
        anota("recursos da pagina", False, "nao encontrei nenhum arquivo citado na pagina")
        return
    quebrados, divergentes = [], []
    for caminho in enderecos:
        try:
            status, dados = busca(SITE + caminho, binario=True)
            if status != 200:
                quebrados.append("%s (HTTP %d)" % (caminho, status))
                continue
            no_repo = os.path.join(PUBLICO, caminho.lstrip("/"))
            if os.path.exists(no_repo) and os.path.getsize(no_repo) != len(dados):
                divergentes.append("%s (%d bytes no ar, %d no repositorio)"
                                   % (caminho, len(dados), os.path.getsize(no_repo)))
        except Exception as e:
            quebrados.append("%s (%s)" % (caminho, e))

    anota("todos os %d arquivos da pagina respondem" % len(enderecos),
          not quebrados, "; ".join(quebrados),
          reparavel=all(os.path.exists(os.path.join(PUBLICO, c.split(" ")[0].lstrip("/")))
                        for c in quebrados) if quebrados else False)
    if divergentes:
        anota("arquivos iguais aos do repositorio", False, "; ".join(divergentes), reparavel=True)


def confere_privacidade():
    try:
        status, _ = busca(SITE + "/privacidade.html")
        anota("pagina de privacidade", status == 200, "codigo HTTP %d" % status, reparavel=True)
    except Exception as e:
        anota("pagina de privacidade", False, str(e), reparavel=True)


def confere_formulario():
    """A lista de espera depende desse formulario continuar publico e com os
    mesmos campos. Nao envia nada: so le, para nao sujar a planilha."""
    try:
        status, html = busca(FORMULARIO)
        if status != 200:
            anota("formulario da lista de espera", False, "codigo HTTP %d" % status)
            return
        faltando = [c for c in CAMPOS_FORMULARIO if c not in html]
        anota("formulario da lista de espera", not faltando,
              "campos que nao achei: " + ", ".join(faltando) if faltando else "")
    except Exception as e:
        anota("formulario da lista de espera", False, str(e))


def confere_certificado():
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection(("tiburciotrader.com.br", 443), timeout=20) as s:
            with ctx.wrap_socket(s, server_hostname="tiburciotrader.com.br") as ss:
                vence = ss.getpeercert()["notAfter"]
        data = datetime.strptime(vence, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        dias = (data - datetime.now(timezone.utc)).days
        anota("certificado HTTPS", dias > 14, "vence em %d dias (%s)" % (dias, vence))
    except Exception as e:
        anota("certificado HTTPS", False, str(e))


def main():
    print("Revisando %s\n" % SITE)
    html = confere_site_no_ar()
    if html:
        confere_igual_ao_repositorio(html)
        confere_marcos(html)
        confere_recursos(html)
    confere_privacidade()
    confere_formulario()
    confere_certificado()

    falhas = [a for a in achados if not a["ok"]]
    relatorio = {
        "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "site": SITE,
        "tudo_ok": not falhas,
        "so_precisa_republicar": bool(falhas) and all(a["reparavel_republicando"] for a in falhas),
        "verificacoes": achados,
    }
    io.open(os.path.join(AQUI, "..", "relatorio-revisao.json"), "w", encoding="utf-8").write(
        json.dumps(relatorio, ensure_ascii=False, indent=2))

    print()
    if not falhas:
        print("Tudo certo: %d verificacoes, nenhuma falha." % len(achados))
        return 0
    print("%d de %d verificacoes falharam." % (len(falhas), len(achados)))
    if relatorio["so_precisa_republicar"]:
        print("Tudo o que falhou se resolve republicando o que ja esta no repositorio.")
        return 1
    print("Pelo menos uma falha precisa de gente olhando.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
