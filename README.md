# Garimpo de Motos — ABC abaixo da FIPE

Robô que varre anúncios de moto no Grande ABC procurando as mais procuradas que estão
à venda **abaixo da tabela FIPE**, e avisa por **e-mail** + uma **página web**.

Roda **sozinho na nuvem do GitHub** (não precisa de PC ligado, não gasta token de IA —
é código puro).

## O que ele faz

1. Busca no **usadosbr.com** os anúncios de moto nas cidades do ABC (Santo André, São
   Bernardo, São Caetano, Diadema, Mauá, Ribeirão Pires, Rio Grande da Serra).
2. Filtra: só modelos monitorados (`config/modelos.json`), **sem leilão/sinistro**,
   **km ≤ 30.000**.
3. Compara cada anúncio com a **Tabela FIPE** (API pública).
4. Guarda os que estão abaixo da FIPE no mínimo `desconto_min_pct` %.
5. Manda e-mail (só quando acha algo) e atualiza a página web.

### Por que usadosbr, e não OLX?
O OLX tem muito mais anúncio (inclusive particular), **mas bloqueia o IP de datacenter**
(Cloudflare) — então não roda de graça na nuvem. O usadosbr **responde da nuvem**, tem
vendedor **particular** (onde aparecem as pechinchas) e filtra por cidade exata. A troca:
o usadosbr tem **menos inventário** no ABC, então as ofertas aparecem com menos frequência.
Ver "Quero mais cobertura" no fim.

---

## Testar no seu PC (opcional)

```bash
pip install -r requirements.txt
python src/garimpo.py
```

Só imprime os achados no terminal (não manda e-mail).

---

## Colocar pra rodar sozinho (GitHub) — passo a passo

### 1. Repositório
Já está em `https://github.com/mariaritaboaretoo-eng/garimpo-motos-abc`. Se for recriar:
suba estes arquivos num repositório **público** (Actions ilimitado de graça).

### 2. Chave de e-mail (Resend) — grátis
- Crie conta em https://resend.com (3.000 e-mails/mês grátis).
- Em **API Keys**, gere uma chave (`re_...`).
- Pra testar rápido, o remetente `onboarding@resend.dev` já funciona.

### 3. Cadastrar os segredos (Settings → Secrets and variables → Actions)

| Nome | Valor | Obrigatório |
|------|-------|:-:|
| `RESEND_API_KEY` | a chave `re_...` do Resend | sim (p/ e-mail) |
| `EMAIL_PARA` | o e-mail dele (destino) | sim (p/ e-mail) |
| `EMAIL_DE` | `Garimpo de Motos <onboarding@resend.dev>` | opcional |
| `SITE_URL` | link da página (passo 5) | opcional |

> Sem esses secrets o robô ainda roda e atualiza a página — só não manda e-mail.

### 4. Ligar o robô
Aba **Actions** → habilite os workflows → **Garimpo de Motos** → **Run workflow**.
Depois roda sozinho todo dia às 08:00 (BRT).

### 5. Página web (GitHub Pages)
**Settings → Pages → Deploy from a branch → `main` / pasta `/docs`**. Fica em
`https://mariaritaboaretoo-eng.github.io/garimpo-motos-abc/`. Ponha esse link no secret `SITE_URL`.

---

## Ajustar (arquivo `config/modelos.json`)

- `km_max`: quilometragem máxima (padrão 30.000).
- `desconto_min_pct`: quão abaixo da FIPE pra alertar. **5** (padrão) pega oportunidades
  reais; **0** mostra tudo abaixo da FIPE; **8–10** só gemas raras.
- `modelos`: cada moto tem `fipe_marca` (marca na FIPE) e `fipe_tokens` (termos que travam
  o modelo certo na FIPE e identificam o anúncio — ex: `pcx` impede casar PCX com ADV).

Lista atual = campeões de emplacamento no Brasil/SP (proxy real de "mais procuradas"):
CG 160, Biz, PCX, Bros, XRE 300, Elite, Factor 150, Fazer 250, NMAX, Crosser, Lander.

---

## Quero mais cobertura (ofertas com mais frequência)

O usadosbr tem inventário limitado no ABC. Se quiser pescar mais ofertas (do OLX, que é
muito maior), há duas opções:

1. **Rodar o OLX no PC dele** (quando ligado): o módulo `src/olx.py` já funciona de IP
   residencial. Dá pra agendar no PC dele (Agendador de Tarefas) — pega muito mais anúncio
   de particular, mas só roda com o PC ligado.
2. **Proxy pago** pra rodar o OLX na nuvem: cadastre a secret `SCRAPER_API_KEY` (conta em
   scraperapi.com) e troque a fonte pra `olx` — o grátis dá ~100 buscas/mês (roda a cada
   ~4 dias); pago roda diário.

---

## Observações honestas

- O casamento anúncio → versão da FIPE é **aproximado** — confira a versão no anúncio.
- É um **radar de oportunidades**, não recomendação de compra.
- Fontes avaliadas: **OLX** (rico, mas bloqueia datacenter), **Mercado Livre** (exige token
  de app), **Webmotors** (captcha), **Mobiauto** (nuvem ok, mas só loja → raramente abaixo
  da FIPE). Escolhida: **usadosbr** (nuvem + particular + cidade exata).
