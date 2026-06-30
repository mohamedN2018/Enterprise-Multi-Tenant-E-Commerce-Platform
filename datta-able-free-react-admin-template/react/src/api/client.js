// Axios client for the Marketplace API.
//
// - Attaches the JWT access token and the active store header (X-Store-Id).
// - Unwraps the standard response envelope { success, message, data, meta }.
// - On 401, tries a one-shot token refresh, then redirects to /login.

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const tokenStore = {
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

export const storeHeader = {
  get id() {
    return localStorage.getItem('active_store_id') || '';
  },
  set(id) {
    if (id) localStorage.setItem('active_store_id', id);
    else localStorage.removeItem('active_store_id');
  }
};

const api = axios.create({ baseURL: BASE_URL, headers: { 'Content-Type': 'application/json' } });

api.interceptors.request.use((config) => {
  const token = tokenStore.access;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  const storeId = storeHeader.id;
  if (storeId) config.headers['X-Store-Id'] = storeId;
  return config;
});

let refreshing = null;

api.interceptors.response.use(
  (response) => {
    // Unwrap the envelope: callers receive `data` directly, with pagination meta attached.
    const body = response.data;
    if (body && typeof body === 'object' && 'success' in body && 'data' in body) {
      const unwrapped = body.data;
      if (unwrapped && typeof unwrapped === 'object' && !Array.isArray(unwrapped)) {
        Object.defineProperty(unwrapped, '$meta', { value: body.meta, enumerable: false });
      }
      response.data = unwrapped;
      response.$meta = body.meta;
    }
    return response;
  },
  async (error) => {
    const { response, config } = error;
    if (response && response.status === 401 && !config._retried && tokenStore.refresh) {
      config._retried = true;
      try {
        refreshing =
          refreshing ||
          axios.post(`${BASE_URL}/auth/token/refresh/`, { refresh: tokenStore.refresh });
        const refreshResp = await refreshing;
        refreshing = null;
        const newAccess = refreshResp.data?.data?.access || refreshResp.data?.access;
        if (newAccess) {
          tokenStore.set({ access: newAccess });
          config.headers.Authorization = `Bearer ${newAccess}`;
          return api(config);
        }
      } catch (e) {
        refreshing = null;
      }
      tokenStore.clear();
      if (!window.location.pathname.endsWith('/login')) window.location.assign('/login');
    }
    return Promise.reject(error);
  }
);

// Convenience helpers returning the unwrapped payload.
export const apiGet = (url, params) => api.get(url, { params }).then((r) => r.data);
export const apiPost = (url, data) => api.post(url, data).then((r) => r.data);
export const apiPut = (url, data) => api.put(url, data).then((r) => r.data);
export const apiPatch = (url, data) => api.patch(url, data).then((r) => r.data);
export const apiDelete = (url) => api.delete(url).then((r) => r.data);

// Error message extractor for the standard envelope.
export const errorMessage = (err) =>
  err?.response?.data?.message ||
  err?.response?.data?.errors?.detail ||
  err?.message ||
  'Something went wrong.';

export default api;
