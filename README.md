# Garimpo de Motos — ABC abaixo da FIPE

Robô que varre o **OLX** procurando as motos mais procuradas do Grande ABC à venda
**abaixo da tabela FIPE**, e avisa por **e-mail** + uma **página web**.

Roda **sozinho na nuvem do GitHub** (não precisa de PC ligado, não gasta token de IA —
é código puro).

## O que ele faz

1. Busca no **OLX** os modelos da lista (`config/modelos.json`) no estado de SP.
2. Filtra: só cidades do ABC, **sem leilão/sinistro**, **km ≤ 30.000**.
3. Compara cada anúncio com a **Tabela FIPE** (API pública).
4. Guarda os que estão abaixo da FIPE no mínimo `desconto_min_pct` %.
5. Manda e-mail (só quando acha algo) e atualiza a página web.

### O truque pra rodar na nuvem
O OLX fica atrás da **Cloudflare**, que bloqueia IP de datacenter para robôs HTTP comuns
(`requests`/`curl` → erro 403). A saída: o robô usa um **navegador real** (Playwright +
Chromium headless), que resolve o desafio JavaScript da Cloudflare — e assim funciona até
do GitHub Actions, de graça. É por isso que o workflow instala o Chromium antes de rodar.

---

## Testar no seu PC (opcional)

```bash
pip install -r requirements.txt
python -m playwright install chromium
python src/garimpo.py
```

Só imprime os achados no terminal (não manda e-mail). Se o disco C: estiver cheio, aponte
o navegador pra outro drive: `set PLAYWRIGHT_BROWSERS_PATH=D:\.ms-playwright` antes de instalar.

---

## Colocar pra rodar sozinho (GitHub) — passo a passo

### 1. Repositório
Já está em `https://github.com/mariaritaboaretoo-eng/garimpo-motos-abc` (público → Actions
ilimitado de graça). Se for recriar, suba estes arquivos num repositório público.

### 2. E-mail — via Gmail (Senha de app)
Usa o SMTP do Gmail (manda pra qualquer destinatário de graça; o Resend só manda pra
qualquer um com domínio próprio verificado). Na conta Gmail que vai ENVIAR:
1. Ative a **Verificação em duas etapas** (Conta Google → Segurança).
2. Gere uma **Senha de app** (Segurança → Senhas de app) — 16 dígitos. **Não** é a senha normal.

### 3. Cadastrar os segredos (Settings → Secrets and variables → Actions)

| Nome | Valor | Obrigatório |
|------|-------|:-:|
| `GMAIL_USER` | o Gmail que envia (ex: `criativaria.contato@gmail.com`) | sim (p/ e-mail) |
| `GMAIL_APP_PASSWORD` | a Senha de app de 16 dígitos | sim (p/ e-mail) |
| `EMAIL_PARA` | o e-mail dele (destino) | sim (p/ e-mail) |
| `SITE_URL` | link da página (passo 5) | opcional |

> Sem esses secrets o robô ainda roda e atualiza a página — só não manda e-mail.
> O robô roda 2×/dia: **09:00** (página + e-mail) e **12:00** (só página). Horários em `.github/workflows/garimpo.yml`.

### 4. Ligar o robô
Aba **Actions** → habilite os workflows → **Garimpo de Motos** → **Run workflow**.
Depois roda sozinho todo dia às 08:00 (BRT).

### 5. Página web (GitHub Pages)
**Settings → Pages → Deploy from a branch → `main` / pasta `/docs`**. Fica em
`https://mariaritaboaretoo-eng.github.io/garimpo-motos-abc/`. Ponha o link no secret `SITE_URL`.

---

## Ajustar (arquivo `config/modelos.json`)

- `km_max`: quilometragem máxima (padrão 30.000).
- `desconto_min_pct`: quão abaixo da FIPE pra alertar. **5** (padrão) pega oportunidades
  reais de km baixa; **0** mostra tudo abaixo da FIPE; **8–10** só gemas raras.
- `paginas_por_busca`: quantas páginas do OLX varrer por modelo (mais = mais cobertura, mais lento).
- `modelos`: cada moto tem `busca_olx` (o que buscar), `fipe_marca` (marca na FIPE) e
  `fipe_tokens` (termos que travam o modelo certo na FIPE — ex: `pcx` impede casar PCX com ADV).

Lista atual = campeões de emplacamento no Brasil/SP (proxy real de "mais procuradas"):
CG 160, Biz, PCX, Bros, XRE 300, Elite, Factor 150, Fazer 250, NMAX, Crosser, Lander.

---

## Observações honestas

- O casamento anúncio → versão da FIPE é **aproximado** — confira a versão no anúncio.
- É um **radar de oportunidades**, não recomendação de compra.
- Fontes avaliadas: **OLX** (escolhida — rica, com particular; furada via navegador),
  **Mercado Livre** (exige token de app), **Webmotors** (captcha pesado), **Mobiauto**
  (só loja → raramente abaixo da FIPE), **usadosbr** (nuvem ok, mas inventário pequeno no ABC).
