import { API_BASE_URL } from "./config.js";

export class WeatherError extends Error {
  constructor(code) {
    super(code);
    this.name = "WeatherError";
    this.code = code;
  }
}

export async function getWeather(city) {
  let res;
  try {
    res = await fetch(`${API_BASE_URL}/api/weather?city=${encodeURIComponent(city)}`);
  } catch {
    throw new WeatherError("BACKEND_DOWN");
  }

  let body = null;
  try {
    body = await res.json();
  } catch {
    // ditangani di bawah
  }

  if (res.ok && body) return body;
  const known = ["WEATHER_KEY_MISSING", "WEATHER_KEY_INVALID", "CITY_NOT_FOUND", "WEATHER_UPSTREAM"];
  throw new WeatherError(known.includes(body?.error) ? body.error : "UNKNOWN");
}

