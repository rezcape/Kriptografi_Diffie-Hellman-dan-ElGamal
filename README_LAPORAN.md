# LAPORAN PROGRAM

## Implementasi Pertukaran Kunci Diffie-Hellman pada Autentikasi Login dan Algoritma ElGamal pada Percakapan Multi-Akun

---

## 1. Identitas Kelompok

| Keterangan | Isi |
|---|---|
| Mata kuliah | Kriptografi |
| Kelas | A |
| Kelompok | 4 |
| Dosen pengampu | Annisaa Sri Indrawanti, S.Kom., M.Kom. |

### Anggota Kelompok

| No. | Nama lengkap | NRP |
|---:|---|---|
| 1 | Arya Bisma Putra Refman | 5027241036 |
| 2 | M.Hikari Reiziq Rakhmadinta | 5027241079 |
| 3 | Ahmad Syauqi Reza | 5027141085 |

---

## 2. Latar Belakang

Dalam komunikasi jaringan modern, terdapat dua kebutuhan keamanan utama yang saling melengkapi:
1. **Penyepakatan Kunci Sesi Bersama (*Key Exchange*):** Bagaimana dua pihak (klien dan server) dapat menyepakati satu kunci rahasia bersama melalui saluran komunikasi publik yang tidak aman tanpa pernah mengirimkan kunci tersebut secara langsung. Persoalan ini diselesaikan oleh **Algoritma Pertukaran Kunci Diffie-Hellman (1976)**.
2. **Enkripsi Pesan Asimetris Berbasis Logaritma Diskrit:** Bagaimana seorang pengirim dapat mengenkripsi pesan teks secara langsung menggunakan kunci publik penerima sehingga hanya penerima yang memiliki kunci privat yang dapat mendekripsinya, sekaligus menghasilkan cipherteks yang berbeda setiap kali pengiriman (*probabilistic encryption*). Persoalan ini diselesaikan oleh **Algoritma ElGamal (1984)**.

Pada proyek ini, Kelompok 4 membangun program murni **tanpa library atau framework kriptografi jadi** yang menerapkan kedua algoritma tersebut ke dalam aplikasi web:
- **Diffie-Hellman (`diffie_hellman.py`)** digunakan pada proses **Pendaftaran dan Login** untuk menyepakati *Shared Secret Key* ($K$) antara browser dan server sebelum mengirimkan password.
- **ElGamal (`ElGamal.py`)** digunakan pada fitur **Chat Multi-Akun (ala WhatsApp)** di halaman utama, di mana setiap akun memiliki **User ID** unik serta pasangan kunci publik/privat ElGamal masing-masing, dapat menambahkan teman menggunakan **User ID**, dan bertukar pesan terenkripsi pasangan $(a, b)$ lengkap dengan rincian setiap tahapannya.

---

## 3. Tujuan

1. Mengimplementasikan algoritma **Diffie-Hellman** dari nol (tanpa library kriptografi) dan menampilkan seluruh tahapannya (Tahap 1 s.d. Tahap 5).
2. Mengimplementasikan algoritma **ElGamal** dari nol (tanpa library kriptografi) dan menampilkan seluruh tahapannya (Tahap 1 Pembangkitan Kunci, Tahap 2 Enkripsi pasangan $(a, b)$, dan Tahap 3 Dekripsi invers modulo).
3. Menerapkan Diffie-Hellman pada alur autentikasi Login dan Pendaftaran.
4. Menerapkan ElGamal pada fitur percakapan (*chat*) antar-akun yang terhubung melalui **User ID**.
5. Menampilkan informasi cuaca Surabaya secara *real-time* dari OpenWeather API menggunakan konfigurasi `.env`.

---

## 4. Arsitektur dan Struktur Program

```text
Kriptografi_Diffie-Hellman-dan-ElGamal/
├── diffie_hellman.py        # Modul & CLI Diffie-Hellman murni (Tahap 1 - 5)
├── ElGamal.py               # Modul & CLI ElGamal murni (Tahap 1 - 4)
├── crypto/
│   └── index.js             # Modul Diffie-Hellman BigInt murni di sisi browser
├── backend/
│   ├── .env                 # Menyimpan OPENWEATHER_API_KEY
│   ├── .env.example         # Template konfigurasi environment
│   └── server.py            # HTTP server Python murni (import diffie_hellman & ElGamal)
└── frontend/
    ├── login.html           # Halaman Login (Figma 1-3772)
    ├── signup.html          # Halaman Pendaftaran (Figma 1-3905)
    ├── home.html            # Halaman Beranda: Cuaca + Bukti DH + Chat ElGamal (Figma 1006-273)
    ├── dev_server.py        # Server statis frontend (port 5173)
    ├── css/                 # Styling halaman & komponen gelembung chat
    └── js/                  # Logika autentikasi, cuaca, tambah teman User ID, dan chat ElGamal
```

---

