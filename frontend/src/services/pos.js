import http from './http';

// Cashier (POS) integration for the active store. Store context (X-Store-Id) is
// attached by the http interceptor. The plaintext API key is returned only by
// `link` and `rotate` — it is never re-readable afterwards.
export const pos = {
  connection: () => http.get('/pos/connection/'),
  link: (payload) => http.post('/pos/connection/', payload),
  update: (payload) => http.patch('/pos/connection/', payload),
  unlink: () => http.delete('/pos/connection/'),
  rotate: () => http.post('/pos/connection/rotate/', {})
};
