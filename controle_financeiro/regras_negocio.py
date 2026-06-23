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


def eh_pagamento_cartao_conta(descricao: str | None) -> bool:
    """Saída da conta corrente pra pagar o cartão (débito automático ou Pix).
    Excluída do gasto pra não contar em dobro com as compras do cartão."""
    d = (descricao or "").strip().lower()
    return ("pagamento para banco xp" in d) or ("pagamento de fatura" in d)
