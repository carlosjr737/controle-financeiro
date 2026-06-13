import openpyxl
from controle_financeiro.models import Categoria, Transacao
from controle_financeiro.regras_negocio import eh_estorno

def _garantir_categoria(sessao, nome: str) -> Categoria:
    cat = sessao.query(Categoria).filter_by(nome=nome).one_or_none()
    if cat is None:
        cat = Categoria(nome=nome)
        sessao.add(cat); sessao.flush()
    return cat

def importar_historico(caminho_xlsx: str, sessao) -> None:
    wb = openpyxl.load_workbook(caminho_xlsx, data_only=True)

    # 1) vocabulario de categorias
    if "Classificações" in wb.sheetnames:
        for row in wb["Classificações"].iter_rows(min_row=2, values_only=True):
            nome = row[0] if row else None
            if nome and str(nome).strip():
                _garantir_categoria(sessao, str(nome).strip())

    # 2) transacoes das abas "Fatura ..."
    for nome_aba in wb.sheetnames:
        if not nome_aba.startswith("Fatura"):
            continue
        ws = wb[nome_aba]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or row[1] in (None, "", "Estabelecimento"):
                continue
            row_padded = list(row) + [None] * 7
            data, estab, portador, valor, parcela, classificacao = row_padded[:6]
            if valor is None or estab is None:
                continue
            if eh_estorno(float(valor), classificacao):
                sessao.add(Transacao(
                    estabelecimento=str(estab),
                    portador=portador,
                    valor=float(valor),
                    parcela=_str(parcela),
                    status_classificacao="estorno",
                    mes_competencia=_competencia(data)))
                continue
            cat = _garantir_categoria(sessao, str(classificacao).strip()) if classificacao else None
            sessao.add(Transacao(
                estabelecimento=str(estab),
                portador=portador,
                valor=float(valor),
                parcela=_str(parcela),
                categoria_id=cat.id if cat else None,
                status_classificacao="confirmada" if cat else "pendente",
                confianca=1.0 if cat else 0.0,
                mes_competencia=_competencia(data)))
    sessao.commit()

def _str(v):
    return None if v is None else str(v)

def _competencia(data) -> str | None:
    if data is None:
        return None
    txt = str(data)
    return txt[:7] if len(txt) >= 7 else None
