import datetime
from deploy.runner import janela_datas, cron_autorizado

def test_janela_datas():
    hoje = datetime.date(2026, 6, 13)
    desde, ate = janela_datas(hoje, 7)
    assert desde == "2026-06-06"
    assert ate == "2026-06-13"

def test_cron_autorizado_ok():
    assert cron_autorizado("Bearer s3cr3t", "s3cr3t") is True

def test_cron_recusa_sem_secret_ou_errado():
    assert cron_autorizado("Bearer x", None) is False      # sem secret -> fail-closed
    assert cron_autorizado(None, "s3cr3t") is False
    assert cron_autorizado("Bearer outro", "s3cr3t") is False
