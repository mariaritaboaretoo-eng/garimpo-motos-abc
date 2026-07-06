"""Gera a pagina web estatica (docs/index.html) publicada pelo GitHub Pages."""

import html
import json
import os
from datetime import datetime, timedelta, timezone

RAIZ = os.path.dirname(os.path.dirname(__file__))
DOCS = os.path.join(RAIZ, "docs")

BRT = timezone(timedelta(hours=-3))  # horario de Brasilia (sem horario de verao)


def _agora():
    return datetime.now(BRT).strftime("%d/%m/%Y as %H:%M")


def br(n):
    """Formata numero com ponto de milhar (padrao BR): 14990 -> '14.990'."""
    return f"{round(n):,}".replace(",", ".")


def _card(a):
    tipo = "particular" if a.get("particular") else "loja"
    meta = f"{a['ano']} &middot; {br(a['km'])} km &middot; {html.escape(str(a['municipio']))} &middot; {tipo}"
    return f"""
    <a class="card" href="{html.escape(a['url'])}" target="_blank" rel="noopener">
      <div class="badge">-{a['desconto_pct']}%</div>
      <h3>{html.escape(a['titulo'])}</h3>
      <div class="linha"><span>Anuncio</span><b>R$ {br(a['preco'])}</b></div>
      <div class="linha"><span>FIPE ({html.escape(str(a['modelo_fipe']))})</span><span>R$ {br(a['fipe'])}</span></div>
      <div class="linha economia"><span>Economia</span><b>R$ {br(a['economia'])}</b></div>
      <div class="meta">{meta}</div>
    </a>"""


def gerar(achados, cfg):
    os.makedirs(DOCS, exist_ok=True)
    if achados:
        corpo = '<div class="grid">' + "".join(_card(a) for a in achados) + "</div>"
        subtitulo = f"{len(achados)} moto(s) abaixo da tabela FIPE agora"
    else:
        corpo = (
            '<div class="vazio">Nenhuma moto abaixo da FIPE no momento '
            "(dentro dos filtros). O robo checa de novo no proximo horario.</div>"
        )
        subtitulo = "Nenhuma oferta agora"

    modelos = ", ".join(m["nome"] for m in cfg["modelos"])
    info = (
        f"Atualizado em {_agora()} (BRT). Filtros: ate {br(cfg['km_max'])} km, no minimo "
        f"{cfg['desconto_min_pct']}% abaixo da FIPE, sem leilao/sinistro, so cidades do ABC."
    )
    pagina = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Garimpo de Motos - ABC abaixo da FIPE</title>
<style>
  :root {{ --bg:#0f1115; --card:#1a1e27; --line:#2a2f3a; --txt:#e8eaed; --mut:#9aa0aa; --ok:#31c48d; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--txt); font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }}
  header {{ padding:28px 20px 16px; max-width:1000px; margin:0 auto; }}
  h1 {{ margin:0 0 4px; font-size:22px; }}
  .sub {{ color:var(--ok); font-weight:600; }}
  .info {{ color:var(--mut); font-size:13px; margin-top:8px; line-height:1.5; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:14px; padding:8px 20px 40px; max-width:1000px; margin:0 auto; }}
  .card {{ position:relative; display:block; background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; text-decoration:none; color:inherit; transition:transform .1s, border-color .1s; }}
  .card:hover {{ transform:translateY(-2px); border-color:var(--ok); }}
  .badge {{ position:absolute; top:12px; right:12px; background:var(--ok); color:#04150d; font-weight:800; font-size:13px; padding:3px 8px; border-radius:8px; }}
  .card h3 {{ margin:0 8px 12px 0; font-size:15px; line-height:1.3; padding-right:52px; }}
  .linha {{ display:flex; justify-content:space-between; font-size:13px; color:var(--mut); padding:2px 0; }}
  .linha b {{ color:var(--txt); }}
  .economia b {{ color:var(--ok); }}
  .meta {{ margin-top:10px; padding-top:10px; border-top:1px solid var(--line); font-size:12px; color:var(--mut); }}
  .vazio {{ max-width:1000px; margin:0 auto; padding:24px 20px 60px; color:var(--mut); }}
  footer {{ max-width:1000px; margin:0 auto; padding:20px; color:var(--mut); font-size:12px; border-top:1px solid var(--line); }}
</style>
</head>
<body>
<header>
  <h1>Garimpo de Motos &middot; Grande ABC</h1>
  <div class="sub">{subtitulo}</div>
  <div class="info">{info}</div>
</header>
{corpo}
<footer>
  Modelos monitorados: {html.escape(modelos)}.<br>
  Precos comparados com a Tabela FIPE (referencia; o casamento de versao e aproximado, confira no anuncio).
  Fonte dos anuncios: OLX. Radar automatico de oportunidades, nao e recomendacao de compra.
</footer>
</body>
</html>"""

    caminho = os.path.join(DOCS, "index.html")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(pagina)
    with open(os.path.join(DOCS, "achados.json"), "w", encoding="utf-8") as f:
        json.dump({"atualizado": _agora(), "achados": achados}, f, ensure_ascii=False, indent=2)
    return caminho
