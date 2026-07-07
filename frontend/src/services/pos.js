import http from './http';

// Cashier (POS) integration for the active store. Store context (X-Store-Id) is
// attached by the http interceptor.
export const pos = {
  // Outbound: link an external POS supplier (e.g. q-shop POS) and import its
  // catalog. The API key is stored server-side and never returned.
  supplier: () => http.get('/pos/supplier/'),
  connect: (payload) => http.post('/pos/supplier/', payload),
  disconnect: () => http.delete('/pos/supplier/'),
  importProducts: () => http.post('/pos/supplier/import/', {}),

  // Inbound: our own key that a cashier uses to push sales / read stock.
  connection: () => http.get('/pos/connection/'),
  link: (payload) => http.post('/pos/connection/', payload),
  update: (payload) => http.patch('/pos/connection/', payload),
  unlink: () => http.delete('/pos/connection/'),
  rotate: () => http.post('/pos/connection/rotate/', {})
};
