"""Envio de email via Resend (https://resend.com).

Escolhido porque funciona sem PC ligado e sem login interativo: basta uma API key.
Le tres variaveis de ambiente (secrets no GitHub Actions):
  RESEND_API_KEY  - a chave da conta Resend
  EMAIL_DE        - remetente (ex: 'Garimpo <onboarding@resend.dev>' p/ testar)
  EMAIL_PARA      - destinatario (email dele)

So envia quando ha achados - nada de email vazio todo dia.
"""

import os

import requests

RESEND_URL = "https://api.resend.com/emails"


def _linha(a):
    tipo = "particular" if a.get("particular") else "loja"
    return f"""
    <tr>
      <td style="padding:10px;border-bottom:1px solid #eee">
        <a href="{a['url']}" style="color:#0b7;font-weight:600;text-decoration:none">{a['titulo']}</a><br>
        <span style="color:#666;font-size:13px">{a['ano']} &middot; {a['km']:,} km &middot; {a['municipio']} &middot; {tipo}</span>
      </td>
      <td style="padding:10px;border-bottom:1px solid #eee;text-align:right;white-space:nowrap">
        <b>R$ {a['preco']:,}</b><br>
        <span style="color:#0a0;font-size:13px">-{a['desconto_pct']}% (FIPE R$ {a['fipe']:,.0f})</span>
      </td>
    </tr>""".replace(",", ".")


def _html(achados, cfg, url_pagina):
    linhas = "".join(_linha(a) for a in achados)
    link = f'<p><a href="{url_pagina}">Ver todas na pagina</a></p>' if url_pagina else ""
    return f"""
    <div style="font-family:system-ui,Arial,sans-serif;max-width:640px;margin:auto">
      <h2>{len(achados)} moto(s) abaixo da FIPE no ABC</h2>
      <p style="color:#666">Ate {cfg['km_max']:,} km, minimo {cfg['desconto_min_pct']}% abaixo da tabela, sem leilao.</p>
      <table style="width:100%;border-collapse:collapse">{linhas}</table>
      {link}
      <p style="color:#999;font-size:12px">Casamento de versao FIPE e aproximado - confira no anuncio.</p>
    </div>""".replace(",", ".")


def enviar(achados, cfg, url_pagina=None):
    if not achados:
        print("[email] sem achados - nao envia.")
        return False
    api_key = os.environ.get("RESEND_API_KEY")
    de = os.environ.get("EMAIL_DE", "Garimpo de Motos <onboarding@resend.dev>")
    para = os.environ.get("EMAIL_PARA")
    if not api_key or not para:
        print("[email] faltando RESEND_API_KEY ou EMAIL_PARA - pulando envio.")
        return False
    try:
        r = requests.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "from": de,
                "to": [para],
                "subject": f"{len(achados)} moto(s) abaixo da FIPE no ABC",
                "html": _html(achados, cfg, url_pagina),
            },
            timeout=30,
        )
        if r.status_code in (200, 201):
            print(f"[email] enviado para {para}.")
            return True
        print(f"[email] falhou: {r.status_code} {r.text[:200]}")
    except requests.RequestException as e:
        print(f"[email] erro de rede: {e}")
    return False
