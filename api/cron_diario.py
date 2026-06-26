"""Entrypoint único do Vercel.
- GET: ciclo diário (cron). Protegido por CRON_SECRET (Authorization: Bearer).
- POST: webhook do Telegram (cliques de botão). Protegido pelo secret_token."""
import os, sys, json, datetime
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deploy.runner import cron_autorizado
from deploy.main import rodar_ciclo
from deploy.fechar_mes_main import rodar_fechamento
from deploy.telegram_callback import tratar_update


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
        probe = self.headers.get("X-Probe") or ("fatura" if "probe=fatura" in (self.path or "") else None)
        if probe:
            try:
                from deploy.probe_fatura import probar_fatura, probar_parcelas
                fn = {"fatura": probar_fatura, "parcelas": probar_parcelas}.get(probe)
                if fn:
                    return self._responder(200, {"ok": True, "probe": fn()})
                return self._responder(400, {"ok": False, "erro": f"probe '{probe}' desconhecido"})
            except Exception as e:  # noqa: BLE001
                return self._responder(500, {"ok": False, "erro": str(e)})
        try:
            hoje = _hoje_sp()
            ciclo = rodar_ciclo(hoje=hoje)
            fechamento = rodar_fechamento(hoje=hoje) if hoje.day == 1 else None
            self._responder(200, {"ok": True, "ciclo": ciclo, "fechamento": fechamento})
        except Exception as e:  # noqa: BLE001
            self._responder(500, {"ok": False, "erro": str(e)})

    def do_POST(self):
        # Telegram envia o secret no header X-Telegram-Bot-Api-Secret-Token
        if self.headers.get("X-Telegram-Bot-Api-Secret-Token") != os.environ.get("CRON_SECRET"):
            return self._responder(401, {"ok": False})
        try:
            n = int(self.headers.get("Content-Length", 0))
            update = json.loads(self.rfile.read(n) or b"{}")
            tratar_update(update)
            self._responder(200, {"ok": True})
        except Exception as e:  # noqa: BLE001
            self._responder(200, {"ok": False, "erro": str(e)})  # 200 p/ o Telegram não reenviar

    def _responder(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
