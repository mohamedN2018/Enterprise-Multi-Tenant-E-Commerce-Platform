<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  Phone,
  ChevronDown,
  Search,
  Shuffle,
  Heart,
  ShoppingCart,
  User,
  LogOut,
  LayoutDashboard,
  Menu,
  X,
  Facebook,
  Twitter,
  Instagram,
  Linkedin,
  Mail,
  MapPin
} from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { useCartStore } from '@/stores/cart';
import { storefront } from '@/services/storefront';

const router = useRouter();
const auth = useAuthStore();
const cart = useCartStore();

const term = ref('');
const cat = ref('');
const categories = ref([]);
const catOpen = ref(false);
const accountOpen = ref(false);
const mobileNav = ref(false);

const nav = [
  { label: 'Home', to: { name: 'home' } },
  { label: 'Shop', to: { name: 'products' } },
  { label: 'Stores', to: { name: 'stores' } }
];

const cartCount = computed(() => cart.count);
const cartTotal = computed(() => cart.cart?.total || '0.00');
const currency = computed(() => cart.shopStore?.currency || 'USD');

const search = () => {
  const q = {};
  if (term.value.trim()) q.search = term.value.trim();
  if (cat.value) q.category = cat.value;
  router.push({ name: 'products', query: q });
  mobileNav.value = false;
};

const goCategory = (name) => {
  catOpen.value = false;
  router.push({ name: 'products', query: { category: name } });
};

const logout = async () => {
  await auth.logout();
  accountOpen.value = false;
  router.push({ name: 'home' });
};

onMounted(async () => {
  if (auth.isAuthenticated) cart.refreshCart();
  try {
    const res = await storefront.categories();
    categories.value = res.data || [];
  } catch {
    categories.value = [];
  }
});
</script>

