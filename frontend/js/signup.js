import { register } from "./auth-service.js";
import {
  normalizePhone,
  passwordStrength,
  STRENGTH_LABELS,
  validateAgreement,
  validateConfirm,
  validateEmail,
  validatePassword,
  validatePhone,
  validateRequired,
} from "./validators.js";
import {
  attachLiveValidation,
  initPasswordToggles,
  setFlash,
  setLoading,
  showStatus,
  validateAll,
} from "./ui.js";

const REDIRECT_DELAY_MS = 1400;

const ERROR_MESSAGES = {
  EMAIL_TAKEN: "Email ini sudah terdaftar. Silakan masuk.",
  NETWORK: "Server tidak bisa dihubungi. Pastikan backend sudah berjalan.",
  SERVER: "Terjadi kesalahan di server. Coba lagi.",
};

const form = document.getElementById("signup-form");
const $ = (id) => document.getElementById(id);
const firstName = $("firstName");
const lastName = $("lastName");
const email = $("email");
const phone = $("phone");
const password = $("password");
const confirmPassword = $("confirmPassword");
const agree = $("agree");
const status = $("form-status");
const strength = $("strength");
const strengthLabel = $("password-strength");
const submit = form.querySelector('button[type="submit"]');

const rules = [
  { input: firstName, validate: () => validateRequired(firstName.value, "Nama depan wajib diisi.") },
  { input: lastName, validate: () => validateRequired(lastName.value, "Nama belakang wajib diisi.") },
  { input: email, validate: () => validateEmail(email.value) },
  { input: phone, validate: () => validatePhone(phone.value) },
  { input: password, validate: () => validatePassword(password.value) },
  { input: confirmPassword, validate: () => validateConfirm(password.value, confirmPassword.value) },
  { input: agree, validate: () => validateAgreement(agree.checked) },
];

initPasswordToggles(form);
attachLiveValidation(rules);

password.addEventListener("input", () => {
  const level = passwordStrength(password.value);
  const text = level === null ? "" : `Kekuatan: ${STRENGTH_LABELS[level]}`;
  strength.dataset.level = level ?? "";
  if (strengthLabel.textContent !== text) strengthLabel.textContent = text;
  if (confirmPassword.getAttribute("aria-invalid") === "true") {
    confirmPassword.dispatchEvent(new Event("input"));
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showStatus(status, "");
  if (!validateAll(rules)) return;

  setLoading(submit, true);
  try {
    const userId = await register({
      firstName: firstName.value.trim(),
      lastName: lastName.value.trim(),
      email: email.value.trim(),
      phone: normalizePhone(phone.value),
      password: password.value,
    });
    const msg = `Akun berhasil dibuat (${userId}). Silakan masuk.`;
    showStatus(status, msg, "success");
    setFlash(msg);
    setTimeout(() => location.assign("login.html"), REDIRECT_DELAY_MS);
  } catch (err) {
    showStatus(status, ERROR_MESSAGES[err.code] ?? ERROR_MESSAGES.SERVER, "error");
    setLoading(submit, false);
  }
});