## 5. Tahapan Algoritma pada Kode Program

### 5.1 Tahapan Diffie-Hellman (`diffie_hellman.py`)

Keamanan Diffie-Hellman bertumpu pada sulitnya menghitung **logaritma diskrit** pada aritmetika modulo.

1. **Tahap 1 — Parameter Publik ($p$ dan $g$):**
   Menentukan bilangan prima $p$ (diuji dengan *Miller-Rabin* pada fungsi `is_prime(n)`) dan akar primitif / generator $g$ (diuji dengan `is_primitive_root(g, p, factors)`).
2. **Tahap 2 — Pembangkitan Kunci Privat dan Publik:**
   - Alice (Browser) memilih kunci privat acak $a \in [2, p-2]$ dan menghitung kunci publik:
     $$A = g^a \bmod p$$
   - Bob (Server) memilih kunci privat acak $b \in [2, p-2]$ dan menghitung kunci publik:
     $$B = g^b \bmod p$$
3. **Tahap 3 — Pertukaran Kunci Publik:**
   Alice mengirimkan $A$ ke Bob dan Bob mengirimkan $B$ ke Alice melalui jaringan.
4. **Tahap 4 — Perhitungan *Shared Secret Key* ($K$):**
   - Alice menghitung:
     $$K_{\text{Alice}} = B^a \bmod p$$
   - Bob menghitung:
     $$K_{\text{Bob}} = A^b \bmod p$$
5. **Tahap 5 — Verifikasi:**
   Karena $(g^b)^a \bmod p = (g^a)^b \bmod p = g^{ab} \bmod p$, maka $K_{\text{Alice}} = K_{\text{Bob}} = K$. Kunci bersama $K$ ini digunakan untuk mengamankan pengiriman password saat login.

---

### 5.2 Tahapan Algoritma ElGamal (`ElGamal.py`)

Setiap pengguna yang mendaftar di aplikasi mendapatkan **User ID** (misalnya `USR-1001`, `USR-1002`) serta pasangan kunci ElGamal miliknya sendiri:

1. **Tahap 1 — Pembangkitan Kunci Privat dan Publik (`generate_keys`):**
   - Disepakati bilangan prima $p = 2273$ dan akar primitif $g = 3$.
   - Penerima memilih kunci privat acak $x \in [2, p - 2]$.
   - Penerima menghitung kunci publik:
     $$y = g^x \bmod p$$
   - **Kunci Publik Penerima:** $(y, g, p)$ | **Kunci Privat Penerima:** $x$.

2. **Tahap 2 — Enkripsi Pesan Chat (`encrypt_block` & `encrypt_text`):**
   Saat pengirim mengirim pesan teks ke penerima, setiap karakter diubah menjadi integer $m \in [0, p-1]$, lalu untuk setiap blok dipilih bilangan acak baru $k \in [2, p-2]$:
   $$a = g^k \bmod p$$
   $$b = (y^k \cdot m) \bmod p$$
   Hasil enkripsi untuk setiap karakter adalah pasangan $(a, b)$, sehingga ukuran cipherteks menjadi dua kali ukuran plainteksnya.

3. **Tahap 3 — Dekripsi Pesan Chat (`decrypt_block` & `decrypt_text`):**
   Penerima menggunakan kunci privatnya $x$ untuk menghitung invers modulo $(a^x)^{-1} \bmod p$ menggunakan **Teorema Kecil Fermat**:
   $$(a^x)^{-1} \equiv a^{p - 1 - x} \pmod p$$
   Kemudian plainteks $m$ diperoleh kembali dengan persamaan:
   $$m = \left(b \cdot (a^x)^{-1}\right) \bmod p$$

---

## 6. Alur Penggunaan Aplikasi Web

### 6.1 Pendaftaran & Login dengan Diffie-Hellman
1. Pengguna membuka `http://localhost:5173/signup.html` dan mendaftarkan akun baru.
2. Browser mengambil parameter publik $(p, g, B)$ dari `GET /api/dh/params`, membangkitkan $(a, A)$, menghitung $K = B^a \bmod p$, dan mengenkripsi password sebelum dikirim ke `POST /api/auth/register`.
3. Server menghitung $K = A^b \bmod p$ melalui `diffie_hellman.py`, mendekripsi password, menyimpan hash `scrypt`, serta memberikan **User ID** unik (misal `USR-1001`) dan kunci ElGamal $(y, g, p, x)$.
4. Saat login di `login.html`, proses pertukaran kunci Diffie-Hellman yang sama dijalankan dan rincian setiap tahapannya ditampilkan pada kartu **Login diamankan Diffie-Hellman** di halaman Home.

