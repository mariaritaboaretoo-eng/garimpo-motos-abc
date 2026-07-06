# Garimpo de Motos — ABC abaixo da FIPE

Robô que varre o OLX todo dia procurando as motos mais procuradas do Grande ABC
que estão à venda **abaixo da tabela FIPE**, e avisa por **e-mail** + uma **página web**.

Roda **sozinho na nuvem do GitHub** (não precisa de PC ligado, não gasta token de IA —
é código puro).

## O que ele faz

1. Busca no OLX os modelos da lista (`config/modelos.json`) no estado de SP.
2. Filtra: só cidades do ABC, **sem leilão/sinistro**, **km ≤ 30.000**.
3. Compara cada anúncio com a **Tabela FIPE** (API pública).
4. Guarda os que estão abaixo da FIPE no mínimo `desconto_min_pct` %.
5. Manda e-mail (só quando acha algo) e atualiza a página web.

---

## Testar no seu PC (opcional, pra ver funcionando)

```bash
pip install -r requirements.txt
python src/garimpo.py
```

Isso só imprime os achados no terminal (não manda e-mail). Bom pra conferir.

---

## Colocar pra rodar sozinho (GitHub) — passo a passo

### 1. Criar o repositório
- Crie uma conta grátis no GitHub (a dele).
- Crie um repositório novo (pode ser **público** — deixa o GitHub Actions ilimitado).
- Suba estes arquivos pra lá (`git push` ou pelo site, "upload files").

### 2. Pegar uma chave de e-mail (Resend) — grátis
- Crie conta em https://resend.com (3.000 e-mails/mês grátis).
- Em **API Keys**, gere uma chave (começa com `re_...`).
- Pra testar rápido, use o remetente `onboarding@resend.dev`. Depois, se quiser um
  e-mail próprio no remetente, você verifica um domínio no Resend.

### 3. Cadastrar os segredos no repositório
No repositório: **Settings → Secrets and variables → Actions → New repository secret**.
Crie estes:

| Nome | Valor | Obrigatório |
|------|-------|:-:|
| `RESEND_API_KEY` | a chave `re_...` do Resend | sim |
| `EMAIL_PARA` | o e-mail dele (destino) | sim |
| `EMAIL_DE` | `Garimpo de Motos <onboarding@resend.dev>` | opcional |
| `SITE_URL` | link da página (passo 5), ex: `https://usuario.github.io/repo/` | opcional |
| `SCRAPER_API_KEY` | só se o Actions for bloqueado (ver "Se não vier anúncio") | opcional |

### 4. Ligar o robô
- Aba **Actions** → habilite os workflows → abra **Garimpo de Motos** → **Run workflow**
  (roda na hora pra testar). Depois ele roda sozinho todo dia às 08:00 (BRT).

### 5. Ligar a página web (GitHub Pages)
- **Settings → Pages → Source: Deploy from a branch** → branch `main`, pasta **`/docs`** → Save.
- Em ~1 min a página fica no ar em `https://<usuario>.github.io/<repo>/`.
- Copie esse link e coloque no secret `SITE_URL` (pra ir junto no e-mail).

Pronto. Ele varre todo dia, atualiza a página e manda e-mail quando acha oferta.

---

## Ajustar ao gosto (arquivo `config/modelos.json`)

- `km_max`: quilometragem máxima (padrão 30.000).
- `desconto_min_pct`: quão abaixo da FIPE pra alertar.
  - **5** (padrão) = pega oportunidades reais de km baixa.
  - **8–10** = só gemas raras (e-mails mais raros).
  - **0** = tudo que estiver abaixo da FIPE.
- `modelos`: adicione/remova motos. Cada uma tem:
  - `busca_olx`: o que buscar no OLX.
  - `fipe_marca`: marca na FIPE (`Honda`, `Yamaha`...).
  - `fipe_tokens`: termos que travam o modelo certo na FIPE (evita casar moto errada).
- `paginas_por_modelo`: quantas páginas do OLX varrer por modelo (mais = mais cobertura, mais lento).

### Por que a lista atual?
São os campeões de emplacamento no Brasil/SP (proxy real de "mais procuradas"):
CG 160, Biz, PCX, Bros, XRE 300, Elite, Factor 150, Fazer 250, NMAX, Crosser, Lander.

---

## Se não vier anúncio nenhum (IP bloqueado no Actions)

O OLX usa Cloudflare. Do seu PC o robô fura numa boa. Do datacenter do GitHub **pode**
ser bloqueado. Se o log do Actions mostrar 0 anúncios em todos os modelos:

1. Crie conta grátis em https://scraperapi.com (≈1.000 requisições/mês).
2. Pegue a API key e cadastre como secret `SCRAPER_API_KEY`.
3. Rode de novo — o robô passa a usar o proxy automaticamente (sem mexer no código).

---

## Observações honestas

- O casamento anúncio → versão da FIPE é **aproximado** (a FIPE tem muitas variantes).
  Sempre confira a versão no anúncio antes de decidir.
- É um **radar de oportunidades**, não recomendação de compra.
- Fontes descartadas: Mercado Livre (exige token de app) e Webmotors (captcha pesado).
