"""
Diffie-Hellman Key Exchange (tanpa library kriptografi)
Tugas Kriptografi - Kelompok X

Catatan: modul `random` hanya dipakai untuk membangkitkan angka acak.
Seluruh logika kriptografi (modular exponentiation, uji prima,
generator, kunci publik/privat, shared secret) ditulis sendiri.
"""
import random


# ---------------------------------------------------------------
# FUNGSI MATEMATIKA DASAR
# ---------------------------------------------------------------
def mod_exp(base, exp, mod):
    """Perpangkatan modular (square-and-multiply): base^exp mod mod."""
    result = 1
    base %= mod
    while exp > 0:
        if exp & 1:                      # bit terakhir = 1
            result = (result * base) % mod
        base = (base * base) % mod       # kuadratkan
        exp >>= 1                        # geser bit
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


def generate_prime(bits):
    """Bangkitkan bilangan prima acak dengan panjang `bits` bit."""
    while True:
        n = random.getrandbits(bits) | (1 << (bits - 1)) | 1
        if is_prime(n):
            return n


def prime_factors(n):
    """Faktor prima unik dari n (trial division, cukup untuk p <= ~40 bit)."""
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


# ---------------------------------------------------------------
# TAHAPAN DIFFIE-HELLMAN
# ---------------------------------------------------------------
def is_primitive_root(g, p, factors):
    """g adalah generator mod p jika g^((p-1)/q) != 1 untuk semua faktor prima q dari p-1."""
    return all(mod_exp(g, (p - 1) // q, p) != 1 for q in factors)


def find_generator(p):
    """Tahap 1b: cari generator (primitive root) g dari p."""
    factors = prime_factors(p - 1)
    for g in range(2, p):
        if is_primitive_root(g, p, factors):
            return g
    return None


def generate_private_key(p):
    """Tahap 2: kunci privat acak 2 <= x <= p-2."""
    return random.randrange(2, p - 1)


def generate_public_key(g, private, p):
    """Tahap 2: kunci publik = g^private mod p."""
    return mod_exp(g, private, p)


def compute_shared_secret(other_public, my_private, p):
    """Tahap 4: shared secret = (kunci publik lawan)^(kunci privat saya) mod p."""
    return mod_exp(other_public, my_private, p)


# ---------------------------------------------------------------
# PROGRAM UTAMA (menampilkan setiap tahapan)
# ---------------------------------------------------------------
def header(teks):
    print("\n" + "=" * 60)
    print(teks)
    print("=" * 60)


def run(p, g, a=None, b=None):
    header("TAHAP 1: PARAMETER PUBLIK (p dan g)")
    print(f"p (bilangan prima) : {p}  -> prima? {is_prime(p)}")
    print(f"Faktor prima p-1   : {prime_factors(p - 1)}")
    print(f"g (generator)      : {g}  -> primitive root? "
          f"{is_primitive_root(g, p, prime_factors(p - 1))}")

    header("TAHAP 2: PEMBANGKITAN KUNCI")
    a = a if a is not None else generate_private_key(p)
    b = b if b is not None else generate_private_key(p)
    A = generate_public_key(g, a, p)
    B = generate_public_key(g, b, p)
    print(f"Alice  kunci privat a = {a}")
    print(f"Alice  kunci publik A = g^a mod p = {g}^{a} mod {p} = {A}")
    print(f"Bob    kunci privat b = {b}")
    print(f"Bob    kunci publik B = g^b mod p = {g}^{b} mod {p} = {B}")

    header("TAHAP 3: PERTUKARAN KUNCI PUBLIK (lewat kanal tidak aman)")
    print(f"Alice mengirim A = {A}  ke Bob")
    print(f"Bob   mengirim B = {B}  ke Alice")

    header("TAHAP 4: PERHITUNGAN SHARED SECRET")
    s_alice = compute_shared_secret(B, a, p)
    s_bob = compute_shared_secret(A, b, p)
    print(f"Alice: s = B^a mod p = {B}^{a} mod {p} = {s_alice}")
    print(f"Bob  : s = A^b mod p = {A}^{b} mod {p} = {s_bob}")

    header("TAHAP 5: VERIFIKASI")
    if s_alice == s_bob:
        print(f"BERHASIL! Kunci rahasia bersama = {s_alice}")
    else:
        print("GAGAL! Shared secret berbeda.")
    return s_alice


def main():
    print("DIFFIE-HELLMAN KEY EXCHANGE")
    print("1. Otomatis (p, g, kunci dibangkitkan acak)")
    print("2. Manual   (masukkan p, g, a, b sendiri)")
    pilih = input("Pilih mode [1/2]: ").strip()

    if pilih == "2":
        p = int(input("Masukkan p (prima)     : "))
        if not is_prime(p):
            print("p bukan bilangan prima!")
            return
        g = int(input("Masukkan g (generator) : "))
        if not is_primitive_root(g, p, prime_factors(p - 1)):
            print("Peringatan: g bukan generator dari p (tetap dilanjutkan).")
        a = int(input("Kunci privat Alice (a)  : "))
        b = int(input("Kunci privat Bob   (b)  : "))
        run(p, g, a, b)
    else:
        bits = int(input("Panjang bit p (mis. 16-32): ") or 20)
        p = generate_prime(bits)
        g = find_generator(p)
        run(p, g)


if __name__ == "__main__":
    main()