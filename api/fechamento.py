"""Função serverless do Vercel — disparada pelo Vercel Cron no dia 1.
Fecha o mês anterior e escreve a aba 'Realizado' no Sheets. Protegida por CRON_SECRET."""
import os, sys, json
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deploy.runner import cron_autorizado
from deploy.fechar_mes_main import rodar_fechamento


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not cron_autorizado(self.headers.get("Authorization"),
                               os.environ.get("CRON_SECRET")):
            self._responder(401, {"ok": False, "erro": "nao autorizado"}); return
        try:
            resumo = rodar_fechamento()
            self._responder(200, {"ok": True, "resumo": resumo})
        except Exception as e:  # noqa: BLE001
            self._responder(500, {"ok": False, "erro": str(e)})

    def _responder(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
