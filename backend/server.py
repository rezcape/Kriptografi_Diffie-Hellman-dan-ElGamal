"""
Backend Server (modul bawaan Python, tanpa framework eksternal).
Mengintegrasikan langsung:
- diffie_hellman.py untuk pertukaran kunci sesi saat Login & Register
- ElGamal.py untuk enkripsi dan dekripsi pesan Chat antar-user (ala WhatsApp)

Jalankan dari root repo:
    python3 backend/server.py
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import diffie_hellman
import ElGamal

PORT = 3002
HOST = "127.0.0.1"
ALLOWED_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173"}


def load_env(filepath):
    if not os.path.exists(filepath):
        print("backend/.env tidak ditemukan, lanjut tanpa variabel tambahan.")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip()
            if len(val) >= 2 and ((val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'")):
                val = val[1:-1]
            if key and key not in os.environ:
                os.environ[key] = val


load_env(os.path.join(BACKEND_DIR, ".env"))
load_env(os.path.join(BACKEND_DIR, ".env.example"))

# Parameter publik Diffie-Hellman Server (Bob) untuk Login & Register
DH_P = 49157
DH_G = diffie_hellman.find_generator(DH_P)
DH_SERVER_PRIV_B = diffie_hellman.generate_private_key(DH_P)
DH_SERVER_PUB_B = diffie_hellman.generate_public_key(DH_G, DH_SERVER_PRIV_B, DH_P)

# Parameter grup ElGamal (sesuai contoh PPT Pertemuan ke-9: p = 2273, g = 3)
ELGAMAL_P = 2273
ELGAMAL_G = 3

# Penyimpanan memori: users, sessions, pertemanan, dan pesan chat
users_by_email = {}
users_by_id = {}
sessions = {}       # token -> userId
friendships = {}    # userId -> set of friend userIds
messages = []       # daftar pesan chat
next_user_seq = 1003

weather_cache = {}
WEATHER_TTL_SEC = 600
CITY_PATTERN = re.compile(r"^[\w\s.'-]{1,50}$", re.UNICODE)


def hash_password(password):
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=64)
    return f"{salt.hex()}:{derived.hex()}"


def verify_password(password, stored_hash):
    try:
        salt_hex, key_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(key_hex)
        derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=64)
        return hmac.compare_digest(derived, expected)
    except Exception:
        return False


def seed_initial_users():
    """Seeding kontak demo (USR-1000) dan 2 akun siap login dari .env / .env.example."""
    seed_specs = [
        {
            "userId": "USR-1000",
            "firstName": "Bob",
            "lastName": "(Kontak Demo PPT)",
            "email": "bob@demo.its.ac.id",
            "phone": "081234567890",
            "password": "Demo12345",
            "x": 243,
        },
        {
            "userId": os.environ.get("SEED_USER1_ID", "USR-1001").strip(),
            "firstName": os.environ.get("SEED_USER1_FIRST_NAME", "Hikari").strip(),
            "lastName": os.environ.get("SEED_USER1_LAST_NAME", "Reiziq").strip(),
            "email": os.environ.get("SEED_USER1_EMAIL", "hikari@its.ac.id").strip().lower(),
            "phone": os.environ.get("SEED_USER1_PHONE", "081234567891").strip(),
            "password": os.environ.get("SEED_USER1_PASSWORD", "Password123").strip(),
            "x": int(os.environ.get("SEED_USER1_ELGAMAL_X", "243")),
        },
        {
            "userId": os.environ.get("SEED_USER2_ID", "USR-1002").strip(),
            "firstName": os.environ.get("SEED_USER2_FIRST_NAME", "Arya").strip(),
            "lastName": os.environ.get("SEED_USER2_LAST_NAME", "Bisma").strip(),
            "email": os.environ.get("SEED_USER2_EMAIL", "bisma@its.ac.id").strip().lower(),
            "phone": os.environ.get("SEED_USER2_PHONE", "081234567892").strip(),
            "password": os.environ.get("SEED_USER2_PASSWORD", "Password123").strip(),
            "x": int(os.environ.get("SEED_USER2_ELGAMAL_X", "517")),
        },
    ]

    for spec in seed_specs:
        keys = ElGamal.generate_keys(p=ELGAMAL_P, g=ELGAMAL_G, x=spec["x"])
        full_name = f"{spec['firstName']} {spec['lastName']}".strip()
        user = {
            "userId": spec["userId"],
            "firstName": spec["firstName"],
            "lastName": spec["lastName"],
            "name": full_name,
            "email": spec["email"],
            "phone": spec["phone"],
            "passwordHash": hash_password(spec["password"]),
            "elgamal": keys,
        }
        users_by_email[user["email"]] = user
        users_by_id[user["userId"]] = user
        friendships[user["userId"]] = {"USR-1000"} if user["userId"] != "USR-1000" else set()
        if user["userId"] != "USR-1000":
            friendships.setdefault("USR-1000", set()).add(user["userId"])


seed_initial_users()


def decrypt_dh_password(cipher_list, client_pub_a):
    """Tahap 4 Diffie-Hellman di server: hitung K = A^b mod p lalu buka password."""
    shared_k = diffie_hellman.compute_shared_secret(client_pub_a, DH_SERVER_PRIV_B, DH_P)
    chars = []
    for c_str in cipher_list:
        c_val = int(c_str)
        m_val = (c_val - shared_k) % DH_P
        chars.append(chr(m_val))
    return "".join(chars), shared_k


def public_user_summary(u):
    return {
        "userId": u["userId"],
        "name": u["name"],
        "email": u["email"],
        "elgamalPublic": {
            "p": str(u["elgamal"]["p"]),
            "g": str(u["elgamal"]["g"]),
            "y": str(u["elgamal"]["y"]),
        },
    }


def build_elgamal_message(sender, receiver, text):
    """Menjalankan Tahap 1, 2, dan 3 ElGamal.py untuk satu pesan chat."""
    p = receiver["elgamal"]["p"]
    g = receiver["elgamal"]["g"]
    x = receiver["elgamal"]["x"]
    y = receiver["elgamal"]["y"]

    enc = ElGamal.encrypt_text(text, y, g, p)
    dec = ElGamal.decrypt_text(enc["ciphertext"], x, p)

    msg = {
        "id": f"msg-{int(time.time() * 1000)}-{secrets.token_hex(3)}",
        "fromUserId": sender["userId"],
        "fromName": sender["name"],
        "toUserId": receiver["userId"],
        "toName": receiver["name"],
        "timestamp": time.strftime("%H:%M"),
        "plaintext": dec["plaintext"],
        "ciphertext": enc["ciphertext"],
        "elgamalStages": {
            "stage1": {
                "receiverName": receiver["name"],
                "receiverUserId": receiver["userId"],
                "p": p,
                "g": g,
                "privateX": x,
                "publicY": y,
                "formula": f"y = g^x mod p = {g}^{x} mod {p} = {y}",
            },
            "stage2": enc["steps"][:8],
            "stage3": dec["steps"][:8],
            "totalBlocks": len(enc["steps"]),
        },
    }
    messages.append(msg)
    return msg


class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def send_cors(self):
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 64 * 1024:
            raise ValueError("REQUEST_TOO_LARGE")
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def get_current_user(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:].strip()
            uid = sessions.get(token)
            if uid and uid in users_by_id:
                return users_by_id[uid]
        return None

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/health":
            return self.send_json(200, {"ok": True})

        if path == "/api/dh/params":
            return self.send_json(200, {
                "p": str(DH_P),
                "g": str(DH_G),
                "serverPublicB": str(DH_SERVER_PUB_B),
            })

        if path == "/api/weather":
            city = (query.get("city", [""])[0]).strip()
            return self.handle_weather(city)

        if path == "/api/friends":
            user = self.get_current_user()
            if not user:
                return self.send_json(401, {"error": "UNAUTHORIZED"})
            friend_ids = sorted(friendships.get(user["userId"], set()))
            friend_list = [public_user_summary(users_by_id[fid]) for fid in friend_ids if fid in users_by_id]
            return self.send_json(200, {
                "me": public_user_summary(user),
                "friends": friend_list,
            })

        if path == "/api/chat/messages":
            user = self.get_current_user()
            if not user:
                return self.send_json(401, {"error": "UNAUTHORIZED"})
            friend_id = (query.get("friendId", [""])[0]).strip().upper()
            uid = user["userId"]
            conv = [
                m for m in messages
                if (m["fromUserId"] == uid and m["toUserId"] == friend_id)
                or (m["fromUserId"] == friend_id and m["toUserId"] == uid)
            ]
            return self.send_json(200, {"messages": conv})

        return self.send_json(404, {"error": "NOT_FOUND"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            body = self.read_json()
        except ValueError as e:
            return self.send_json(413 if str(e) == "REQUEST_TOO_LARGE" else 400, {"error": str(e)})
        except Exception:
            return self.send_json(400, {"error": "INVALID_JSON"})

        if path == "/api/auth/register":
            return self.handle_register(body)
        if path == "/api/auth/login":
            return self.handle_login(body)
        if path == "/api/friends/add":
            return self.handle_add_friend(body)
        if path == "/api/chat/send":
            return self.handle_send_message(body)

        return self.send_json(404, {"error": "NOT_FOUND"})

    def handle_register(self, body):
        global next_user_seq
        first_name = str(body.get("firstName", "")).strip()
        last_name = str(body.get("lastName", "")).strip()
        email = str(body.get("email", "")).strip().lower()
        phone = str(body.get("phone", "")).strip()
        enc_pass = body.get("encryptedPassword")
        client_pub_a = body.get("clientPublicA")

        if not first_name or not last_name or not email or not phone or not isinstance(enc_pass, list) or not client_pub_a:
            return self.send_json(400, {"error": "INVALID_REQUEST"})
        if email in users_by_email:
            return self.send_json(409, {"error": "EMAIL_TAKEN"})

        try:
            password, _ = decrypt_dh_password(enc_pass, int(client_pub_a))
        except Exception:
            return self.send_json(400, {"error": "INVALID_PASSWORD"})
        if not password:
            return self.send_json(400, {"error": "INVALID_PASSWORD"})

        user_id = f"USR-{next_user_seq}"
        next_user_seq += 1
        elgamal_keys = ElGamal.generate_keys(p=ELGAMAL_P, g=ELGAMAL_G)
        full_name = f"{first_name} {last_name}".strip()

        user = {
            "userId": user_id,
            "firstName": first_name,
            "lastName": last_name,
            "name": full_name,
            "email": email,
            "phone": phone,
            "passwordHash": hash_password(password),
            "elgamal": elgamal_keys,
        }
        users_by_email[email] = user
        users_by_id[user_id] = user
        friendships[user_id] = {"USR-1000"}
        friendships["USR-1000"].add(user_id)

        # Kirim satu pesan sambutan terenkripsi ElGamal dari Bob (USR-1000)
        build_elgamal_message(
            users_by_id["USR-1000"],
            user,
            f"Halo {first_name}! ID akunmu adalah {user_id}. Kamu bisa tambah teman pakai User ID!",
        )

        return self.send_json(201, {"userId": user_id})

    def handle_login(self, body):
        email = str(body.get("email", "")).strip().lower()
        enc_pass = body.get("encryptedPassword")
        client_pub_a = body.get("clientPublicA")

        user = users_by_email.get(email)
        if not user or not isinstance(enc_pass, list) or not client_pub_a:
            return self.send_json(401, {"error": "INVALID_CREDENTIALS"})

        try:
            password, shared_k = decrypt_dh_password(enc_pass, int(client_pub_a))
        except Exception:
            return self.send_json(401, {"error": "INVALID_CREDENTIALS"})

        if not verify_password(password, user["passwordHash"]):
            return self.send_json(401, {"error": "INVALID_CREDENTIALS"})

        token = f"session-{secrets.token_hex(16)}"
        sessions[token] = user["userId"]

        return self.send_json(200, {
            "token": token,
            "user": public_user_summary(user),
            "dhServer": {
                "p": str(DH_P),
                "g": str(DH_G),
                "serverPublicB": str(DH_SERVER_PUB_B),
                "sharedSecretK": str(shared_k),
                "formulaServerK": f"A^b mod p = {client_pub_a}^{DH_SERVER_PRIV_B} mod {DH_P} = {shared_k}",
            },
        })

    def handle_add_friend(self, body):
        user = self.get_current_user()
        if not user:
            return self.send_json(401, {"error": "UNAUTHORIZED"})

        raw_id = str(body.get("friendId", "")).strip().upper()
        if raw_id.isdigit():
            raw_id = f"USR-{raw_id}"

        if not raw_id or raw_id not in users_by_id:
            return self.send_json(404, {"error": "USER_NOT_FOUND"})
        if raw_id == user["userId"]:
            return self.send_json(400, {"error": "CANNOT_ADD_SELF"})

        friendships.setdefault(user["userId"], set()).add(raw_id)
        friendships.setdefault(raw_id, set()).add(user["userId"])

        friend = users_by_id[raw_id]
        return self.send_json(200, {"friend": public_user_summary(friend)})

    def handle_send_message(self, body):
        user = self.get_current_user()
        if not user:
            return self.send_json(401, {"error": "UNAUTHORIZED"})

        to_id = str(body.get("toUserId", "")).strip().upper()
        text = str(body.get("text", "")).strip()
        if not to_id or to_id not in users_by_id or not text:
            return self.send_json(400, {"error": "INVALID_MESSAGE"})

        receiver = users_by_id[to_id]
        friendships.setdefault(user["userId"], set()).add(to_id)
        friendships.setdefault(to_id, set()).add(user["userId"])

        msg = build_elgamal_message(user, receiver, text)

        # Jika mengirim ke kontak demo USR-1000, balas otomatis agar mudah diuji
        if to_id == "USR-1000":
            reply_text = f"Pesan '{text}' berhasil didekripsi dengan ElGamal (p={ELGAMAL_P}, g={ELGAMAL_G})!"
            build_elgamal_message(receiver, user, reply_text)

        return self.send_json(201, {"message": msg})

    def handle_weather(self, city):
        if not city or not CITY_PATTERN.match(city):
            return self.send_json(400, {"error": "INVALID_CITY"})

        api_key = os.environ.get("OPENWEATHER_API_KEY", "").strip()
        if not api_key or api_key == "isi_api_key_openweather_disini":
            return self.send_json(503, {"error": "WEATHER_KEY_MISSING"})

        cache_key = city.lower()
        now = time.time()
        hit = weather_cache.get(cache_key)
        if hit and hit["expires"] > now:
            return self.send_json(200, hit["data"])

        params = urllib.parse.urlencode({
            "q": city,
            "units": "metric",
            "lang": "id",
            "appid": api_key,
        })
        url = f"https://api.openweathermap.org/data/2.5/weather?{params}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Kriptografi-App/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return self.send_json(502, {"error": "WEATHER_KEY_INVALID"})
            if e.code == 404:
                return self.send_json(404, {"error": "CITY_NOT_FOUND"})
            return self.send_json(502, {"error": "WEATHER_UPSTREAM"})
        except Exception:
            return self.send_json(502, {"error": "WEATHER_UPSTREAM"})

        w = (raw.get("weather") or [{}])[0]
        main = raw.get("main") or {}
        wind = raw.get("wind") or {}
        sys_info = raw.get("sys") or {}
        icon = w.get("icon", "")

        data = {
            "city": raw.get("name", city),
            "country": sys_info.get("country"),
            "temp": round(main.get("temp", 0)),
            "feelsLike": round(main.get("feels_like", 0)),
            "description": w.get("description", ""),
            "humidity": main.get("humidity", 0),
            "windKmh": round(float(wind.get("speed", 0)) * 3.6),
            "pressure": main.get("pressure", 0),
            "conditionCode": w.get("id"),
            "isNight": isinstance(icon, str) and icon.endswith("n"),
            "dt": raw.get("dt", int(now)),
            "timezone": raw.get("timezone", 25200),
        }
        weather_cache[cache_key] = {"data": data, "expires": now + WEATHER_TTL_SEC}
        return self.send_json(200, data)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), RequestHandler)
    print(f"Backend berjalan di http://localhost:{PORT}")
    print(f"Parameter Diffie-Hellman Server: p={DH_P}, g={DH_G}, B={DH_SERVER_PUB_B}")
    print(f"Parameter ElGamal Chat         : p={ELGAMAL_P}, g={ELGAMAL_G}")
    print("Akun Seeding Siap Login:")
    print("  1) USR-1001 | hikari@its.ac.id | Password123")
    print("  2) USR-1002 | bisma@its.ac.id  | Password123")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBackend dihentikan.")

