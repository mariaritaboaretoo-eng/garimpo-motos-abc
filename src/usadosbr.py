"""Fonte de anuncios: usadosbr.com.

Melhor fonte para este robo porque junta as duas coisas que precisamos:
 - **Responde do IP de datacenter** (testado no GitHub Actions) -> roda de graca na nuvem.
 - Tem **vendedor particular** (advertiser.type == 'personal'), nao so loja -> e onde
   aparecem as motos abaixo da FIPE (loja poe margem, particular pechincha).

Filtra por cidade EXATA no path (sem raio): /motos/{uf}/{cidade}/{marca}
Os anuncios vem num JSON limpo no __NEXT_DATA__ com marca/modelo/versao/ano/km/preco/tipo.
"""

import json
import os
import re
import time
import unicodedata

from curl_cffi import requests as http

BASE = "https://www.usadosbr.com"
IMPERSONATE = "chrome124"
HEADERS = {"Accept-Language": "pt-BR,pt;q=0.9"}
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")  # fallback opcional (nao precisa)

# Cidades do ABC (slug do usadosbr). Filtro e exato por cidade (sem raio).
CIDADES_BUSCA = [
    "santo-andre",
    "sao-bernardo-do-campo",
    "sao-caetano-do-sul",
    "diadema",
    "maua",
    "ribeirao-pires",
    "rio-grande-da-serra",
]


def _slug(txt):
    txt = unicodedata.normalize("NFKD", txt or "")
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")


def _get(url):
    if SCRAPER_API_KEY:
        from urllib.parse import urlencode
        url = "https://api.scraperapi.com/?" + urlencode({"api_key": SCRAPER_API_KEY, "url": url})
    return http.get(url, headers=HEADERS, impersonate=IMPERSONATE, timeout=40)


def _extrai(html):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    try:
        pp = json.loads(m.group(1))["props"]["pageProps"]
    except Exception:
        return []

    def walk(o):
        if isinstance(o, list) and o and isinstance(o[0], dict) and "version" in o[0] and (
            "value" in o[0] or "km" in o[0]
        ):
            yield o
        if isinstance(o, dict):
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)

    for lst in walk(pp):
        return lst
    return []


def _normaliza(a, municipio):
    v = a.get("version") or {}
    mdl = v.get("model") or {}
    br = mdl.get("brand") or {}
    marca = br.get("name", "") or ""
    modelo = mdl.get("name", "") or ""
    versao = v.get("name", "") or ""
    cil = (a.get("cylinder") or {}).get("name", "") or ""
    ano = a.get("yearMod") or a.get("yearMan")
    try:
        url = f"{BASE}/motos-e-quadriciclos/{br['slug']}/{mdl['slug']}/{v['slug']}/{a['slug']}"
    except (KeyError, TypeError):
        url = f"{BASE}/motos"
    return {
        "id": a.get("id"),
        "titulo": f"{marca} {modelo} {versao} {ano}".strip(),
        "modelo_olx": f"{modelo} {versao} {cil}".strip(),   # texto p/ casar na FIPE
        "marca_olx": marca,
        "preco": a.get("value"),
        "ano": ano,
        "km": a.get("km"),
        "municipio": municipio,                             # cidade exata da busca
        "uf": "SP",
        "particular": (a.get("advertiser") or {}).get("type") == "personal",
        "url": url,
        "texto": f"{marca} {modelo} {versao} {cil}",
    }


def buscar_abc(marcas, paginas=1, pausa=1.0, log=lambda *_: None):
    """Varre cada cidade do ABC x cada marca. Dedupe por id. (paginas: reservado)"""
    achados, vistos = [], set()
    nomes_cidade = {
        "santo-andre": "Santo Andre", "sao-bernardo-do-campo": "Sao Bernardo do Campo",
        "sao-caetano-do-sul": "Sao Caetano do Sul", "diadema": "Diadema", "maua": "Maua",
        "ribeirao-pires": "Ribeirao Pires", "rio-grande-da-serra": "Rio Grande da Serra",
    }
    for cidade in CIDADES_BUSCA:
        for marca in marcas:
            url = f"{BASE}/motos/sp/{cidade}/{_slug(marca)}"
            try:
                r = _get(url)
            except Exception:
                continue
            if r.status_code != 200:
                continue
            for a in _extrai(r.text):
                if a.get("id") in vistos:
                    continue
                vistos.add(a.get("id"))
                achados.append(_normaliza(a, nomes_cidade.get(cidade, cidade)))
            time.sleep(pausa)
    return achados
