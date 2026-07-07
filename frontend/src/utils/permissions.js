// Granular employee permission areas — must mirror the backend
// apps.stores.access.PERMISSION_AREAS. Owners/managers write everything; an
// employee writes only the areas the owner granted them.
export const AREAS = ['catalog', 'inventory', 'sales', 'marketing', 'shipping', 'finance', 'settings'];

// Console page (route-name suffix) → permission area. `null` = always visible
// (dashboard/analytics) or handled elsewhere (team is owner-only; platform pages
// are admin-only).
export const PAGE_AREA = {
  dashboard: null,
  analytics: null,
  platform: null,
  'seller-detail': null,
  team: null,
  products: 'catalog',
  categories: 'catalog',
  brands: 'catalog',
  attributes: 'catalog',
  inventory: 'inventory',
  orders: 'sales',
  'order-detail': 'sales',
  returns: 'sales',
  payments: 'sales',
  reviews: 'sales',
  promotions: 'marketing',
  campaigns: 'marketing',
  giftcards: 'marketing',
  pricing: 'marketing',
  shipping: 'shipping',
  procurement: 'shipping',
  fraud: 'finance',
  payouts: 'finance',
  finance: 'finance',
  notifications: 'settings',
  settings: 'settings'
};
