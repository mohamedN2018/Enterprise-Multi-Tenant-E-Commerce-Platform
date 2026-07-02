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
  MapPin,
  Sun,
  Moon,
  Languages
} from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { useCartStore } from '@/stores/cart';
import { storefront } from '@/services/storefront';
import { useI18n } from '@/i18n';
import { useTheme } from '@/theme';

const router = useRouter();
const auth = useAuthStore();
const cart = useCartStore();
const { t, locale, setLocale } = useI18n();
const { theme, toggleTheme } = useTheme();

const term = ref('');
const cat = ref('');
const categories = ref([]);
const catOpen = ref(false);
const accountOpen = ref(false);
const cartOpen = ref(false);
const mobileNav = ref(false);

const cartItems = computed(() => cart.cart?.items || []);

const nav = [
  { key: 'home', to: { name: 'home' } },
  { key: 'shop', to: { name: 'products' } },
  { key: 'stores', to: { name: 'stores' } }
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
          <a href="#" class="hover:text-primary-600">{{ t('nav.help') }}</a><span>/</span>
          <a href="#" class="hover:text-primary-600">{{ t('nav.support') }}</a><span>/</span>
          <RouterLink :to="{ name: 'stores' }" class="hover:text-primary-600">{{ t('nav.contact') }}</RouterLink>
        </div>
        <div class="flex items-center gap-1 text-muted">
          <span class="text-ink">{{ t('nav.callUs') }}:</span>
          <a href="tel:+01212345678" class="hover:text-primary-600" dir="ltr">(+012) 1234 567890</a>
        </div>
        <div class="flex items-center gap-3 text-muted">
          <button class="flex items-center gap-1 hover:text-primary-600" @click="setLocale(locale === 'ar' ? 'en' : 'ar')">
            <Languages class="h-4 w-4" /> {{ locale === 'ar' ? 'English' : 'العربية' }}
          </button>
          <button class="hover:text-primary-600" :title="theme === 'dark' ? t('account.light') : t('account.dark')" @click="toggleTheme()">
            <component :is="theme === 'dark' ? Sun : Moon" class="h-4 w-4" />
          </button>
          <div class="relative">
            <button class="flex items-center gap-1 hover:text-primary-600" @click="accountOpen = !accountOpen">
              <User class="h-4 w-4" /> {{ auth.isAuthenticated ? auth.displayName : t('nav.myAccount') }}
              <ChevronDown class="h-3 w-3" />
            </button>
            <div
              v-if="accountOpen"
              class="absolute right-0 z-40 mt-2 w-52 overflow-hidden rounded-lg border border-slate-200 bg-white py-1 shadow-pop"
              @click="accountOpen = false"
            >
              <template v-if="auth.isAuthenticated">
                <RouterLink :to="{ name: 'account' }" class="dropdown-item"><User class="h-4 w-4" /> {{ t('nav.myAccount') }}</RouterLink>
                <RouterLink :to="{ name: 'admin-dashboard' }" class="dropdown-item"><LayoutDashboard class="h-4 w-4" /> {{ t('nav.dashboard') }}</RouterLink>
                <RouterLink :to="{ name: 'cart' }" class="dropdown-item"><ShoppingCart class="h-4 w-4" /> {{ t('nav.myCart') }}</RouterLink>
                <button class="dropdown-item w-full text-secondary-500 hover:bg-secondary-500 hover:text-white" @click="logout">
                  <LogOut class="h-4 w-4" /> {{ t('nav.logout') }}
                </button>
              </template>
              <template v-else>
                <RouterLink :to="{ name: 'login' }" class="dropdown-item">{{ t('nav.login') }}</RouterLink>
                <RouterLink :to="{ name: 'register' }" class="dropdown-item">{{ t('nav.register') }}</RouterLink>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Sticky header: main header + category nav follow on scroll -->
    <div class="sticky top-0 z-40 bg-white shadow-sm dark:bg-slate-900">
    <!-- Main header: logo + search + actions -->
    <div class="border-b border-slate-100">
      <div class="container flex flex-wrap items-center gap-3 py-3 lg:gap-4 lg:py-4">
        <RouterLink :to="{ name: 'home' }" class="flex shrink-0 items-center">
          <img src="/brand/qtech-logo.png" alt="q-shop" class="h-9 w-auto lg:h-12" />
        </RouterLink>

        <form class="order-3 flex w-full flex-1 lg:order-none lg:w-auto" @submit.prevent="search">
          <div class="flex w-full items-center rounded-full border border-slate-200 pl-4">
            <input v-model="term" type="text" :placeholder="t('nav.searchPlaceholder')" class="w-full border-0 bg-transparent py-2.5 text-sm focus:outline-none" />
            <select v-model="cat" class="hidden border-l border-slate-200 bg-transparent px-3 py-2.5 text-sm text-ink focus:outline-none sm:block" style="width: 160px">
              <option value="">{{ t('common.all') }}</option>
              <option v-for="c in categories" :key="c.name" :value="c.name">{{ c.name }}</option>
            </select>
            <button type="submit" class="btn btn-primary rounded-full px-6"><Search class="h-4 w-4" /></button>
          </div>
        </form>

        <div class="ms-auto flex items-center gap-2 lg:gap-3">
          <RouterLink :to="{ name: 'products' }" class="hidden h-11 w-11 place-items-center rounded-full border border-slate-200 text-ink hover:border-primary-500 hover:text-primary-600 sm:grid" title="Compare">
            <Shuffle class="h-4 w-4" />
          </RouterLink>
          <RouterLink :to="{ name: 'account' }" class="grid h-11 w-11 place-items-center rounded-full border border-slate-200 text-ink hover:border-primary-500 hover:text-primary-600" title="Wishlist">
            <Heart class="h-4 w-4" />
          </RouterLink>
          <div class="relative">
            <button class="flex items-center gap-2 text-ink hover:text-primary-600" title="Cart" @click="cartOpen = !cartOpen">
              <span class="relative grid h-11 w-11 place-items-center rounded-full border border-slate-200">
                <ShoppingCart class="h-4 w-4" />
                <span v-if="cartCount" class="absolute -right-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-secondary-500 px-1 text-[11px] font-bold text-white">{{ cartCount }}</span>
              </span>
              <span class="hidden font-semibold sm:inline">{{ cartTotal }} {{ currency }}</span>
            </button>
            <div v-if="cartOpen" class="fixed inset-0 z-30" @click="cartOpen = false"></div>
            <div v-if="cartOpen" class="absolute right-0 z-40 mt-2 w-80 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-pop">
              <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
                <p class="font-heading font-semibold text-ink">{{ t('nav.yourCart') }}</p>
                <span class="text-xs text-muted">{{ cartCount }} {{ t('common.items') }}</span>
              </div>
              <div class="max-h-72 overflow-y-auto">
                <template v-if="cartItems.length">
                  <div v-for="it in cartItems.slice(0, 5)" :key="it.id" class="flex items-center justify-between gap-3 border-b border-slate-50 px-4 py-2.5 text-sm last:border-0">
                    <div class="min-w-0"><p class="clamp-1 font-medium text-ink">{{ it.product_name }}</p><p class="text-xs text-muted">× {{ it.quantity }}</p></div>
                    <span class="shrink-0 font-semibold">{{ it.line_total }} {{ currency }}</span>
                  </div>
                  <p v-if="cartItems.length > 5" class="px-4 py-2 text-center text-xs text-muted">+ {{ cartItems.length - 5 }} {{ t('common.more') }}</p>
                </template>
                <p v-else class="px-4 py-8 text-center text-sm text-muted">{{ t('nav.cartEmpty') }}</p>
              </div>
              <div v-if="cartItems.length" class="border-t border-slate-100 px-4 py-3">
                <div class="mb-3 flex items-center justify-between text-sm"><span class="text-muted">{{ t('common.total') }}</span><span class="font-heading text-lg font-bold text-primary-600">{{ cartTotal }} {{ currency }}</span></div>
                <div class="grid grid-cols-2 gap-2">
                  <RouterLink :to="{ name: 'cart' }" class="btn btn-outline btn-sm" @click="cartOpen = false">{{ t('nav.viewCart') }}</RouterLink>
                  <RouterLink :to="{ name: 'checkout' }" class="btn btn-primary btn-sm" @click="cartOpen = false">{{ t('nav.checkout') }}</RouterLink>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Orange category nav bar -->
    <div class="bg-primary-600">
      <div class="container flex items-stretch">
        <!-- All categories -->
        <div class="relative hidden w-64 shrink-0 lg:block">
          <button class="flex h-full w-full items-center gap-2 py-3.5 text-lg font-medium text-white" @click="catOpen = !catOpen">
            <Menu class="h-5 w-5" /> {{ t('nav.allCategories') }} <ChevronDown class="ms-auto h-4 w-4" />
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
            {{ t('nav.' + item.key) }}
          </RouterLink>
          <RouterLink :to="{ name: 'account' }" class="px-4 py-3.5 font-heading text-[17px] font-medium text-white/90 transition hover:text-white">{{ t('nav.account') }}</RouterLink>
          <a href="tel:+01234567890" class="btn btn-secondary ms-auto my-2 rounded-full" dir="ltr"><Phone class="h-4 w-4" /> +0123 456 7890</a>
        </nav>

        <!-- Mobile nav toggle -->
        <button class="ms-auto flex items-center gap-2 py-3 text-white lg:hidden" @click="mobileNav = !mobileNav">
          <component :is="mobileNav ? X : Menu" class="h-6 w-6" /> {{ t('nav.menu') }}
        </button>
      </div>

      <!-- Mobile nav -->
      <div v-if="mobileNav" class="border-t border-white/10 bg-primary-600 lg:hidden">
        <div class="container py-2">
          <RouterLink v-for="item in nav" :key="item.label" :to="item.to" class="block py-2 font-medium text-white" @click="mobileNav = false">{{ t('nav.' + item.key) }}</RouterLink>
          <RouterLink :to="{ name: 'account' }" class="block py-2 font-medium text-white" @click="mobileNav = false">{{ t('nav.account') }}</RouterLink>
          <RouterLink v-if="!auth.isAuthenticated" :to="{ name: 'login' }" class="block py-2 font-medium text-white" @click="mobileNav = false">{{ t('nav.login') }}</RouterLink>
          <p class="mt-2 border-t border-white/10 pt-2 text-xs font-semibold uppercase text-white/70">{{ t('nav.categories') }}</p>
          <button v-for="c in categories" :key="c.name" class="block w-full py-1.5 text-left text-sm text-white/90" @click="goCategory(c.name)">{{ c.name }}</button>
        </div>
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
          <p class="text-sm leading-7">{{ t('footer.about') }}</p>
          <div class="mt-4 flex gap-2">
            <a href="#" class="grid h-9 w-9 place-items-center rounded-full border border-white/20 hover:bg-primary-600 hover:text-white"><Facebook class="h-4 w-4" /></a>
            <a href="#" class="grid h-9 w-9 place-items-center rounded-full border border-white/20 hover:bg-primary-600 hover:text-white"><Twitter class="h-4 w-4" /></a>
            <a href="#" class="grid h-9 w-9 place-items-center rounded-full border border-white/20 hover:bg-primary-600 hover:text-white"><Instagram class="h-4 w-4" /></a>
            <a href="#" class="grid h-9 w-9 place-items-center rounded-full border border-white/20 hover:bg-primary-600 hover:text-white"><Linkedin class="h-4 w-4" /></a>
          </div>
        </div>
        <div>
          <h4 class="mb-4 font-heading text-lg font-semibold text-white">{{ t('footer.account') }}</h4>
          <ul class="space-y-2 text-sm">
            <li><RouterLink :to="{ name: 'account' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('footer.myAccount') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'account' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('footer.orderHistory') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'account' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('nav.wishlist') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'cart' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('nav.myCart') }}</RouterLink></li>
          </ul>
        </div>
        <div>
          <h4 class="mb-4 font-heading text-lg font-semibold text-white">{{ t('footer.quickLinks') }}</h4>
          <ul class="space-y-2 text-sm">
            <li><RouterLink :to="{ name: 'products' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('nav.shop') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'stores' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('nav.stores') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'seller-login' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('footer.sellOn') }}</RouterLink></li>
            <li><RouterLink :to="{ name: 'account' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('nav.account') }}</RouterLink></li>
          </ul>
        </div>
        <div>
          <h4 class="mb-4 font-heading text-lg font-semibold text-white">{{ t('footer.newsletter') }}</h4>
          <p class="mb-3 text-sm">{{ t('footer.newsletterMsg') }}</p>
          <form class="flex overflow-hidden rounded-full bg-white" @submit.prevent>
            <input type="email" :placeholder="t('footer.yourEmail')" class="w-full border-0 bg-transparent px-4 py-2.5 text-sm text-ink focus:outline-none" />
            <button class="btn btn-primary rounded-none px-5"><Mail class="h-4 w-4" /></button>
          </form>
          <p class="mt-4 flex items-center gap-2 text-sm"><MapPin class="h-4 w-4 text-primary-500" /> 123 Market Street, Cairo</p>
        </div>
      </div>
      <div class="bg-primary-600">
        <div class="container flex flex-col items-center justify-between gap-2 py-4 text-sm text-white sm:flex-row">
          <p>{{ t('footer.rights') }}</p>
          <p class="opacity-90">{{ t('footer.builtOn') }}</p>
        </div>
      </div>
    </footer>
  </div>
</template>
