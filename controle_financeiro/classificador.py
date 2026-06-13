from dataclasses import dataclass
from typing import Callable, Optional
from controle_financeiro.models import Regra, Categoria
from controle_financeiro.normalizacao import normalizar_estabelecimento

@dataclass
class Resultado:
    categoria_nome: Optional[str]
    confianca: float
    origem: str          # "regra" | "substring" | "fallback" | "pendente"
    motivo: str = ""

class Classificador:
    def __init__(self, sessao, fallback: Optional[Callable[[str, list], Optional[str]]] = None):
        self.sessao = sessao
        self.fallback = fallback

    def _nome(self, categoria_id) -> Optional[str]:
        cat = self.sessao.get(Categoria, categoria_id)
        return cat.nome if cat else None

    def classificar(self, estabelecimento: str) -> Resultado:
        chave = normalizar_estabelecimento(estabelecimento)

        # 1) regra exata
        regra = (self.sessao.query(Regra).filter_by(padrao=chave)
                 .order_by(Regra.prioridade.desc()).first())
        if regra:
            return Resultado(self._nome(regra.categoria_id), 1.0, "regra",
                             f"match exato '{chave}'")

        # 2) substring (padrao conhecido contido na chave)
        for r in self.sessao.query(Regra).all():
            if r.padrao and r.padrao in chave:
                return Resultado(self._nome(r.categoria_id), 0.7, "substring",
                                 f"padrao '{r.padrao}' contido em '{chave}'")

        # 3) fallback injetavel (LLM no Plano 3)
        if self.fallback:
            cats = [c.nome for c in self.sessao.query(Categoria).all()]
            nome = self.fallback(chave, cats)
            if nome:
                return Resultado(nome, 0.5, "fallback", "sugerido pelo fallback")

        return Resultado(None, 0.0, "pendente", "sem regra nem fallback")
