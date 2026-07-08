<script setup>
import { ref, computed, onMounted, watch } from 'vue';
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
  LifeBuoy,
  Truck,
  Tag,
  LayoutGrid,
  Flame
} from 'lucide-vue-next';
import { useAuthStore } from '@/stores/auth';
import { useCartStore } from '@/stores/cart';
import { storefront } from '@/services/storefront';
import { useI18n } from '@/i18n';
import { useTheme } from '@/theme';
import { catName } from '@/utils/i18nData';
import CartFlyout from '@/components/CartFlyout.vue';
import SearchBox from '@/components/SearchBox.vue';

const router = useRouter();
const auth = useAuthStore();
const cart = useCartStore();
const { t } = useI18n();
const { theme } = useTheme();

// Support contact points (each shortcut has a distinct function).
const SUPPORT_PHONE = '+0121234567890';
const SUPPORT_EMAIL = 'support@q-shop.com';

const categories = ref([]);
const catOpen = ref(false);
const accountOpen = ref(false);
const mobileNav = ref(false);
const searchOpen = ref(false);

const nav = [
  { key: 'home', to: { name: 'home' } },
  { key: 'shop', to: { name: 'products' } },
  { key: 'stores', to: { name: 'stores' } },
  { key: 'deals', to: { name: 'products', query: { on_sale: 1 } } }
];

const cartCount = computed(() => cart.count);
const cartTotal = computed(() => cart.cart?.total || '0.00');
const currency = computed(() => cart.shopStore?.currency || 'EGP');

// Real category data surfaced in the nav bar.
const sortedCats = computed(() =>
  [...categories.value].sort((a, b) => (b.product_count || 0) - (a.product_count || 0))
);
const topCats = computed(() => sortedCats.value.slice(0, 5));
const totalProducts = computed(() => categories.value.reduce((n, c) => n + (c.product_count || 0), 0));

const goCategory = (name) => {
  catOpen.value = false;
  mobileNav.value = false;
  router.push({ name: 'products', query: { category: name } });
};

