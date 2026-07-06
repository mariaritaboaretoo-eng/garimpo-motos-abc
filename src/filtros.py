"""Regras de filtragem: descarta leilao, km alta, fora do ABC e acima da FIPE."""

import unicodedata


def _norm(txt):
    txt = unicodedata.normalize("NFKD", txt or "")
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return txt.lower()


def eh_leilao(anuncio, palavras_bloqueio):
    texto = _norm(anuncio.get("titulo", "") + " " + anuncio.get("texto", ""))
    return any(_norm(p) in texto for p in palavras_bloqueio)


def passa_regiao(anuncio, cidades_abc):
    """True se o municipio do anuncio pertence ao ABC."""
    m = _norm(anuncio.get("municipio", ""))
    return m in {_norm(c) for c in cidades_abc}


def passa_km(anuncio, km_max):
    """True se km conhecida e <= limite. km desconhecida = nao passa (regra estrita)."""
    km = anuncio.get("km")
    return km is not None and km <= km_max


def avaliar_fipe(anuncio, ref_fipe, desconto_min_pct):
    """Anexa dados FIPE ao anuncio e diz se esta abaixo da tabela no minimo pedido."""
    valor_fipe = ref_fipe["valor"]
    preco = anuncio["preco"]
    desconto_pct = round((valor_fipe - preco) / valor_fipe * 100, 1)
    anuncio["fipe"] = valor_fipe
    anuncio["modelo_fipe"] = ref_fipe["modelo_fipe"]
    anuncio["desconto_pct"] = desconto_pct
    anuncio["economia"] = round(valor_fipe - preco)
    anuncio["confianca_fipe"] = ref_fipe.get("confianca")
    return desconto_pct >= desconto_min_pct
