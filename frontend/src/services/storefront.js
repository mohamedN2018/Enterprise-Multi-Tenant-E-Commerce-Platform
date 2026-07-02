import http from './http';

// Public marketplace browsing (AllowAny). Cross-store, no auth or store header.
export const storefront = {
  stores: (params) => http.get('/storefront/stores/', { params }),
  store: (slug) => http.get(`/storefront/stores/${slug}/`),
  storeProducts: (slug, params) => http.get(`/storefront/stores/${slug}/products/`, { params }),
  categories: () => http.get('/storefront/categories/'),
  products: (params) => http.get('/storefront/products/', { params }),
  product: (id) => http.get(`/storefront/products/${id}/`),
  productReviews: (id) => http.get(`/storefront/products/${id}/reviews/`)
};