// Close all menus whenever the route changes.
watch(
  () => router.currentRoute.value.fullPath,
  () => {
    mobileNav.value = false;
    catOpen.value = false;
    accountOpen.value = false;
    searchOpen.value = false;
  }
);

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
    <!-- Top thin bar: support shortcuts + account (desktop only; on mobile these
         live in the slide-down menu, so the mobile top stays clean). -->
    <div class="hidden border-b border-slate-200 lg:block dark:border-slate-800">
      <div class="container flex h-11 items-center gap-4 text-sm">
        <div class="hidden items-center gap-4 text-muted lg:flex">
          <RouterLink :to="{ name: 'support' }" class="flex items-center gap-1.5 hover:text-primary-600"><LifeBuoy class="h-4 w-4" /> {{ t('nav.help') }}</RouterLink>
          <a :href="`mailto:${SUPPORT_EMAIL}`" class="flex items-center gap-1.5 hover:text-primary-600"><Mail class="h-4 w-4" /> {{ t('nav.contact') }}</a>
          <RouterLink :to="{ name: 'account' }" class="flex items-center gap-1.5 hover:text-primary-600"><Truck class="h-4 w-4" /> {{ t('nav.trackOrder') }}</RouterLink>
        </div>
        <div class="ms-auto flex items-center gap-3 text-muted">
          <div class="hidden items-center gap-1 lg:flex">
            <span class="text-ink">{{ t('nav.callUs') }}:</span>
            <a :href="`tel:${SUPPORT_PHONE}`" class="hover:text-primary-600" dir="ltr">(+012) 1234 567890</a>
          </div>
          <div class="relative">
            <button class="flex items-center gap-1 hover:text-primary-600" @click="accountOpen = !accountOpen">
              <User class="h-4 w-4" /> <span class="hidden sm:inline">{{ auth.isAuthenticated ? auth.displayName : t('nav.myAccount') }}</span>
              <ChevronDown class="h-3 w-3" />
            </button>
            <div
              v-if="accountOpen"
              class="absolute end-0 z-[100] mt-2 w-52 overflow-hidden rounded-lg border border-slate-200 bg-white py-1 shadow-pop dark:border-slate-700 dark:bg-slate-800"
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

    <!-- Main header: logo + search + actions. Sticky on mobile so the logo,
         search, cart and menu stay reachable while scrolling. -->
    <div class="sticky top-0 z-40 border-b border-slate-100 bg-white lg:static dark:border-slate-800 dark:bg-slate-900">
      <div class="container flex items-center gap-3 py-3 lg:gap-4 lg:py-4">
        <!-- Mobile menu toggle -->
        <button
          class="grid h-11 w-11 shrink-0 place-items-center rounded-full border border-slate-200 text-ink transition hover:border-primary-500 hover:text-primary-600 lg:hidden dark:border-slate-700"
          :title="t('nav.menu')"
          @click="mobileNav = !mobileNav"
        >
          <component :is="mobileNav ? X : Menu" class="h-5 w-5" />
        </button>
        <RouterLink :to="{ name: 'home' }" class="flex shrink-0 items-center">
          <img :src="theme === 'dark' ? '/brand/dark-logo.png' : '/brand/qtech-logo.png'" alt="q-shop" class="h-9 w-auto lg:h-12" />
        </RouterLink>

        <!-- Desktop interactive search -->
        <div class="hidden lg:block lg:flex-1 lg:max-w-2xl">
          <SearchBox />
        </div>

        <div class="ms-auto flex items-center gap-2 lg:gap-3">
          <!-- Mobile: tap the icon to open the search -->
          <button
            class="grid h-11 w-11 place-items-center rounded-full border border-slate-200 text-ink transition hover:border-primary-500 hover:text-primary-600 lg:hidden dark:border-slate-700"
            :title="t('common.search')"
            @click="searchOpen = !searchOpen"
          >
            <component :is="searchOpen ? X : Search" class="h-4 w-4" />
          </button>
          <RouterLink :to="{ name: 'products' }" class="hidden h-11 w-11 place-items-center rounded-full border border-slate-200 text-ink hover:border-primary-500 hover:text-primary-600 sm:grid dark:border-slate-700" :title="t('nav.compare')">
            <Shuffle class="h-4 w-4" />
          </RouterLink>
          <RouterLink :to="{ name: 'account' }" class="grid h-11 w-11 place-items-center rounded-full border border-slate-200 text-ink hover:border-primary-500 hover:text-primary-600 dark:border-slate-700" :title="t('nav.wishlist')">
            <Heart class="h-4 w-4" />
          </RouterLink>
          <div class="relative">
            <button class="flex items-center gap-2 text-ink hover:text-primary-600" :title="t('nav.myCart')" @click="cart.openDrawer()">
              <span class="relative grid h-11 w-11 place-items-center rounded-full border border-slate-200 dark:border-slate-700">
                <ShoppingCart class="h-4 w-4" />
                <span v-if="cartCount" class="absolute -end-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-secondary-500 px-1 text-[11px] font-bold text-white">{{ cartCount }}</span>
              </span>
              <span class="whitespace-nowrap text-sm font-semibold sm:text-base">{{ cartTotal }} {{ currency }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile search bar (opens on tap) -->
      <div v-if="searchOpen" class="container pb-3 lg:hidden">
        <SearchBox autofocus @navigate="searchOpen = false" />
      </div>

      <!-- Mobile slide-down menu (clean white panel under the sticky header) -->
      <div v-if="mobileNav" class="max-h-[75vh] overflow-y-auto border-t border-slate-100 lg:hidden dark:border-slate-800">
        <div class="container space-y-1 py-3">
          <RouterLink v-for="item in nav" :key="item.key" :to="item.to" class="flex items-center gap-2 rounded-lg px-3 py-2.5 font-heading font-medium text-ink hover:bg-primary-50 hover:text-primary-700 dark:text-white dark:hover:bg-slate-800" @click="mobileNav = false">
            <Flame v-if="item.key === 'deals'" class="h-4 w-4 text-secondary-500" />{{ t('nav.' + item.key) }}
          </RouterLink>

          <!-- Account -->
          <div class="mt-1 space-y-1 border-t border-slate-100 pt-2 dark:border-slate-800">
            <template v-if="auth.isAuthenticated">
              <RouterLink :to="{ name: 'account' }" class="flex items-center gap-2 rounded-lg px-3 py-2.5 font-medium text-ink hover:bg-primary-50 dark:text-white dark:hover:bg-slate-800" @click="mobileNav = false"><User class="h-4 w-4" /> {{ t('nav.myAccount') }}</RouterLink>
              <RouterLink :to="{ name: 'admin-dashboard' }" class="flex items-center gap-2 rounded-lg px-3 py-2.5 font-medium text-ink hover:bg-primary-50 dark:text-white dark:hover:bg-slate-800" @click="mobileNav = false"><LayoutDashboard class="h-4 w-4" /> {{ t('nav.dashboard') }}</RouterLink>
              <button class="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 font-medium text-secondary-500 hover:bg-secondary-50 dark:hover:bg-slate-800" @click="logout"><LogOut class="h-4 w-4" /> {{ t('nav.logout') }}</button>
            </template>
            <template v-else>
              <RouterLink :to="{ name: 'login' }" class="flex items-center gap-2 rounded-lg px-3 py-2.5 font-medium text-ink hover:bg-primary-50 dark:text-white dark:hover:bg-slate-800" @click="mobileNav = false"><User class="h-4 w-4" /> {{ t('nav.login') }}</RouterLink>
              <RouterLink :to="{ name: 'register' }" class="flex items-center gap-2 rounded-lg px-3 py-2.5 font-medium text-primary-700 hover:bg-primary-50 dark:text-primary-300 dark:hover:bg-slate-800" @click="mobileNav = false">{{ t('nav.register') }}</RouterLink>
            </template>
            <RouterLink :to="{ name: 'support' }" class="flex items-center gap-2 rounded-lg px-3 py-2.5 font-medium text-ink hover:bg-primary-50 dark:text-white dark:hover:bg-slate-800" @click="mobileNav = false"><Phone class="h-4 w-4" /> {{ t('nav.support') }}</RouterLink>
          </div>

          <!-- Categories -->
          <div v-if="categories.length" class="mt-1 border-t border-slate-100 pt-2 dark:border-slate-800">
            <p class="px-3 pb-1 text-xs font-semibold uppercase tracking-wide text-muted">{{ t('nav.categories') }}</p>
            <button v-for="c in categories" :key="c.name" class="flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm text-ink hover:bg-primary-50 hover:text-primary-700 dark:text-slate-200 dark:hover:bg-slate-800" @click="goCategory(c.name)">
              <span class="truncate">{{ catName(c) }}</span>
              <span class="text-xs text-muted">({{ c.product_count }})</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Orange category nav bar (desktop only; sticky, follows on scroll) -->
    <div class="sticky top-0 z-30 hidden bg-primary-600 shadow-md lg:block">
      <div class="container flex items-stretch">
        <!-- All categories — mega menu with real data -->
        <div class="relative hidden w-60 shrink-0 lg:block" @mouseleave="catOpen = false">
          <button class="flex h-full w-full items-center gap-2 py-3.5 text-lg font-medium text-white" @click="catOpen = !catOpen" @mouseenter="catOpen = true">
            <Menu class="h-5 w-5" /> {{ t('nav.allCategories') }}
            <ChevronDown class="ms-auto h-4 w-4 transition" :class="catOpen ? 'rotate-180' : ''" />
          </button>
          <div v-if="catOpen" class="absolute start-0 top-full z-[100] w-[560px] overflow-hidden rounded-b-xl border border-slate-200 bg-white shadow-pop dark:border-slate-700 dark:bg-slate-800">
            <div class="flex items-center justify-between border-b border-slate-100 px-4 py-2.5 dark:border-slate-700">
              <span class="flex items-center gap-2 text-sm font-bold text-ink"><LayoutGrid class="h-4 w-4 text-primary-600" /> {{ t('nav.allCategories') }}</span>
              <span class="text-xs text-muted">{{ totalProducts }} {{ t('home.items') }}</span>
            </div>
            <div class="grid grid-cols-2 gap-0.5 p-2">
              <button
                v-for="c in sortedCats"
                :key="c.name"
                class="group flex items-center gap-2 rounded-lg px-3 py-2 text-start text-sm text-ink transition hover:bg-primary-50 dark:hover:bg-slate-700"
                @click="goCategory(c.name)"
              >
                <span class="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-primary-50 text-primary-600 transition group-hover:bg-primary-600 group-hover:text-white dark:bg-primary-600/10"><Tag class="h-3.5 w-3.5" /></span>
                <span class="min-w-0 flex-1 truncate">{{ catName(c) }}</span>
                <span class="text-xs text-muted">{{ c.product_count }}</span>
              </button>
              <p v-if="!categories.length" class="col-span-2 px-4 py-3 text-sm text-muted">{{ t('categoriesPage.noCategories') }}</p>
            </div>
            <RouterLink :to="{ name: 'products' }" class="block border-t border-slate-100 px-4 py-2.5 text-center text-sm font-medium text-primary-600 hover:bg-lightbg dark:border-slate-700" @click="catOpen = false">{{ t('home.viewAllProducts') }}</RouterLink>
          </div>
        </div>

        <!-- Horizontal nav: core links + real top categories inline -->
        <nav class="hidden flex-1 items-center lg:flex">
          <RouterLink
            v-for="item in nav"
            :key="item.key"
            :to="item.to"
            class="whitespace-nowrap px-3.5 py-3.5 font-heading text-[16px] font-medium text-white/90 transition hover:text-white"
            active-class="text-white"
          >
            <Flame v-if="item.key === 'deals'" class="me-1 inline h-4 w-4 text-secondary-300" />{{ t('nav.' + item.key) }}
          </RouterLink>
          <span v-if="topCats.length" class="mx-1 h-5 w-px bg-white/25"></span>
          <button
            v-for="c in topCats"
            :key="c.name"
            class="whitespace-nowrap px-3 py-3.5 font-heading text-[15px] font-medium text-white/75 transition hover:text-white"
            @click="goCategory(c.name)"
          >
            {{ catName(c) }}
          </button>
          <RouterLink :to="{ name: 'products', query: { on_sale: 1 } }" class="btn btn-secondary ms-auto my-2 shrink-0 rounded-full"><Flame class="h-4 w-4" /> {{ t('nav.todayDeals') }}</RouterLink>
        </nav>
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
    <footer class="bg-ink text-slate-300">
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
            <li><RouterLink :to="{ name: 'support' }" class="text-slate-300 hover:text-primary-500 hover:tracking-wide">{{ t('nav.support') }}</RouterLink></li>
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

    <!-- Global slide-in cart -->
    <CartFlyout />
  </div>
</template>
