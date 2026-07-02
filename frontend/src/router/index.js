import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

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
      { path: 'shipping', name: 'admin-shipping', component: () => import('@/pages/admin/Shipping.vue') },
      { path: 'returns', name: 'admin-returns', component: () => import('@/pages/admin/Returns.vue') },
      { path: 'payouts', name: 'admin-payouts', component: () => import('@/pages/admin/Payouts.vue') },
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

// Dynamic document titles.
const TITLES = {
  home: 'Home',
  stores: 'Stores',
  store: 'Store',
  products: 'Shop',
  product: 'Product',
  cart: 'Cart',
  checkout: 'Checkout',
  'order-confirmation': 'Order Confirmation',
  account: 'My Account',
  login: 'Sign in',
  register: 'Register',
  'forgot-password': 'Forgot password',
  'reset-password': 'Reset password',
  'verify-email': 'Verify email',
  'admin-dashboard': 'Dashboard',
  'admin-platform': 'Platform',
  'admin-products': 'Products',
  'admin-categories': 'Categories',
  'admin-brands': 'Brands',
  'admin-orders': 'Orders',
  'admin-order-detail': 'Order',
  'admin-inventory': 'Inventory',
  'admin-shipping': 'Shipping',
  'admin-returns': 'Returns',
  'admin-promotions': 'Promotions',
  'admin-reviews': 'Reviews',
  'admin-payouts': 'Payouts',
  'admin-notifications': 'Notifications',
  'admin-team': 'Team',
  'admin-settings': 'Settings',
  'not-found': 'Not found'
};
router.afterEach((to) => {
  const t = TITLES[to.name];
  document.title = t ? `${t} · Electro` : 'Electro Marketplace';
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