<template>
  <div class="flex min-h-screen flex-col bg-white text-ink">
    <!-- Top thin bar -->
    <div class="hidden border-b border-slate-200 lg:block">
      <div class="container flex h-11 items-center justify-between text-sm">
        <div class="flex items-center gap-2 text-muted">
          <a href="#" class="hover:text-primary-600">Help</a><span>/</span>
          <a href="#" class="hover:text-primary-600">Support</a><span>/</span>
          <RouterLink :to="{ name: 'stores' }" class="hover:text-primary-600">Contact</RouterLink>
        </div>
        <div class="flex items-center gap-1 text-muted">
          <span class="text-ink">Call Us:</span>
          <a href="tel:+01212345678" class="hover:text-primary-600">(+012) 1234 567890</a>
        </div>
        <div class="flex items-center gap-4 text-muted">
          <span>{{ currency }}</span>
          <span>English</span>
          <div class="relative">
            <button class="flex items-center gap-1 hover:text-primary-600" @click="accountOpen = !accountOpen">
              <User class="h-4 w-4" /> {{ auth.isAuthenticated ? auth.displayName : 'My Account' }}
              <ChevronDown class="h-3 w-3" />
            </button>
            <div
              v-if="accountOpen"
              class="absolute right-0 z-40 mt-2 w-52 overflow-hidden rounded-lg border border-slate-200 bg-white py-1 shadow-pop"
              @click="accountOpen = false"
            >
              <template v-if="auth.isAuthenticated">
                <RouterLink :to="{ name: 'account' }" class="dropdown-item"><User class="h-4 w-4" /> My Account</RouterLink>
                <RouterLink :to="{ name: 'admin-dashboard' }" class="dropdown-item"><LayoutDashboard class="h-4 w-4" /> Dashboard</RouterLink>
                <RouterLink :to="{ name: 'cart' }" class="dropdown-item"><ShoppingCart class="h-4 w-4" /> My Cart</RouterLink>
                <button class="dropdown-item w-full text-secondary-500 hover:bg-secondary-500 hover:text-white" @click="logout">
                  <LogOut class="h-4 w-4" /> Log Out
                </button>
              </template>
              <template v-else>
                <RouterLink :to="{ name: 'login' }" class="dropdown-item">Login</RouterLink>
                <RouterLink :to="{ name: 'register' }" class="dropdown-item">Register</RouterLink>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main header: logo + search + actions -->
    <div class="border-b border-slate-100">
      <div class="container flex flex-wrap items-center gap-4 py-4">
        <RouterLink :to="{ name: 'home' }" class="flex items-center">
          <img src="/brand/qtech-logo.png" alt="q-shop" class="h-12 w-auto" />
        </RouterLink>

        <form class="order-3 flex w-full flex-1 lg:order-none lg:w-auto" @submit.prevent="search">
          <div class="flex w-full items-center rounded-full border border-slate-200 pl-4">
            <input v-model="term" type="text" placeholder="Search Looking For?" class="w-full border-0 bg-transparent py-2.5 text-sm focus:outline-none" />
            <select v-model="cat" class="hidden border-l border-slate-200 bg-transparent px-3 py-2.5 text-sm text-ink focus:outline-none sm:block" style="width: 160px">
              <option value="">All Category</option>
              <option v-for="c in categories" :key="c.name" :value="c.name">{{ c.name }}</option>
            </select>
            <button type="submit" class="btn btn-primary rounded-full px-6"><Search class="h-4 w-4" /></button>
          </div>
        </form>

        <div class="ml-auto flex items-center gap-3">
          <RouterLink :to="{ name: 'products' }" class="grid h-11 w-11 place-items-center rounded-full border border-slate-200 text-ink hover:border-primary-500 hover:text-primary-600" title="Compare">
            <Shuffle class="h-4 w-4" />
          </RouterLink>
          <RouterLink :to="{ name: 'account' }" class="grid h-11 w-11 place-items-center rounded-full border border-slate-200 text-ink hover:border-primary-500 hover:text-primary-600" title="Wishlist">
            <Heart class="h-4 w-4" />
          </RouterLink>
          <RouterLink :to="{ name: 'cart' }" class="flex items-center gap-2 text-ink hover:text-primary-600" title="Cart">
            <span class="relative grid h-11 w-11 place-items-center rounded-full border border-slate-200">
              <ShoppingCart class="h-4 w-4" />
              <span v-if="cartCount" class="absolute -right-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-secondary-500 px-1 text-[11px] font-bold text-white">{{ cartCount }}</span>
            </span>
            <span class="hidden font-semibold sm:inline">{{ cartTotal }} {{ currency }}</span>
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- Orange category nav bar -->
    <div class="bg-primary-600">
      <div class="container flex items-stretch">
        <!-- All categories -->
        <div class="relative hidden w-64 shrink-0 lg:block">
          <button class="flex h-full w-full items-center gap-2 py-3.5 text-lg font-medium text-white" @click="catOpen = !catOpen">
            <Menu class="h-5 w-5" /> All Categories <ChevronDown class="ml-auto h-4 w-4" />
          </button>
          <div v-if="catOpen" class="absolute left-0 top-full z-40 w-64 rounded-b-lg bg-lightbg py-1 shadow-pop">
            <button
              v-for="c in categories"
              :key="c.name"
              class="flex w-full items-center justify-between border-b border-black/5 px-4 py-2.5 text-sm text-ink transition last:border-0 hover:bg-primary-600 hover:text-white"
              @click="goCategory(c.name)"
            >
              <span>{{ c.name }}</span>
              <span class="text-xs opacity-70">({{ c.product_count }})</span>
            </button>
            <p v-if="!categories.length" class="px-4 py-3 text-sm text-muted">No categories</p>
          </div>
        </div>

        <!-- Horizontal nav -->
        <nav class="hidden flex-1 items-center lg:flex">
          <RouterLink
            v-for="item in nav"
            :key="item.label"
            :to="item.to"
            class="px-4 py-3.5 font-heading text-[17px] font-medium text-white/90 transition hover:text-white"
            active-class="text-white"
          >
            {{ item.label }}
          </RouterLink>
          <RouterLink :to="{ name: 'account' }" class="px-4 py-3.5 font-heading text-[17px] font-medium text-white/90 transition hover:text-white">Account</RouterLink>
          <a href="tel:+01234567890" class="btn btn-secondary ml-auto my-2 rounded-full"><Phone class="h-4 w-4" /> +0123 456 7890</a>
        </nav>

        <!-- Mobile nav toggle -->
        <button class="ml-auto flex items-center gap-2 py-3 text-white lg:hidden" @click="mobileNav = !mobileNav">
          <component :is="mobileNav ? X : Menu" class="h-6 w-6" /> Menu
        </button>
      </div>

      <!-- Mobile nav -->
      <div v-if="mobileNav" class="border-t border-white/10 bg-primary-600 lg:hidden">
        <div class="container py-2">
          <RouterLink v-for="item in nav" :key="item.label" :to="item.to" class="block py-2 font-medium text-white" @click="mobileNav = false">{{ item.label }}</RouterLink>
          <RouterLink :to="{ name: 'account' }" class="block py-2 font-medium text-white" @click="mobileNav = false">Account</RouterLink>
          <RouterLink v-if="!auth.isAuthenticated" :to="{ name: 'login' }" class="block py-2 font-medium text-white" @click="mobileNav = false">Login</RouterLink>
          <p class="mt-2 border-t border-white/10 pt-2 text-xs font-semibold uppercase text-white/70">Categories</p>
          <button v-for="c in categories" :key="c.name" class="block w-full py-1.5 text-left text-sm text-white/90" @click="goCategory(c.name)">{{ c.name }}</button>
        </div>
      </div>
    </div>

    <!-- Content -->
    <main class="flex-1">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>

    <!-- Footer -->
    <footer class="mt-16 bg-ink text-slate-300">
      <div class="container grid gap-8 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <img src="/brand/dark-logo.png" alt="q-shop" class="mb-4 h-16 w-auto" />
          <p class="text-sm leading-7">q-shop — your multi-vendor marketplace for electronics, fashion, home and more, curated from verified independent stores.</p>
          <div class="mt-4 flex gap-2">
            <a href="#" class="grid h-9 w-9 place-items-center rounded-full border border-white/20 hover:bg-primary-600 hover:text-white"><Facebook class="h-4 w-4" /></a>
            <a href="#" class="grid h-9 w-9 place-items-center rounded-full border border-white/20 hover:bg-primary-600 hover:text-white"><Twitter class="h-4 w-4" /></a>
            <a href="#" class="grid h-9 w-9 place-items-center rounded-full border border-white/20 hover:bg-primary-600 hover:text-white"><Instagram class="h-4 w-4" /></a>
            <a href="#" class="grid h-9 w-9 place-items-center rounded-full border border-white/20 hover:bg-primary-600 hover:text-white"><Linkedin class="h-4 w-4" /></a>
          </div>
        </div>
        <div>
          <h4 class="mb-4 font-heading text-lg font-semibold text-white">Account</h4>
          <ul class="space-y-2 text-sm">
            <li><RouterLink :to="{ name: 'account' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">My Account</RouterLink></li>
            <li><RouterLink :to="{ name: 'account' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">Order History</RouterLink></li>
            <li><RouterLink :to="{ name: 'account' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">Wishlist</RouterLink></li>
            <li><RouterLink :to="{ name: 'cart' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">Shopping Cart</RouterLink></li>
          </ul>
        </div>
        <div>
          <h4 class="mb-4 font-heading text-lg font-semibold text-white">Quick Links</h4>
          <ul class="space-y-2 text-sm">
            <li><RouterLink :to="{ name: 'products' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">Shop</RouterLink></li>
            <li><RouterLink :to="{ name: 'stores' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">Stores</RouterLink></li>
            <li><RouterLink :to="{ name: 'admin-dashboard' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">Sell on q-shop</RouterLink></li>
            <li><RouterLink :to="{ name: 'register' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">Open a Store</RouterLink></li>
          </ul>
        </div>
        <div>
          <h4 class="mb-4 font-heading text-lg font-semibold text-white">Newsletter</h4>
          <p class="mb-3 text-sm">Subscribe for deals and new arrivals.</p>
          <form class="flex overflow-hidden rounded-full bg-white" @submit.prevent>
            <input type="email" placeholder="Your email" class="w-full border-0 bg-transparent px-4 py-2.5 text-sm text-ink focus:outline-none" />
            <button class="btn btn-primary rounded-none px-5"><Mail class="h-4 w-4" /></button>
          </form>
          <p class="mt-4 flex items-center gap-2 text-sm"><MapPin class="h-4 w-4 text-primary-500" /> 123 Market Street, Cairo</p>
        </div>
      </div>
      <div class="bg-primary-600">
        <div class="container flex flex-col items-center justify-between gap-2 py-4 text-sm text-white sm:flex-row">
          <p>© 2026 q-shop Marketplace. All rights reserved.</p>
          <p class="opacity-90">Built on an enterprise multi-tenant platform.</p>
        </div>
      </div>
    </footer>
  </div>
</template>
