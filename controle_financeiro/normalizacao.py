import re

# prefixos de adquirencia/gateway que poluem o nome do estabelecimento
_PREFIXOS = re.compile(r"^(DL|MP|MC|EBN|EC|PG|IFD|STB|TB|PARC=\d*)\s*\*?\s*", re.IGNORECASE)

def normalizar_estabelecimento(texto: str) -> str:
    s = (texto or "").strip().upper()
    s = re.sub(r"\s+", " ", s)
    anterior = None
    while anterior != s:                 # remove prefixos encadeados
        anterior = s
        s = _PREFIXOS.sub("", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s
