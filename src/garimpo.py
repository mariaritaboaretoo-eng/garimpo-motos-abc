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

sys.path.insert(0, os.path.dirname(__file__))

import fipe
import filtros
import olx

RAIZ = os.path.dirname(os.path.dirname(__file__))
CONFIG = os.path.join(RAIZ, "config", "modelos.json")


def carregar_config():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def garimpar(cfg, log=print):
    achados = []
    paginas = cfg.get("paginas_por_busca", 3)
    try:
        for modelo in cfg["modelos"]:
            log(f"  buscando: {modelo['nome']} ...")
            anuncios = olx.buscar(modelo["busca_olx"], paginas=paginas)
            abc = [a for a in anuncios if filtros.passa_regiao(a, cfg["cidades_abc"])]
            log(f"    {len(anuncios)} no estado / {len(abc)} no ABC")
            for a in abc:
                a["modelo_monitorado"] = modelo["nome"]

                # 1) fora leilao/sinistro
                if filtros.eh_leilao(a, cfg["palavras_bloqueio"]):
                    continue
                # 2) precisa ter ano (pra casar FIPE)
                if not a.get("ano"):
                    continue
                # 3) km <= limite (regra estrita)
                if not filtros.passa_km(a, cfg["km_max"]):
                    continue

                # 4) referencia FIPE (modelo normalizado do OLX + tokens que travam a familia)
                ref = fipe.valor_referencia(
                    modelo["fipe_marca"], a["modelo_olx"], a["ano"],
                    tokens_obrigatorios=modelo.get("fipe_tokens"),
                )
                if not ref:
                    continue
                if not filtros.avaliar_fipe(a, ref, cfg["desconto_min_pct"]):
                    continue

                achados.append(a)
    finally:
        olx.fechar()

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

    # --pagina: so atualiza a pagina | --notificar: pagina + email
    if "--notificar" in sys.argv or "--pagina" in sys.argv:
        import pagina
        pagina.gerar(achados, cfg)
    if "--notificar" in sys.argv:
        import notificar
        notificar.enviar(achados, cfg, url_pagina=os.environ.get("SITE_URL"))


if __name__ == "__main__":
    main()
