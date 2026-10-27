const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function validateRequired(value, message) {
  return value.trim() ? "" : message;
}

export function validateEmail(value) {
  const v = value.trim();
  if (!v) return "Email wajib diisi.";
  if (!EMAIL_PATTERN.test(v)) return "Format email belum benar, contoh: nama@email.com.";
  return "";
}

export function validatePhone(value) {
  const v = value.replace(/[\s-]/g, "");
  if (!v) return "Nomor HP wajib diisi.";
  if (!/^(\+62|08)\d*$/.test(v)) return "Nomor HP harus diawali 08 atau +62.";
  const digits = v.replace("+", "").length;
  if (digits < 9 || digits > 13) return "Nomor HP harus 9 sampai 13 digit.";
  return "";
}

export function normalizePhone(value) {
  return value.replace(/[\s-]/g, "");
}

export function validatePassword(value) {
  if (!value) return "Password wajib diisi.";
  if (value.length < 8) return "Password minimal 8 karakter.";
  if (!/[A-Za-z]/.test(value) || !/\d/.test(value)) return "Password harus berisi huruf dan angka.";
  return "";
}

export function validateConfirm(password, confirm) {
  if (!confirm) return "Ulangi password di sini.";
  if (password !== confirm) return "Konfirmasi password tidak sama.";
  return "";
}

export function validateAgreement(checked) {
  return checked ? "" : "Centang persetujuan untuk melanjutkan.";
}

export function passwordStrength(value) {
  if (!value) return null;
  if (validatePassword(value)) return 0;
  const extras = [
    value.length >= 12,
    /[a-z]/.test(value) && /[A-Z]/.test(value),
    /[^A-Za-z0-9]/.test(value),
  ].filter(Boolean).length;
  return extras >= 2 ? 2 : 1;
}

export const STRENGTH_LABELS = ["Lemah", "Cukup", "Kuat"];

