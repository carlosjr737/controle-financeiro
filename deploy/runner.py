"""Helpers para os entrypoints (janela de datas e autorização do cron Vercel)."""
import datetime

def janela_datas(hoje: datetime.date, dias: int) -> tuple[str, str]:
    """Janela rolante: do (hoje - dias) até hoje, em ISO YYYY-MM-DD.
    Rodando diariamente + dedup por id_externo, cobre todas as transações novas."""
    desde = (hoje - datetime.timedelta(days=dias)).isoformat()
    return desde, hoje.isoformat()

def cron_autorizado(auth_header: str | None, secret: str | None) -> bool:
    """Vercel envia 'Authorization: Bearer <CRON_SECRET>' nos disparos de cron.
    Sem secret configurado, recusa (fail-closed)."""
    if not secret:
        return False
    return auth_header == f"Bearer {secret}"
