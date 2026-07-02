import http from './http';

// Seller/admin resources. Store context comes from the admin's active store
// (X-Store-Id auto-attached by the http interceptor). Requires membership.
export const seller = {
  // Stores & team
  stores: () => http.get('/stores/'),
  createStore: (payload) => http.post('/stores/', payload),
  store: (id) => http.get(`/stores/${id}/`),
  updateStore: (id, payload) => http.patch(`/stores/${id}/`, payload),
  storeSettings: (id) => http.get(`/stores/${id}/settings/`),
  updateStoreSettings: (id, payload) => http.patch(`/stores/${id}/settings/`, payload),
  members: (id) => http.get(`/stores/${id}/members/`),
  addMember: (id, payload) => http.post(`/stores/${id}/members/`, payload),
  updateMember: (id, memberId, payload) =>
    http.patch(`/stores/${id}/members/${memberId}/`, payload),
  removeMember: (id, memberId) => http.delete(`/stores/${id}/members/${memberId}/`),

  // Analytics
  dashboard: () => http.get('/analytics/dashboard/'),

  // Catalog
  products: (params) => http.get('/catalog/products/', { params }),
  product: (id) => http.get(`/catalog/products/${id}/`),
  createProduct: (payload) => http.post('/catalog/products/', payload),
  updateProduct: (id, payload) => http.patch(`/catalog/products/${id}/`, payload),
  deleteProduct: (id) => http.delete(`/catalog/products/${id}/`),
  variants: (productId) => http.get(`/catalog/products/${productId}/variants/`),
  createVariant: (productId, payload) =>
    http.post(`/catalog/products/${productId}/variants/`, payload),
  updateVariant: (productId, variantId, payload) =>
    http.patch(`/catalog/products/${productId}/variants/${variantId}/`, payload),
  deleteVariant: (productId, variantId) =>
    http.delete(`/catalog/products/${productId}/variants/${variantId}/`),

  categories: (params) => http.get('/catalog/categories/', { params }),
  createCategory: (payload) => http.post('/catalog/categories/', payload),
  updateCategory: (id, payload) => http.patch(`/catalog/categories/${id}/`, payload),
  deleteCategory: (id) => http.delete(`/catalog/categories/${id}/`),

  brands: (params) => http.get('/catalog/brands/', { params }),
  createBrand: (payload) => http.post('/catalog/brands/', payload),
  updateBrand: (id, payload) => http.patch(`/catalog/brands/${id}/`, payload),
  deleteBrand: (id) => http.delete(`/catalog/brands/${id}/`),

  // Shipping (staff)
  shippingZones: () => http.get('/shipping/zones/'),
  createShippingZone: (payload) => http.post('/shipping/zones/', payload),
  updateShippingZone: (id, payload) => http.patch(`/shipping/zones/${id}/`, payload),
  deleteShippingZone: (id) => http.delete(`/shipping/zones/${id}/`),
  shippingMethods: (zoneId) => http.get(`/shipping/zones/${zoneId}/methods/`),
  createShippingMethod: (zoneId, payload) => http.post(`/shipping/zones/${zoneId}/methods/`, payload),
  setOrderTracking: (orderId, payload) => http.post(`/shipping/orders/${orderId}/tracking/`, payload),

  // Payouts (staff)
  payoutAccount: () => http.get('/payouts/account/'),
  payoutLedger: (params) => http.get('/payouts/ledger/', { params }),
  payouts: (params) => http.get('/payouts/', { params }),
  requestPayout: (payload) => http.post('/payouts/', payload),
  markPayoutPaid: (id) => http.post(`/payouts/${id}/mark-paid/`),
  commission: () => http.get('/payouts/commission/'),
  setCommission: (payload) => http.put('/payouts/commission/', payload),

  // Returns (staff)
  returnsManage: (params) => http.get('/returns/manage/', { params }),
  approveReturn: (id) => http.post(`/returns/${id}/approve/`),
  rejectReturn: (id, payload) => http.post(`/returns/${id}/reject/`, payload || {}),
  refundReturn: (id) => http.post(`/returns/${id}/refund/`),

  // Campaigns (promotions)
  campaigns: (params) => http.get('/promotions/campaigns/', { params }),
  activeCampaigns: () => http.get('/promotions/campaigns/active/'),
  createCampaign: (payload) => http.post('/promotions/campaigns/', payload),
  updateCampaign: (id, payload) => http.patch(`/promotions/campaigns/${id}/`, payload),
  deleteCampaign: (id) => http.delete(`/promotions/campaigns/${id}/`),

  // Gift cards (staff)
  giftCards: (params) => http.get('/rewards/gift-cards/', { params }),
  issueGiftCard: (payload) => http.post('/rewards/gift-cards/', payload),

  // Payments (staff)
  paymentsManage: (params) => http.get('/payments/manage/', { params }),
  paymentDetail: (id) => http.get(`/payments/manage/${id}/`),
  capturePayment: (id) => http.post(`/payments/manage/${id}/capture/`),
  gateways: () => http.get('/payments/gateways/'),

  // Fraud (staff)
  fraudChecks: (params) => http.get('/fraud/checks/', { params }),
  clearFraud: (id) => http.post(`/fraud/checks/${id}/clear/`),
  rejectFraud: (id) => http.post(`/fraud/checks/${id}/reject/`),

  // Finance (staff)
  taxZones: () => http.get('/finance/tax-zones/'),
  createTaxZone: (payload) => http.post('/finance/tax-zones/', payload),
  taxRates: (zoneId) => http.get(`/finance/tax-zones/${zoneId}/rates/`),
  createTaxRate: (zoneId, payload) => http.post(`/finance/tax-zones/${zoneId}/rates/`, payload),
  currencies: () => http.get('/finance/currencies/'),
  createCurrency: (payload) => http.post('/finance/currencies/', payload),
  exchangeRates: () => http.get('/finance/exchange-rates/'),
  createExchangeRate: (payload) => http.post('/finance/exchange-rates/', payload),

  // Pricing (staff)
  customerGroups: () => http.get('/pricing/groups/'),
  createCustomerGroup: (payload) => http.post('/pricing/groups/', payload),
  groupMembers: (groupId) => http.get(`/pricing/groups/${groupId}/members/`),
  addGroupMember: (groupId, payload) => http.post(`/pricing/groups/${groupId}/members/`, payload),
  priceRules: (params) => http.get('/pricing/rules/', { params }),
  createPriceRule: (payload) => http.post('/pricing/rules/', payload),
  deletePriceRule: (id) => http.delete(`/pricing/rules/${id}/`),

  // Procurement (staff)
  suppliers: () => http.get('/procurement/suppliers/'),
  createSupplier: (payload) => http.post('/procurement/suppliers/', payload),
  updateSupplier: (id, payload) => http.patch(`/procurement/suppliers/${id}/`, payload),
  purchaseOrders: (params) => http.get('/procurement/purchase-orders/', { params }),
  purchaseOrder: (id) => http.get(`/procurement/purchase-orders/${id}/`),
  createPurchaseOrder: (payload) => http.post('/procurement/purchase-orders/', payload),
  submitPurchaseOrder: (id) => http.post(`/procurement/purchase-orders/${id}/submit/`),
  receivePurchaseOrder: (id, payload) => http.post(`/procurement/purchase-orders/${id}/receive/`, payload || {}),
  cancelPurchaseOrder: (id) => http.post(`/procurement/purchase-orders/${id}/cancel/`),

  // Attributes (catalog)
  attributes: () => http.get('/catalog/attributes/'),
  createAttribute: (payload) => http.post('/catalog/attributes/', payload),
  attributeValues: (attrId) => http.get(`/catalog/attributes/${attrId}/values/`),
  createAttributeValue: (attrId, payload) => http.post(`/catalog/attributes/${attrId}/values/`, payload),

  // Analytics (staff)
  analyticsSummary: (params) => http.get('/analytics/summary/', { params }),
  analyticsEvents: (params) => http.get('/analytics/events/', { params }),

  // Orders (staff)
  orders: (params) => http.get('/orders/manage/', { params }),
  order: (id) => http.get(`/orders/manage/${id}/`),
  confirmOrder: (id) => http.post(`/orders/manage/${id}/confirm/`),
  cancelOrder: (id) => http.post(`/orders/manage/${id}/cancel/`),

  // Inventory
  stock: (params) => http.get('/inventory/stock/', { params }),
  lowStock: () => http.get('/inventory/stock/low/'),
  warehouses: () => http.get('/inventory/warehouses/'),
  createWarehouse: (payload) => http.post('/inventory/warehouses/', payload),
  receiveStock: (payload) => http.post('/inventory/stock/receive/', payload),
  adjustStock: (payload) => http.post('/inventory/stock/adjust/', payload),
  transferStock: (payload) => http.post('/inventory/stock/transfer/', payload),
  movements: (params) => http.get('/inventory/movements/', { params }),

  // Reviews moderation (view: any member; approve/reject: manager|owner)
  reviewsModeration: (params) => http.get('/reviews/moderation/', { params }),
  approveReview: (id) => http.post(`/reviews/${id}/approve/`),
  rejectReview: (id) => http.post(`/reviews/${id}/reject/`),

  // Notifications (per-user inbox, store-scoped)
  notifications: (params) => http.get('/notifications/', { params }),
  notificationsUnread: () => http.get('/notifications/unread-count/'),
  markNotificationRead: (id) => http.post(`/notifications/${id}/read/`),
  markAllNotificationsRead: () => http.post('/notifications/read-all/'),

  // Promotions
  coupons: (params) => http.get('/promotions/coupons/', { params }),
  createCoupon: (payload) => http.post('/promotions/coupons/', payload),
  updateCoupon: (id, payload) => http.patch(`/promotions/coupons/${id}/`, payload),
  deleteCoupon: (id) => http.delete(`/promotions/coupons/${id}/`),
  campaigns: (params) => http.get('/promotions/campaigns/', { params }),
  createCampaign: (payload) => http.post('/promotions/campaigns/', payload),
  updateCampaign: (id, payload) => http.patch(`/promotions/campaigns/${id}/`, payload),
  deleteCampaign: (id) => http.delete(`/promotions/campaigns/${id}/`)
};
