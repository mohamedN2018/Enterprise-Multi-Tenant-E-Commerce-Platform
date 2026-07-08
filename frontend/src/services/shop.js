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
  wishlistToCart: (headers, id) => http.post(`/wishlist/${id}/move-to-cart/`, null, { headers }),

  // Shipping (buyer)
  availableShipping: (headers, params) => http.get('/shipping/methods/', { headers, params }),

  // Checkout totals preview (subtotal + discount + tax + shipping = total)
  quote: (headers, payload) => http.post('/cart/quote/', payload, { headers }),

  // Returns (buyer)
  returns: (headers) => http.get('/returns/', { headers }),
  createReturn: (headers, payload) => http.post('/returns/', payload, { headers }),
  cancelReturn: (headers, id) => http.post(`/returns/${id}/cancel/`, null, { headers }),

  // Rewards (buyer)
  wallet: (headers) => http.get('/rewards/wallet/', { headers }),
  loyalty: (headers) => http.get('/rewards/loyalty/', { headers }),
  redeemLoyalty: (headers, payload) => http.post('/rewards/loyalty/redeem/', payload, { headers }),
  redeemGiftCard: (headers, payload) => http.post('/rewards/gift-cards/redeem/', payload, { headers }),

  // Notification preferences (buyer, store-scoped)
  notificationPrefs: (headers) => http.get('/notifications/preferences/', { headers }),
  updateNotificationPrefs: (headers, payload) => http.put('/notifications/preferences/', payload, { headers }),

  // Devices / sessions (not store-scoped)
  devices: () => http.get('/auth/devices/'),
  revokeDevice: (id) => http.delete(`/auth/devices/${id}/`),
  revokeAllDevices: () => http.post('/auth/devices/revoke-all/'),

  // Digital downloads (buyer, store-scoped)
  downloads: (headers) => http.get('/downloads/', { headers }),

  // Referrals (buyer, store-scoped)
  referralStats: (headers) => http.get('/rewards/referrals/code/', { headers }),
  referrals: (headers) => http.get('/rewards/referrals/', { headers }),
  applyReferral: (headers, payload) => http.post('/rewards/referrals/apply/', payload, { headers })
};
