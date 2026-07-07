"""Scraper do OLX - lista de anuncios de moto.

O OLX embute um JSON limpo por anuncio no HTML (stream React). Extraimos dele:
titulo, modelo normalizado, preco, ano, km exato, municipio e se e vendedor PJ.
Muito mais robusto que raspar o DOM. Sem login, sem API oficial.

A busca textual (q=) do OLX ignora a regiao no path e devolve o estado inteiro,
entao a filtragem por ABC e feita no cliente pelo campo 'municipio' (exato).
"""

import json
import re
import unicodedata
from urllib.parse import quote

BASE_URL = "https://www.olx.com.br/autos-e-pecas/motos/estado-sp"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

# O OLX fica atras da Cloudflare, que bloqueia IP de datacenter para requisicoes HTTP
# comuns (requests/curl_cffi -> 403). A saida e usar um NAVEGADOR real (Playwright/
# Chromium): ele resolve o desafio JavaScript da Cloudflare e funciona ate do GitHub
# Actions. O navegador e reaproveitado entre as buscas -> o cookie de "aprovado" da
# Cloudflare fica no contexto e so a 1a pagina espera o desafio.
_pw = _browser = _page = None


def _garante_navegador():
    global _pw, _browser, _page
    if _page is not None:
        return _page
    from playwright.sync_api import sync_playwright
    _pw = sync_playwright().start()
    _browser = _pw.chromium.launch(
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
    )
    ctx = _browser.new_context(
        locale="pt-BR", user_agent=UA, viewport={"width": 1366, "height": 768}
    )
    _page = ctx.new_page()
    return _page


def fechar():
    """Fecha o navegador. Chamar no fim da execucao."""
    global _pw, _browser, _page
    try:
        if _browser:
            _browser.close()
        if _pw:
            _pw.stop()
    finally:
        _pw = _browser = _page = None


def _fetch(url):
    pg = _garante_navegador()
    pg.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        pg.wait_for_selector(".olx-adcard__price", timeout=20000)
    except Exception:
        pass  # pagina sem resultados, ou desafio ainda resolvendo
    return pg.content()


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


def buscar(termo, paginas=1):
    """Retorna lista de anuncios (dict normalizado) do estado inteiro para o termo."""
    achados = []
    for pagina in range(1, paginas + 1):
        url = f"{BASE_URL}?q={quote(termo)}"
        if pagina > 1:
            url += f"&o={pagina}"
        try:
            html = _fetch(url)
        except Exception:
            break
        for obj in _extrair_ads(html):
            a = _normaliza(obj)
            if a["preco"]:
                achados.append(a)
    return achados
