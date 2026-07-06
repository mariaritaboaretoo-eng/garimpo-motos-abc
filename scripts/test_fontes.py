"""Teste-relampago: quais fontes de anuncio respondem do IP do GitHub (datacenter)?
Roda no Actions via workflow test-fontes. Descartavel."""

import requests
from curl_cffi import requests as cc

SITES = {
    "OLX":      "https://www.olx.com.br/autos-e-pecas/motos/estado-sp?q=honda%20cg%20160",
    "Mobiauto": "https://www.mobiauto.com.br/comprar/motos/sp-santo-andre",
    "usadosbr": "https://www.usadosbr.com/motos",
    "iCarros":  "https://www.icarros.com.br/ache/listadeofertas.jsp?tipoveiculo=2&estados=27",
    "iCarros-bff": "https://icarros-api-ext-bff-textenchance.icarros.com.br/similarity/searches?searchTerm=cg%20160",
}
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept-Language": "pt-BR"}

for nome, url in SITES.items():
    for cli in ("plain", "cffi"):
        try:
            if cli == "cffi":
                r = cc.get(url, headers=H, impersonate="chrome124", timeout=30)
            else:
                r = requests.get(url, headers=H, timeout=30)
            txt = r.text
            price = ("R$" in txt) or ('"price"' in txt.lower()) or ("preco" in txt.lower())
            print(f"{nome:13} {cli:5} HTTP {r.status_code} bytes {len(txt):>7} price={price}")
        except Exception as e:
            print(f"{nome:13} {cli:5} ERRO {type(e).__name__} {str(e)[:50]}")
