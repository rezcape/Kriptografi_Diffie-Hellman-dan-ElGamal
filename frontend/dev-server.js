// Server statis untuk pengembangan (opsional jika ingin menjalankan dengan Node).
// Menyajikan frontend/ di http://localhost:5173 dan memetakan /crypto/* ke folder crypto/.
//
// Jalankan dari root repo: node frontend/dev-server.js (atau python3 frontend/dev_server.py)

import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const PORT = 5173;
const HOST = "127.0.0.1";

const FRONTEND_DIR = path.dirname(fileURLToPath(import.meta.url));
const CRYPTO_DIR = path.resolve(FRONTEND_DIR, "..", "crypto");
const SELF = fileURLToPath(import.meta.url);

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".ico": "image/x-icon",
};

function resolveRequest(urlPath) {
  let decoded;
  try {
    decoded = decodeURIComponent(urlPath);
  } catch {
    return null;
  }
  if (decoded.includes("\0")) return null;

  let root = FRONTEND_DIR;
  let rel = decoded;
  if (decoded === "/crypto" || decoded.startsWith("/crypto/")) {
    root = CRYPTO_DIR;
    rel = decoded.slice("/crypto".length);
  }
  if (rel === "/" || rel === "") rel = root === FRONTEND_DIR ? "/login.html" : "/index.js";

  const filePath = path.resolve(root, "." + rel);
  if (filePath !== root && !filePath.startsWith(root + path.sep)) return null;
  if (filePath === SELF) return null;
  if (path.basename(filePath).startsWith(".")) return null;
  return filePath;
}

function notFound(res) {
  res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
  res.end("404 Tidak ditemukan");
}

const server = http.createServer((req, res) => {
  if (req.method !== "GET" && req.method !== "HEAD") {
    res.writeHead(405, { Allow: "GET, HEAD" });
    res.end();
    return;
  }

  const { pathname } = new URL(req.url, `http://${req.headers.host || "localhost"}`);
  const filePath = resolveRequest(pathname);
  if (!filePath) return notFound(res);

  fs.stat(filePath, (err, stat) => {
    if (err || !stat.isFile()) return notFound(res);
    const type = MIME[path.extname(filePath).toLowerCase()];
    if (!type) return notFound(res);
    res.writeHead(200, {
      "Content-Type": type,
      "Content-Length": stat.size,
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    });
    if (req.method === "HEAD") return res.end();
    fs.createReadStream(filePath).pipe(res);
  });
});

server.listen(PORT, HOST, () => {
  console.log(`Frontend berjalan di http://localhost:${PORT}`);
});

