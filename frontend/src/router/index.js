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
      { path: 'register', name: 'register', component: () => import('@/pages/auth/Register.vue') }
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
      { path: 'orders', name: 'admin-orders', component: () => import('@/pages/admin/Orders.vue') },
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
