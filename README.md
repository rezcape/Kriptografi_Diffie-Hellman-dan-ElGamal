# Implementasi Diffie-Hellman Key Exchange dan ElGamal Cryptography

> Tugas Praktikum Kriptografi (Kelas A) — Week 7  
> Departemen Teknologi Informasi, Fakultas Teknologi Elektro dan Informatika Cerdas  
> Institut Teknologi Sepuluh Nopember (ITS), Surabaya  
> Semester Gasal 2026/2027

Aplikasi web autentikasi dan percakapan terenkripsi multi-pengguna menggunakan algoritma **Diffie-Hellman Key Exchange** (`diffie_hellman.py`) untuk pengamanan sesi login serta **ElGamal Public-Key Cryptography** (`ElGamal.py`) untuk enkripsi pesan chat antar-pengguna, dilengkapi integrasi cuaca dari OpenWeather API.

Seluruh operasi matematis kriptografi ditulis **murni dari nol tanpa library atau framework kriptografi eksternal**.

---

## Identitas Kelompok 4 (Kelas A)

| No. | Nama Lengkap | NRP |
|:---:|---|:---:|
| 1 | Arya Bisma Putra Refman | 5027241036 |
| 2 | M. Hikari Reiziq Rakhmadinta | 5027241079 |
| 3 | Ahmad Syauqi Reza | 5027141085 *(atau 5027241085)* |

**Dosen Pengampu:** Annisaa Sri Indrawanti, S.Kom., M.Kom.

---

## Dokumen dan Laporan Resmi

Laporan lengkap berstandar akademik yang memuat teori, perancangan arsitektur, pemetaan fungsi ke kode sumber, 13 skenario pengujian endpoint, analisis batasan, dan daftar pustaka tersedia dalam berkas berikut:

- **Laporan Format Markdown:** [README_LAPORAN.md](README_LAPORAN.md) *(Laporan komprehensif 7 bagian dengan diagram alur dan tangkapan layar)*
- **Laporan Format Word (.docx):** [Laporan_Kelompok_4_Diffie-Hellman_ElGamal.docx](Laporan_Kelompok_4_Diffie-Hellman_ElGamal.docx) *(Format dokumen resmi 21 halaman dengan gambar tersemat)*
- **Arsip Pengumpulan ZIP:** `Kelompok_4_Arya_Hikari_Syauqi.zip` *(Arsip final sesuai penamaan tugas Classroom ITS)*

---

## Fitur Utama Sistem

1. **Implementasi Kriptografi Mandiri (From Scratch):**
   - Modul `random` pada Python hanya difungsikan untuk pembangkitan bilangan acak.
   - Perpangkatan modular (*square-and-multiply* berbobot $O(\log e)$), uji prima *Miller-Rabin*, pencarian akar primitif / generator, pembangkitan kunci, enkripsi pasangan $(a, b)$, dan dekripsi invers modulo via *Teorema Kecil Fermat* ditulis murni dari nol.
2. **Antarmuka CLI untuk Pembuktian Tahapan:**
   - Menyediakan simulasi setiap tahapan perhitungan matematis secara terisolasi, baik dengan data acak, masukan parameter manual, maupun verifikasi contoh resmi dari slide materi perkuliahan Pertemuan ke-9.
3. **Pengamanan Login Menggunakan Diffie-Hellman:**
   - Klien (browser) dan server menyepakati *Shared Secret Key* ($K$) melalui kanal tidak aman tanpa pernah mentransmisikan kunci privat maupun kata sandi asli dalam bentuk plainteks.
4. **Percakapan Multi-Akun Menggunakan ElGamal:**
   - Setiap pengguna memiliki User ID unik (misalnya `USR-1001` dan `USR-1002`) serta pasangan kunci ElGamal masing-masing.
   - Menggunakan enkripsi probabilistik di mana teks yang sama menghasilkan pasangan cipherteks $(a, b)$ yang berbeda pada setiap pengiriman.
   - Dilengkapi inspektur tahapan pada setiap gelembung pesan untuk membedah perhitungan Tahap 1, 2, dan 3.
5. **Seeding Akun Otomatis:**
   - Server otomatis menyiapkan 2 akun siap pakai saat pertama kali dijalankan sehingga proses pengujian multi-tab dapat dilakukan tanpa registrasi manual.

---

## 1. Menjalankan Program lewat Terminal (CLI)

Kedua modul kriptografi dapat dijalankan secara langsung melalui terminal untuk memverifikasi langkah perhitungan matematis:

```bash
# Menjalankan simulasi tahapan Diffie-Hellman (Tahap 1 s.d. 5)
python3 diffie_hellman.py

# Menjalankan simulasi tahapan ElGamal (Tahap 1 s.d. 4, termasuk contoh slide PPT 'HALO')
python3 ElGamal.py
```

### Opsi Menu CLI:
- **`diffie_hellman.py`:**
  - `[1]` Bangkitkan parameter acak (prima $p$ dan generator $g$)
  - `[2]` Masukkan parameter manual (misal: contoh slide $p=251, g=6, a=124, b=158 \implies K=79$)
- **`ElGamal.py`:**
  - `[1]` Pembangkitan kunci dan enkripsi string acak
  - `[2]` Masukan manual parameter dan teks
  - `[3]` Menjalankan contoh resmi slide materi perkuliahan ($p=2273, g=3, x=243, y=461$, pesan `'HALO'`)

---

