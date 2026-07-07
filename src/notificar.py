"""Envio de e-mail por SMTP (funciona com qualquer provedor: Brevo, SMTP2GO, Gmail...).

Escolhemos um provedor SMTP com chave (ex: Brevo) porque manda pra QUALQUER destinatario
de graca, sem precisar de dominio proprio (Resend exigiria) e sem "Senha de app" do Gmail
(que o Google nao oferece mais para varias contas). Funciona sem PC ligado e sem login
interativo (ao contrario do MCP do Gmail).

Variaveis de ambiente (secrets no GitHub Actions):
  SMTP_HOST      - servidor SMTP (ex: smtp-relay.brevo.com). Padrao: smtp.gmail.com
  SMTP_PORT      - porta (padrao 587, STARTTLS)
  SMTP_LOGIN     - usuario/login SMTP do provedor
  SMTP_PASSWORD  - a chave/senha SMTP do provedor
  EMAIL_DE       - remetente que aparece no "De:" (padrao = SMTP_LOGIN)
  EMAIL_PARA     - destinatario (o e-mail dele)

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
      <p style="color:#0a0;font-size:14px;text-align:center;margin-top:16px">Feito com carinho pro tio Robson &#128154;</p>
    </div>""".replace(",", ".")


def enviar(achados, cfg, url_pagina=None):
    if not achados:
        print("[email] sem achados - nao envia.")
        return False
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    login = os.environ.get("SMTP_LOGIN")
    senha = os.environ.get("SMTP_PASSWORD")
    para = os.environ.get("EMAIL_PARA")
    de = os.environ.get("EMAIL_DE", login)
    if not (login and senha and para):
        print("[email] faltando SMTP_LOGIN / SMTP_PASSWORD / EMAIL_PARA - pulando envio.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{len(achados)} moto(s) abaixo da FIPE no ABC"
    msg["From"] = f"Garimpo de Motos <{de}>"
    msg["To"] = para
    msg.attach(MIMEText(_html(achados, cfg, url_pagina), "html"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls(context=ctx)
            s.login(login, senha)
            s.sendmail(de, [para], msg.as_string())
        print(f"[email] enviado para {para} via {host}.")
        return True
    except Exception as e:
        print(f"[email] falhou: {type(e).__name__}: {str(e)[:200]}")
        return False
