"""Competência por ciclo de fatura do cartão.
Se o gasto é depois do dia de fechamento, ele cai na fatura do mês seguinte."""

def competencia_fatura(data_iso: str, dia_fechamento: int) -> str:
    ano = int(data_iso[:4]); mes = int(data_iso[5:7]); dia = int(data_iso[8:10])
    if dia > dia_fechamento:
        mes += 1
        if mes > 12:
            mes = 1; ano += 1
    return f"{ano:04d}-{mes:02d}"
