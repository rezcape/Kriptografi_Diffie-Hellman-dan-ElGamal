"""
Algoritma Kriptografi Kunci Publik ElGamal (tanpa library kriptografi)
Tugas Kriptografi - Kelompok 4

Catatan: modul `random` hanya dipakai untuk membangkitkan angka acak.
Seluruh logika kriptografi (perpangkatan modular, uji prima, akar primitif,
pembangkitan kunci, enkripsi pasangan (a, b), dan dekripsi invers modulo)
ditulis sendiri dari nol.
"""
import random


def mod_exp(base, exp, mod):
    """Perpangkatan modular (square-and-multiply): base^exp mod mod."""
    result = 1
    base %= mod
    while exp > 0:
        if exp & 1:
            result = (result * base) % mod
        base = (base * base) % mod
        exp >>= 1
    return result


def is_prime(n, k=20):
    """Uji keprimaan Miller-Rabin."""
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29):
        if n == p:
            return True
        if n % p == 0:
            return False
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = mod_exp(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_prime(bits=16):
    """Bangkitkan bilangan prima acak dengan panjang `bits` bit."""
    while True:
        n = random.getrandbits(bits) | (1 << (bits - 1)) | 1
        if is_prime(n):
            return n


def prime_factors(n):
    """Faktor prima unik dari n (trial division)."""
    factors = set()
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.add(d)
            n //= d
        d += 1
    if n > 1:
        factors.add(n)
    return sorted(factors)


def is_primitive_root(g, p, factors=None):
    """g adalah akar primitif mod p jika g^((p-1)/q) != 1 untuk semua faktor prima q dari p-1."""
    if factors is None:
        factors = prime_factors(p - 1)
    return all(mod_exp(g, (p - 1) // q, p) != 1 for q in factors)


def find_generator(p):
    """Cari akar primitif (generator) g terkecil dari bilangan prima p."""
    factors = prime_factors(p - 1)
    for g in range(2, p):
        if is_primitive_root(g, p, factors):
            return g
    return None


def generate_keys(p=None, g=None, x=None, bits=16):
    """
    Tahap 1 ElGamal: Pembangkitan kunci privat dan kunci publik.
    - Kunci privat : x (1 < x < p - 1)
    - Kunci publik : (y, g, p) dengan y = g^x mod p
    """
    if p is None:
        p = generate_prime(bits)
    if g is None:
        g = find_generator(p)
    if x is None:
        x = random.randrange(2, p - 1)
    y = mod_exp(g, x, p)
    return {
        "p": p,
        "g": g,
        "x": x,
        "y": y,
    }


def encrypt_block(m, y, g, p, k=None):
    """
    Tahap 2 ElGamal (per blok integer m):
    - Pilih bilangan acak k (1 < k < p - 1)
    - Hitung a = g^k mod p
    - Hitung b = (y^k * m) mod p
    """
    if m < 0 or m >= p:
        raise ValueError(f"Nilai blok m={m} harus berada di rentang [0, {p - 1}]")
    if k is None:
        k = random.randrange(2, p - 1)
    a = mod_exp(g, k, p)
    yk = mod_exp(y, k, p)
    b = (yk * m) % p
    return {
        "m": m,
        "k": k,
        "a": a,
        "b": b,
        "yk": yk,
        "formula_a": f"{g}^{k} mod {p} = {a}",
        "formula_b": f"({y}^{k} * {m}) mod {p} = {b}",
    }


def decrypt_block(a, b, x, p):
    """
    Tahap 3 ElGamal (per pasangan cipherteks (a, b)):
    - Hitung invers modulo (a^x)^(-1) = a^(p - 1 - x) mod p (Teorema Kecil Fermat)
    - Hitung plainteks m = (b * (a^x)^(-1)) mod p
    """
    inv_exp = p - 1 - x
    ax_inv = mod_exp(a, inv_exp, p)
    m = (b * ax_inv) % p
    return {
        "a": a,
        "b": b,
        "inv_exp": inv_exp,
        "ax_inv": ax_inv,
        "m": m,
        "formula_inv": f"{a}^({p}-1-{x}) mod {p} = {a}^{inv_exp} mod {p} = {ax_inv}",
        "formula_m": f"({b} * {ax_inv}) mod {p} = {m}",
    }


def encrypt_text(plaintext, y, g, p, k_list=None):
    """Enkripsi string teks per karakter ASCII menjadi daftar pasangan (a, b)."""
    steps = []
    ciphertext = []
    for idx, ch in enumerate(plaintext):
        m = ord(ch)
        k = k_list[idx] if (k_list and idx < len(k_list)) else None
        step = encrypt_block(m, y, g, p, k=k)
        step["char"] = ch
        steps.append(step)
        ciphertext.append([step["a"], step["b"]])
    return {
        "ciphertext": ciphertext,
        "steps": steps,
    }


def decrypt_text(ciphertext, x, p):
    """Dekripsi daftar pasangan (a, b) kembali menjadi string teks."""
    steps = []
    chars = []
    for pair in ciphertext:
        a, b = int(pair[0]), int(pair[1])
        step = decrypt_block(a, b, x, p)
        ch = chr(step["m"]) if 0 <= step["m"] <= 0x10FFFF else "?"
        step["char"] = ch
        steps.append(step)
        chars.append(ch)
    return {
        "plaintext": "".join(chars),
        "steps": steps,
    }


def header(teks):
    print("\n" + "=" * 60)
    print(teks)
    print("=" * 60)


def run(p, g, plaintext, x=None):
    header("TAHAP 1: PEMBANGKITAN KUNCI PRIVAT DAN PUBLIK")
    keys = generate_keys(p=p, g=g, x=x)
    p, g, x, y = keys["p"], keys["g"], keys["x"], keys["y"]
    factors = prime_factors(p - 1)
    print(f"p (bilangan prima)       : {p} -> prima? {is_prime(p)}")
    print(f"Faktor prima p-1         : {factors}")
    print(f"g (akar primitif)        : {g} -> akar primitif? {is_primitive_root(g, p, factors)}")
    print(f"Kunci privat Alice (x)   : {x}")
    print(f"Kunci publik Alice (y)   : g^x mod p = {g}^{x} mod {p} = {y}")
    print(f"Kunci publik lengkap     : (y={y}, g={g}, p={p})")

    header("TAHAP 2: ENKRIPSI PESAN (OLEH PENGIRIM)")
    print(f"Plainteks asli           : {plaintext!r}")
    enc = encrypt_text(plaintext, y, g, p)
    for idx, s in enumerate(enc["steps"], start=1):
        print(f"  Blok {idx} ('{s['char']}' -> m={s['m']}): pilih k={s['k']}")
        print(f"    a = {s['formula_a']}")
        print(f"    b = {s['formula_b']}")
        print(f"    Cipherteks c_{idx} = ({s['a']}, {s['b']})")

    header("TAHAP 3: DEKRIPSI PESAN (OLEH PENERIMA)")
    dec = decrypt_text(enc["ciphertext"], x, p)
    for idx, s in enumerate(dec["steps"], start=1):
        print(f"  Blok {idx} c_{idx}=({s['a']}, {s['b']}):")
        print(f"    (a^x)^(-1) = {s['formula_inv']}")
        print(f"    m          = {s['formula_m']} -> '{s['char']}'")

    header("TAHAP 4: VERIFIKASI")
    print(f"Plainteks awal      : {plaintext}")
    print(f"Hasil dekripsi      : {dec['plaintext']}")
    if dec["plaintext"] == plaintext:
        print("BERHASIL! Pesan hasil dekripsi sama persis dengan plainteks awal.")
    else:
        print("GAGAL! Hasil dekripsi berbeda.")
    return dec["plaintext"]


def run_ppt_example():
    """Menjalankan contoh persis dari PPT Pertemuan ke-9 (pesan 'HALO', p=2273, g=3, x=243)."""
    p, g, x = 2273, 3, 243
    header("CONTOH SLIDE PPT PERTEMUAN KE-9 (PESAN 'HALO')")
    keys = generate_keys(p=p, g=g, x=x)
    y = keys["y"]
    print(f"Tahap 1 - Kunci Privat x = {x}, Kunci Publik (y={y}, g={g}, p={p})")

    blocks = [("0700", 700, 1463), ("1114", 1114, 2001)]
    cipher_pairs = []
    print("\nTahap 2 - Enkripsi Blok 'HALO' (H=07, A=00 -> 0700 | L=11, O=14 -> 1114):")
    for label, m_val, k_val in blocks:
        s = encrypt_block(m_val, y, g, p, k=k_val)
        cipher_pairs.append((label, s["a"], s["b"]))
        print(f"  Blok m={label} (k={k_val}): a = {s['formula_a']}, b = {s['formula_b']} -> c = ({s['a']}, {s['b']})")

    print("\nTahap 3 - Dekripsi dengan x = 243:")
    for label, a_val, b_val in cipher_pairs:
        d = decrypt_block(a_val, b_val, x, p)
        print(f"  Cipher ({a_val}, {b_val}): (a^x)^(-1) = {d['formula_inv']} -> m = {d['formula_m']} (blok {d['m']:04d})")


def main():
    print("ALGORITMA KRIPTOGRAFI ELGAMAL")
    print("1. Otomatis (p, g, kunci dibangkitkan acak)")
    print("2. Manual   (masukkan p, g, x, dan pesan sendiri)")
    print("3. Demo PPT (uji contoh slide dosen p=2273, g=3, x=243, pesan 'HALO')")
    pilih = input("Pilih mode [1/2/3]: ").strip()

    if pilih == "2":
        p = int(input("Masukkan p (prima > 255) : "))
        if not is_prime(p):
            print("p bukan bilangan prima!")
            return
        g = int(input("Masukkan g (generator)   : "))
        x = int(input("Kunci privat Alice (x)   : "))
        pesan = input("Masukkan pesan plainteks : ")
        run(p, g, pesan, x=x)
    elif pilih == "3":
        run_ppt_example()
    else:
        bits = int(input("Panjang bit p (mis. 16-24, default 16): ") or 16)
        pesan = input("Masukkan pesan plainteks (default 'HALO SURABAYA'): ") or "HALO SURABAYA"
        p = generate_prime(max(bits, 12))
        g = find_generator(p)
        run(p, g, pesan)


if __name__ == "__main__":
    main()
