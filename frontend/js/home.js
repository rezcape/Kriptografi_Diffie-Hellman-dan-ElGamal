import {
  addFriendById,
  fetchFriends,
  fetchMessages,
  logout,
  sendChatMessage,
} from "./auth-service.js";
import { WEATHER_CITY } from "./config.js";
import { requireSession } from "./ui.js";
import { getWeather } from "./weather-service.js";

const $ = (id) => document.getElementById(id);

const WEATHER_ERRORS = {
  BACKEND_DOWN: "Server belum berjalan. Jalankan python3 backend/server.py, lalu coba lagi.",
  WEATHER_KEY_INVALID: "Key OpenWeather belum aktif atau salah.",
  WEATHER_KEY_MISSING: "OPENWEATHER_API_KEY belum diisi di backend/.env.",
  CITY_NOT_FOUND: "Kota tidak ditemukan di OpenWeather.",
  WEATHER_UPSTREAM: "OpenWeather sedang tidak bisa dihubungi. Coba beberapa saat lagi.",
  UNKNOWN: "Terjadi kesalahan saat memuat cuaca.",
};

let currentUser = null;
let friendsList = [];
let activeFriend = null;
let lastRenderedSignature = "";

function initials(name) {
  return (name || "U")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

function capitalize(text) {
  return text ? text[0].toUpperCase() + text.slice(1) : "";
}

function countryName(code) {
  if (!code) return "";
  try {
    return new Intl.DisplayNames(["id"], { type: "region" }).of(code) ?? code;
  } catch {
    return code;
  }
}

function localTime(dt, timezone) {
  const d = new Date((dt + timezone) * 1000);
  return `${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`;
}

function illustrationFor(code, isNight) {
  if (code >= 200 && code < 300) return "badai";
  if (code >= 300 && code < 600) return "hujan";
  if (code === 800) return isNight ? "malam" : "cerah";
  if (code === 801 || code === 802) return isNight ? "malam" : "cerah-berawan";
  return "berawan";
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderAccount(user) {
  $("account-initials").textContent = initials(user.name);
  $("account-name").textContent = user.name;
  $("account-email").textContent = user.email;
  $("account-userid").textContent = user.userId || "-";
  const firstName = user.name.split(/\s+/)[0];
  $("greeting").textContent = `Halo, ${firstName}. Kamu berhasil masuk.`;

  if (user.elgamalPublic) {
    const { y, g, p } = user.elgamalPublic;
    $("my-elgamal-key").textContent = `ID Saya: ${user.userId} · Kunci Publik ElGamal (y=${y}, g=${g}, p=${p})`;
  }
}

function renderDiffieHellman(dh) {
  if (!dh) return;
  $("dh-params").textContent = `p = ${dh.p}, g = ${dh.g}`;
  $("dh-pubkeys").textContent = `Client A = ${dh.clientPublicA} | Server B = ${dh.serverPublicB}`;
  $("dh-shared").textContent = `K = ${dh.sharedSecretK}`;
  $("dh-cipher").textContent = (dh.ciphertext || []).join(" ");
}

function setWeatherState(state) {
  const card = $("weather");
  for (const el of card.querySelectorAll("[data-state]")) {
    el.hidden = el.dataset.state !== state;
  }
  card.setAttribute("aria-busy", String(state === "loading"));
}

function renderWeather(w) {
  const country = countryName(w.country);
  $("weather-location").textContent = country ? `${w.city}, ${country}` : w.city;
  $("weather-intro").textContent = `Berikut cuaca ${w.city} hari ini.`;
  $("weather-temp").textContent = `${w.temp}°`;
  $("weather-desc").textContent = capitalize(w.description);
  $("weather-feels").textContent = `· Terasa seperti ${w.feelsLike}°`;
  $("weather-humidity").textContent = `${w.humidity}%`;
  $("weather-wind").textContent = `${w.windKmh} km/j`;
  $("weather-pressure").textContent = `${w.pressure} hPa`;
  $("weather-updated").textContent = `Diperbarui ${localTime(w.dt, w.timezone)}`;
  $("weather-art").src = `assets/weather/${illustrationFor(w.conditionCode, w.isNight)}.svg`;
}

async function loadWeather({ moveFocus = false } = {}) {
  setWeatherState("loading");
  try {
    renderWeather(await getWeather(WEATHER_CITY));
    setWeatherState("ready");
  } catch (err) {
    $("weather-error").textContent = WEATHER_ERRORS[err.code] ?? WEATHER_ERRORS.UNKNOWN;
    setWeatherState("error");
  }
  if (moveFocus) {
    const card = $("weather");
    card.tabIndex = -1;
    card.focus();
  }
}

function renderContacts() {
  const listEl = $("contact-list");
  listEl.innerHTML = "";

  for (const f of friendsList) {
    const li = document.createElement("li");
    li.className = "wa__contact" + (activeFriend?.userId === f.userId ? " wa__contact--active" : "");
    li.setAttribute("role", "option");
    li.setAttribute("aria-selected", String(activeFriend?.userId === f.userId));
    li.innerHTML = `
      <span class="wa__contact-avatar">${escapeHtml(initials(f.name))}</span>
      <div class="wa__contact-info">
        <div class="wa__contact-name">${escapeHtml(f.name)}</div>
        <div class="wa__contact-meta">${escapeHtml(f.userId)} · y=${escapeHtml(f.elgamalPublic?.y ?? "")}</div>
      </div>
    `;
    li.addEventListener("click", () => selectFriend(f));
    listEl.appendChild(li);
  }
}

async function selectFriend(friend) {
  activeFriend = friend;
  lastRenderedSignature = "";
  renderContacts();

  $("peer-avatar").textContent = initials(friend.name);
  $("peer-name").textContent = `${friend.name} (${friend.userId})`;
  const pub = friend.elgamalPublic;
  $("peer-pubkey").textContent = pub
    ? `Kunci Publik ElGamal Penerima: (y=${pub.y}, g=${pub.g}, p=${pub.p})`
    : "";

  await refreshMessages(true);
}

function formatElgamalStages(msg) {
  const st = msg.elgamalStages;
  if (!st) return "";
  const s1 = st.stage1 || {};
  const s2 = st.stage2 || [];
  const s3 = st.stage3 || [];

  const encLines = s2
    .map(
      (b, i) =>
        `Blok ${i + 1} ('${escapeHtml(b.char)}' -> m=${b.m}, k=${b.k}): a = ${escapeHtml(b.formula_a)} | b = ${escapeHtml(b.formula_b)}`
    )
    .join("<br>");

  const decLines = s3
    .map(
      (d, i) =>
        `Blok ${i + 1} (${d.a}, ${d.b}): (a^x)^(-1) = ${escapeHtml(d.formula_inv)} | m = ${escapeHtml(d.formula_m)} -> '${escapeHtml(d.char)}'`
    )
    .join("<br>");

  const moreNote =
    st.totalBlocks > s2.length
      ? `<br><em>... (${st.totalBlocks - s2.length} karakter lainnya dihitung dengan cara yang sama)</em>`
      : "";

  return `
    <details class="wa__details">
      <summary>Lihat Tahapan ElGamal (Tahap 1, 2, 3)</summary>
      <div class="wa__stages">
        <div class="wa__stage-title">Tahap 1 — Kunci Penerima (${escapeHtml(s1.receiverName || "")}):</div>
        <div>Prima p = ${s1.p}, Generator g = ${s1.g}, Kunci Privat x = ${s1.privateX}</div>
        <div>Kunci Publik: ${escapeHtml(s1.formula || "")}</div>
        <div class="wa__stage-title">Tahap 2 — Enkripsi Pengirim (a = g^k mod p, b = y^k * m mod p):</div>
        <div>${encLines}${moreNote}</div>
        <div class="wa__stage-title">Tahap 3 — Dekripsi Penerima (m = b * a^(p-1-x) mod p):</div>
        <div>${decLines}${moreNote}</div>
      </div>
    </details>
  `;
}

async function refreshMessages(forceScroll = false) {
  if (!activeFriend) return;
  try {
    const msgs = await fetchMessages(activeFriend.userId);
    const sig = msgs.map((m) => m.id).join("|");
    if (sig === lastRenderedSignature && !forceScroll) return;
    lastRenderedSignature = sig;

    const container = $("chat-messages");
    if (msgs.length === 0) {
      container.innerHTML = `<div class="wa__empty">Belum ada percakapan dengan ${escapeHtml(activeFriend.name)}. Ketik pesan di bawah untuk mengenkripsi dengan ElGamal!</div>`;
      return;
    }

    container.innerHTML = msgs
      .map((m) => {
        const mine = m.fromUserId === currentUser.userId;
        const pairsPreview = (m.ciphertext || [])
          .slice(0, 5)
          .map((pair) => `(${pair[0]}, ${pair[1]})`)
          .join(" ");
        const suffix = (m.ciphertext || []).length > 5 ? " ..." : "";

        return `
          <div class="wa__bubble ${mine ? "wa__bubble--mine" : ""}">
            <div class="wa__bubble-top">
              <span class="wa__sender">${escapeHtml(m.fromName)} (${escapeHtml(m.fromUserId)})</span>
              <span class="wa__time">${escapeHtml(m.timestamp)}</span>
            </div>
            <div class="wa__text">${escapeHtml(m.plaintext)}</div>
            <div class="wa__cipher-preview">Cipher (a, b): ${escapeHtml(pairsPreview + suffix)}</div>
            ${formatElgamalStages(m)}
          </div>
        `;
      })
      .join("");

    container.scrollTop = container.scrollHeight;
  } catch {
    // abaikan gangguan jaringan sementara saat polling
  }
}

async function initChat() {
  try {
    const data = await fetchFriends();
    if (data.me) {
      currentUser = data.me;
      renderAccount(currentUser);
    }
    friendsList = data.friends || [];
    renderContacts();
    if (friendsList.length > 0 && !activeFriend) {
      await selectFriend(friendsList[0]);
    }
  } catch {
    // sesi tidak valid atau server mati
  }
}

function init() {
  const session = requireSession();
  if (!session) return;

  currentUser = session.user;
  document.body.hidden = false;
  $("year").textContent = String(new Date().getFullYear());
  $("weather-intro").textContent = `Berikut cuaca ${WEATHER_CITY} hari ini.`;

  renderAccount(session.user);
  renderDiffieHellman(session.dh);

  $("copy-userid").addEventListener("click", async () => {
    const code = $("account-userid").textContent;
    try {
      await navigator.clipboard.writeText(code);
      $("copy-userid").textContent = "Tersalin!";
      setTimeout(() => {
        $("copy-userid").textContent = "Salin";
      }, 1500);
    } catch {
      // fallback
    }
  });

  $("logout").addEventListener("click", () => {
    logout();
    location.replace("login.html");
  });

  $("weather-retry").addEventListener("click", () => loadWeather({ moveFocus: true }));

  $("add-friend-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = $("friend-id-input");
    const feedback = $("add-friend-feedback");
    const friendId = input.value.trim().toUpperCase();
    feedback.className = "wa__add-feedback";
    if (!friendId) return;

    try {
      const friend = await addFriendById(friendId);
      feedback.textContent = `Berhasil menambahkan ${friend.name} (${friend.userId})!`;
      feedback.classList.add("wa__add-feedback--ok");
      input.value = "";
      const exists = friendsList.some((f) => f.userId === friend.userId);
      if (!exists) friendsList.push(friend);
      await selectFriend(friend);
    } catch (err) {
      feedback.classList.add("wa__add-feedback--error");
      if (err.code === "USER_NOT_FOUND") {
        feedback.textContent = "User ID tidak ditemukan. Pastikan temanmu sudah daftar.";
      } else if (err.code === "CANNOT_ADD_SELF") {
        feedback.textContent = "Tidak bisa menambahkan User ID milik sendiri.";
      } else {
        feedback.textContent = "Gagal menambahkan teman.";
      }
    }
  });

  $("chat-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!activeFriend) return;
    const input = $("chat-input");
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    try {
      await sendChatMessage(activeFriend.userId, text);
      await refreshMessages(true);
    } catch (err) {
      input.value = text;
      if (err && err.code === "INVALID_CHARACTER") {
        alert("Pesan mengandung karakter di luar rentang ElGamal p=2273 (misalnya emoji). Silakan gunakan karakter teks standar / ASCII.");
      }
    }
  });

  loadWeather();
  initChat();
  setInterval(() => refreshMessages(false), 2500);
}

init();

