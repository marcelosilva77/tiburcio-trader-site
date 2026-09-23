# Site Tibúrcio Trader

Página de apresentação do Ramon Tibúrcio (campeão Expert Trader XP), com foco em B3 (WIN/WDO)
e direcionamento para a plataforma de estudo.

## Endereços

- **Site oficial: https://tiburciotrader.com.br** (www redireciona; HTTPS obrigatório)
- Repositório: https://github.com/marcelosilva77/tiburcio-trader-site (público; serve as fotos)
- Prévia no Claude: https://claude.ai/code/artifact/ce8ddf24-2b36-42a1-ad3e-6f26b3966d45

Hospedagem: GitHub Pages (branch `gh-pages` = conteúdo de `site/public`).
DNS no Registro.br em **modo avançado**: 4 registros A (185.199.108/109/110/111.153)
e CNAME `www` apontando para `marcelosilva77.github.io`.

### Para republicar depois de mudar algo

```bash
cd "C:\Users\marce\PROJETO B3" && python site\build.py && git add -A && git commit -m "atualiza site" && git push && git subtree split --prefix site/public -b gh-pages && git push -f origin gh-pages
```

## Pastas

- `site/index.template.html` — o site (edite aqui textos, cores e links).
- `site/build.py` — gera o `site/index.html` final embutindo as fotos já tratadas.
- `site/fotos/` — coloque as fotos originais aqui com estes nomes:
  - `hero.jpg` → foto no Expert Trader XP (com o crachá).
  - `b3.jpg` → foto no estande da B3.
  - `avatar.jpg` → foto de perfil (opcional; se faltar, usa a `hero.jpg`).
- `site/index.html` — versão para o Artifact do Claude (gerado, não edite à mão).
- `site/public/index.html` — site completo, é este que vai para a Vercel (gerado).

## Como gerar o site depois de colocar as fotos

```bash
python "C:\Users\marce\PROJETO B3\site\build.py"
```

O script corrige a orientação, recorta na proporção certa, dá um leve tratamento
(contraste, cor e nitidez) e salva cópias em `site/fotos/tratadas/`.

## Links para trocar

No final do `index.template.html`, no bloco `LINKS`:

- `plataforma` → URL da plataforma de estudo ou do checkout (ex.: link da Lastlink).
- `whatsapp` → `https://wa.me/55DDDNUMERO`.
- `email` → `mailto:...`.

Depois de trocar, rode o `build.py` de novo.

## Pendências de conteúdo

- Confirmar o título exato da competição (ano e nome da arena) com o Ramon.
- CNPJ real no rodapé.
- Logo definitiva (hoje é um monograma "T" dourado provisório).
- Preço e condições do curso (o card "Turma aberta" está sem valor de propósito).
