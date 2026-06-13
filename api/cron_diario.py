"""Entrypoint único do Vercel (Python). Roda o ciclo diário e, no dia 1 (fuso de
São Paulo), também o fechamento do mês anterior. Protegido por CRON_SECRET."""
import os, sys, json, datetime
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deploy.runner import cron_autorizado
from deploy.main import rodar_ciclo
from deploy.fechar_mes_main import rodar_fechamento


def _hoje_sp() -> datetime.date:
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    except Exception:  # noqa: BLE001
        return datetime.date.today()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not cron_autorizado(self.headers.get("Authorization"),
                               os.environ.get("CRON_SECRET")):
            return self._responder(401, {"ok": False, "erro": "nao autorizado"})
        try:
            hoje = _hoje_sp()
            ciclo = rodar_ciclo(hoje=hoje)
            fechamento = rodar_fechamento(hoje=hoje) if hoje.day == 1 else None
            self._responder(200, {"ok": True, "ciclo": ciclo, "fechamento": fechamento})
        except Exception as e:  # noqa: BLE001
            self._responder(500, {"ok": False, "erro": str(e)})

    def _responder(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
