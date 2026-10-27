"""
Server statis untuk frontend di http://localhost:5173 (modul bawaan Python).
Menyajikan folder frontend/ dan memetakan /crypto/* ke folder crypto/.

Jalankan dari root repo:
    python3 frontend/dev_server.py
"""
import mimetypes
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 5173
HOST = "127.0.0.1"

FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
CRYPTO_DIR = os.path.abspath(os.path.join(FRONTEND_DIR, "..", "crypto"))
SELF_FILE = os.path.abspath(__file__)

MIME_MAP = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".ico": "image/x-icon",
}


def resolve_request_path(url_path):
    try:
        decoded = urllib.parse.unquote(url_path)
    except Exception:
        return None
    if "\0" in decoded:
        return None

    root = FRONTEND_DIR
    rel = decoded
    if decoded == "/crypto" or decoded.startswith("/crypto/"):
        root = CRYPTO_DIR
        rel = decoded[len("/crypto"):]
    if rel in ("", "/"):
        rel = "/login.html" if root == FRONTEND_DIR else "/index.js"

    full_path = os.path.abspath(os.path.join(root, "." + rel))
    if full_path != root and not full_path.startswith(root + os.sep):
        return None
    if full_path == SELF_FILE or os.path.basename(full_path).startswith("."):
        return None
    return full_path


class StaticHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        self.serve_file(head_only=False)

    def do_HEAD(self):
        self.serve_file(head_only=True)

    def serve_file(self, head_only=False):
        parsed = urllib.parse.urlparse(self.path)
        file_path = resolve_request_path(parsed.path)
        if not file_path or not os.path.isfile(file_path):
            body = "404 Tidak ditemukan".encode("utf-8")
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if not head_only:
                self.wfile.write(body)
            return

        ext = os.path.splitext(file_path)[1].lower()
        content_type = MIME_MAP.get(ext) or mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        size = os.path.getsize(file_path)

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if not head_only:
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), StaticHandler)
    print(f"Frontend berjalan di http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nFrontend dihentikan.")

