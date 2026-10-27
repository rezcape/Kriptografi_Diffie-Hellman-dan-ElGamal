# Kriptografi: Diffie-Hellman Login & ElGamal Multi-User Chat

Aplikasi web autentikasi dan percakapan terenkripsi (ala WhatsApp) menggunakan algoritma **Diffie-Hellman Key Exchange** (`diffie_hellman.py`) untuk pengamanan Login serta **ElGamal Public-Key Cryptography** (`ElGamal.py`) untuk enkripsi pesan Chat antar-pengguna, dilengkapi tampilan Cuaca Surabaya dari OpenWeather API.

Seluruh perhitungan kriptografi ditulis **murni dari nol tanpa library atau framework kriptografi eksternal**.

## Identitas Kelompok 4 (Kelas A)

| No. | Nama Lengkap | NRP |
|---:|---|---|
| 1 | Arya Bisma Putra Refman | 5027241036 |
| 2 | M.Hikari Reiziq Rakhmadinta | 5027241079 |
| 3 | Ahmad Syauqi Reza | 5027141085 |

---

## 1. Menjalankan Program lewat Terminal (CLI)

Kedua modul utama dapat dijalankan langsung untuk menampilkan setiap tahapan perhitungan matematis:

```bash
# Menjalankan simulasi tahapan Diffie-Hellman (Tahap 1 s.d. 5)
python3 diffie_hellman.py

# Menjalankan simulasi tahapan ElGamal (Tahap 1 s.d. 4, termasuk contoh slide PPT 'HALO')
python3 ElGamal.py
```

---

## 2. Menjalankan Aplikasi Web (2 Terminal dari Root Repo)

### Terminal 1 — Backend Server (Port 3002)
```bash
python3 backend/server.py
```
*(File `backend/.env` sudah berisi `OPENWEATHER_API_KEY` untuk memuat data cuaca Surabaya).*

### Terminal 2 — Frontend Server (Port 5173)
```bash
python3 frontend/dev_server.py
```

---

## 3. Akun Seeding Siap Login (Dari `.env.example` / `.env`)

Saat `backend/server.py` dijalankan, **2 akun sudah otomatis di-seed** sehingga Anda dan teman kelompok bisa langsung login di 2 tab berbeda tanpa perlu daftar manual:

| Akun | User ID | Email | Password | Kunci Publik ElGamal $(y, g, p)$ |
|---|---|---|---|---|
| **Akun 1 (Hikari)** | `USR-1001` | `hikari@its.ac.id` | `Password123` | `(461, 3, 2273)` |
| **Akun 2 (Bisma)** | `USR-1002` | `bisma@its.ac.id` | `Password123` | `(1806, 3, 2273)` |

### Langkah Uji Cepat:
1. Buka **Tab 1** di **http://localhost:5173** $\rightarrow$ Login dengan `hikari@its.ac.id` / `Password123`.
2. Buka **Tab 2** di **http://localhost:5173** $\rightarrow$ Login dengan `bisma@its.ac.id` / `Password123`.
3. Di kotak **Chat ElGamal** (Tab 1), ketik `USR-1002` pada kolom **Tambah teman pakai User ID**, klik **+ Tambah**, lalu kirim pesan!
4. Klik **"Lihat Tahapan ElGamal (Tahap 1, 2, 3)"** di bawah gelembung pesan untuk melihat proses pembangkitan kunci penerima $(y, g, p)$, enkripsi pasangan cipherteks $(a, b)$, dan dekripsi invers modulo $m = b \cdot (a^x)^{-1} \bmod p$.

