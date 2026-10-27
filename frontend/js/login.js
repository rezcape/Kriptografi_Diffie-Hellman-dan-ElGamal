import { login } from "./auth-service.js";
import { validateEmail, validateRequired } from "./validators.js";
import {
  attachLiveValidation,
  initPasswordToggles,
  setLoading,
  showStatus,
  takeFlash,
  validateAll,
} from "./ui.js";

const ERROR_MESSAGES = {
  INVALID_CREDENTIALS: "Email atau password tidak cocok.",
  NETWORK: "Server tidak bisa dihubungi. Pastikan backend sudah berjalan.",
  SERVER: "Terjadi kesalahan di server. Coba lagi.",
};

const form = document.getElementById("login-form");
const email = document.getElementById("email");
const password = document.getElementById("password");
const status = document.getElementById("form-status");
const submit = form.querySelector('button[type="submit"]');

const rules = [
  { input: email, validate: () => validateEmail(email.value) },
  { input: password, validate: () => validateRequired(password.value, "Password wajib diisi.") },
];

initPasswordToggles(form);
attachLiveValidation(rules);

const flash = takeFlash();
if (flash) showStatus(status, flash, "success");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showStatus(status, "");
  if (!validateAll(rules)) return;

  setLoading(submit, true);
  try {
    await login(email.value, password.value);
    location.href = "home.html";
  } catch (err) {
    showStatus(status, ERROR_MESSAGES[err.code] ?? ERROR_MESSAGES.SERVER, "error");
    setLoading(submit, false);
  }
});

