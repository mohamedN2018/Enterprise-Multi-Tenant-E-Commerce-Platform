import http from './http';

// Buyer-facing, store-scoped resources. Every call must carry the shopped
// store as X-Store-Id (pass `headers` from the cart store).
export const shop = {
  // Orders
  orders: (headers, params) => http.get('/orders/', { headers, params }),
  order: (headers, id) => http.get(`/orders/${id}/`, { headers }),
  cancelOrder: (headers, id) => http.post(`/orders/${id}/cancel/`, null, { headers }),

  // Addresses
  addresses: (headers) => http.get('/addresses/', { headers }),
  createAddress: (headers, payload) => http.post('/addresses/', payload, { headers }),
  updateAddress: (headers, id, payload) => http.patch(`/addresses/${id}/`, payload, { headers }),
  deleteAddress: (headers, id) => http.delete(`/addresses/${id}/`, { headers }),
  setDefaultAddress: (headers, id) => http.post(`/addresses/${id}/default/`, null, { headers }),

  // Reviews (buyer)
  myReviews: (headers) => http.get('/reviews/mine/', { headers }),
  createReview: (headers, payload) => http.post('/reviews/', payload, { headers }),
  voteReview: (headers, id, isHelpful) =>
    http.post(`/reviews/${id}/vote/`, { is_helpful: isHelpful }, { headers }),

  // Wishlist
  wishlist: (headers) => http.get('/wishlist/', { headers }),
  addWishlist: (headers, payload) => http.post('/wishlist/', payload, { headers }),
  removeWishlist: (headers, id) => http.delete(`/wishlist/${id}/`, { headers }),
  wishlistToCart: (headers, id) => http.post(`/wishlist/${id}/move-to-cart/`, null, { headers })
};
