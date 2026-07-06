"""Scraper do OLX - lista de anuncios de moto.

O OLX embute um JSON limpo por anuncio no HTML (stream React). Extraimos dele:
titulo, modelo normalizado, preco, ano, km exato, municipio e se e vendedor PJ.
Muito mais robusto que raspar o DOM. Sem login, sem API oficial.

A busca textual (q=) do OLX ignora a regiao no path e devolve o estado inteiro,
entao a filtragem por ABC e feita no cliente pelo campo 'municipio' (exato).
"""

import json
import os
import re
import time
import unicodedata
from urllib.parse import quote, urlencode

from curl_cffi import requests as http  # imita fingerprint TLS do Chrome p/ furar Cloudflare

BASE_URL = "https://www.olx.com.br/autos-e-pecas/motos/estado-sp"
IMPERSONATE = "chrome124"
HEADERS = {"Accept-Language": "pt-BR,pt;q=0.9"}

# Fallback opcional: se o IP direto (ex: GitHub Actions) for bloqueado pela Cloudflare,
# defina a secret SCRAPER_API_KEY (conta gratuita em scraperapi.com) que as requisicoes
# passam por um proxy que resolve o desafio. Sem a key, vai direto via curl_cffi.
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")


def _get(url):
    if SCRAPER_API_KEY:
        proxied = "https://api.scraperapi.com/?" + urlencode(
            {"api_key": SCRAPER_API_KEY, "url": url}
        )
        return http.get(proxied, headers=HEADERS, impersonate=IMPERSONATE, timeout=70)
    return http.get(url, headers=HEADERS, impersonate=IMPERSONATE, timeout=30)


def _norm(txt):
    txt = unicodedata.normalize("NFKD", txt or "")
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return txt.lower().strip()


def _int(txt):
    d = re.sub(r"[^\d]", "", str(txt or ""))
    return int(d) if d else None


def _extrair_ads(html):
    """Extrai os objetos JSON de anuncio do stream RSC do OLX."""
    esc = html.replace('\\"', '"')
    ads, vistos = [], set()
    for m in re.finditer(r'"listId"\s*:\s*\d+', esc):
        inicio = esc.rfind("{", 0, m.start())
        profundidade = 0
        for i in range(inicio, min(inicio + 8000, len(esc))):
            c = esc[i]
            if c == "{":
                profundidade += 1
            elif c == "}":
                profundidade -= 1
                if profundidade == 0:
                    try:
                        obj = json.loads(esc[inicio:i + 1])
                        if obj.get("listId") not in vistos:
                            vistos.add(obj["listId"])
                            ads.append(obj)
                    except Exception:
                        pass
                    break
    return ads


def _normaliza(obj):
    props = {p["name"]: p.get("value") for p in (obj.get("properties") or [])}
    ld = obj.get("locationDetails") or {}
    return {
        "titulo": obj.get("subject", ""),
        "modelo_olx": props.get("vehicle_model") or obj.get("subject", ""),
        "marca_olx": props.get("vehicle_brand"),
        "preco": _int(obj.get("priceValue") or obj.get("price")),
        "ano": _int(props.get("regdate")),
        "km": _int(props.get("mileage")),
        "municipio": ld.get("municipality"),
        "uf": ld.get("uf"),
        "particular": not obj.get("professionalAd", False),
        "url": (obj.get("url") or "").split("?")[0],
        "texto": obj.get("subject", ""),
    }


def buscar(termo, paginas=1, pausa=1.5):
    """Retorna lista de anuncios (dict normalizado) do estado inteiro para o termo."""
    achados = []
    for pagina in range(1, paginas + 1):
        url = f"{BASE_URL}?q={quote(termo)}"
        if pagina > 1:
            url += f"&o={pagina}"
        try:
            r = _get(url)
        except Exception:
            break
        if r.status_code != 200:
            break
        for obj in _extrair_ads(r.text):
            a = _normaliza(obj)
            if a["preco"]:
                achados.append(a)
        time.sleep(pausa)  # educado com o OLX
    return achados
