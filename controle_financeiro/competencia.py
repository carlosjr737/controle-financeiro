"""Competência por ciclo de fatura do cartão.
Se o gasto é depois do dia de fechamento, ele cai na fatura do mês seguinte."""

def competencia_fatura(data_iso: str, dia_fechamento: int) -> str:
    ano = int(data_iso[:4]); mes = int(data_iso[5:7]); dia = int(data_iso[8:10])
    if dia > dia_fechamento:
        mes += 1
        if mes > 12:
            mes = 1; ano += 1
    return f"{ano:04d}-{mes:02d}"


def competencia_ciclo(data_iso: str, dia_fechamento: int) -> str:
    """Ciclo da fatura ABERTA, rotulado pelo mês que ele COBRE (não o que paga).
    A fatura fecha no dia `dia_fechamento`. Tudo até o fechamento pertence ao
    ciclo do mês anterior; depois do fechamento, ao ciclo do mês corrente.
    Ex. (fecha dia 7): 10/jun -> 2026-06 ; 05/jun -> 2026-05 ; 03/jul -> 2026-06."""
    if len(data_iso) < 10:
        return data_iso[:7] if len(data_iso) >= 7 else ""
    ano = int(data_iso[:4]); mes = int(data_iso[5:7]); dia = int(data_iso[8:10])
    if dia <= dia_fechamento:
        mes -= 1
        if mes < 1:
            mes = 12; ano -= 1
    return f"{ano:04d}-{mes:02d}"
