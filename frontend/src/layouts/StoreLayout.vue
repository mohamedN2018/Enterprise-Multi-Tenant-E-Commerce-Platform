<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  Search,
  ShoppingCart,
  User,
  LayoutDashboard,
  LogOut,
  Menu,
  X,
  Store as StoreIcon
} from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { useCartStore } from '@/stores/cart';

const router = useRouter();
const auth = useAuthStore();
const cart = useCartStore();

const term = ref('');
const menuOpen = ref(false);
const accountOpen = ref(false);

const nav = [
  { label: 'Home', to: { name: 'home' } },
  { label: 'Stores', to: { name: 'stores' } },
  { label: 'Products', to: { name: 'products' } }
];

const cartCount = computed(() => cart.count);

const search = () => {
  const q = term.value.trim();
  router.push({ name: 'products', query: q ? { search: q } : {} });
  menuOpen.value = false;
};

const logout = async () => {
  await auth.logout();
  accountOpen.value = false;
  router.push({ name: 'home' });
};

onMounted(() => {
  if (auth.isAuthenticated) cart.refreshCart();
});
</script>

<template>
  <div class="flex min-h-screen flex-col bg-slate-50 text-ink">
    <header class="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div class="container flex h-16 items-center gap-4">
        <RouterLink :to="{ name: 'home' }" class="flex items-center gap-2 font-bold">
          <span class="grid h-9 w-9 place-items-center rounded-lg bg-primary-600 text-white">
            <StoreIcon class="h-5 w-5" />
          </span>
          <span class="hidden text-lg sm:inline">Marketplace</span>
        </RouterLink>

        <nav class="hidden items-center gap-1 md:flex">
          <RouterLink
            v-for="item in nav"
            :key="item.label"
            :to="item.to"
            class="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-ink"
            active-class="text-primary-700"
          >
            {{ item.label }}
          </RouterLink>
        </nav>

        <form class="relative ml-auto hidden max-w-xs flex-1 md:block" @submit.prevent="search">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            v-model="term"
            type="search"
            placeholder="Search products…"
            class="input pl-9"
          />
        </form>

        <div class="ml-auto flex items-center gap-1 md:ml-0">
          <RouterLink
            :to="{ name: 'cart' }"
            class="relative grid h-10 w-10 place-items-center rounded-lg text-slate-600 hover:bg-slate-100"
            aria-label="Cart"
          >
            <ShoppingCart class="h-5 w-5" />
            <span
              v-if="cartCount"
              class="absolute -right-0.5 -top-0.5 grid h-5 min-w-5 place-items-center rounded-full bg-primary-600 px-1 text-[11px] font-bold text-white"
            >
              {{ cartCount }}
            </span>
          </RouterLink>

          <div v-if="auth.isAuthenticated" class="relative">
            <button
              class="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-slate-100"
              @click="accountOpen = !accountOpen"
            >
              <span class="grid h-8 w-8 place-items-center rounded-full bg-primary-100 text-sm font-semibold text-primary-700">
                {{ auth.displayName.charAt(0).toUpperCase() }}
              </span>
            </button>
            <div
              v-if="accountOpen"
              class="absolute right-0 mt-2 w-52 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-pop"
              @click="accountOpen = false"
            >
              <div class="border-b border-slate-100 px-4 py-2.5">
                <p class="truncate text-sm font-semibold">{{ auth.displayName }}</p>
                <p class="truncate text-xs text-slate-500">{{ auth.user?.email }}</p>
              </div>
              <RouterLink :to="{ name: 'account' }" class="dropdown-item">
                <User class="h-4 w-4" /> My account
              </RouterLink>
              <RouterLink :to="{ name: 'admin-dashboard' }" class="dropdown-item">
                <LayoutDashboard class="h-4 w-4" /> Seller dashboard
              </RouterLink>
              <button class="dropdown-item w-full text-rose-600" @click="logout">
                <LogOut class="h-4 w-4" /> Sign out
              </button>
            </div>
          </div>
          <RouterLink v-else :to="{ name: 'login' }" class="btn btn-primary btn-sm ml-1 hidden sm:inline-flex">
            Sign in
          </RouterLink>

          <button
            class="grid h-10 w-10 place-items-center rounded-lg text-slate-600 hover:bg-slate-100 md:hidden"
            @click="menuOpen = !menuOpen"
          >
            <component :is="menuOpen ? X : Menu" class="h-5 w-5" />
          </button>
        </div>
      </div>

      <div v-if="menuOpen" class="border-t border-slate-100 bg-white px-4 py-3 md:hidden">
        <form class="relative mb-3" @submit.prevent="search">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input v-model="term" type="search" placeholder="Search products…" class="input pl-9" />
        </form>
        <nav class="flex flex-col">
          <RouterLink
            v-for="item in nav"
            :key="item.label"
            :to="item.to"
            class="rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
            @click="menuOpen = false"
          >
            {{ item.label }}
          </RouterLink>
          <RouterLink v-if="!auth.isAuthenticated" :to="{ name: 'login' }" class="btn btn-primary btn-sm mt-2" @click="menuOpen = false">
            Sign in
          </RouterLink>
        </nav>
      </div>
    </header>

    <main class="flex-1">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>

    <footer class="border-t border-slate-200 bg-white">
      <div class="container grid gap-8 py-10 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <div class="mb-3 flex items-center gap-2 font-bold">
            <span class="grid h-8 w-8 place-items-center rounded-lg bg-primary-600 text-white">
              <StoreIcon class="h-4 w-4" />
            </span>
            Marketplace
          </div>
          <p class="text-sm text-slate-500">
            A modern multi-tenant commerce platform for independent stores.
          </p>
        </div>
        <div>
          <h4 class="mb-3 text-sm font-semibold">Shop</h4>
          <ul class="space-y-2 text-sm text-slate-500">
            <li><RouterLink :to="{ name: 'products' }" class="hover:text-primary-600">All products</RouterLink></li>
            <li><RouterLink :to="{ name: 'stores' }" class="hover:text-primary-600">Browse stores</RouterLink></li>
            <li><RouterLink :to="{ name: 'cart' }" class="hover:text-primary-600">Your cart</RouterLink></li>
          </ul>
        </div>
        <div>
          <h4 class="mb-3 text-sm font-semibold">Sell</h4>
          <ul class="space-y-2 text-sm text-slate-500">
            <li><RouterLink :to="{ name: 'admin-dashboard' }" class="hover:text-primary-600">Seller dashboard</RouterLink></li>
            <li><RouterLink :to="{ name: 'register' }" class="hover:text-primary-600">Open a store</RouterLink></li>
          </ul>
        </div>
        <div>
          <h4 class="mb-3 text-sm font-semibold">Account</h4>
          <ul class="space-y-2 text-sm text-slate-500">
            <li><RouterLink :to="{ name: 'account' }" class="hover:text-primary-600">My orders</RouterLink></li>
            <li><RouterLink :to="{ name: 'login' }" class="hover:text-primary-600">Sign in</RouterLink></li>
          </ul>
        </div>
      </div>
      <div class="border-t border-slate-100 py-5 text-center text-xs text-slate-400">
        © 2026 Marketplace. Built on an enterprise multi-tenant platform.
      </div>
    </footer>
  </div>
</template>
