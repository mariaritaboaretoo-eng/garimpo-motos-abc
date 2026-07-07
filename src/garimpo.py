"""Orquestrador: varre o Mobiauto na regiao do ABC e devolve os achados
(motos monitoradas, sem leilao, km <= limite, abaixo da FIPE no minimo pedido).

Fonte = Mobiauto (roda de graca na nuvem; o OLX bloqueia IP de datacenter).

Uso local (so imprime, sem enviar nada):
    python src/garimpo.py

Uso completo (email + pagina), chamado pelo GitHub Actions:
    python src/garimpo.py --notificar
"""

import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(__file__))

import fipe
import filtros
import usadosbr as fonte

RAIZ = os.path.dirname(os.path.dirname(__file__))
CONFIG = os.path.join(RAIZ, "config", "modelos.json")


def _norm(txt):
    txt = unicodedata.normalize("NFKD", txt or "")
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return txt.lower()


def _identifica_modelo(a, modelos):
    """Descobre qual modelo monitorado o anuncio e (marca + tokens no texto)."""
    marca = _norm(a.get("marca_olx"))
    texto = _norm(a.get("texto"))
    for m in modelos:
        if _norm(m["fipe_marca"]) != marca:
            continue
        if all(_norm(t) in texto for t in m.get("fipe_tokens", [])):
            return m
    return None


def carregar_config():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def garimpar(cfg, log=print):
    achados = []
    marcas = sorted({m["fipe_marca"] for m in cfg["modelos"]})
    paginas = cfg.get("paginas_por_busca", 1)
    log(f"  buscando {marcas} no ABC ({len(fonte.CIDADES_BUSCA)} cidades)...")
    deals = fonte.buscar_abc(marcas, paginas=paginas)
    abc = [a for a in deals if filtros.passa_regiao(a, cfg["cidades_abc"])]
    log(f"    {len(deals)} anuncios / {len(abc)} no ABC")

    for a in abc:
        # 1) e um modelo monitorado?
        modelo = _identifica_modelo(a, cfg["modelos"])
        if not modelo:
            continue
        a["modelo_monitorado"] = modelo["nome"]

        # 2) fora leilao/sinistro
        if filtros.eh_leilao(a, cfg["palavras_bloqueio"]):
            continue
        # 3) precisa ter ano (pra casar FIPE)
        if not a.get("ano"):
            continue
        # 4) km <= limite (regra estrita)
        if not filtros.passa_km(a, cfg["km_max"]):
            continue

        # 5) referencia FIPE (modelo do anuncio + tokens que travam a familia certa)
        ref = fipe.valor_referencia(
            modelo["fipe_marca"], a["modelo_olx"], a["ano"],
            tokens_obrigatorios=modelo.get("fipe_tokens"),
        )
        if not ref:
            continue
        if not filtros.avaliar_fipe(a, ref, cfg["desconto_min_pct"]):
            continue

        achados.append(a)

    achados.sort(key=lambda x: x["desconto_pct"], reverse=True)
    return achados


def imprimir(achados):
    if not achados:
        print("\nNenhuma moto abaixo da FIPE encontrada nesta rodada.")
        return
    print(f"\n=== {len(achados)} ACHADOS (abaixo da FIPE) ===\n")
    for a in achados:
        print(f"[-{a['desconto_pct']}% | economiza R$ {a['economia']:,}]".replace(",", "."))
        tipo = "particular" if a.get("particular") else "loja"
        print(f"  {a['titulo']}  ({a['ano']}, {a['km']} km, {a['municipio']}, {tipo})")
        print(f"  Anuncio: R$ {a['preco']:,}".replace(",", ".") +
              f"  |  FIPE ({a['modelo_fipe']}): R$ {a['fipe']:,.0f}".replace(",", "."))
        print(f"  {a['url']}\n")


def main():
    cfg = carregar_config()
    print(f"Garimpando {len(cfg['modelos'])} modelos no ABC "
          f"(km<= {cfg['km_max']}, min {cfg['desconto_min_pct']}% abaixo da FIPE)...\n")
    achados = garimpar(cfg)
    imprimir(achados)

    if "--notificar" in sys.argv:
        import notificar
        import pagina
        pagina.gerar(achados, cfg)
        notificar.enviar(achados, cfg, url_pagina=os.environ.get("SITE_URL"))


if __name__ == "__main__":
    main()
