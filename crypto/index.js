// Modul Diffie-Hellman murni (tanpa dependency) di sisi browser untuk pertukaran
// kunci sesi saat Login dan Register.

export function modPow(base, exponent, modulus) {
  if (modulus === 1n) return 0n;
  let result = 1n;
  let current = ((base % modulus) + modulus) % modulus;
  let remaining = exponent;

  while (remaining > 0n) {
    if (remaining & 1n) result = (result * current) % modulus;
    current = (current * current) % modulus;
    remaining >>= 1n;
  }
  return result;
}

function randomPrivateKey(pBig) {
  const bytes = new Uint32Array(1);
  globalThis.crypto.getRandomValues(bytes);
  const range = pBig - 3n;
  return 2n + (BigInt(bytes[0]) % range);
}

/**
 * Menjalankan pertukaran kunci Diffie-Hellman di sisi client (Alice) dan
 * mengenkripsi password dengan Shared Secret K yang dihasilkan.
 */
export function establishDiffieHellmanAndEncrypt(password, pStr, gStr, serverPublicBStr) {
  const p = BigInt(pStr);
  const g = BigInt(gStr);
  const B = BigInt(serverPublicBStr);

  // Tahap 2: Client (Alice) membangkitkan kunci privat a dan kunci publik A = g^a mod p
  const a = randomPrivateKey(p);
  const A = modPow(g, a, p);

  // Tahap 4: Client menghitung shared secret K = B^a mod p
  const K = modPow(B, a, p);

  // Enkripsi password menggunakan kunci simetris hasil Diffie-Hellman (K)
  const ciphertext = [];
  for (let i = 0; i < password.length; i += 1) {
    const m = BigInt(password.charCodeAt(i));
    const c = (m + K) % p;
    ciphertext.push(c.toString());
  }

  return {
    p: p.toString(),
    g: g.toString(),
    clientPrivateA: a.toString(),
    clientPublicA: A.toString(),
    serverPublicB: B.toString(),
    sharedSecretK: K.toString(),
    ciphertext,
  };
}

