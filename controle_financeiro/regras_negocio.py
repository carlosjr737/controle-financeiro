_CATEGORIAS_TRANSFERENCIA = {"transferência", "transferencia", "movimentação interna"}

def eh_estorno(valor: float, classificacao: str | None) -> bool:
    if classificacao and classificacao.strip().lower() == "estornado":
        return True
    return False

def eh_transferencia_interna(estabelecimento: str, categoria: str | None) -> bool:
    cat = (categoria or "").strip().lower()
    return cat in _CATEGORIAS_TRANSFERENCIA


def eh_pagamento_fatura(descricao: str | None) -> bool:
    return "pagamento recebido" in (descricao or "").strip().lower()


NOME_PGTO_FATURA = "PGTO FATURA"

def eh_categoria_pagamento(nome: str | None) -> bool:
    return (nome or "").strip().upper() == NOME_PGTO_FATURA
