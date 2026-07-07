import http from './http';

// Super-admin (platform) resources. Superuser-only on the backend — the only
// place a store can be assigned to another seller and where per-seller /
// per-store limits are configured.
export const platform = {
  stores: (params) => http.get('/platform/stores/', { params }),
  createStore: (payload) => http.post('/platform/stores/', payload),
  updateStore: (id, payload) => http.patch(`/platform/stores/${id}/`, payload),
  deleteStore: (id) => http.delete(`/platform/stores/${id}/`),
  sellers: (params) => http.get('/platform/sellers/', { params }),
  seller: (id) => http.get(`/platform/sellers/${id}/`),
  createSeller: (payload) => http.post('/platform/sellers/', payload),
  updateSeller: (id, payload) => http.patch(`/platform/sellers/${id}/`, payload),
  requests: (params) => http.get('/platform/requests/', { params }),
  approveRequest: (id) => http.post(`/platform/requests/${id}/approve/`),
  rejectRequest: (id) => http.post(`/platform/requests/${id}/reject/`)
};
