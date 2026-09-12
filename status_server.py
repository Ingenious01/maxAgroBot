"""API статуса онбординга для miniapp. Запуск: python status_server.py"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json

from backend.storage.storage import get_user

HOST = "0.0.0.0"
PORT = 8765


class Handler(BaseHTTPRequestHandler):
    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/status":
            self.send_response(404)
            self._cors()
            self.end_headers()
            return

        qs = parse_qs(parsed.query)
        try:
            user_id = int(qs.get("user_id", [""])[0])
        except (TypeError, ValueError):
            body = b'{"error":"user_id required"}'
            self.send_response(400)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return

        row = get_user(user_id=user_id)
        payload = {
            "user_id": user_id,
            "consent": bool(row.get("consent")),
            "onboarded": bool(row.get("onboarded")),
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[status] {args[0]}")


if __name__ == "__main__":
    print(f"Status API: http://127.0.0.1:{PORT}/api/status?user_id=...")
    HTTPServer((HOST, PORT), Handler).serve_forever()