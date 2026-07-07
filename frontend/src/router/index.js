import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useTenantStore } from '@/stores/tenant';
import { activeStore } from '@/services/http';
import { PAGE_AREA } from '@/utils/permissions';
import { t } from '@/i18n';

// Layouts are eager (small, always needed); pages are lazy for route-splitting.
import StoreLayout from '@/layouts/StoreLayout.vue';
import AdminLayout from '@/layouts/AdminLayout.vue';
import AuthLayout from '@/layouts/AuthLayout.vue';

// The admin console pages are shared by two URL prefixes:
//   /admin/*  → super-admin console   ·   /seller/* → seller console
// A router guard (below) keeps each role inside its own prefix.
const CONSOLE_PAGES = [
  ['', 'dashboard', () => import('@/pages/admin/Dashboard.vue')],
  ['platform', 'platform', () => import('@/pages/admin/Platform.vue')],
  ['sellers/:id', 'seller-detail', () => import('@/pages/admin/SellerDetail.vue')],
  ['analytics', 'analytics', () => import('@/pages/admin/Analytics.vue')],
  ['products', 'products', () => import('@/pages/admin/Products.vue')],
  ['categories', 'categories', () => import('@/pages/admin/Categories.vue')],
  ['brands', 'brands', () => import('@/pages/admin/Brands.vue')],
  ['attributes', 'attributes', () => import('@/pages/admin/Attributes.vue')],
  ['orders', 'orders', () => import('@/pages/admin/Orders.vue')],
  ['orders/:id', 'order-detail', () => import('@/pages/admin/OrderDetail.vue')],
  ['inventory', 'inventory', () => import('@/pages/admin/Inventory.vue')],
  ['promotions', 'promotions', () => import('@/pages/admin/Promotions.vue')],
  ['campaigns', 'campaigns', () => import('@/pages/admin/Campaigns.vue')],
  ['gift-cards', 'giftcards', () => import('@/pages/admin/GiftCards.vue')],
  ['shipping', 'shipping', () => import('@/pages/admin/Shipping.vue')],
  ['returns', 'returns', () => import('@/pages/admin/Returns.vue')],
  ['payments', 'payments', () => import('@/pages/admin/Payments.vue')],
  ['payouts', 'payouts', () => import('@/pages/admin/Payouts.vue')],
  ['finance', 'finance', () => import('@/pages/admin/Finance.vue')],
  ['pricing', 'pricing', () => import('@/pages/admin/Pricing.vue')],
  ['procurement', 'procurement', () => import('@/pages/admin/Procurement.vue')],
  ['fraud', 'fraud', () => import('@/pages/admin/Fraud.vue')],
  ['reviews', 'reviews', () => import('@/pages/admin/Reviews.vue')],
  ['notifications', 'notifications', () => import('@/pages/admin/Notifications.vue')],
  ['team', 'team', () => import('@/pages/admin/Team.vue')],
  ['settings', 'settings', () => import('@/pages/admin/Settings.vue')]
];
const consoleChildren = (prefix) =>
  CONSOLE_PAGES.map(([path, key, component]) => ({ path, name: `${prefix}-${key}`, component }));

const routes = [
  {
    path: '/',
    component: StoreLayout,
    children: [
      { path: '', name: 'home', component: () => import('@/pages/store/Home.vue') },
      { path: 'stores', name: 'stores', component: () => import('@/pages/store/Stores.vue') },
      { path: 'store/:slug', name: 'store', component: () => import('@/pages/store/StorePage.vue') },
      { path: 'products', name: 'products', component: () => import('@/pages/store/Products.vue') },
      { path: 'support', name: 'support', component: () => import('@/pages/store/Support.vue') },
      { path: 'testimonials', name: 'testimonials', component: () => import('@/pages/store/Testimonials.vue') },
      {
        path: 'product/:id',
        name: 'product',
        component: () => import('@/pages/store/ProductDetail.vue')
      },
      { path: 'cart', name: 'cart', component: () => import('@/pages/store/Cart.vue') },
      {
        path: 'checkout',
        name: 'checkout',
        meta: { requiresAuth: true },
        component: () => import('@/pages/store/Checkout.vue')
      },
      {
        path: 'order/:id',
        name: 'order-confirmation',
        meta: { requiresAuth: true },
        component: () => import('@/pages/store/OrderConfirmation.vue')
      },
      {
        path: 'account',
        name: 'account',
        meta: { requiresAuth: true },
        component: () => import('@/pages/store/Account.vue')
      }
    ]
  },
  {
    path: '/auth',
    component: AuthLayout,
    meta: { guestOnly: true },
    children: [
      { path: 'login', name: 'login', component: () => import('@/pages/auth/Login.vue') },
      { path: 'seller', name: 'seller-login', meta: { seller: true }, component: () => import('@/pages/auth/Login.vue') },
      { path: 'register', name: 'register', component: () => import('@/pages/auth/Register.vue') },
      {
        path: 'forgot',
        name: 'forgot-password',
        component: () => import('@/pages/auth/ForgotPassword.vue')
      },
      {
        path: 'reset',
        name: 'reset-password',
        component: () => import('@/pages/auth/ResetPassword.vue')
      },
      { path: 'verify', name: 'verify-email', component: () => import('@/pages/auth/VerifyEmail.vue') }
    ]
  },
  // Super-admin console.
  { path: '/admin', component: AdminLayout, meta: { requiresAuth: true }, children: consoleChildren('admin') },
  // Seller console (same pages, different URL prefix).
  { path: '/seller', component: AdminLayout, meta: { requiresAuth: true }, children: consoleChildren('seller') },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/pages/NotFound.vue') }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, saved) {
    if (saved) return saved;
    return { top: 0 };
  }
});

