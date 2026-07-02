import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// --- Token + tenant persistence -------------------------------------------
export const tokens = {
  get access() {
    return localStorage.getItem('access_token') || '';
  },
  get refresh() {
    return localStorage.getItem('refresh_token') || '';
  },
  set({ access, refresh }) {
    if (access) localStorage.setItem('access_token', access);
    if (refresh) localStorage.setItem('refresh_token', refresh);
  },
  clear() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
};

export const activeStore = {
  get id() {
    return localStorage.getItem('active_store_id') || '';
  },
  set(id) {
    if (id) localStorage.setItem('active_store_id', id);
    else localStorage.removeItem('active_store_id');
  }
};

const http = axios.create({ baseURL: BASE_URL, headers: { 'Content-Type': 'application/json' } });

http.interceptors.request.use((config) => {
  const token = tokens.access;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  // Respect an explicit per-call X-Store-Id (storefront targets a store);
  // otherwise fall back to the admin's active store.
  const sid = activeStore.id;
  if (sid && !config.headers['X-Store-Id']) config.headers['X-Store-Id'] = sid;
  return config;
});

let refreshing = null;

http.interceptors.response.use(
  (response) => {
    // Unwrap the { success, message, data, meta } envelope.
    const body = response.data;
    if (body && typeof body === 'object' && 'success' in body && 'data' in body) {
      response.$meta = body.meta;
      response.data = body.data;
    }
    return response;
  },
  async (error) => {
    const { response, config } = error;
    if (response && response.status === 401 && config && !config._retried && tokens.refresh) {
      config._retried = true;
      try {
        refreshing = refreshing || axios.post(`${BASE_URL}/auth/token/refresh/`, { refresh: tokens.refresh });
        const r = await refreshing;
        refreshing = null;
        const payload = r.data?.data || r.data || {};
        if (payload.access) {
          tokens.set({ access: payload.access, refresh: payload.refresh });
          config.headers.Authorization = `Bearer ${payload.access}`;
          return http(config);
        }
      } catch {
        refreshing = null;
      }
      tokens.clear();
      if (!window.location.pathname.endsWith('/login')) window.location.assign('/auth/login');
    }
    return Promise.reject(error);
  }
);

// Convenience helpers returning the unwrapped payload.
export const apiGet = (url, config) => http.get(url, config).then((r) => r.data);
export const apiPost = (url, data, config) => http.post(url, data, config).then((r) => r.data);
export const apiPatch = (url, data, config) => http.patch(url, data, config).then((r) => r.data);
export const apiPut = (url, data, config) => http.put(url, data, config).then((r) => r.data);
export const apiDelete = (url, config) => http.delete(url, config).then((r) => r.data);

export const errorMessage = (err) => {
  const body = err?.response?.data;
  const errors = body?.errors;
  // Field validation errors arrive as { field: ["msg", ...] } or { detail: "…" }.
  if (errors && typeof errors === 'object') {
    if (errors.detail) return String(errors.detail);
    const first = Object.values(errors)[0];
    if (Array.isArray(first) && first.length) return String(first[0]);
    if (typeof first === 'string') return first;
  }
  return body?.message || err?.message || 'Something went wrong.';
};

export default http;
