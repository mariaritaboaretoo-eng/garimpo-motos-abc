"""Testa se um navegador REAL (Chromium headless) consegue abrir o OLX do IP do
datacenter (GitHub Actions), furando a Cloudflare. Descartavel."""

import sys
from playwright.sync_api import sync_playwright

URL = "https://www.olx.com.br/autos-e-pecas/motos/estado-sp?q=honda%20cg%20160"

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(
        locale="pt-BR",
        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"),
        viewport={"width": 1366, "height": 768},
    )
    pg = ctx.new_page()
    try:
        pg.goto(URL, timeout=60000, wait_until="domcontentloaded")
    except Exception as e:
        print("goto erro:", e)
    pg.wait_for_timeout(9000)  # tempo pro desafio JS da Cloudflare resolver
    html = pg.content()
    print(f"title={pg.title()!r}")
    print(f"bytes={len(html)}")
    print(f"adcard_price={html.count('olx-adcard__price')}")
    print(f"blocked={'Attention Required' in html or 'challenge-platform' in html}")
    b.close()
