import openpyxl, pytest

@pytest.fixture
def planilha_fake(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Fatura Mai"
    ws.append(["Data", "Estabelecimento", "Portador", "Valor", "Parcela", "Classificação", "Status"])
    ws.append(["2026-05-06", "DL *UBERRIDES", "CARLOS JUNIOR", 27.98, "-", "Uber", "Fatura atual"])
    ws.append(["2026-05-06", "EBN *SPOTIFY", "CARLOS JUNIOR", 40.90, "-", "Streamings", "Fatura atual"])
    ws.append(["2026-05-05", "TB* HOTELC", "CARLOS JUNIOR", -124.55, "-", "Estornado", "Fatura atual"])
    cls = wb.create_sheet("Classificações")
    cls.append(["Classificações"])
    for nome in ["Uber", "Streamings", "Supermercado", "Outros"]:
        cls.append([nome])
    caminho = tmp_path / "fake.xlsx"
    wb.save(caminho)
    return str(caminho)