## 2. Menjalankan Aplikasi Web (Dua Terminal)

Jalankan perintah berikut dari direktori root repositori:

### Terminal 1 — Backend Server (Port 3002)
```bash
python3 backend/server.py
```
> Server HTTP Python murni akan aktif melayani API pada `http://127.0.0.1:3002`.

### Terminal 2 — Frontend Server (Port 5173)
```bash
python3 frontend/dev_server.py
```
> Server statis frontend akan aktif melayani antarmuka pada `http://localhost:5173`.

---

## 3. Akun Uji Coba Terdaftar (Seeding)

Dua akun telah di-seed secara otomatis pada file konfigurasi:

| Akun | User ID | Email | Password | Kunci Privat $x$ | Kunci Publik ElGamal $(y, g, p)$ |
|---|---|---|---|:---:|:---:|
| Hikari Reiziq | `USR-1001` | `hikari@its.ac.id` | `Password123` | `243` | `(461, 3, 2273)` |
| Arya Bisma | `USR-1002` | `bisma@its.ac.id` | `Password123` | `517` | `(571, 3, 2273)` |

*Keterangan:* Kunci publik Bisma dihitung melalui formula $y = g^x \bmod p = 3^{517} \bmod 2273 = 571$.

### Prosedur Pengujian Aplikasi:
1. Buka **Tab 1** pada `http://localhost:5173`, kemudian login menggunakan `hikari@its.ac.id` / `Password123`.
2. Buka **Tab 2** pada `http://localhost:5173`, kemudian login menggunakan `bisma@its.ac.id` / `Password123`.
3. Pada Tab 1, masukkan `USR-1002` pada kolom **Tambah teman pakai User ID**, lalu klik **+ Tambah**.
4. Kirim pesan (misalnya `HALO BISMA`).
5. Klik **Lihat Tahapan ElGamal (Tahap 1, 2, 3)** pada gelembung pesan untuk memverifikasi proses pembangkitan pasangan cipherteks $(a, b)$ dan pemulihan plainteks $m = b \cdot (a^x)^{-1} \bmod p$.

---

## 4. Ringkasan Verifikasi Contoh Slide Perkuliahan

### A. Diffie-Hellman ($p=251, g=6$)
- Kunci privat Alice $a = 124 \implies A = 6^{124} \bmod 251 = 209$
- Kunci privat Bob $b = 158 \implies B = 6^{158} \bmod 251 = 197$
- Kunci bersama Alice: $K_{\text{Alice}} = 197^{124} \bmod 251 = \mathbf{79}$
- Kunci bersama Bob: $K_{\text{Bob}} = 209^{158} \bmod 251 = \mathbf{79}$
- **Hasil:** $K_{\text{Alice}} = K_{\text{Bob}} = 79$ *(Cocok 100% dengan materi perkuliahan)*

### B. ElGamal ($p=2273, g=3, x=243 \implies y=461$, Pesan `'HALO'`)
- Blok 1: $m = 700$, $k = 1463 \implies a = 3^{1463} \bmod 2273 = 1439$, $b = (461^{1463} \cdot 700) \bmod 2273 = 74 \implies \mathbf{(1439, 74)}$
- Blok 2: $m = 1114$, $k = 2001 \implies a = 3^{2001} \bmod 2273 = 1220$, $b = (461^{2001} \cdot 1114) \bmod 2273 = 1682 \implies \mathbf{(1220, 1682)}$
- Dekripsi Invers: $a^{p-1-x} \bmod p = a^{2029} \bmod 2273$
  - Blok 1: $74 \cdot 1791 \bmod 2273 = \mathbf{700}$ (`HA`)
  - Blok 2: $1682 \cdot 1125 \bmod 2273 = \mathbf{1114}$ (`LO`)
- **Hasil:** Pesan `'HALO'` pulih sempurna *(Cocok 100% dengan materi perkuliahan)*

---

## 5. Struktur Direktori Proyek

```text
Kriptografi_Diffie-Hellman-dan-ElGamal/
├── README.md                                    # Panduan utama repositori
├── README_LAPORAN.md                            # Laporan lengkap versi Markdown (7 Bagian)
├── Laporan_Kelompok_4_Diffie-Hellman_ElGamal.docx # Laporan lengkap versi Word (.docx)
├── images/                                      # Diagram alur dan tangkapan layar aplikasi/CLI
├── diffie_hellman.py                            # Modul dan simulasi CLI Diffie-Hellman murni
├── ElGamal.py                                   # Modul dan simulasi CLI ElGamal murni
├── crypto/
│   └── index.js                                 # Implementasi Diffie-Hellman BigInt di browser
├── backend/
│   ├── server.py                                # Server HTTP Python murni (port 3002)
│   ├── .env.example                             # Template environment dan seeding akun
│   └── .env                                     # Konfigurasi API OpenWeather (opsional)
└── frontend/
    ├── dev_server.py                            # Server statis frontend Python (port 5173)
    ├── dev-server.js                            # Alternatif server frontend Node.js
    ├── login.html                               # Antarmuka login dengan Diffie-Hellman
    ├── signup.html                              # Antarmuka registrasi akun
    ├── home.html                                # Dashboard cuaca dan chat ElGamal
    ├── css/                                     # Lembar gaya dan komponen antarmuka
    ├── js/                                      # Logika klien (autentikasi, chat, cuaca)
    └── assets/                                  # Aset ilustrasi dan ikon SVG
```