### 6.2 Tambah Teman dengan User ID & Chat ElGamal (Termasuk 2 Akun Seeding)
Untuk memudahkan pengujian, `backend/.env.example` dan `backend/server.py` telah dilengkapi *seeding* otomatis 2 akun siap pakai:
- **Akun 1 (`USR-1001`):** `hikari@its.ac.id` | Password: `Password123` | Kunci ElGamal: $x=243, y=461$
- **Akun 2 (`USR-1002`):** `bisma@its.ac.id` | Password: `Password123` | Kunci ElGamal: $x=517, y=1806$

Langkah pengujian:
1. Pengguna langsung login sebagai `hikari@its.ac.id` di Tab 1 (`USR-1001`) dan `bisma@its.ac.id` di Tab 2 (`USR-1002`).
2. Pada panel **Chat ElGamal**, pengguna memasukkan `USR-1002` di kolom **Tambah teman pakai User ID** lalu menekan **+ Tambah**.
3. Ketika pengguna mengirim pesan (misalnya `"HALO"`), server memproses pesan melalui `ElGamal.py` menggunakan kunci publik penerima.
4. Di dalam setiap gelembung pesan (*chat bubble*), pengguna dapat menekan **"Lihat Tahapan ElGamal (Tahap 1, 2, 3)"** untuk memeriksa rumus dan angka hasil perhitungan Tahap 1, Tahap 2, dan Tahap 3 secara transparan.

---

## 7. Pengujian Program

### 7.1 Pengujian CLI Mandiri dengan Contoh Slide Perkuliahan

Program diuji langsung terhadap contoh soal pada materi perkuliahan Pertemuan ke-9:
- **Diffie-Hellman ($p=251, g=6, a=124, b=158$):**
  - $A = 6^{124} \bmod 251 = 209$
  - $B = 6^{158} \bmod 251 = 197$
  - $K_{\text{Alice}} = 197^{124} \bmod 251 = \mathbf{79}$ dan $K_{\text{Bob}} = 209^{158} \bmod 251 = \mathbf{79}$ (**Cocok**).
- **ElGamal ($p=2273, g=3, x=243 \rightarrow y=461$, pesan `'HALO'` $\rightarrow m_1=0700, m_2=1114$):**
  - Blok 1 ($k=1463$): $a = 3^{1463} \bmod 2273 = 1439$, $b = 461^{1463} \cdot 700 \bmod 2273 = 74 \rightarrow c_1 = (1439, 74)$.
  - Blok 2 ($k=2001$): $a = 3^{2001} \bmod 2273 = 1220$, $b = 461^{2001} \cdot 1114 \bmod 2273 = 1682 \rightarrow c_2 = (1220, 1682)$.
  - Dekripsi $c_1$: $(a^x)^{-1} = 1439^{2029} \bmod 2273 = 1791 \rightarrow m_1 = 74 \cdot 1791 \bmod 2273 = \mathbf{0700}$.
  - Dekripsi $c_2$: $(a^x)^{-1} = 1220^{2029} \bmod 2273 = 1125 \rightarrow m_2 = 1682 \cdot 1125 \bmod 2273 = \mathbf{1114}$.

### 7.2 Pengujian Endpoint Integrasi Web

| Skenario Uji | Endpoint | Status | Hasil |
|---|---|---|---|
| Mengambil parameter Diffie-Hellman | `GET /api/dh/params` | `200 OK` | Mengembalikan $(p, g, B)$ |
| Pendaftaran Akun 1 (`USR-1001`) | `POST /api/auth/register` | `201 Created` | Akun & kunci ElGamal terbentuk |
| Pendaftaran Akun 2 (`USR-1002`) | `POST /api/auth/register` | `201 Created` | Akun & kunci ElGamal terbentuk |
| Login dengan Diffie-Hellman | `POST /api/auth/login` | `200 OK` | $K_{\text{client}} = K_{\text{server}}$, sesi aktif |
| Tambah teman dengan User ID | `POST /api/friends/add` | `200 OK` | Kontak `USR-1002` terhubung |
| Kirim pesan chat terenkripsi ElGamal | `POST /api/chat/send` | `201 Created` | Pesan dienkripsi $(a,b)$ & didekripsi kembali |
| Mengambil data cuaca Surabaya | `GET /api/weather?city=Surabaya` | `200 OK` | Data suhu, kelembapan, angin tampil |

---

## 8. Kesimpulan

1. **Diffie-Hellman (`diffie_hellman.py`)** berhasil diimplementasikan tanpa library eksternal untuk membangun kunci rahasia bersama ($K$) antara browser dan server pada proses autentikasi login tanpa pernah mempertukarkan kunci privat.
2. **ElGamal (`ElGamal.py`)** berhasil diimplementasikan tanpa library eksternal untuk mengenkripsi dan mendekripsi percakapan antar-pengguna yang dihubungkan melalui **User ID**, di mana setiap karakter pesan diubah menjadi pasangan cipherteks $(a, b)$ menggunakan angka acak $k$ dan dikembalikan secara akurat menggunakan invers modulo $a^{p-1-x} \bmod p$.

