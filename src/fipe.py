"""Cliente da tabela FIPE (API publica parallelum.com.br).

Resolve, a partir de uma marca + titulo de anuncio + ano, o preco de tabela FIPE.
O casamento titulo -> modelo FIPE e aproximado (a FIPE tem varias variantes por modelo),
por isso o robo sempre guarda qual modelo FIPE foi usado, pra dar pra conferir.
"""

import json
import os
import re
import time
import unicodedata

import requests

BASE = "https://parallelum.com.br/fipe/api/v1/motos"
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _norm(txt):
    """minusculo, sem acento, sem pontuacao - pra comparar texto de forma tolerante."""
    txt = unicodedata.normalize("NFKD", txt or "")
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", txt.lower())


def _cache_get(chave):
    caminho = os.path.join(CACHE_DIR, chave + ".json")
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    return None


def _cache_set(chave, valor):
    caminho = os.path.join(CACHE_DIR, chave + ".json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(valor, f, ensure_ascii=False)


def _get(url, chave):
    em_cache = _cache_get(chave)
    if em_cache is not None:
        return em_cache
    for tentativa in range(3):
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                dados = r.json()
                _cache_set(chave, dados)
                return dados
            if r.status_code == 429:  # rate limit
                time.sleep(3 * (tentativa + 1))
                continue
        except requests.RequestException:
            time.sleep(2)
    return None


def marcas():
    return _get(f"{BASE}/marcas", "fipe_marcas") or []


def codigo_marca(nome_marca):
    alvo = _norm(nome_marca)
    for m in marcas():
        if _norm(m["nome"]) == alvo:
            return m["codigo"]
    for m in marcas():
        if alvo in _norm(m["nome"]):
            return m["codigo"]
    return None


def modelos(cod_marca):
    dados = _get(f"{BASE}/marcas/{cod_marca}/modelos", f"fipe_modelos_{cod_marca}")
    return (dados or {}).get("modelos", [])


def anos(cod_marca, cod_modelo):
    return _get(
        f"{BASE}/marcas/{cod_marca}/modelos/{cod_modelo}/anos",
        f"fipe_anos_{cod_marca}_{cod_modelo}",
    ) or []


def preco(cod_marca, cod_modelo, cod_ano):
    return _get(
        f"{BASE}/marcas/{cod_marca}/modelos/{cod_modelo}/anos/{cod_ano}",
        f"fipe_preco_{cod_marca}_{cod_modelo}_{cod_ano}",
    )


CILINDRADAS = {"50", "110", "125", "150", "160", "190", "200", "250", "300", "600"}


def _melhor_entre(candidatos, texto):
    """Escolhe, dentre os modelos FIPE ja filtrados por familia, o que mais combina
    com o texto do anuncio (variante + cilindrada). Sempre devolve um (a familia ja
    foi travada pelos tokens obrigatorios)."""
    tokens_texto = set(_norm(texto).split())
    disp_texto = tokens_texto & CILINDRADAS
    melhor, melhor_score = candidatos[0], -99
    for m in candidatos:
        tokens_modelo = set(_norm(m["nome"]).split())
        score = len(tokens_texto & tokens_modelo) / max(len(tokens_modelo), 1)
        disp_modelo = tokens_modelo & CILINDRADAS
        if disp_texto and disp_modelo:  # premia/penaliza casamento de cilindrada
            score += 0.6 if (disp_texto & disp_modelo) else -0.6
        if score > melhor_score:
            melhor, melhor_score = m, score
    return melhor, round(melhor_score, 2)


def _codigo_ano(cod_marca, cod_modelo, ano, tolerancia=1):
    """Codigo FIPE do ano do anuncio. So aceita se o ano existir na tabela daquele
    modelo dentro da tolerancia (evita precificar uma moto 2010 com a tabela de uma
    geracao que so comeca em 2018)."""
    lista = anos(cod_marca, cod_modelo)
    exato = [a for a in lista if a["codigo"].startswith(f"{ano}-")]
    if exato:
        return exato[0]["codigo"]
    candidatos = [a for a in lista if re.match(r"\d{4}-", a["codigo"])]
    if not candidatos:
        return None
    def yr(a):
        return int(a["codigo"][:4])
    mais_perto = min(candidatos, key=lambda a: abs(yr(a) - ano))
    return mais_perto["codigo"] if abs(yr(mais_perto) - ano) <= tolerancia else None


def valor_referencia(fipe_marca, texto, ano, tokens_obrigatorios=None):
    """Retorna dict {valor, modelo_fipe, ano_fipe, confianca} ou None se nao casar.

    tokens_obrigatorios: lista de termos que o nome do modelo FIPE PRECISA conter
    (trava a familia certa, ex: ['pcx'] evita casar PCX com ADV 160).
    """
    cod_marca = codigo_marca(fipe_marca)
    if not cod_marca:
        return None
    candidatos = modelos(cod_marca)
    if tokens_obrigatorios:
        candidatos = [
            m for m in candidatos
            if all(_norm(t) in _norm(m["nome"]) for t in tokens_obrigatorios)
        ]
    if not candidatos:
        return None
    modelo, score = _melhor_entre(candidatos, texto)
    cod_ano = _codigo_ano(cod_marca, modelo["codigo"], ano)
    if not cod_ano:
        return None
    p = preco(cod_marca, modelo["codigo"], cod_ano)
    if not p or "Valor" not in p:
        return None
    valor = float(re.sub(r"[^\d,]", "", p["Valor"]).replace(",", "."))
    return {
        "valor": valor,
        "modelo_fipe": p.get("Modelo", modelo["nome"]),
        "ano_fipe": p.get("AnoModelo"),
        "confianca": round(score, 2),
    }
