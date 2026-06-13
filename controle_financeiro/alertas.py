# controle_financeiro/alertas.py
def linhas_em_alerta(linhas: list[dict], amarelo: float = 0.8) -> list[dict]:
    em_alerta = [l for l in linhas if l.get("pct", 0.0) >= amarelo]
    return sorted(em_alerta, key=lambda l: l.get("pct", 0.0), reverse=True)
