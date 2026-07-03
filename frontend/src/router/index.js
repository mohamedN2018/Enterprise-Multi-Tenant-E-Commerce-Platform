import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { t } from '@/i18n';

// Layouts are eager (small, always needed); pages are lazy for route-splitting.
import StoreLayout from '@/layouts/StoreLayout.vue';
import AdminLayout from '@/layouts/AdminLayout.vue';
import AuthLayout from '@/layouts/AuthLayout.vue';

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
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'admin-dashboard', component: () => import('@/pages/admin/Dashboard.vue') },
      {
        path: 'platform',
        name: 'admin-platform',
        component: () => import('@/pages/admin/Platform.vue')
      },
      { path: 'analytics', name: 'admin-analytics', component: () => import('@/pages/admin/Analytics.vue') },
      {
        path: 'products',
        name: 'admin-products',
        component: () => import('@/pages/admin/Products.vue')
      },
      {
        path: 'categories',
        name: 'admin-categories',
        component: () => import('@/pages/admin/Categories.vue')
      },
      { path: 'brands', name: 'admin-brands', component: () => import('@/pages/admin/Brands.vue') },
      { path: 'attributes', name: 'admin-attributes', component: () => import('@/pages/admin/Attributes.vue') },
      { path: 'orders', name: 'admin-orders', component: () => import('@/pages/admin/Orders.vue') },
      {
        path: 'orders/:id',
        name: 'admin-order-detail',
        component: () => import('@/pages/admin/OrderDetail.vue')
      },
      {
        path: 'inventory',
        name: 'admin-inventory',
        component: () => import('@/pages/admin/Inventory.vue')
      },
      {
        path: 'promotions',
        name: 'admin-promotions',
        component: () => import('@/pages/admin/Promotions.vue')
      },
      { path: 'campaigns', name: 'admin-campaigns', component: () => import('@/pages/admin/Campaigns.vue') },
      { path: 'gift-cards', name: 'admin-giftcards', component: () => import('@/pages/admin/GiftCards.vue') },
      { path: 'shipping', name: 'admin-shipping', component: () => import('@/pages/admin/Shipping.vue') },
      { path: 'returns', name: 'admin-returns', component: () => import('@/pages/admin/Returns.vue') },
      { path: 'payments', name: 'admin-payments', component: () => import('@/pages/admin/Payments.vue') },
      { path: 'payouts', name: 'admin-payouts', component: () => import('@/pages/admin/Payouts.vue') },
      { path: 'finance', name: 'admin-finance', component: () => import('@/pages/admin/Finance.vue') },
      { path: 'pricing', name: 'admin-pricing', component: () => import('@/pages/admin/Pricing.vue') },
      { path: 'procurement', name: 'admin-procurement', component: () => import('@/pages/admin/Procurement.vue') },
      { path: 'fraud', name: 'admin-fraud', component: () => import('@/pages/admin/Fraud.vue') },
      { path: 'reviews', name: 'admin-reviews', component: () => import('@/pages/admin/Reviews.vue') },
      {
        path: 'notifications',
        name: 'admin-notifications',
        component: () => import('@/pages/admin/Notifications.vue')
      },
      { path: 'team', name: 'admin-team', component: () => import('@/pages/admin/Team.vue') },
      {
        path: 'settings',
        name: 'admin-settings',
        component: () => import('@/pages/admin/Settings.vue')
      }
    ]
  },
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
  'admin-dashboard': 'admin.dashboard',
  'admin-platform': 'admin.platform',
  'admin-analytics': 'admin.analytics',
  'admin-products': 'admin.products',
  'admin-categories': 'admin.categories',
  'admin-brands': 'admin.brands',
  'admin-attributes': 'admin.attributes',
  'admin-orders': 'admin.orders',
  'admin-order-detail': 'orderDetailPage.title',
  'admin-inventory': 'admin.inventory',
  'admin-shipping': 'admin.shipping',
  'admin-returns': 'admin.returns',
  'admin-promotions': 'admin.promotions',
  'admin-campaigns': 'admin.campaigns',
  'admin-giftcards': 'admin.giftCards',
  'admin-reviews': 'admin.reviews',
  'admin-payments': 'admin.payments',
  'admin-payouts': 'admin.payouts',
  'admin-finance': 'admin.finance',
  'admin-pricing': 'admin.pricing',
  'admin-procurement': 'admin.procurement',
  'admin-fraud': 'admin.fraud',
  'admin-notifications': 'admin.notifications',
  'admin-team': 'admin.team',
  'admin-settings': 'admin.settings',
  'not-found': 'common.pageNotFound'
};
router.afterEach((to) => {
  const key = TITLE_KEYS[to.name];
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
  return true;
});

export default router;
