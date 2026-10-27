import { getSession } from "./auth-service.js";

const FLASH_KEY = "dheg.flash";

export function setFieldError(input, message) {
  const field = input.closest(".field, .check-group");
  const error = document.getElementById(`${input.id}-error`);
  if (error) error.textContent = message;
  field?.classList.toggle("is-invalid", Boolean(message));
  if (message) input.setAttribute("aria-invalid", "true");
  else input.removeAttribute("aria-invalid");
}

export function validateAll(rules) {
  let firstInvalid = null;
  for (const { input, validate } of rules) {
    const message = validate();
    setFieldError(input, message);
    if (message && !firstInvalid) firstInvalid = input;
  }
  firstInvalid?.focus();
  return !firstInvalid;
}

export function attachLiveValidation(rules) {
  for (const { input, validate } of rules) {
    const recheck = () => setFieldError(input, validate());
    input.addEventListener("blur", () => {
      if (input.type === "checkbox" || input.value !== "") recheck();
    });
    input.addEventListener(input.type === "checkbox" ? "change" : "input", () => {
      if (input.getAttribute("aria-invalid") === "true") recheck();
    });
  }
}

export function initPasswordToggles(root = document) {
  for (const button of root.querySelectorAll("[data-toggle-password]")) {
    const input = document.getElementById(button.dataset.togglePassword);
    const icon = button.querySelector("img");
    button.addEventListener("click", () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      button.setAttribute("aria-pressed", String(show));
      icon.src = show ? "assets/eye.svg" : "assets/eye-off.svg";
    });
  }
}

export function setLoading(button, loading, text = "Memverifikasi...") {
  if (loading) {
    button.dataset.label = button.textContent;
    button.textContent = text;
    button.disabled = true;
  } else {
    button.textContent = button.dataset.label ?? button.textContent;
    button.disabled = false;
  }
}

export function showStatus(el, message, type = "error") {
  el.classList.remove("form-status--error", "form-status--success");
  if (message) el.classList.add(`form-status--${type}`);
  el.textContent = message;
}

export function setFlash(message) {
  sessionStorage.setItem(FLASH_KEY, message);
}

export function takeFlash() {
  const message = sessionStorage.getItem(FLASH_KEY);
  sessionStorage.removeItem(FLASH_KEY);
  return message;
}

export function requireSession() {
  const session = getSession();
  if (!session) location.replace("login.html");
  return session;
}