// Dynamic document titles — resolved through i18n so the tab follows the locale.
const TITLE_KEYS = {
  home: 'nav.home',
  stores: 'stores.title',
  store: 'nav.stores',
  products: 'shop.title',
  support: 'support.title',
  testimonials: 'home.testimonials',
  product: 'product.shopDetail',
  cart: 'cart.title',
  checkout: 'checkout.title',
  'order-confirmation': 'order.confirmation',
  account: 'account.title',
  login: 'auth.signIn',
  'seller-login': 'auth.sellerSignIn',
  register: 'auth.createAccount',
  'forgot-password': 'auth.forgotPassword',
  'reset-password': 'auth.resetTitle',
  'verify-email': 'auth.verifyTitle',
  'not-found': 'common.pageNotFound'
};
// Console pages are keyed by their suffix (dashboard/products/…) for either prefix.
const CONSOLE_TITLE_KEYS = {
  dashboard: 'admin.dashboard',
  platform: 'admin.platform',
  'seller-detail': 'platformPage.sellerDetailTitle',
  analytics: 'admin.analytics',
  products: 'admin.products',
  categories: 'admin.categories',
  brands: 'admin.brands',
  attributes: 'admin.attributes',
  orders: 'admin.orders',
  'order-detail': 'orderDetailPage.title',
  inventory: 'admin.inventory',
  shipping: 'admin.shipping',
  returns: 'admin.returns',
  promotions: 'admin.promotions',
  campaigns: 'admin.campaigns',
  giftcards: 'admin.giftCards',
  reviews: 'admin.reviews',
  payments: 'admin.payments',
  payouts: 'admin.payouts',
  finance: 'admin.finance',
  pricing: 'admin.pricing',
  procurement: 'admin.procurement',
  fraud: 'admin.fraud',
  notifications: 'admin.notifications',
  team: 'admin.team',
  settings: 'admin.settings'
};
router.afterEach((to) => {
  const name = to.name || '';
  const consoleMatch = /^(?:admin|seller)-(.+)$/.exec(name);
  const key = consoleMatch ? CONSOLE_TITLE_KEYS[consoleMatch[1]] : TITLE_KEYS[name];
  const label = key ? t(key) : '';
  document.title = label ? `${label} · q-shop` : 'q-shop';
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (!auth.ready) await auth.bootstrap();

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } };
  }
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'home' };
  }
  // Keep each role inside its own console prefix (also catches any stray links).
  if (auth.isAuthenticated) {
    const isSuper = !!auth.user?.is_superuser;
    if (to.path.startsWith('/admin') && !isSuper) {
      return { path: to.path.replace(/^\/admin/, '/seller'), query: to.query, hash: to.hash };
    }
    if (to.path.startsWith('/seller') && isSuper) {
      return { path: to.path.replace(/^\/seller/, '/admin'), query: to.query, hash: to.hash };
    }
    // The admin panel is separate from the stores: a super-admin must enter a
    // store before opening any store-scoped console page. Platform-panel pages
    // (the panel itself + a seller's detail page) are reachable without one.
    const PLATFORM_PAGES = new Set(['admin-platform', 'admin-seller-detail']);
    if (isSuper && to.path.startsWith('/admin') && !PLATFORM_PAGES.has(to.name) && !activeStore.id) {
      return { name: 'admin-platform' };
    }
    // Employees can only open console pages in the areas the owner granted them
    // (once their role is resolved; the nav hides the rest, this catches deep links).
    if (!isSuper) {
      const tenant = useTenantStore();
      const seg = /^(?:admin|seller)-(.+)$/.exec(to.name || '');
      if (seg && tenant.role === 'employee') {
        const area = PAGE_AREA[seg[1]];
        if (area && !tenant.canArea(area)) return { name: 'seller-dashboard' };
      }
    }
  }
  return true;
});

export default router;
