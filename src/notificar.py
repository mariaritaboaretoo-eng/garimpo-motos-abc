"""Envio de e-mail via SMTP do Gmail (com App Password).

Por que Gmail SMTP e nao Resend/outro: pra mandar e-mail pra um destinatario qualquer
(o e-mail dele) de graca, o Gmail e o caminho sem dor - o Resend so manda pra qualquer
um se voce tiver um dominio proprio verificado. O Gmail manda pra qualquer endereco.

Funciona sem PC ligado e sem login interativo (ao contrario do MCP do Gmail, que exige
OAuth na hora): usa uma "Senha de app" de 16 digitos, gerada 1 vez na conta Google.

Variaveis de ambiente (secrets no GitHub Actions):
  GMAIL_USER          - o Gmail que ENVIA (ex: criativaria.contato@gmail.com)
  GMAIL_APP_PASSWORD  - a Senha de app de 16 digitos (NAO e a senha normal da conta)
  EMAIL_PARA          - destinatario (o e-mail dele)

So envia quando ha achados - nada de e-mail vazio.
"""

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


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
    user = os.environ.get("GMAIL_USER")
    senha = os.environ.get("GMAIL_APP_PASSWORD")
    para = os.environ.get("EMAIL_PARA")
    if not (user and senha and para):
        print("[email] faltando GMAIL_USER / GMAIL_APP_PASSWORD / EMAIL_PARA - pulando envio.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{len(achados)} moto(s) abaixo da FIPE no ABC"
    msg["From"] = f"Garimpo de Motos <{user}>"
    msg["To"] = para
    msg.attach(MIMEText(_html(achados, cfg, url_pagina), "html"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
            s.starttls(context=ctx)
            s.login(user, senha)
            s.sendmail(user, [para], msg.as_string())
        print(f"[email] enviado para {para}.")
        return True
    except Exception as e:
        print(f"[email] falhou: {type(e).__name__}: {str(e)[:200]}")
        return False
