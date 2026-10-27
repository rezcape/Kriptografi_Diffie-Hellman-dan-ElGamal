import { API_BASE_URL } from "./config.js";
import { establishDiffieHellmanAndEncrypt } from "/crypto/index.js";

const SESSION_KEY = "dheg.session";

export class AuthError extends Error {
  constructor(code) {
    super(code);
    this.name = "AuthError";
    this.code = code;
  }
}

async function request(method, path, body, token = null) {
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: Object.keys(headers).length ? headers : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new AuthError("NETWORK");
  }

  let data = {};
  try {
    data = await res.json();
  } catch {
    // balasan kosong
  }
  return { status: res.status, body: data };
}

function failFrom({ status, body }) {
  if (status === 401) return new AuthError("INVALID_CREDENTIALS");
  if (status === 409 || body?.error === "EMAIL_TAKEN") return new AuthError("EMAIL_TAKEN");
  if (status === 404 && body?.error === "USER_NOT_FOUND") return new AuthError("USER_NOT_FOUND");
  if (status === 400 && body?.error === "CANNOT_ADD_SELF") return new AuthError("CANNOT_ADD_SELF");
  if (body?.error) return new AuthError(body.error, body?.message);
  return new AuthError("SERVER");
}

async function performDiffieHellman(password) {
  const paramRes = await request("GET", "/api/dh/params");
  if (paramRes.status !== 200) throw failFrom(paramRes);
  const { p, g, serverPublicB } = paramRes.body;
  return establishDiffieHellmanAndEncrypt(password, p, g, serverPublicB);
}

function saveSession(session) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function getSession() {
  try {
    const session = JSON.parse(sessionStorage.getItem(SESSION_KEY));
    return session?.token ? session : null;
  } catch {
    return null;
  }
}

export function logout() {
  sessionStorage.removeItem(SESSION_KEY);
}

export async function login(email, password) {
  const dh = await performDiffieHellman(password);
  const res = await request("POST", "/api/auth/login", {
    email: email.trim(),
    encryptedPassword: dh.ciphertext,
    clientPublicA: dh.clientPublicA,
  });
  if (res.status !== 200) throw failFrom(res);

  saveSession({
    token: res.body.token,
    user: res.body.user,
    dh: {
      ...dh,
      formulaServerK: res.body.dhServer?.formulaServerK ?? "",
    },
  });
  return res.body.user;
}

export async function register(data) {
  const { firstName, lastName, email, phone, password } = data;
  const dh = await performDiffieHellman(password);
  const res = await request("POST", "/api/auth/register", {
    firstName: firstName.trim(),
    lastName: lastName.trim(),
    email: email.trim(),
    phone,
    encryptedPassword: dh.ciphertext,
    clientPublicA: dh.clientPublicA,
  });
  if (res.status !== 201) throw failFrom(res);
  return res.body.userId;
}

export async function fetchFriends() {
  const session = getSession();
  const res = await request("GET", "/api/friends", null, session?.token);
  if (res.status !== 200) throw failFrom(res);
  return res.body;
}

export async function addFriendById(friendId) {
  const session = getSession();
  const res = await request("POST", "/api/friends/add", { friendId }, session?.token);
  if (res.status !== 200) throw failFrom(res);
  return res.body.friend;
}

export async function fetchMessages(friendId) {
  const session = getSession();
  const res = await request(
    "GET",
    `/api/chat/messages?friendId=${encodeURIComponent(friendId)}`,
    null,
    session?.token
  );
  if (res.status !== 200) throw failFrom(res);
  return res.body.messages;
}

export async function sendChatMessage(toUserId, text) {
  const session = getSession();
  const res = await request("POST", "/api/chat/send", { toUserId, text }, session?.token);
  if (res.status !== 201) throw failFrom(res);
  return res.body.message;
}

